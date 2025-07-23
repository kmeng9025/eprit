# """
# Simplified Python automation pipeline for processing medical imaging data
# Uses direct MATLAB function calls instead of eval for better reliability
# """

# import matlab.engine
# import os
# import glob
# import time
# from pathlib import Path

# class SimpleEPRIAutomation:
#     def __init__(self):
#         self.eng = None
#         self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        
#         # Image naming as specified in requirements
#         self.image_mapping = [
#             # Pre-transfusion (BE)
#             {'name': 'BE1', 'type': 'PO2_pEPRI'},
#             {'name': 'BE2', 'type': 'PO2_pEPRI'},
#             {'name': 'BE3', 'type': 'PO2_pEPRI'},
#             {'name': 'BE4', 'type': 'PO2_pEPRI'},
            
#             # Mid-transfusion (ME)
#             {'name': 'ME1', 'type': 'PO2_pEPRI'},
#             {'name': 'ME2', 'type': 'PO2_pEPRI'},
#             {'name': 'ME3', 'type': 'PO2_pEPRI'},
#             {'name': 'ME4', 'type': 'PO2_pEPRI'},
            
#             # Post-transfusion (AE)
#             {'name': 'AE1', 'type': 'PO2_pEPRI'},
#             {'name': 'AE2', 'type': 'PO2_pEPRI'},
#             {'name': 'AE3', 'type': 'PO2_pEPRI'},
#             {'name': 'AE4', 'type': 'PO2_pEPRI'}
#         ]
        
#     def start_matlab_engine(self):
#         """Initialize MATLAB engine and add necessary paths"""
#         print("🔧 Starting MATLAB engine...")
#         self.eng = matlab.engine.start_matlab()
        
#         # Add necessary paths
#         paths = [
#             r'c:\Users\ftmen\Documents\v3',
#             r'c:\Users\ftmen\Documents\v3\Arbuz2.0',
#             r'c:\Users\ftmen\Documents\v3\epri',
#             r'c:\Users\ftmen\Documents\v3\common',
#             r'c:\Users\ftmen\Documents\v3\process'
#         ]
        
#         for path in paths:
#             self.eng.addpath(path, nargout=0)
        
#         print("✅ MATLAB engine started and paths added")
        
#     def find_image_files(self):
#         """Find image .tdms files (excluding FID_GRAD_MIN files)"""
#         pattern = os.path.join(self.data_folder, '*image4D_18x18_0p75gcm_file.tdms')
#         tdms_files = glob.glob(pattern)
#         tdms_files.sort()  # Sort to ensure consistent ordering
        
#         print(f"📁 Found {len(tdms_files)} image .tdms files:")
#         for i, f in enumerate(tdms_files[:12]):  # Show only first 12
#             print(f"   {i+1:2d}. {Path(f).name}")
        
#         return tdms_files[:12]  # Return only first 12 files
        
#     def process_tdms_file(self, tdms_file):
#         """Process a single .tdms file using MATLAB ese_fbp"""
#         print(f"🔄 Processing {Path(tdms_file).name}...")
        
#         try:
#             # Set up processing parameters
#             file_suffix = ""
#             output_path = str(Path(tdms_file).parent)
            
#             # Create simplified fields structure for ese_fbp
#             fields = {
#                 'prc': {'process_method': 'ese_fbp', 'save_data': 'yes', 'fit_data': 'yes', 'recon_data': 'yes'},
#                 'fbp': {'MaxGradient': 8.0, 'projection_order': 'default'},
#                 'rec': {'Size': 1, 'Sub_points': 64},
#                 'td': {'off_res_baseline': 'yes', 'prj_transpose': 'no'},
#                 'fft': {'FOV': 1, 'xshift_mode': 'none'},
#                 'clb': {'amp1mM': 1, 'ampHH': 1, 'Torr_per_mGauss': 1.84},
#                 'fit': {},
#                 'img': {'mirror_image': [0, 0, 0], 'reg_method': 'none'}
#             }
            
#             # Call MATLAB processing function directly
#             result = self.eng.ese_fbp(tdms_file, file_suffix, output_path, fields)
            
#             # Generate expected output filenames
#             base_name = Path(tdms_file).stem
#             raw_file = Path(tdms_file).parent / f"{base_name}.mat"
#             p_file = Path(tdms_file).parent / f"p{base_name}.mat"
            
#             if raw_file.exists() and p_file.exists():
#                 print(f"  ✅ Generated: {raw_file.name} and {p_file.name}")
#                 return str(raw_file), str(p_file)
#             else:
#                 print(f"  ⚠️  Output files not found")
#                 return None, None
                
#         except Exception as e:
#             print(f"  ❌ Error processing {tdms_file}: {e}")
#             return None, None
            
#     def create_project_using_matlab_script(self, processed_files, project_name):
#         """Create project using a custom MATLAB script approach"""
#         print("🏗️  Creating ArbuzGUI project using MATLAB backend...")
        
#         # Create a temporary MATLAB script to handle the workflow
#         temp_script = f"""
#         function create_python_project()
#             % Create project with images using proper ArbuzGUI workflow
#             disp('Starting Python-driven project creation...');
            
#             % Launch ArbuzGUI
#             hGUI = ArbuzGUI();
#             pause(2);
            
#             if isempty(hGUI) || ~isvalid(hGUI)
#                 error('Failed to launch ArbuzGUI');
#             end
            
#             disp('ArbuzGUI launched successfully');
            
#             % File paths and names
#             files = {{
#         """
        
#         # Add file information to the script
#         for i, (_, p_file) in enumerate(processed_files[:12]):
#             safe_path = str(p_file).replace('\\', '/')
#             if i < len(self.image_mapping):
#                 image_info = self.image_mapping[i]
#                 temp_script += f"        '{safe_path}', '{image_info['name']}', '{image_info['type']}';\n"
        
#         temp_script += """
#             };
            
#             % Add BE_AMP first (amplitude version of first file)
#             if size(files, 1) > 0
#                 try
#                     add_image_to_gui(hGUI, files{1,1}, 'BE_AMP', 'AMP_pEPRI');
#                 catch ME
#                     disp(['Warning: Could not add BE_AMP: ', ME.message]);
#                 end
#             end
            
#             % Add all other images
#             success_count = 0;
#             for i = 1:size(files, 1)
#                 try
#                     add_image_to_gui(hGUI, files{i,1}, files{i,2}, files{i,3});
#                     success_count = success_count + 1;
#                 catch ME
#                     disp(['Error adding ', files{i,2}, ': ', ME.message]);
#                 end
#                 pause(0.2);
#             end
            
#             disp(['Added ', num2str(success_count), ' images']);
            
#             % Save project
#             project_path = fullfile(pwd, '""" + project_name + """');
#             try
#                 arbuz_SaveProject(hGUI, project_path);
#                 disp(['Project saved: ', project_path]);
#             catch ME
#                 disp(['Error saving project: ', ME.message]);
#             end
            
#         end
        
#         function add_image_to_gui(hGUI, file_path, image_name, image_type)
#             % Helper function to add image to ArbuzGUI
            
#             % Inject AutoAccept flag if needed
#             try
#                 tmp = load(file_path);
#                 if isfield(tmp, 'pO2_info')
#                     tmp.pO2_info.AutoAccept = true;
#                     save(file_path, '-struct', 'tmp');
#                 end
#             catch
#                 % Ignore errors
#             end
            
#             % Create image structure
#             imageStruct = struct();
#             imageStruct.FileName = file_path;
#             imageStruct.Name = image_name;
#             imageStruct.ImageType = image_type;
#             imageStruct.isStore = 1;
#             imageStruct.isLoaded = 0;
            
#             % Load image data
#             [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
            
#             % Complete image structure
#             imageStruct.data = imageData;
#             imageStruct.data_info = imageInfo;
#             imageStruct.ImageType = actualType;
            
#             if isfield(imageInfo, 'Bbox')
#                 imageStruct.box = imageInfo.Bbox;
#             else
#                 imageStruct.box = size(imageData);
#             end
            
#             if isfield(imageInfo, 'Anative')
#                 imageStruct.Anative = imageInfo.Anative;
#             else
#                 imageStruct.Anative = eye(4);
#             end
            
#             imageStruct.isLoaded = 1;
            
#             % Add to ArbuzGUI
#             arbuz_AddImage(hGUI, imageStruct);
            
#             disp(['  Added: ', image_name, ' [', actualType, ']']);
            
#             % Handle slaves for AMP images
#             if contains(image_name, 'AMP') && ~isempty(slaveImages)
#                 try
#                     idxCell = arbuz_FindImage(hGUI, 'master', 'Name', image_name, {'ImageIdx'});
#                     if ~isempty(idxCell)
#                         masterIdx = idxCell{1}.ImageIdx;
#                         for k = 1:length(slaveImages)
#                             arbuz_AddImage(hGUI, slaveImages{k}, masterIdx);
#                         end
#                         disp(['    Added ', num2str(length(slaveImages)), ' slaves']);
#                     end
#                 catch
#                     % Continue if slave addition fails
#                 end
#             end
            
#             % Clean AutoAccept flag
#             try
#                 tmp = load(file_path);
#                 if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
#                     tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
#                     save(file_path, '-struct', 'tmp');
#                 end
#             catch
#                 % Ignore errors
#             end
#         end
#         """
        
#         # Write the temporary script
#         script_path = 'temp_create_project.m'
#         with open(script_path, 'w', encoding='utf-8') as f:
#             f.write(temp_script)
        
#         try:
#             # Execute the MATLAB script content directly
#             print("🚀 Running MATLAB project creation script...")
#             self.eng.eval(temp_script, nargout=0)
#             self.eng.eval("create_python_project()", nargout=0)
            
#             print("✅ Project creation completed")
            
#         except Exception as e:
#             print(f"❌ Error running MATLAB script: {e}")
#         finally:
#             # Clean up temporary script
#             if os.path.exists(script_path):
#                 os.remove(script_path)
                
#     def verify_project(self, project_name):
#         """Verify the created project"""
#         print("\\n📋 Project Verification:")
        
#         if not project_name.endswith('.mat'):
#             project_name += '.mat'
        
#         if not os.path.exists(project_name):
#             print(f"❌ Project file not found: {project_name}")
#             return
            
#         try:
#             # Load and examine project file
#             project_data = self.eng.load(project_name)
            
#             if 'images' in project_data:
#                 images = project_data['images']
#                 num_images = len(images[0]) if hasattr(images, '__len__') else 0
                
#                 print(f"✅ Project contains {num_images} images")
                
#                 # Try to get image names
#                 for i in range(min(num_images, 15)):  # Limit output
#                     try:
#                         img = images[0][i] if hasattr(images[0], '__getitem__') else None
#                         if img and hasattr(img, 'Name') and hasattr(img, 'ImageType'):
#                             name = img.Name
#                             img_type = img.ImageType
#                             print(f"   {i+1:2d}. {name} ({img_type})")
#                     except:
#                         print(f"   {i+1:2d}. (Error reading image info)")
                        
#                 print(f"🎯 Project verification completed")
#             else:
#                 print("❌ No images field found in project")
                
#         except Exception as e:
#             print(f"❌ Error verifying project: {e}")
    
#     def cleanup(self):
#         """Clean up MATLAB engine"""
#         if self.eng:
#             try:
#                 self.eng.quit()
#                 print("🔧 MATLAB engine closed")
#             except:
#                 pass
                
#     def run_automation(self):
#         """Run the complete automation pipeline"""
#         print("🔬 Simple EPRI Automation Pipeline")
#         print("=" * 50)
        
#         try:
#             # Step 1: Initialize MATLAB engine
#             self.start_matlab_engine()
            
#             # Step 2: Find image files
#             tdms_files = self.find_image_files()
#             if not tdms_files:
#                 raise ValueError("No image .tdms files found")
            
#             # Step 3: Process .tdms files
#             print(f"\\n🔄 Processing {len(tdms_files)} .tdms files...")
#             processed_files = []
            
#             for tdms_file in tdms_files:
#                 base_name = Path(tdms_file).stem
#                 raw_file = Path(tdms_file).parent / f"{base_name}.mat"
#                 p_file = Path(tdms_file).parent / f"p{base_name}.mat"
                
#                 # Check if already processed
#                 if raw_file.exists() and p_file.exists():
#                     print(f"✅ Already processed: {base_name}")
#                     processed_files.append((str(raw_file), str(p_file)))
#                 else:
#                     # Process the file
#                     raw_out, p_out = self.process_tdms_file(tdms_file)
#                     if raw_out and p_out:
#                         processed_files.append((raw_out, p_out))
            
#             if not processed_files:
#                 raise ValueError("No processed .mat files available")
            
#             print(f"✅ {len(processed_files)} files ready for project creation")
            
#             # Step 4: Create ArbuzGUI project using MATLAB backend
#             project_name = "epri_simple_automation.mat"
#             self.create_project_using_matlab_script(processed_files, project_name)
            
#             # Step 5: Verify project
#             self.verify_project(project_name)
            
#             print(f"\\n🎉 Automation completed!")
#             print(f"📄 Project file: {project_name}")
            
#         except Exception as e:
#             print(f"❌ Automation failed: {e}")
            
#         finally:
#             self.cleanup()

# def main():
#     """Main entry point"""
#     automation = SimpleEPRIAutomation()
#     automation.run_automation()

# if __name__ == "__main__":
#     main()
