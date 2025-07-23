"""
Clean Medical Imaging Pipeline - MATLAB-Safe Version
Uses proven project creation + Draw_ROI API + MATLAB-native saving
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

class CleanMedicalPipeline:
    def __init__(self):
        self.eng = None
        self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        self.output_base = Path('automated_outputs')
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
        """Create timestamped output directory"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_output_dir = self.output_base / f"matlab_safe_run_{timestamp}"
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
        
    def find_image_files(self):
        """Find image .tdms files"""
        pattern = os.path.join(self.data_folder, '*image4D_18x18_0p75gcm_file.tdms')
        tdms_files = glob.glob(pattern)
        tdms_files.sort()
        return tdms_files[:12]  # First 12 files
        
    def create_proven_project(self):
        """Use the proven project creation method"""
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
        project_name = "matlab_safe_project.mat"
        return self.create_matlab_project(processed_files, project_name)
        
    def create_matlab_project(self, processed_files, project_name):
        """Create project using the proven MATLAB script method"""
        
        # Create the complete MATLAB script - same method that worked before
        script_content = f"""
function create_matlab_safe_project()
    disp('Creating MATLAB-safe ArbuzGUI project...');
    
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
        script_path = 'temp_matlab_safe_project.m'
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
            # Add process directory to path
            process_path = os.path.join(os.getcwd(), 'process')
            if process_path not in sys.path:
                sys.path.insert(0, process_path)
            
            # Import Draw_ROI
            import Draw_ROI
            
            # Use the API
            output_file = Draw_ROI.apply_kidney_roi_to_project(
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
    
    def copy_roi_using_matlab(self, roi_project_file):
        """Copy ROI to all images using MATLAB to maintain proper structure"""
        print("📋 Copying ROI to all images using MATLAB...")
        
        # Create MATLAB script to handle ROI copying in a MATLAB-safe way
        script_content = f"""
function copy_roi_matlab_safe()
    project_file = '{roi_project_file.replace(chr(92), '/')}';
    
    try
        % Load project
        project_data = load(project_file);
        
        if ~isfield(project_data, 'images')
            error('No images field found in project');
        end
        
        images = project_data.images;
        fprintf('Loaded project with %d images\\n', length(images));
        
        % Find ROI source (BE_AMP) - use simple indexing
        source_rois = [];
        source_idx = 0;
        
        for i = 1:length(images)
            img_name = '';
            
            % Extract name safely - handle different formats
            if isfield(images(i), 'Name')
                name_field = images(i).Name;
                if ischar(name_field)
                    img_name = name_field;
                elseif iscell(name_field) && ~isempty(name_field)
                    img_name = name_field{{1}};
                elseif isnumeric(name_field) && ~isempty(name_field)
                    img_name = char(name_field);
                end
            end
            
            if strcmp(img_name, 'BE_AMP')
                fprintf('Found BE_AMP at index %d\\n', i);
                if isfield(images(i), 'slaves') && ~isempty(images(i).slaves)
                    source_rois = images(i).slaves;
                    source_idx = i;
                    fprintf('Found ROIs in BE_AMP\\n');
                    break;
                end
            end
        end
        
        if isempty(source_rois)
            error('No ROIs found in BE_AMP');
        end
        
        % Copy ROIs to target images - minimal manipulation
        target_names = {{'BE1', 'BE2', 'BE3', 'BE4', 'ME1', 'ME2', 'ME3', 'ME4', 'AE1', 'AE2', 'AE3', 'AE4'}};
        copied_count = 0;
        
        for i = 1:length(images)
            img_name = '';
            
            % Extract name safely
            if isfield(images(i), 'Name')
                name_field = images(i).Name;
                if ischar(name_field)
                    img_name = name_field;
                elseif iscell(name_field) && ~isempty(name_field)
                    img_name = name_field{{1}};
                elseif isnumeric(name_field) && ~isempty(name_field)
                    img_name = char(name_field);
                end
            end
            
            % Check if this is a target image
            is_target = false;
            for j = 1:length(target_names)
                if strcmp(img_name, target_names{{j}})
                    is_target = true;
                    break;
                end
            end
            
            if is_target
                % Direct assignment - let MATLAB handle the structure
                images(i).slaves = source_rois;
                copied_count = copied_count + 1;
                fprintf('  Copied ROIs to %s\\n', img_name);
            end
        end
        
        % Update project data
        project_data.images = images;
        
        % Save using MATLAB (maintains proper structure)
        output_file = '{str(self.current_output_dir / f"complete_matlab_safe_{os.path.basename(roi_project_file)}").replace(chr(92), '/')}';
        save(output_file, '-struct', 'project_data');
        
        fprintf('ROIs copied to %d images\\n', copied_count);
        fprintf('Complete project saved: %s\\n', output_file);
        
    catch ME
        fprintf('Error in ROI copying: %s\\n', ME.message);
        rethrow(ME);
    end
end
        """
        
        script_path = 'temp_copy_roi.m'
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            self.eng.run(script_path[:-2], nargout=0)
            output_file = self.current_output_dir / f"complete_matlab_safe_{os.path.basename(roi_project_file)}"
            
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
                        roi_name = getattr(roi, 'Name', f'Kidney{i+1}')
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
                stats_file = self.current_output_dir / "matlab_safe_statistics.xlsx"
                df.to_excel(stats_file, index=False)
                print(f"✅ Statistics saved: {stats_file.name}")
                return str(stats_file)
            else:
                print("❌ No statistics extracted")
                return None
                
        except Exception as e:
            print(f"❌ Error extracting statistics: {e}")
            return None
    
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
    
    def cleanup(self):
        """Clean up MATLAB engine"""
        if self.eng:
            self.eng.quit()
            print("🧹 MATLAB engine closed")
    
    def run_pipeline(self):
        """Execute the complete pipeline"""
        print("🔬 MATLAB-Safe Medical Imaging Pipeline")
        print("=" * 50)
        print("MATLAB-Native Project Creation + Draw_ROI API + Statistics")
        print("=" * 50)
        
        try:
            # Setup
            self.setup_output_directory()
            self.start_matlab_engine()
            
            # Step 1: Create project
            print("\n📁 Step 1: Creating project using proven method...")
            project_file = self.create_proven_project()
            if not project_file:
                print("❌ Pipeline failed at project creation")
                return
            
            # Step 2: Apply ROI
            print("\n🎯 Step 2: Applying ROI using Draw_ROI API...")
            roi_project = self.apply_roi_with_draw_roi(project_file)
            if not roi_project:
                print("❌ Pipeline failed at ROI application")
                return
            
            # Step 3: Copy ROI using MATLAB
            print("\n📋 Step 3: Copying ROI using MATLAB...")
            complete_project = self.copy_roi_using_matlab(roi_project)
            if not complete_project:
                print("❌ Pipeline failed at ROI copying")
                return
            
            # Step 4: Extract statistics
            print("\n📊 Step 4: Extracting statistics...")
            stats_file = self.extract_statistics(complete_project)
            
            # Summary
            print("\n🎉 MATLAB-SAFE PIPELINE COMPLETE!")
            print(f"📁 Output: {self.current_output_dir}")
            print(f"📄 Final project: {os.path.basename(complete_project)}")
            if stats_file:
                print(f"📊 Statistics: {os.path.basename(stats_file)}")
            
            print(f"\n✅ Success! Results in: {self.current_output_dir}")
            
        except Exception as e:
            print(f"\n❌ Pipeline failed: {e}")
        finally:
            self.cleanup()

def main():
    """Main function"""
    pipeline = CleanMedicalPipeline()
    pipeline.run_pipeline()

if __name__ == "__main__":
    main()
