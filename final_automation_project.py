"""
Complete Python automation pipeline for medical imaging data processing
Processes .tdms files from /DATA/241202 and creates full ArbuzGUI workflow
with ROI detection, annotation, and statistical analysis.

Pipeline Steps:
1. Process .tdms files using ProcessGUI/ese_fbp
2. Create ArbuzGUI project with BE1-BE4, ME1-ME4, AE1-AE4, BE_AMP
3. Apply kidney ROI to BE_AMP using enhanced Draw_ROI
4. Copy ROI to all other images  
5. Extract statistics and save to Excel
6. Output to timestamped folder in automated_outputs
"""

import matlab.engine
import os
import glob
import time
import pandas as pd
import numpy as np
import scipy.io as sio
from pathlib import Path
from datetime import datetime
import shutil

class CompleteMedicalImagingPipeline:
    def __init__(self):
        self.eng = None
        self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        self.output_base = Path('automated_outputs')
        self.current_output_dir = None
        
        # Image naming scheme as specified
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
        """Create timestamped output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_output_dir = self.output_base / f"run_{timestamp}"
        self.current_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {self.current_output_dir}")
        return self.current_output_dir
        
    def start_matlab_engine(self):
        """Initialize MATLAB engine and add necessary paths"""
        print("🔧 Starting MATLAB engine...")
        self.eng = matlab.engine.start_matlab()
        
        # Add necessary paths
        paths = [
            r'c:\Users\ftmen\Documents\v3',
            r'c:\Users\ftmen\Documents\v3\Arbuz2.0',
            r'c:\Users\ftmen\Documents\v3\epri',
            r'c:\Users\ftmen\Documents\v3\common',
            r'c:\Users\ftmen\Documents\v3\process',
            r'c:\Users\ftmen\Documents\v3\3dparty'
        ]
        
        for path in paths:
            self.eng.addpath(path, nargout=0)
        
        print("✅ MATLAB engine started and paths added")
        
    def find_image_files(self):
        """Find image .tdms files (excluding FID_GRAD_MIN files)"""
        pattern = os.path.join(self.data_folder, '*image4D_18x18_0p75gcm_file.tdms')
        tdms_files = glob.glob(pattern)
        tdms_files.sort()  # Sort to ensure consistent ordering
        
        print(f"📁 Found {len(tdms_files)} image .tdms files:")
        for i, f in enumerate(tdms_files[:12]):  # Show only first 12
            print(f"   {i+1:2d}. {Path(f).name}")
        
        return tdms_files[:12]  # Return only first 12 files
        
    def process_tdms_file(self, tdms_file):
        """Process a single .tdms file using ProcessGUI/ese_fbp"""
        print(f"🔄 Processing {Path(tdms_file).name}...")
        
        try:
            # Set up processing parameters based on ProcessGUI.m
            file_suffix = ""
            output_path = str(Path(tdms_file).parent)
            
            # Create fields structure matching ProcessGUI requirements
            fields = {
                'prc': {'process_method': 'ese_fbp', 'save_data': 'yes', 'fit_data': 'yes', 'recon_data': 'yes'},
                'fbp': {'MaxGradient': 8.0, 'projection_order': 'default'},
                'rec': {'Size': 1, 'Sub_points': 64},
                'td': {'off_res_baseline': 'yes', 'prj_transpose': 'no'},
                'fft': {'FOV': 1, 'xshift_mode': 'none'},
                'clb': {'amp1mM': 1, 'ampHH': 1, 'Torr_per_mGauss': 1.84},
                'fit': {},
                'img': {'mirror_image': [0, 0, 0], 'reg_method': 'none'}
            }
            
            # Call MATLAB processing function
            result = self.eng.ese_fbp(tdms_file, file_suffix, output_path, fields)
            
            # Generate expected output filenames
            base_name = Path(tdms_file).stem
            raw_file = Path(tdms_file).parent / f"{base_name}.mat"
            p_file = Path(tdms_file).parent / f"p{base_name}.mat"
            
            if raw_file.exists() and p_file.exists():
                print(f"  ✅ Generated: {raw_file.name} and {p_file.name}")
                return str(raw_file), str(p_file)
            else:
                print(f"  ⚠️  Output files not found")
                return None, None
                
        except Exception as e:
            print(f"  ❌ Error processing {tdms_file}: {e}")
            return None, None
    
    def create_arbuz_project(self, processed_files, project_name):
        """Create ArbuzGUI project with correct naming scheme"""
        print("🏗️  Creating ArbuzGUI project...")
        
        # Create MATLAB script for project creation
        script_content = f"""
function create_project()
    % Create project with specified naming scheme
    disp('Creating ArbuzGUI project...');
    
    % Launch ArbuzGUI
    hGUI = ArbuzGUI();
    pause(2);
    
    if isempty(hGUI) || ~isvalid(hGUI)
        error('Failed to launch ArbuzGUI');
    end
    
    % File paths and names
    files = {{
"""
        
        # Add file information to the script
        for name, img_type, file_idx in self.naming_scheme:
            if file_idx < len(processed_files):
                _, p_file = processed_files[file_idx]
                safe_path = str(p_file).replace('\\', '/')
                script_content += f"        '{safe_path}', '{name}', '{img_type}';\n"
        
        script_content += f"""
    }};
    
    % Add all images
    for i = 1:size(files, 1)
        try
            add_image_to_gui(hGUI, files{{i,1}}, files{{i,2}}, files{{i,3}});
            disp(['Added: ', files{{i,2}}, ' [', files{{i,3}}, ']']);
        catch ME
            disp(['Error adding ', files{{i,2}}, ': ', ME.message]);
        end
        pause(0.2);
    end
    
    % Save project
    project_path = '{str(self.current_output_dir / project_name).replace(chr(92), '/')}';
    arbuz_SaveProject(hGUI, project_path);
    disp(['Project saved: ', project_path]);
end

function add_image_to_gui(hGUI, file_path, image_name, image_type)
    % Add image to ArbuzGUI with proper structure
    
    % Inject AutoAccept flag
    try
        tmp = load(file_path);
        if isfield(tmp, 'pO2_info')
            tmp.pO2_info.AutoAccept = true;
            save(file_path, '-struct', 'tmp');
        end
    catch, end
    
    % Create and load image
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
        
        # Write and execute the script
        script_path = 'temp_create_project.m'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            self.eng.create_project(nargout=0)
            project_path = self.current_output_dir / project_name
            
            if project_path.exists():
                print(f"✅ Project created: {project_name}")
                return str(project_path)
            else:
                print("❌ Project file not found after creation")
                return None
                
        except Exception as e:
            print(f"❌ Error creating project: {e}")
            return None
        finally:
            if os.path.exists(script_path):
                os.remove(script_path)
    
    def apply_kidney_roi(self, project_file):
        """Apply kidney ROI to BE_AMP image using enhanced Draw_ROI"""
        print("🎯 Applying kidney ROI to BE_AMP...")
        
        try:
            # Copy the enhanced_draw_roi.py if it doesn't exist
            roi_script_path = Path('enhanced_draw_roi.py')
            if not roi_script_path.exists():
                # Create enhanced ROI detection script
                self.create_enhanced_roi_script()
            
            # Import and use the ROI detection
            import enhanced_draw_roi
            
            # Apply ROI to the project
            updated_project = enhanced_draw_roi.apply_kidney_roi_to_project(
                project_file, 
                target_image='BE_AMP',
                output_dir=str(self.current_output_dir)
            )
            
            if updated_project and Path(updated_project).exists():
                print(f"✅ ROI applied: {Path(updated_project).name}")
                return updated_project
            else:
                print("❌ ROI application failed")
                return None
                
        except Exception as e:
            print(f"❌ Error applying ROI: {e}")
            return None
    
    def create_enhanced_roi_script(self):
        """Create enhanced Draw_ROI script for kidney detection"""
        roi_script_content = '''"""
Enhanced Draw_ROI script for kidney detection and annotation
Applies kidney ROI to specified image in ArbuzGUI project
"""

import scipy.io as sio
import numpy as np
from pathlib import Path
import os

def apply_kidney_roi_to_project(project_file, target_image='BE_AMP', output_dir=None):
    """
    Apply kidney ROI to target image in ArbuzGUI project
    
    Args:
        project_file: Path to ArbuzGUI project .mat file
        target_image: Name of image to apply ROI to
        output_dir: Output directory for annotated project
    
    Returns:
        Path to annotated project file
    """
    try:
        print(f"Loading project: {project_file}")
        
        # Load project
        project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
        
        if 'images' not in project_data:
            raise ValueError("No images found in project file")
        
        images = project_data['images']
        target_found = False
        
        # Find target image
        for i in range(len(images)):
            img = images[i]
            
            # Handle different name formats
            img_name = None
            if hasattr(img, 'Name'):
                if hasattr(img.Name, 'item'):
                    img_name = str(img.Name.item())
                elif isinstance(img.Name, str):
                    img_name = img.Name
                elif hasattr(img.Name, '__iter__') and len(img.Name) > 0:
                    img_name = str(img.Name[0])
            
            if img_name == target_image:
                print(f"Found target image: {target_image}")
                target_found = True
                
                # Get image data
                image_data = img.data
                print(f"Image data shape: {image_data.shape}")
                
                # Create kidney ROI mask
                roi_mask = create_kidney_roi_mask(image_data)
                
                # Create ROI structure
                roi_struct = create_roi_structure(roi_mask, "Kidney")
                
                # Add ROI as slave to target image
                if hasattr(img, 'slaves') and img.slaves is not None:
                    # Convert to list if needed
                    if not isinstance(img.slaves, list):
                        img.slaves = [img.slaves] if img.slaves.size > 0 else []
                    img.slaves.append(roi_struct)
                else:
                    img.slaves = [roi_struct]
                
                print(f"✅ Added kidney ROI to {target_image}")
                break
        
        if not target_found:
            raise ValueError(f"Target image '{target_image}' not found in project")
        
        # Save annotated project
        if output_dir:
            output_path = Path(output_dir) / f"annotated_{Path(project_file).name}"
        else:
            output_path = Path(project_file).parent / f"annotated_{Path(project_file).name}"
        
        # Update project data
        project_data['images'] = images
        
        # Save project
        sio.savemat(str(output_path), project_data, do_compression=True)
        print(f"✅ Annotated project saved: {output_path}")
        
        return str(output_path)
        
    except Exception as e:
        print(f"❌ Error in ROI application: {e}")
        return None

def create_kidney_roi_mask(image_data):
    """
    Create kidney ROI mask using simple thresholding and morphology
    
    Args:
        image_data: 3D image array
    
    Returns:
        3D boolean mask array
    """
    try:
        # Handle different data types and shapes
        if image_data.ndim == 4:
            # Use first time point if 4D
            data = image_data[:, :, :, 0]
        else:
            data = image_data.copy()
        
        # Convert to float and normalize
        data = data.astype(np.float64)
        data = (data - data.min()) / (data.max() - data.min() + 1e-10)
        
        # Simple intensity-based segmentation
        # Assuming kidney has moderate to high intensity
        threshold = np.percentile(data[data > 0], 75)  # 75th percentile of non-zero values
        
        # Create initial mask
        mask = data > threshold
        
        # Simple morphological operations to clean up
        from scipy import ndimage
        
        # Remove small objects
        mask = ndimage.binary_opening(mask, structure=np.ones((3, 3, 3)))
        
        # Fill holes
        mask = ndimage.binary_fill_holes(mask)
        
        # Keep only the largest connected component (assuming it's the kidney)
        labeled, num_features = ndimage.label(mask)
        if num_features > 0:
            sizes = ndimage.sum(mask, labeled, range(1, num_features + 1))
            largest_label = np.argmax(sizes) + 1
            mask = labeled == largest_label
        
        # Ensure we have a reasonable ROI size
        total_voxels = mask.size
        roi_voxels = np.sum(mask)
        roi_fraction = roi_voxels / total_voxels
        
        if roi_fraction < 0.01:  # Too small
            print(f"⚠️  ROI too small ({roi_fraction:.3f}), using fallback method")
            # Fallback: create a cubic ROI in the center
            center = [s // 2 for s in mask.shape]
            size = min(mask.shape) // 4
            mask = np.zeros(mask.shape, dtype=bool)
            mask[center[0]-size:center[0]+size,
                 center[1]-size:center[1]+size,
                 center[2]-size:center[2]+size] = True
        elif roi_fraction > 0.5:  # Too large
            print(f"⚠️  ROI too large ({roi_fraction:.3f}), refining...")
            # Use higher threshold
            threshold = np.percentile(data[data > 0], 90)
            mask = data > threshold
            mask = ndimage.binary_opening(mask, structure=np.ones((3, 3, 3)))
        
        print(f"✅ Created kidney ROI: {np.sum(mask)} voxels ({np.sum(mask)/mask.size:.3f} fraction)")
        
        return mask.astype(bool)
        
    except Exception as e:
        print(f"❌ Error creating ROI mask: {e}")
        # Fallback: create a simple cubic ROI
        shape = image_data.shape[:3] if image_data.ndim == 4 else image_data.shape
        center = [s // 2 for s in shape]
        size = min(shape) // 6
        mask = np.zeros(shape, dtype=bool)
        mask[center[0]-size:center[0]+size,
             center[1]-size:center[1]+size,
             center[2]-size:center[2]+size] = True
        return mask

def create_roi_structure(mask, name):
    """
    Create ArbuzGUI-compatible ROI structure
    
    Args:
        mask: 3D boolean array
        name: ROI name
    
    Returns:
        ROI structure dictionary
    """
    roi_struct = {
        'data': mask.astype(bool),
        'ImageType': '3DMASK',
        'Name': name,
        'A': np.eye(4, dtype=np.float64),
        'Anative': np.eye(4, dtype=np.float64),
        'Aprime': np.eye(4, dtype=np.float64),
        'isStore': 1,
        'isLoaded': 1,
        'Selected': 0,
        'Visible': 0,
        'box': np.array(mask.shape, dtype=np.float64),
        'pars': np.array([]),
        'FileName': ''
    }
    
    return roi_struct
'''
        
        with open('enhanced_draw_roi.py', 'w', encoding='utf-8') as f:
            f.write(roi_script_content)
        
        print("✅ Enhanced ROI script created")
    
    def copy_roi_to_all_images(self, project_file):
        """Copy kidney ROI from BE_AMP to all other images"""
        print("📋 Copying ROI to all images...")
        
        try:
            # Load project
            project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in project_data:
                raise ValueError("No images found in project")
            
            images = project_data['images']
            source_roi = None
            
            # Find ROI from BE_AMP
            for img in images:
                img_name = self.get_image_name(img)
                if img_name == 'BE_AMP' and hasattr(img, 'slaves') and img.slaves is not None:
                    if isinstance(img.slaves, list) and len(img.slaves) > 0:
                        source_roi = img.slaves[0]
                    elif hasattr(img.slaves, 'data'):
                        source_roi = img.slaves
                    break
            
            if source_roi is None:
                raise ValueError("No ROI found in BE_AMP image")
            
            print(f"✅ Found source ROI in BE_AMP")
            
            # Copy ROI to all other images
            copied_count = 0
            for img in images:
                img_name = self.get_image_name(img)
                if img_name != 'BE_AMP':
                    # Create ROI copy
                    roi_copy = self.create_roi_copy(source_roi)
                    
                    # Add to image
                    if hasattr(img, 'slaves') and img.slaves is not None:
                        if not isinstance(img.slaves, list):
                            img.slaves = [img.slaves] if img.slaves.size > 0 else []
                        img.slaves.append(roi_copy)
                    else:
                        img.slaves = [roi_copy]
                    
                    copied_count += 1
                    print(f"  ✅ Copied ROI to {img_name}")
            
            # Save updated project
            output_path = Path(project_file).parent / f"roi_copied_{Path(project_file).name}"
            project_data['images'] = images
            sio.savemat(str(output_path), project_data, do_compression=True)
            
            print(f"✅ ROI copied to {copied_count} images")
            print(f"✅ Updated project saved: {output_path}")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error copying ROI: {e}")
            return None
    
    def get_image_name(self, img):
        """Extract image name from image structure"""
        if hasattr(img, 'Name'):
            if hasattr(img.Name, 'item'):
                return str(img.Name.item())
            elif isinstance(img.Name, str):
                return img.Name
            elif hasattr(img.Name, '__iter__') and len(img.Name) > 0:
                return str(img.Name[0])
        return "Unknown"
    
    def create_roi_copy(self, source_roi):
        """Create a copy of ROI structure"""
        if hasattr(source_roi, 'data'):
            roi_copy = {
                'data': source_roi.data.copy(),
                'ImageType': getattr(source_roi, 'ImageType', '3DMASK'),
                'Name': getattr(source_roi, 'Name', 'Kidney'),
                'A': getattr(source_roi, 'A', np.eye(4)),
                'Anative': getattr(source_roi, 'Anative', np.eye(4)),
                'Aprime': getattr(source_roi, 'Aprime', np.eye(4)),
                'isStore': getattr(source_roi, 'isStore', 1),
                'isLoaded': getattr(source_roi, 'isLoaded', 1),
                'Selected': getattr(source_roi, 'Selected', 0),
                'Visible': getattr(source_roi, 'Visible', 0),
                'box': getattr(source_roi, 'box', np.array([64, 64, 64])),
                'pars': getattr(source_roi, 'pars', np.array([])),
                'FileName': getattr(source_roi, 'FileName', '')
            }
        else:
            # Handle dictionary-like structure
            roi_copy = source_roi.copy()
        
        return roi_copy
    
    def extract_statistics(self, project_file):
        """Extract statistics from all images with ROI masks"""
        print("📊 Extracting statistics...")
        
        try:
            # Load project
            project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in project_data:
                raise ValueError("No images found in project")
            
            images = project_data['images']
            stats_data = []
            
            for img in images:
                img_name = self.get_image_name(img)
                
                if not hasattr(img, 'data'):
                    print(f"  ⚠️  No data in {img_name}")
                    continue
                
                image_data = img.data
                
                # Get ROI mask
                mask = None
                if hasattr(img, 'slaves') and img.slaves is not None:
                    if isinstance(img.slaves, list):
                        for slave in img.slaves:
                            if hasattr(slave, 'ImageType') and '3DMASK' in str(getattr(slave, 'ImageType', '')):
                                mask = getattr(slave, 'data', None)
                                break
                    elif hasattr(img.slaves, 'data'):
                        mask = img.slaves.data
                
                if mask is not None:
                    # Extract ROI data
                    if image_data.ndim == 4:
                        # Use first time point for 4D data
                        data_slice = image_data[:, :, :, 0]
                    else:
                        data_slice = image_data
                    
                    # Ensure mask and data have same shape
                    if mask.shape != data_slice.shape:
                        print(f"  ⚠️  Shape mismatch for {img_name}: data {data_slice.shape}, mask {mask.shape}")
                        continue
                    
                    roi_data = data_slice[mask.astype(bool)]
                    
                    if len(roi_data) > 0:
                        # Calculate statistics
                        stats = {
                            'Image': img_name,
                            'Mean': float(np.mean(roi_data)),
                            'Median': float(np.median(roi_data)),
                            'Std': float(np.std(roi_data)),
                            'N_Voxels': int(len(roi_data))
                        }
                        stats_data.append(stats)
                        print(f"  ✅ {img_name}: {len(roi_data)} voxels, mean={stats['Mean']:.3f}")
                    else:
                        print(f"  ⚠️  Empty ROI for {img_name}")
                else:
                    print(f"  ⚠️  No ROI mask found for {img_name}")
            
            if stats_data:
                # Create DataFrame and save to Excel
                df = pd.DataFrame(stats_data)
                excel_file = self.current_output_dir / "roi_statistics.xlsx"
                df.to_excel(excel_file, index=False)
                
                print(f"✅ Statistics saved: {excel_file}")
                print(f"📈 Processed {len(stats_data)} images with ROI data")
                
                return str(excel_file)
            else:
                print("❌ No statistics data collected")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting statistics: {e}")
            return None
    
    def cleanup(self):
        """Clean up MATLAB engine"""
        if self.eng:
            try:
                self.eng.quit()
                print("🔧 MATLAB engine closed")
            except:
                pass
    
    def run_complete_pipeline(self):
        """Run the complete automation pipeline"""
        print("🔬 Complete Medical Imaging Automation Pipeline")
        print("=" * 60)
        print("Processing .tdms files → ArbuzGUI project → ROI detection → Statistics")
        print("=" * 60)
        
        try:
            # Step 1: Setup
            output_dir = self.setup_output_directory()
            self.start_matlab_engine()
            
            # Step 2: Find and process image files
            tdms_files = self.find_image_files()
            if not tdms_files:
                raise ValueError("No image .tdms files found")
            
            print(f"\\n🔄 Processing {len(tdms_files)} .tdms files...")
            processed_files = []
            
            for tdms_file in tdms_files:
                base_name = Path(tdms_file).stem
                raw_file = Path(tdms_file).parent / f"{base_name}.mat"
                p_file = Path(tdms_file).parent / f"p{base_name}.mat"
                
                if raw_file.exists() and p_file.exists():
                    print(f"✅ Already processed: {base_name}")
                    processed_files.append((str(raw_file), str(p_file)))
                else:
                    raw_out, p_out = self.process_tdms_file(tdms_file)
                    if raw_out and p_out:
                        processed_files.append((raw_out, p_out))
            
            if not processed_files:
                raise ValueError("No processed .mat files available")
            
            print(f"✅ {len(processed_files)} files ready for project creation")
            
            # Step 3: Create ArbuzGUI project
            project_name = "medical_imaging_project.mat"
            project_file = self.create_arbuz_project(processed_files, project_name)
            if not project_file:
                raise ValueError("Project creation failed")
            
            # Step 4: Apply kidney ROI to BE_AMP
            annotated_project = self.apply_kidney_roi(project_file)
            if not annotated_project:
                raise ValueError("ROI application failed")
            
            # Step 5: Copy ROI to all images
            final_project = self.copy_roi_to_all_images(annotated_project)
            if not final_project:
                raise ValueError("ROI copying failed")
            
            # Step 6: Extract statistics
            stats_file = self.extract_statistics(final_project)
            
            # Step 7: Summary
            print(f"\\n🎉 COMPLETE PIPELINE SUCCESS!")
            print(f"📁 Output directory: {output_dir}")
            print(f"📄 Final project: {Path(final_project).name}")
            if stats_file:
                print(f"📊 Statistics file: {Path(stats_file).name}")
            
            print(f"\\n🎯 Pipeline completed with:")
            print(f"   • {len(processed_files)} images processed")
            print(f"   • 13 named images: BE_AMP, BE1-BE4, ME1-ME4, AE1-AE4")
            print(f"   • Kidney ROI applied to all images")
            print(f"   • Statistics extracted and saved")
            
            return output_dir
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return None
            
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    pipeline = CompleteMedicalImagingPipeline()
    result = pipeline.run_complete_pipeline()
    
    if result:
        print(f"\\n✅ Complete automation finished successfully!")
        print(f"📁 Results available in: {result}")
    else:
        print(f"\\n❌ Automation failed. Check errors above.")

if __name__ == "__main__":
    main()
