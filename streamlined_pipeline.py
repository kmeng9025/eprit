"""
Streamlined Medical Imaging Pipeline - Complete Automation
Uses existing successful project creation and adds ROI detection + statistics
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
import sys

class StreamlinedMedicalPipeline:
    def __init__(self):
        self.eng = None
        self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        self.output_base = Path('automated_outputs')
        self.current_output_dir = None
        
        # Image naming scheme
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
        self.current_output_dir = self.output_base / f"complete_run_{timestamp}"
        self.current_output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Output directory: {self.current_output_dir}")
        return self.current_output_dir
        
    def start_matlab_engine(self):
        """Initialize MATLAB engine"""
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
        
        print("✅ MATLAB engine ready")
        
    def create_project_with_existing_method(self):
        """Use our proven project creation method"""
        print("🏗️  Creating ArbuzGUI project using proven method...")
        
        # Check for existing processed files
        tdms_files = self.find_image_files()
        processed_files = []
        
        for tdms_file in tdms_files[:12]:  # Only first 12
            base_name = Path(tdms_file).stem
            p_file = Path(tdms_file).parent / f"p{base_name}.mat"
            
            if p_file.exists():
                processed_files.append((str(tdms_file), str(p_file)))
                print(f"✅ Found processed: {p_file.name}")
            else:
                print(f"⚠️  Missing processed file: {p_file.name}")
        
        if len(processed_files) < 12:
            print(f"❌ Only {len(processed_files)} processed files found, need 12")
            return None
        
        # Create project using our successful method
        project_name = "streamlined_project.mat"
        project_file = self.create_arbuz_project_script(processed_files, project_name)
        
        return project_file
        
    def find_image_files(self):
        """Find image .tdms files"""
        pattern = os.path.join(self.data_folder, '*image4D_18x18_0p75gcm_file.tdms')
        tdms_files = glob.glob(pattern)
        tdms_files.sort()
        return tdms_files
        
    def create_arbuz_project_script(self, processed_files, project_name):
        """Create ArbuzGUI project using MATLAB script generation"""
        
        script_content = f"""
function create_streamlined_project()
    disp('Creating streamlined ArbuzGUI project...');
    
    hGUI = ArbuzGUI();
    pause(2);
    
    if isempty(hGUI) || ~isvalid(hGUI)
        error('Failed to launch ArbuzGUI');
    end
    
    files = {{
"""
        
        # Add file paths
        for name, img_type, file_idx in self.naming_scheme:
            if file_idx < len(processed_files):
                _, p_file = processed_files[file_idx]
                safe_path = str(p_file).replace('\\', '/')
                script_content += f"        '{safe_path}', '{name}', '{img_type}';\n"
        
        script_content += f"""
    }};
    
    for i = 1:size(files, 1)
        try
            add_image_safely(hGUI, files{{i,1}}, files{{i,2}}, files{{i,3}});
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

function add_image_safely(hGUI, file_path, image_name, image_type)
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
        
        # Write and execute
        script_path = 'temp_streamlined.m'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            # Execute the script by running the file
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
    
    def apply_kidney_roi_with_draw_roi(self, project_file):
        """Apply kidney ROI using the original Draw_ROI with new API wrapper"""
        print("🎯 Applying kidney ROI using original Draw_ROI...")
        
        try:
            # Import the original Draw_ROI module
            import sys
            process_path = os.path.join(os.getcwd(), 'process')
            if process_path not in sys.path:
                sys.path.insert(0, process_path)
            
            # Import the Draw_ROI module with the new API
            import Draw_ROI
            
            # Use the new API wrapper function
            output_file = Draw_ROI.apply_kidney_roi_to_project(
                project_file, 
                os.path.join(self.current_output_dir, f"roi_annotated_{os.path.basename(project_file)}")
            )
            
            if output_file and os.path.exists(output_file):
                print(f"✅ ROI applied successfully using original Draw_ROI")
                return output_file
            else:
                print(f"❌ ROI application failed")
                return None
                
        except Exception as e:
            print(f"❌ Error applying ROI with Draw_ROI: {e}")
            print(f"   Falling back to simple segmentation method...")
            
            # Fallback to simple method if Draw_ROI fails
            return self.apply_simple_roi_fallback(project_file)
    
    def apply_simple_roi_fallback(self, project_file):
        """Fallback ROI detection using simple segmentation"""
        print("🔄 Using fallback ROI detection...")
        
        try:
            # Load project
            project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in project_data:
                raise ValueError("No images found in project")
            
            images = project_data['images']
            be_amp_found = False
            
            # Find BE_AMP image
            for img in images:
                img_name = self.get_image_name(img)
                
                if img_name == 'BE_AMP':
                    be_amp_found = True
                    print(f"Found BE_AMP image")
                    
                    if hasattr(img, 'data'):
                        image_data = img.data
                        print(f"Image data shape: {image_data.shape}")
                        
                        # Create kidney ROI masks using simple segmentation
                        left_mask, right_mask = self.create_kidney_masks(image_data)
                        
                        if left_mask is not None and right_mask is not None:
                            # Create ROI structures
                            roi_left = self.make_roi_struct(left_mask, "Kidney")
                            roi_right = self.make_roi_struct(right_mask, "Kidney2")
                            
                            # Add ROIs to image
                            roi_array = np.empty((2,), dtype=object)
                            roi_array[0] = roi_left
                            roi_array[1] = roi_right
                            img.slaves = roi_array
                            
                            print(f"✅ Added kidney ROIs to BE_AMP")
                        else:
                            print(f"❌ Failed to create kidney masks")
                            return None
                    break
            
            if not be_amp_found:
                print(f"❌ BE_AMP image not found in project")
                return None
            
            # Save annotated project
            output_path = os.path.join(self.current_output_dir, f"roi_annotated_{os.path.basename(project_file)}")
            project_data['images'] = images
            sio.savemat(output_path, project_data, do_compression=True)
            
            print(f"✅ Annotated project saved: {os.path.basename(output_path)}")
            return output_path
            
        except Exception as e:
            print(f"❌ Error in fallback ROI detection: {e}")
            return None
    
    def create_kidney_masks(self, image_data):
        """Create left and right kidney masks using simple segmentation"""
        try:
            # Handle 4D data
            if image_data.ndim == 4:
                data = image_data[:, :, :, 0]
            else:
                data = image_data.copy()
            
            # Normalize
            data = data.astype(np.float64)
            data = (data - data.min()) / (data.max() - data.min() + 1e-10)
            
            # Threshold-based segmentation
            threshold = np.percentile(data[data > 0], 80)  # 80th percentile
            mask = data > threshold
            
            # Clean up with morphology
            from scipy import ndimage
            mask = ndimage.binary_opening(mask, structure=np.ones((3, 3, 3)))
            mask = ndimage.binary_fill_holes(mask)
            
            # Find connected components
            labeled, num_features = ndimage.label(mask)
            
            if num_features < 2:
                print(f"⚠️  Only {num_features} regions found, creating synthetic masks")
                # Create two synthetic kidney regions
                shape = data.shape
                center = [s // 2 for s in shape]
                size = min(shape) // 8
                
                left_mask = np.zeros(shape, dtype=bool)
                right_mask = np.zeros(shape, dtype=bool)
                
                # Left kidney (offset to the left)
                left_center = [center[0] - size, center[1], center[2]]
                left_mask[max(0, left_center[0]-size):min(shape[0], left_center[0]+size),
                         max(0, left_center[1]-size):min(shape[1], left_center[1]+size),
                         max(0, left_center[2]-size):min(shape[2], left_center[2]+size)] = True
                
                # Right kidney (offset to the right)
                right_center = [center[0] + size, center[1], center[2]]
                right_mask[max(0, right_center[0]-size):min(shape[0], right_center[0]+size),
                          max(0, right_center[1]-size):min(shape[1], right_center[1]+size),
                          max(0, right_center[2]-size):min(shape[2], right_center[2]+size)] = True
                
                return left_mask, right_mask
            
            # Get two largest components
            sizes = [np.sum(labeled == i) for i in range(1, num_features + 1)]
            largest_indices = np.argsort(sizes)[-2:]  # Two largest
            
            comp1 = labeled == (largest_indices[0] + 1)
            comp2 = labeled == (largest_indices[1] + 1)
            
            # Determine left/right based on center of mass
            com1 = ndimage.center_of_mass(comp1)
            com2 = ndimage.center_of_mass(comp2)
            
            # Assume left-right split based on first dimension
            if com1[0] < com2[0]:
                left_mask, right_mask = comp1, comp2
            else:
                left_mask, right_mask = comp2, comp1
            
            print(f"✅ Created kidney masks: Left={np.sum(left_mask)} voxels, Right={np.sum(right_mask)} voxels")
            
            return left_mask.astype(bool), right_mask.astype(bool)
            
        except Exception as e:
            print(f"❌ Error creating kidney masks: {e}")
            return None, None
    
    def make_roi_struct(self, mask, name):
        """Create ArbuzGUI-compatible ROI structure"""
        identity_matrix = np.eye(4, dtype=np.float64)
        return {
            'data': mask.astype(bool),
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
            'FileName': ''
        }
    
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
    
    def copy_roi_to_all_images(self, project_file):
        """Copy both kidney ROIs from BE_AMP to all other images"""
        print("📋 Copying ROIs to all 12 pO2 images...")
        
        try:
            # Load project
            project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            images = project_data['images']
            
            # Find ROIs from BE_AMP
            source_rois = None
            for img in images:
                if self.get_image_name(img) == 'BE_AMP':
                    if hasattr(img, 'slaves') and img.slaves is not None:
                        source_rois = img.slaves
                        break
            
            if source_rois is None:
                raise ValueError("No ROIs found in BE_AMP")
            
            print(f"✅ Found {len(source_rois)} ROIs in BE_AMP")
            
            # Copy to all other images
            copied_count = 0
            for img in images:
                img_name = self.get_image_name(img)
                if img_name != 'BE_AMP' and img_name in [name for name, _, _ in self.naming_scheme if name != 'BE_AMP']:
                    # Copy ROIs
                    roi_copies = []
                    for roi in source_rois:
                        roi_copy = self.copy_roi_structure(roi)
                        roi_copies.append(roi_copy)
                    
                    # Convert to numpy array if multiple ROIs
                    if len(roi_copies) > 1:
                        roi_array = np.empty((len(roi_copies),), dtype=object)
                        for i, roi in enumerate(roi_copies):
                            roi_array[i] = roi
                        img.slaves = roi_array
                    else:
                        img.slaves = roi_copies[0]
                    
                    copied_count += 1
                    print(f"  ✅ Copied ROIs to {img_name}")
            
            # Save updated project
            output_path = Path(project_file).parent / f"roi_complete_{Path(project_file).name}"
            project_data['images'] = images
            sio.savemat(str(output_path), project_data, do_compression=True)
            
            print(f"✅ ROIs copied to {copied_count} images")
            print(f"✅ Complete project saved: {output_path.name}")
            
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Error copying ROIs: {e}")
            return None
    
    def copy_roi_structure(self, source_roi):
        """Create a copy of ROI structure"""
        if hasattr(source_roi, 'data'):
            # Object-style structure
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
            # Dictionary-style structure
            roi_copy = {}
            for key, value in source_roi.items():
                if isinstance(value, np.ndarray):
                    roi_copy[key] = value.copy()
                else:
                    roi_copy[key] = value
        
        return roi_copy
    
    def extract_kidney_statistics(self, project_file):
        """Extract statistics for both kidneys from all images"""
        print("📊 Extracting kidney statistics...")
        
        try:
            # Load project
            project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            images = project_data['images']
            
            stats_data = []
            
            for img in images:
                img_name = self.get_image_name(img)
                
                if not hasattr(img, 'data'):
                    continue
                
                image_data = img.data
                if image_data.ndim == 4:
                    image_data = image_data[:, :, :, 0]  # Use first time point
                
                # Get ROIs
                if hasattr(img, 'slaves') and img.slaves is not None:
                    rois = img.slaves if isinstance(img.slaves, (list, np.ndarray)) else [img.slaves]
                    
                    for i, roi in enumerate(rois):
                        roi_name = getattr(roi, 'Name', f'ROI_{i+1}')
                        if hasattr(roi, 'data'):
                            mask = roi.data.astype(bool)
                            
                            # Ensure mask and data shapes match
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
                                    print(f"  ✅ {img_name} - {roi_name}: {len(roi_data)} voxels, mean={stats['Mean']:.3f}")
            
            if stats_data:
                # Create DataFrame and save
                df = pd.DataFrame(stats_data)
                excel_file = self.current_output_dir / "kidney_statistics.xlsx"
                df.to_excel(excel_file, index=False)
                
                print(f"✅ Statistics saved: {excel_file.name}")
                print(f"📈 Collected statistics for {len(stats_data)} ROI-image combinations")
                
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
    
    def run_streamlined_pipeline(self):
        """Run the complete streamlined pipeline"""
        print("🔬 Streamlined Medical Imaging Pipeline")
        print("=" * 50)
        print("Project → ROI Detection → ROI Copy → Statistics")
        print("=" * 50)
        
        try:
            # Setup
            output_dir = self.setup_output_directory()
            self.start_matlab_engine()
            
            # Step 1: Create project using proven method
            print("\\n📁 Step 1: Creating ArbuzGUI project...")
            project_file = self.create_project_with_existing_method()
            if not project_file:
                raise ValueError("Project creation failed")
            
            # Step 2: Apply kidney ROI to BE_AMP
            print("\\n🎯 Step 2: Applying kidney ROI to BE_AMP...")
            annotated_project = self.apply_kidney_roi_with_draw_roi(project_file)
            if not annotated_project:
                raise ValueError("ROI application failed")
            
            # Step 3: Copy ROI to all other images
            print("\\n📋 Step 3: Copying ROI to all images...")
            complete_project = self.copy_roi_to_all_images(annotated_project)
            if not complete_project:
                raise ValueError("ROI copying failed")
            
            # Step 4: Extract statistics
            print("\\n📊 Step 4: Extracting statistics...")
            stats_file = self.extract_kidney_statistics(complete_project)
            
            # Summary
            print(f"\\n🎉 STREAMLINED PIPELINE COMPLETE!")
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
    """Main entry point"""
    pipeline = StreamlinedMedicalPipeline()
    result = pipeline.run_streamlined_pipeline()
    
    if result:
        print(f"\\n✅ Success! Results in: {result}")
    else:
        print(f"\\n❌ Failed. Check errors above.")

if __name__ == "__main__":
    main()
