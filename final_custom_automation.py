# """
# Final working Python automation for EPRI data processing
# Uses the successful approach with your exact naming requirements:
# BE1-BE4 (Pre-transfusion), ME1-ME4 (Mid-transfusion), AE1-AE4 (Post-transfusion), BE_AMP
# """

# import matlab.engine
# import os
# import glob
# import time
# from pathlib import Path

# class FinalEPRIAutomation:
#     def __init__(self):
#         self.eng = None
#         self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        
#     def start_matlab_engine(self):
#         """Initialize MATLAB engine and add necessary paths"""
#         print("Starting MATLAB engine...")
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
        
#         print(f"Found {len(tdms_files)} image .tdms files:")
#         for i, f in enumerate(tdms_files[:12]):  # Show only first 12
#             print(f"   {i+1:2d}. {Path(f).name}")
        
#         return tdms_files[:12]  # Return only first 12 files
        
#     def process_tdms_file(self, tdms_file):
#         """Process a single .tdms file using MATLAB ese_fbp"""
#         print(f"Processing {Path(tdms_file).name}...")
        
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
#                 print(f"  Warning: Output files not found")
#                 return None, None
                
#         except Exception as e:
#             print(f"  Error processing {tdms_file}: {e}")
#             return None, None
    
#     def create_custom_matlab_script(self, processed_files, project_name):
#         """Create a custom MATLAB script with your exact naming requirements"""
#         print("Creating custom project with your exact naming...")
        
#         # Create a MATLAB script file with your naming requirements
#         script_content = """
# function create_custom_project()
#     % Create project with exact naming requirements
#     disp('Creating project with BE1-BE4, ME1-ME4, AE1-AE4, BE_AMP...');
    
#     % Launch ArbuzGUI
#     hGUI = ArbuzGUI();
#     pause(2);
    
#     if isempty(hGUI) || ~isvalid(hGUI)
#         error('Failed to launch ArbuzGUI');
#     end
    
#     disp('ArbuzGUI launched successfully');
    
#     % File paths and names with your exact requirements
#     files = {
# """
        
#         # Your exact naming requirements:
#         # Pre-transfusion: BE1, BE2, BE3, BE4
#         # Mid-transfusion: ME1, ME2, ME3, ME4  
#         # Post-transfusion: AE1, AE2, AE3, AE4
#         # Special: BE_AMP (amplitude version of BE1)
        
#         naming_scheme = [
#             ('BE_AMP', 'AMP_pEPRI', 0),  # Amplitude version of first file
#             ('BE1', 'PO2_pEPRI', 0),     # Pre-transfusion
#             ('BE2', 'PO2_pEPRI', 1),     
#             ('BE3', 'PO2_pEPRI', 2),     
#             ('BE4', 'PO2_pEPRI', 3),     
#             ('ME1', 'PO2_pEPRI', 4),     # Mid-transfusion
#             ('ME2', 'PO2_pEPRI', 5),     
#             ('ME3', 'PO2_pEPRI', 6),     
#             ('ME4', 'PO2_pEPRI', 7),     
#             ('AE1', 'PO2_pEPRI', 8),     # Post-transfusion
#             ('AE2', 'PO2_pEPRI', 9),     
#             ('AE3', 'PO2_pEPRI', 10),    
#             ('AE4', 'PO2_pEPRI', 11)     
#         ]
        
#         # Add file information to the script
#         for name, img_type, file_idx in naming_scheme:
#             if file_idx < len(processed_files):
#                 _, p_file = processed_files[file_idx]
#                 safe_path = str(p_file).replace('\\', '/')
#                 script_content += f"        '{safe_path}', '{name}', '{img_type}';\n"
        
#         script_content += """
#     };
    
#     % Add all images
#     success_count = 0;
#     for i = 1:size(files, 1)
#         try
#             add_image_to_gui(hGUI, files{i,1}, files{i,2}, files{i,3});
#             success_count = success_count + 1;
#             disp(['Added: ', files{i,2}, ' [', files{i,3}, ']']);
#         catch ME
#             disp(['Error adding ', files{i,2}, ': ', ME.message]);
#         end
#         pause(0.2);
#     end
    
#     disp(['Successfully added ', num2str(success_count), ' images']);
    
#     % Save project
#     project_path = fullfile(pwd, '""" + project_name + """');
#     try
#         arbuz_SaveProject(hGUI, project_path);
#         disp(['Project saved: ', project_path]);
#     catch ME
#         disp(['Error saving project: ', ME.message]);
#     end
    
#     % Verify project
#     try
#         projectData = load(project_path);
#         if isfield(projectData, 'images')
#             images = projectData.images;
#             num_images = size(images, 2);
#             disp(['Project verification: ', num2str(num_images), ' images found']);
            
#             % List images
#             for i = 1:min(num_images, 15)
#                 try
#                     img = images(1, i);
#                     if iscell(img.Name)
#                         name = img.Name{1};
#                     else
#                         name = img.Name;
#                     end
#                     if iscell(img.ImageType)
#                         img_type = img.ImageType{1};
#                     else
#                         img_type = img.ImageType;
#                     end
#                     disp(['  ', num2str(i), ': ', name, ' (', img_type, ')']);
#                 catch
#                     disp(['  ', num2str(i), ': Error reading image']);
#                 end
#             end
#         else
#             disp('No images field found in project');
#         end
#     catch ME
#         disp(['Error verifying project: ', ME.message]);
#     end
    
# end

# function add_image_to_gui(hGUI, file_path, image_name, image_type)
#     % Helper function to add image to ArbuzGUI
    
#     % Inject AutoAccept flag if needed
#     try
#         tmp = load(file_path);
#         if isfield(tmp, 'pO2_info')
#             tmp.pO2_info.AutoAccept = true;
#             save(file_path, '-struct', 'tmp');
#         end
#     catch
#         % Ignore errors
#     end
    
#     % Create image structure
#     imageStruct = struct();
#     imageStruct.FileName = file_path;
#     imageStruct.Name = image_name;
#     imageStruct.ImageType = image_type;
#     imageStruct.isStore = 1;
#     imageStruct.isLoaded = 0;
    
#     % Load image data
#     [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
    
#     % Complete image structure
#     imageStruct.data = imageData;
#     imageStruct.data_info = imageInfo;
#     imageStruct.ImageType = actualType;
    
#     if isfield(imageInfo, 'Bbox')
#         imageStruct.box = imageInfo.Bbox;
#     else
#         imageStruct.box = size(imageData);
#     end
    
#     if isfield(imageInfo, 'Anative')
#         imageStruct.Anative = imageInfo.Anative;
#     else
#         imageStruct.Anative = eye(4);
#     end
    
#     imageStruct.isLoaded = 1;
    
#     % Add to ArbuzGUI
#     arbuz_AddImage(hGUI, imageStruct);
    
#     % Handle slaves for AMP images
#     if contains(image_name, 'AMP') && ~isempty(slaveImages)
#         try
#             idxCell = arbuz_FindImage(hGUI, 'master', 'Name', image_name, {'ImageIdx'});
#             if ~isempty(idxCell)
#                 masterIdx = idxCell{1}.ImageIdx;
#                 for k = 1:length(slaveImages)
#                     arbuz_AddImage(hGUI, slaveImages{k}, masterIdx);
#                 end
#                 disp(['    Added ', num2str(length(slaveImages)), ' slaves']);
#             end
#         catch
#             % Continue if slave addition fails
#         end
#     end
    
#     % Clean AutoAccept flag
#     try
#         tmp = load(file_path);
#         if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
#             tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
#             save(file_path, '-struct', 'tmp');
#         end
#     catch
#         % Ignore errors
#     end
# end
#         """
        
#         # Write the script file
#         script_path = 'create_custom_project.m'
#         with open(script_path, 'w', encoding='utf-8') as f:
#             f.write(script_content)
        
#         try:
#             # Run the MATLAB script
#             print("Running custom project creation...")
#             self.eng.create_custom_project(nargout=0)
            
#             print("✅ Custom project creation completed")
#             return True
            
#         except Exception as e:
#             print(f"Error running custom script: {e}")
#             return False
#         finally:
#             # Clean up temporary script
#             if os.path.exists(script_path):
#                 os.remove(script_path)
    
#     def cleanup(self):
#         """Clean up MATLAB engine"""
#         if self.eng:
#             try:
#                 self.eng.quit()
#                 print("MATLAB engine closed")
#             except:
#                 pass
                
#     def run_automation(self):
#         """Run the complete automation pipeline"""
#         print("🔬 Final EPRI Automation with Your Exact Naming")
#         print("BE1-BE4 (Pre), ME1-ME4 (Mid), AE1-AE4 (Post), BE_AMP")
#         print("=" * 55)
        
#         try:
#             # Step 1: Initialize MATLAB engine
#             self.start_matlab_engine()
            
#             # Step 2: Find image files
#             tdms_files = self.find_image_files()
#             if not tdms_files:
#                 raise ValueError("No image .tdms files found")
            
#             # Step 3: Process .tdms files
#             print(f"\\nProcessing {len(tdms_files)} .tdms files...")
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
            
#             # Step 4: Create custom project with your exact naming
#             project_name = "final_custom_project.mat"
#             if self.create_custom_matlab_script(processed_files, project_name):
#                 print(f"\\n🎉 SUCCESS: Project created with your exact naming!")
#                 print(f"📄 Project file: {project_name}")
#                 print("\\n🎯 Images created:")
#                 print("   BE_AMP (amplitude), BE1-BE4 (Pre-transfusion)")
#                 print("   ME1-ME4 (Mid-transfusion), AE1-AE4 (Post-transfusion)")
#             else:
#                 print("\\n❌ Project creation failed")
            
#         except Exception as e:
#             print(f"❌ Automation failed: {e}")
            
#         finally:
#             self.cleanup()

# def main():
#     """Main entry point"""
#     automation = FinalEPRIAutomation()
#     automation.run_automation()

# if __name__ == "__main__":
#     main()
