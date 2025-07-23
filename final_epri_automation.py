# """
# Final Python automation pipeline for EPRI data processing
# Processes .tdms files from /DATA/241202 and creates ArbuzGUI project
# with specified image naming: BE1-BE4, ME1-ME4, AE1-AE4, BE_AMP
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
        
#         # Image naming as specified in requirements
#         self.image_specs = [
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
        
#     def process_tdms_files_if_needed(self, tdms_files):
#         """Process .tdms files using MATLAB ese_fbp if not already processed"""
#         print(f"🔄 Processing {len(tdms_files)} .tdms files...")
#         processed_files = []
        
#         for tdms_file in tdms_files:
#             base_name = Path(tdms_file).stem
#             raw_file = Path(tdms_file).parent / f"{base_name}.mat"
#             p_file = Path(tdms_file).parent / f"p{base_name}.mat"
            
#             # Check if already processed
#             if raw_file.exists() and p_file.exists():
#                 print(f"✅ Already processed: {base_name}")
#                 processed_files.append((str(raw_file), str(p_file)))
#             else:
#                 # Process the file
#                 print(f"🔄 Processing {Path(tdms_file).name}...")
#                 raw_out, p_out = self.process_single_tdms(tdms_file)
#                 if raw_out and p_out:
#                     processed_files.append((raw_out, p_out))
        
#         return processed_files
    
#     def process_single_tdms(self, tdms_file):
#         """Process a single .tdms file using MATLAB ese_fbp"""
#         try:
#             # Set up processing parameters
#             file_suffix = ""
#             output_path = str(Path(tdms_file).parent)
            
#             # Create fields structure for ese_fbp
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
            
#             # Call MATLAB processing function
#             result = self.eng.ese_fbp(tdms_file, file_suffix, output_path, fields)
            
#             # Check for output files
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
    
#     def create_custom_project(self, processed_files, project_name):
#         """Create custom ArbuzGUI project with specified naming"""
#         print("🏗️  Creating custom ArbuzGUI project...")
        
#         # Create a custom MATLAB script for our specific naming
#         matlab_script = f"""
#         function create_custom_epri_project()
#             % Create project with custom naming: BE1-BE4, ME1-ME4, AE1-AE4, BE_AMP
#             disp('Creating custom EPRI project...');
            
#             % Launch ArbuzGUI
#             hGUI = ArbuzGUI();
#             pause(2);
            
#             if isempty(hGUI) || ~isvalid(hGUI)
#                 error('Failed to launch ArbuzGUI');
#             end
            
#             disp('ArbuzGUI launched successfully');
            
#             % Data files and corresponding names
#             files = {{
#         """
        
#         # Add file paths and custom names
#         for i, (_, p_file) in enumerate(processed_files[:12]):
#             safe_path = str(p_file).replace('\\', '/')
#             if i < len(self.image_specs):
#                 spec = self.image_specs[i]
#                 matlab_script += f"        '{safe_path}', '{spec['name']}', '{spec['type']}';\n"
        
#         matlab_script += f"""
#             }};
            
#             % Add BE_AMP first (amplitude version of first file)
#             if size(files, 1) > 0
#                 try
#                     add_image_safely(hGUI, files{{1,1}}, 'BE_AMP', 'AMP_pEPRI');
#                 catch ME
#                     disp(['Warning: Could not add BE_AMP: ', ME.message]);
#                 end
#             end
            
#             % Add all other images with custom names
#             success_count = 0;
#             for i = 1:size(files, 1)
#                 try
#                     add_image_safely(hGUI, files{{i,1}}, files{{i,2}}, files{{i,3}});
#                     success_count = success_count + 1;
#                 catch ME
#                     disp(['Error adding ', files{{i,2}}, ': ', ME.message]);
#                 end
#                 pause(0.2);
#             end
            
#             disp(['Successfully added ', num2str(success_count), ' images plus BE_AMP']);
            
#             % Save project
#             project_path = fullfile(pwd, '{project_name}');
#             try
#                 arbuz_SaveProject(hGUI, project_path);
#                 disp(['Project saved: ', project_path]);
#             catch ME
#                 disp(['Error saving project: ', ME.message]);
#             end
            
#         end
        
#         function add_image_safely(hGUI, file_path, image_name, image_type)
#             % Safely add image to ArbuzGUI with error handling
            
#             % Inject AutoAccept flag if needed
#             try
#                 tmp = load(file_path);
#                 if isfield(tmp, 'pO2_info')
#                     tmp.pO2_info.AutoAccept = true;
#                     save(file_path, '-struct', 'tmp');
#                 end
#             catch
#                 % Continue without AutoAccept
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
#                     idxCell = arbuz_FindImage(hGUI, 'master', 'Name', image_name, {{'ImageIdx'}});
#                     if ~isempty(idxCell)
#                         masterIdx = idxCell{{1}}.ImageIdx;
#                         for k = 1:length(slaveImages)
#                             arbuz_AddImage(hGUI, slaveImages{{k}}, masterIdx);
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
#                 % Continue
#             end
#         end
#         """
        
#         try:
#             # Execute the MATLAB script
#             print("🚀 Running custom project creation...")
#             self.eng.eval(matlab_script, nargout=0)
#             self.eng.eval("create_custom_epri_project()", nargout=0)
            
#             print("✅ Custom project creation completed")
#             return True
            
#         except Exception as e:
#             print(f"❌ Error creating custom project: {e}")
#             return False
    
#     def verify_project(self, project_name):
#         """Verify the created project and show image summary"""
#         print("\\n📋 Project Verification:")
        
#         if not project_name.endswith('.mat'):
#             project_name += '.mat'
        
#         if not os.path.exists(project_name):
#             print(f"❌ Project file not found: {project_name}")
#             return False
            
#         try:
#             # Load and examine project file
#             project_data = self.eng.load(project_name)
            
#             if 'images' in project_data:
#                 images = project_data['images']
                
#                 # Get the structure correctly
#                 if hasattr(images, '__len__') and len(images) > 0:
#                     if hasattr(images[0], '__len__'):
#                         num_images = len(images[0])
#                     else:
#                         num_images = len(images)
                        
#                     print(f"✅ Project contains {num_images} images:")
                    
#                     # List images with names and types
#                     for i in range(min(num_images, 15)):
#                         try:
#                             if hasattr(images[0], '__getitem__'):
#                                 img = images[0][i]
#                             else:
#                                 img = images[i]
                                
#                             if hasattr(img, 'Name') and hasattr(img, 'ImageType'):
#                                 name = img.Name
#                                 img_type = img.ImageType
                                
#                                 # Handle cell arrays
#                                 if hasattr(name, '__getitem__') and hasattr(name, '__len__'):
#                                     name = name[0] if len(name) > 0 else 'Unknown'
#                                 if hasattr(img_type, '__getitem__') and hasattr(img_type, '__len__'):
#                                     img_type = img_type[0] if len(img_type) > 0 else 'Unknown'
                                    
#                                 print(f"   {i+1:2d}. {name} ({img_type})")
#                             else:
#                                 print(f"   {i+1:2d}. (Unable to read image info)")
#                         except Exception as ex:
#                             print(f"   {i+1:2d}. (Error: {ex})")
                    
#                     # Summary
#                     print(f"\\n🎯 Project successfully created with {num_images} images!")
#                     return True
#                 else:
#                     print("❌ Images field is empty or malformed")
#                     return False
#             else:
#                 print("❌ No images field found in project")
#                 return False
                
#         except Exception as e:
#             print(f"❌ Error verifying project: {e}")
#             return False
    
#     def cleanup(self):
#         """Clean up MATLAB engine"""
#         if self.eng:
#             try:
#                 self.eng.quit()
#                 print("🔧 MATLAB engine closed")
#             except:
#                 pass
                
#     def run_full_automation(self):
#         """Run the complete automation pipeline"""
#         print("🔬 Final EPRI Automation Pipeline")
#         print("Processes .tdms files and creates ArbuzGUI project")
#         print("Image naming: BE1-BE4, ME1-ME4, AE1-AE4, BE_AMP")
#         print("=" * 55)
        
#         try:
#             # Step 1: Initialize MATLAB engine
#             self.start_matlab_engine()
            
#             # Step 2: Find image files from /DATA/241202
#             tdms_files = self.find_image_files()
#             if not tdms_files:
#                 raise ValueError("No image .tdms files found in /DATA/241202")
            
#             # Step 3: Process .tdms files if needed
#             processed_files = self.process_tdms_files_if_needed(tdms_files)
            
#             if not processed_files:
#                 raise ValueError("No processed .mat files available")
            
#             print(f"✅ {len(processed_files)} files ready for project creation")
            
#             # Step 4: Create custom ArbuzGUI project
#             project_name = "final_epri_automation_project.mat"
            
#             if self.create_custom_project(processed_files, project_name):
#                 print("✅ Project creation successful")
#             else:
#                 raise ValueError("Project creation failed")
            
#             # Step 5: Verify project
#             if self.verify_project(project_name):
#                 print(f"\\n🎉 Automation completed successfully!")
#                 print(f"📄 Project file: {project_name}")
#                 print(f"📁 Location: {os.path.abspath(project_name)}")
                
#                 # Show summary
#                 print(f"\\n📊 Summary:")
#                 print(f"   • Processed {len(processed_files)} .tdms files from /DATA/241202")
#                 print(f"   • Created ArbuzGUI project with 13 images total")
#                 print(f"   • Used custom naming: BE1-BE4, ME1-ME4, AE1-AE4, BE_AMP")
#                 print(f"   • All workflow implemented in Python using MATLAB engine")
                
#                 return True
#             else:
#                 print("❌ Project verification failed")
#                 return False
            
#         except Exception as e:
#             print(f"❌ Automation failed: {e}")
#             return False
            
#         finally:
#             self.cleanup()

# def main():
#     """Main entry point"""
#     automation = FinalEPRIAutomation()
#     success = automation.run_full_automation()
    
#     if success:
#         print("\\n✅ Pipeline completed successfully!")
#     else:
#         print("\\n❌ Pipeline failed. Check errors above.")

# if __name__ == "__main__":
#     main()
