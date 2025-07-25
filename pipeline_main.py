"""
Clean Medical Imaging Pipeline - Uses proven project creation + Draw_ROI API
Keeps the working project creation method and adds ROI functionality
"""

import matlab.engine
import os
import glob
import pandas as pd
import numpy as np
import scipy.io as sio
from pathlib import Path
from datetime import datetime
import sys
import torch
import torch.nn as nn
import torch.nn.functional as F
from skimage.transform import resize
from scipy.ndimage import label, center_of_mass
import argparse

# UNet3D Model Definition
class UNet3D(nn.Module):
    def __init__(self):
        super(UNet3D, self).__init__()

        def conv_block(in_channels, out_channels):
            return nn.Sequential(
                nn.Conv3d(in_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm3d(out_channels),
                nn.ReLU(inplace=True),
                nn.Conv3d(out_channels, out_channels, kernel_size=3, padding=1),
                nn.BatchNorm3d(out_channels),
                nn.ReLU(inplace=True)
            )

        self.enc1 = conv_block(1, 32)
        self.pool1 = nn.MaxPool3d(2)
        self.enc2 = conv_block(32, 64)
        self.pool2 = nn.MaxPool3d(2)

        self.bottleneck = conv_block(64, 128)

        self.up2 = nn.ConvTranspose3d(128, 64, kernel_size=2, stride=2)
        self.dec2 = conv_block(128, 64)
        self.up1 = nn.ConvTranspose3d(64, 32, kernel_size=2, stride=2)
        self.dec1 = conv_block(64, 32)

        self.final = nn.Conv3d(32, 1, kernel_size=1)

    def forward(self, x):
        enc1 = self.enc1(x)
        enc2 = self.enc2(self.pool1(enc1))
        bottleneck = self.bottleneck(self.pool2(enc2))

        up2 = self.up2(bottleneck)
        dec2 = self.dec2(torch.cat([up2, enc2], dim=1))
        up1 = self.up1(dec2)
        dec1 = self.dec1(torch.cat([up1, enc1], dim=1))

        return torch.sigmoid(self.final(dec1))

# Set device and load model globally
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = None
try:
    # Try multiple possible locations for the model
    model_paths = [
        "./unet3d_kidney.pth",
        "unet3d_kidney.pth", 
        "pipeline/unet3d_kidney.pth",
        os.path.join(os.path.dirname(__file__), "unet3d_kidney.pth"),
        r"c:\Users\ftmen\Documents\v3\pipeline\unet3d_kidney.pth"
    ]
    
    model_loaded = False
    for model_path in model_paths:
        if os.path.exists(model_path):
            model = UNet3D().to(device)
            model.load_state_dict(torch.load(model_path, map_location=device))
            model.eval()
            print(f"✅ UNet3D model loaded successfully from: {model_path}")
            model_loaded = True
            break
    
    if not model_loaded:
        raise FileNotFoundError("UNet3D model file not found in any expected location")
        
except Exception as e:
    print(f"UNet3D model not available: {e}")
    print("   API will use fallback segmentation method")

def make_roi_struct(mask, name):
    """Create ROI structure for MATLAB"""
    identity_matrix = np.eye(4, dtype=np.float64)
    return {
        'data': mask.astype(np.bool_),
        'ImageType': '3DMASK',
        'Name': name,
        'A': identity_matrix.copy(),
        'Anative': identity_matrix.copy(),
        'Aprime': identity_matrix.copy(),
        'isStore': 1,
        'isLoaded': 0,
        'Selected': 0,
        'Visible': 0,
        'box': np.array(mask.shape, dtype=np.float64),
        'pars': np.array([]),
        'FileName': np.array('', dtype='U')
    }

def apply_kidney_roi_to_project(input_file_path, output_file_path=None):
    """
    API wrapper function: Apply kidney ROI detection to BE_AMP in a project file.
    """
    global model, device
    try:
        # Auto-generate output path if not provided
        if output_file_path is None:
            input_dir = os.path.dirname(input_file_path)
            input_name = os.path.splitext(os.path.basename(input_file_path))[0]
            output_file_path = os.path.join(input_dir, f"{input_name}_with_kidney_roi.mat")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        # Process the file using existing logic
        result = predict_and_save_to_path(input_file_path, output_file_path)
        
        if result:
            print(f"✅ Kidney ROI applied successfully: {output_file_path}")
            return output_file_path
        else:
            print(f"❌ Failed to apply kidney ROI to {input_file_path}")
            return None
            
    except Exception as e:
        print(f"❌ Error in apply_kidney_roi_to_project: {e}")
        return None

def predict_and_save_to_path(input_path, output_path):
    """
    Modified version of predict_and_save that uses specific input/output paths
    """
    global model, device
    try:
        mat = sio.loadmat(input_path, struct_as_record=False, squeeze_me=True)
        if 'images' not in mat:
            raise KeyError("'images' not found")

        images_struct = mat['images']
        identity = np.eye(4, dtype=np.float64)
        for img in images_struct:
            if hasattr(img, 'data') and isinstance(img.data, np.ndarray):
                img.data = img.data.astype(np.float64)
                img.A = identity.copy()
                img.Anative = identity.copy()
                img.Aprime = identity.copy()
                img.box = np.array(img.data.shape[:3], dtype=np.float64)

                if hasattr(img, 'data_info'):
                    # Make sure 'Mask' field is logical
                    if hasattr(img.data_info, 'Mask'):
                        img.data_info.Mask = img.data_info.Mask.astype(bool)
                    else:
                        img.data_info.Mask = np.ones(img.data.shape, dtype=bool)

                if hasattr(img, 'slaves') and isinstance(img.slaves, np.ndarray):
                    for slave in img.slaves:
                        if hasattr(slave, 'data'):
                            slave.data = slave.data.astype(bool)
                            slave.A = identity.copy()
                            slave.Anative = identity.copy()
                            slave.Aprime = identity.copy()
                            slave.box = np.array(slave.data.shape[:3], dtype=np.float64)

        # Find BE_AMP
        be_amp_data = None
        image_entry = None
        for entry in images_struct:
            if hasattr(entry, 'Name') and 'BE_AMP' in str(entry.Name):
                be_amp_data = entry.data
                image_entry = entry
                break

        if be_amp_data is None or be_amp_data.ndim != 3:
            raise ValueError("Invalid or missing BE_AMP data")

        # Normalize input
        img_resized = resize(be_amp_data, (64, 64, 64), preserve_range=True)
        img_norm = (img_resized - img_resized.min()) / (np.ptp(img_resized) + 1e-8)
        input_tensor = torch.tensor(img_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)

        # Run prediction
        if model is not None:
            # Use UNet model if available
            with torch.no_grad():
                pred = model(input_tensor).squeeze().cpu().numpy()
                mask = (pred > 0.5)
        else:
            # Fallback to simple thresholding if model not available
            print("   Using fallback segmentation (no UNet model)")
            # Simple intensity-based segmentation
            threshold = np.percentile(img_norm[img_norm > 0], 75)
            mask = img_norm > threshold

        if np.sum(mask) == 0:
            print(f"⚠️ Empty mask predicted for {input_path}")
            return False

        # Split components
        labeled, num = label(mask)
        if num < 2:
            print(f"⚠️ Only {num} component(s) found — skipping split.")
            return False

        # Find two largest components
        sizes = [(labeled == i).sum() for i in range(1, num + 1)]
        largest = np.argsort(sizes)[-2:][::-1]
        comp1 = (labeled == (largest[0] + 1))
        comp2 = (labeled == (largest[1] + 1))

        # Determine left/right
        com1 = center_of_mass(comp1)
        com2 = center_of_mass(comp2)

        if com1[0] > com2[0]:
            right_mask, left_mask = comp1, comp2
        else:
            right_mask, left_mask = comp2, comp1

        # Create ROI structs
        roi1 = make_roi_struct(right_mask, "Kidney")
        roi2 = make_roi_struct(left_mask, "Kidney2")

        # Attach both ROIs
        roi_array = np.empty((2,), dtype=object)
        roi_array[0] = roi1
        roi_array[1] = roi2
        setattr(image_entry, 'slaves', roi_array)

        # Save output
        sio.savemat(output_path, mat, do_compression=True)
        print(f"Final saved with split kidneys: {output_path}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

class CleanMedicalPipeline:
    def __init__(self, data_folder=None):
        self.eng = None
        # Use provided data folder or default
        if data_folder == None:
            data_folder = input("Please enter the data folder:")
        self.data_folder = data_folder or r'c:\Users\ftmen\Documents\v3\DATA\241202'
        
        # Extract experiment name from data folder path
        self.experiment_name = os.path.basename(self.data_folder.rstrip(os.sep))
        
        # Set output to AutoPipelineResults with experiment name
        self.output_base = Path('AutoPipelineResults')
        self.current_output_dir = None
        
        # Proven naming scheme that works
        self.naming_scheme = [
            ('BE_AMP', 'AMP_pEPRI', 0),  # Amplitude version of first file
            ('BE1', 'PO2_pEPRI', 0),     # Pre-transfusion
            ('BE2', 'PO2_pEPRI', 1),     
            ('BE3', 'PO2_pEPRI', 2),     
            ('BE4', 'PO2_pEPRI', 3),     
            ('ME1', 'PO2_pEPRI', 4),     # Mid-transfusion
            ('ME2', 'PO2_pEPRI', 5),     
            ('ME3', 'PO2_pEPRI', 6),     
            ('ME4', 'PO2_pEPRI', 7),     
            ('AE1', 'PO2_pEPRI', 8),     # Post-transfusion
            ('AE2', 'PO2_pEPRI', 9),     
            ('AE3', 'PO2_pEPRI', 10),    
            ('AE4', 'PO2_pEPRI', 11)     
        ]
        
    def setup_output_directory(self):
        """Create experiment-named output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_output_dir = self.output_base / f"{self.experiment_name}_{timestamp}"
        self.current_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {self.current_output_dir}")
        return self.current_output_dir
        
    def start_matlab_engine(self):
        """Initialize MATLAB engine"""
        print("🔧 Starting MATLAB engine...")
        self.eng = matlab.engine.start_matlab()
        
        # Get the main v3 directory path (we're now in root)
        v3_dir = os.getcwd()
        
        # Add necessary paths relative to v3 directory
        paths = [
            v3_dir,  # Main v3 directory
            os.path.join(v3_dir, 'Arbuz2.0'),
            os.path.join(v3_dir, 'epri'),
            os.path.join(v3_dir, 'common'),
            os.path.join(v3_dir, 'process'),
            os.path.join(v3_dir, '3dparty')
        ]
        
        for path in paths:
            if os.path.exists(path):
                self.eng.addpath(path, nargout=0)
                print(f"  Added path: {path}")
            else:
                print(f"  Warning: Path not found: {path}")
        
        print("✅ MATLAB engine ready")
        
    def find_image_files(self):
        """Find image .tdms files"""
        pattern = os.path.join(self.data_folder, '*image4D_18x18_0p75gcm_file.tdms')
        tdms_files = glob.glob(pattern)
        tdms_files.sort()
        return tdms_files[:12]  # First 12 files
        
    def create_proven_project(self):
        """Use the proven project creation method from final_custom_automation.py"""
        print("🏗️  Creating project using proven method...")
        
        # Check for existing processed files
        tdms_files = self.find_image_files()
        processed_files = []
        
        for tdms_file in tdms_files:
            base_name = Path(tdms_file).stem
            p_file = Path(tdms_file).parent / f"p{base_name}.mat"
            
            if p_file.exists():
                processed_files.append((str(tdms_file), str(p_file)))
                print(f"✅ Found processed: {p_file.name}")
            else:
                print(f"⚠️  Missing: {p_file.name}")
        
        if len(processed_files) < 12:
            print(f"❌ Only {len(processed_files)} processed files found, need 12")
            return None
        
        # Create the project using proven MATLAB script approach
        project_name = "clean_project.mat"
        return self.create_matlab_project(processed_files, project_name)
        
    def create_matlab_project(self, processed_files, project_name):
        """Create project using the proven MATLAB script method"""
        
        # Create the complete MATLAB script - same method that worked before
        script_content = f"""
function create_clean_project()
    disp('Creating clean ArbuzGUI project...');
    
    hGUI = ArbuzGUI();
    pause(2);
    
    if isempty(hGUI) || ~isvalid(hGUI)
        error('Failed to launch ArbuzGUI');
    end
    
    files = {{
"""
        
        # Add file paths using proven approach
        for name, img_type, file_idx in self.naming_scheme:
            if file_idx < len(processed_files):
                _, p_file = processed_files[file_idx]
                safe_path = str(p_file).replace('\\', '/')
                script_content += f"        '{safe_path}', '{name}', '{img_type}';\n"
        
        script_content += f"""
    }};
    
    for i = 1:size(files, 1)
        try
            add_image_to_project(hGUI, files{{i,1}}, files{{i,2}}, files{{i,3}});
            disp(['Added: ', files{{i,2}}, ' [', files{{i,3}}, ']']);
        catch ME
            disp(['Error adding ', files{{i,2}}, ': ', ME.message]);
        end
        pause(0.3);
    end
    
    project_path = '{str(self.current_output_dir / project_name).replace(chr(92), '/')}';
    arbuz_SaveProject(hGUI, project_path);
    disp(['Project saved: ', project_path]);
end

function add_image_to_project(hGUI, file_path, image_name, image_type)
    % Add image using proven method
    
    % Inject AutoAccept flag
    try
        tmp = load(file_path);
        if isfield(tmp, 'pO2_info')
            tmp.pO2_info.AutoAccept = true;
            save(file_path, '-struct', 'tmp');
        end
    catch, end
    
    imageStruct = struct();
    imageStruct.FileName = file_path;
    imageStruct.Name = image_name;
    imageStruct.ImageType = image_type;
    imageStruct.isStore = 1;
    imageStruct.isLoaded = 0;
    
    [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
    
    imageStruct.data = imageData;
    imageStruct.data_info = imageInfo;
    imageStruct.ImageType = actualType;
    imageStruct.box = safeget(imageInfo, 'Bbox', size(imageData));
    imageStruct.Anative = safeget(imageInfo, 'Anative', eye(4));
    imageStruct.isLoaded = 1;
    
    arbuz_AddImage(hGUI, imageStruct);
    
    % Handle slaves for AMP images
    if contains(image_name, 'AMP') && ~isempty(slaveImages)
        try
            idxCell = arbuz_FindImage(hGUI, 'master', 'Name', image_name, {{'ImageIdx'}});
            if ~isempty(idxCell)
                masterIdx = idxCell{{1}}.ImageIdx;
                for k = 1:length(slaveImages)
                    arbuz_AddImage(hGUI, slaveImages{{k}}, masterIdx);
                end
            end
        catch, end
    end
    
    % Clean AutoAccept flag
    try
        tmp = load(file_path);
        if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
            tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
            save(file_path, '-struct', 'tmp');
        end
    catch, end
end

function val = safeget(s, field, default)
    if isfield(s, field)
        val = s.(field);
    else
        val = default;
    end
end
        """
        
        # Write and execute script
        script_path = 'temp_clean_project.m'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            self.eng.run(script_path[:-2], nargout=0)  # Remove .m extension
            project_path = self.current_output_dir / project_name
            
            if project_path.exists():
                print(f"✅ Project created: {project_name}")
                return str(project_path)
            else:
                print("❌ Project creation failed")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
    
    def apply_roi_with_draw_roi(self, project_file):
        """Apply ROI using the Draw_ROI API"""
        print("🎯 Applying kidney ROI using Draw_ROI API...")
        
        try:
            # Use the global functions defined above
            output_file = apply_kidney_roi_to_project(
                project_file, 
                os.path.join(self.current_output_dir, f"roi_{os.path.basename(project_file)}")
            )
            
            if output_file and os.path.exists(output_file):
                print(f"✅ ROI applied: {os.path.basename(output_file)}")
                return output_file
            else:
                print("❌ ROI application failed")
                return None
                
        except Exception as e:
            print(f"❌ Error with Draw_ROI: {e}")
            return None
    
    def copy_roi_to_all_images(self, project_file):
        """Copy ROI to all other images using MATLAB to avoid corruption"""
        print("📋 Copying ROI to all images...")
        
        # Create MATLAB script to handle ROI copying safely
        script_content = f"""
function copy_roi_safely()
    project_file = '{project_file.replace(chr(92), '/')}';
    
    try
        % Load project
        project_data = load(project_file);
        
        % Handle different structure formats
        if isfield(project_data, 'images')
            images = project_data.images;
        else
            error('No images field found in project');
        end
        
        fprintf('Loaded project with %d images\\n', length(images));
        
        % Find BE_AMP with ROIs
        source_rois = [];
        source_idx = 0;
        
        % Handle both cell and struct array formats
        for i = 1:length(images)
            img_name = '';
            
            % Extract name safely
            if iscell(images)
                img = images{{i}};
                if isfield(img, 'Name')
                    img_name = img.Name;
                end
                has_slaves = isfield(img, 'slaves') && ~isempty(img.slaves);
            else
                if isfield(images(i), 'Name')
                    img_name = images(i).Name;
                end
                has_slaves = isfield(images(i), 'slaves') && ~isempty(images(i).slaves);
            end
            
            if strcmp(img_name, 'BE_AMP') && has_slaves
                if iscell(images)
                    source_rois = images{{i}}.slaves;
                else
                    source_rois = images(i).slaves;
                end
                source_idx = i;
                fprintf('Found ROIs in BE_AMP at index %d\\n', i);
                break;
            end
        end
        
        if isempty(source_rois)
            error('No ROIs found in BE_AMP');
        end
        
        % Copy ROIs to target images
        target_names = {{'BE1', 'BE2', 'BE3', 'BE4', 'ME1', 'ME2', 'ME3', 'ME4', 'AE1', 'AE2', 'AE3', 'AE4'}};
        copied_count = 0;
        
        for i = 1:length(images)
            if i == source_idx
                continue;  % Skip BE_AMP itself
            end
            
            img_name = '';
            if iscell(images)
                if isfield(images{{i}}, 'Name')
                    img_name = images{{i}}.Name;
                end
            else
                if isfield(images(i), 'Name')
                    img_name = images(i).Name;
                end
            end
            
            % Check if this is a target image
            if any(strcmp(img_name, target_names))
                % Copy ROIs directly - MATLAB handles structure properly
                if iscell(images)
                    images{{i}}.slaves = source_rois;
                else
                    images(i).slaves = source_rois;
                end
                copied_count = copied_count + 1;
                fprintf('  Copied ROIs to %s\\n', img_name);
            end
        end
        
        % Save using MATLAB (preserves structure integrity)
        output_file = '{str(self.current_output_dir / f"complete_{os.path.basename(project_file)}").replace(chr(92), '/')}';
        project_data.images = images;
        save(output_file, '-struct', 'project_data');
        
        fprintf('ROIs copied to %d images\\n', copied_count);
        fprintf('Complete project saved: %s\\n', output_file);
        
    catch ME
        fprintf('Error in ROI copying: %s\\n', ME.message);
        rethrow(ME);
    end
end
        """
        
        script_path = 'temp_copy_roi_safe.m'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            self.eng.run(script_path[:-2], nargout=0)
            output_file = self.current_output_dir / f"complete_{os.path.basename(project_file)}"
            
            if output_file.exists():
                print(f"✅ ROIs copied using MATLAB: {output_file.name}")
                return str(output_file)
            else:
                print("❌ MATLAB ROI copying failed")
                return None
                
        except Exception as e:
            print(f"❌ Error in MATLAB ROI copying: {e}")
            return None
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
    
    def get_image_name(self, img):
        """Extract image name from structure"""
        if hasattr(img, 'Name'):
            if hasattr(img.Name, 'item'):
                return str(img.Name.item())
            elif isinstance(img.Name, str):
                return img.Name
            elif hasattr(img.Name, '__iter__') and len(img.Name) > 0:
                return str(img.Name[0])
        return "Unknown"
    
    def copy_roi_structure(self, source_roi):
        """Create copy of ROI structure"""
        if hasattr(source_roi, 'data'):
            roi_copy = {
                'data': source_roi.data.copy(),
                'ImageType': getattr(source_roi, 'ImageType', '3DMASK'),
                'Name': getattr(source_roi, 'Name', 'Kidney'),
                'A': getattr(source_roi, 'A', np.eye(4)).copy(),
                'Anative': getattr(source_roi, 'Anative', np.eye(4)).copy(),
                'Aprime': getattr(source_roi, 'Aprime', np.eye(4)).copy(),
                'isStore': getattr(source_roi, 'isStore', 1),
                'isLoaded': getattr(source_roi, 'isLoaded', 0),
                'Selected': getattr(source_roi, 'Selected', 0),
                'Visible': getattr(source_roi, 'Visible', 0),
                'box': getattr(source_roi, 'box', np.array([64, 64, 64])).copy(),
                'pars': getattr(source_roi, 'pars', np.array([])).copy(),
                'FileName': getattr(source_roi, 'FileName', '')
            }
        else:
            roi_copy = {}
            for key, value in source_roi.items():
                if isinstance(value, np.ndarray):
                    roi_copy[key] = value.copy()
                else:
                    roi_copy[key] = value
        
        return roi_copy
    
    def extract_statistics(self, project_file):
        """Extract statistics for both kidneys"""
        print("📊 Extracting statistics...")
        
        try:
            project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            images = project_data['images']
            
            stats_data = []
            
            for img in images:
                img_name = self.get_image_name(img)
                
                if hasattr(img, 'data') and hasattr(img, 'slaves') and img.slaves is not None:
                    image_data = img.data
                    if image_data.ndim == 4:
                        image_data = image_data[:, :, :, 0]  # First time point
                    
                    rois = img.slaves if isinstance(img.slaves, (list, np.ndarray)) else [img.slaves]
                    
                    for i, roi in enumerate(rois):
                        roi_name = getattr(roi, 'Name', f'ROI_{i+1}')
                        if hasattr(roi, 'data'):
                            mask = roi.data.astype(bool)
                            
                            if mask.shape == image_data.shape:
                                roi_data = image_data[mask]
                                
                                if len(roi_data) > 0:
                                    stats = {
                                        'Image': img_name,
                                        'ROI': roi_name,
                                        'Mean': float(np.mean(roi_data)),
                                        'Median': float(np.median(roi_data)),
                                        'Std': float(np.std(roi_data)),
                                        'N_Voxels': int(len(roi_data))
                                    }
                                    stats_data.append(stats)
                                    print(f"  ✅ {img_name} - {roi_name}: {len(roi_data)} voxels")
            
            if stats_data:
                df = pd.DataFrame(stats_data)
                excel_file = self.current_output_dir / f"{self.experiment_name}_statistics.xlsx"
                df.to_excel(excel_file, index=False)
                
                print(f"✅ Statistics saved: {excel_file.name}")
                return str(excel_file)
            else:
                print("❌ No statistics collected")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting statistics: {e}")
            return None
    
    def cleanup(self):
        """Clean up MATLAB engine"""
        if self.eng:
            try:
                self.eng.quit()
            except:
                pass
    
    def run_clean_pipeline(self):
        """Run the clean pipeline with proven methods"""
        print("🔬 Clean Medical Imaging Pipeline")
        print("=" * 45)
        print("Proven Project Creation + Draw_ROI API + Statistics")
        print("=" * 45)
        
        try:
            # Setup
            output_dir = self.setup_output_directory()
            self.start_matlab_engine()
            
            # Step 1: Create project using proven method
            print("\\n📁 Step 1: Creating project using proven method...")
            project_file = self.create_proven_project()
            if not project_file:
                raise ValueError("Project creation failed")
            
            # Step 2: Apply ROI using Draw_ROI API
            print("\\n🎯 Step 2: Applying ROI using Draw_ROI API...")
            roi_project = self.apply_roi_with_draw_roi(project_file)
            if not roi_project:
                raise ValueError("ROI application failed")
            
            # Step 3: Copy ROI to all images
            print("\\n📋 Step 3: Copying ROI to all images...")
            complete_project = self.copy_roi_to_all_images(roi_project)
            if not complete_project:
                raise ValueError("ROI copying failed")
            
            # Step 4: Extract statistics
            print("\\n📊 Step 4: Extracting statistics...")
            stats_file = self.extract_statistics(complete_project)
            
            # Step 5: Clean up intermediate files - keep only final project
            print("\\n🧹 Step 5: Cleaning up intermediate files...")
            try:
                if os.path.exists(project_file):
                    os.remove(project_file)
                    print(f"  🗑️ Removed: {os.path.basename(project_file)}")
                
                if os.path.exists(roi_project):
                    os.remove(roi_project)
                    print(f"  🗑️ Removed: {os.path.basename(roi_project)}")
                
                # Rename final project to have a cleaner name
                final_name = f"{self.experiment_name}_complete_analysis.mat"
                final_path = self.current_output_dir / final_name
                
                if os.path.exists(complete_project):
                    os.rename(complete_project, final_path)
                    print(f"  📁 Final project: {final_name}")
                    complete_project = str(final_path)
                
            except Exception as e:
                print(f"  ⚠️ Cleanup warning: {e}")
            
            # Summary
            print(f"\\n🎉 PIPELINE COMPLETE!")
            print(f"📁 Output: {output_dir}")
            print(f"📄 Final project: {Path(complete_project).name}")
            if stats_file:
                print(f"📊 Statistics: {Path(stats_file).name}")
            
            return output_dir
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return None
            
        finally:
            self.cleanup()

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Clean Medical Imaging Pipeline - Automated ROI detection and analysis')
    parser.add_argument('--data', '-d', 
                       type=str, 
                       default="",
                       help='Path to the data directory containing .tdms files')
    parser.add_argument('--output', '-o',
                       type=str,
                       default='AutoPipelineResults',
                       help='Output directory for results (default: AutoPipelineResults)')
    
    args = parser.parse_args()
    
    # Validate data directory
    while not os.path.exists(args.data):
        # print("You can specify a valid data directory using --data or -d")
        args.data = input("Please enter a directory with data: ")
        # print(f"❌ Error: Data directory '{args.data}' does not exist")
        # sys.exit(1)
    
    # Check for .tdms files in the directory
    tdms_pattern = os.path.join(args.data, '*image4D_18x18_0p75gcm_file.tdms')
    tdms_files = glob.glob(tdms_pattern)
    if len(tdms_files) == 0:
        print(f"❌ Error: No .tdms files found in '{args.data}'")
        print("Expected files matching pattern: *image4D_18x18_0p75gcm_file.tdms")
        sys.exit(1)
    
    print(f"📁 Using data directory: {args.data}")
    print(f"📁 Output directory: {args.output}")
    print(f"🔍 Found {len(tdms_files)} .tdms files")
    
    # Create pipeline with specified data folder
    pipeline = CleanMedicalPipeline(data_folder=args.data)
    
    # Override output base if specified
    if args.output != 'AutoPipelineResults':
        pipeline.output_base = Path(args.output)
    
    result = pipeline.run_clean_pipeline()
    
    if result:
        print(f"\\n✅ Success! Results in: {result}")
    else:
        print(f"\\n❌ Failed. Check errors above.")

if __name__ == "__main__":
    main()
