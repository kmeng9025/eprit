# """
# Direct Python automation for EPRI data processing
# Uses existing MATLAB functions directly without complex scripting
# """

# import matlab.engine
# import os
# import glob
# import time
# from pathlib import Path

# class DirectEPRIAutomation:
#     def __init__(self):
#         self.eng = None
#         self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        
#         # Image naming as specified in requirements
#         self.image_names = [
#             'BE1', 'BE2', 'BE3', 'BE4',     # Pre-transfusion
#             'ME1', 'ME2', 'ME3', 'ME4',     # Mid-transfusion  
#             'AE1', 'AE2', 'AE3', 'AE4'      # Post-transfusion
#         ]
        
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
    
#     def use_existing_matlab_script(self, processed_files, project_name):
#         """Use the existing load13ImagesIntoArbuz.m script with modifications"""
#         print("Using existing MATLAB script for project creation...")
        
#         # Check if the script exists
#         script_path = 'load13ImagesIntoArbuz.m'
#         if not os.path.exists(script_path):
#             print(f"Error: {script_path} not found")
#             return False
        
#         try:
#             # Modify the script to use our processed files
#             # First, let's call the existing MATLAB script directly
#             print("Calling load13ImagesIntoArbuz MATLAB function...")
            
#             # The existing script loads 13 images, but we only have 12 + BE_AMP
#             # Let's try to call it and see what happens
#             self.eng.load13ImagesIntoArbuz(nargout=0)
            
#             print("✅ MATLAB script execution completed")
#             return True
            
#         except Exception as e:
#             print(f"Error running MATLAB script: {e}")
#             return False
    
#     def create_simple_project_manually(self, processed_files, project_name):
#         """Create a simple project file manually using MATLAB data structures"""
#         print("Creating project manually...")
        
#         try:
#             # Load the reference project to understand the structure
#             ref_path = r'c:\Users\ftmen\Documents\v3\process\exampleCorrect\correctExample.mat'
#             if os.path.exists(ref_path):
#                 print("Loading reference project structure...")
#                 ref_data = self.eng.load(ref_path)
#                 print("Reference loaded successfully")
            
#             # Create a basic project structure
#             project_data = {}
#             images_list = []
            
#             # Add BE_AMP first (amplitude version of first file)
#             if processed_files:
#                 first_p_file = processed_files[0][1]
#                 try:
#                     # Load the processed data
#                     mat_data = self.eng.load(first_p_file)
                    
#                     # Create BE_AMP image structure  
#                     be_amp = {
#                         'Name': 'BE_AMP',
#                         'ImageType': 'AMP_pEPRI',
#                         'FileName': first_p_file,
#                         'isLoaded': 1,
#                         'isStore': 1,
#                         'Selected': 0,
#                         'Visible': 0
#                     }
                    
#                     # Add amplitude data if available
#                     if 'Amp' in mat_data:
#                         be_amp['data'] = mat_data['Amp']
                    
#                     images_list.append(be_amp)
#                     print("  Added BE_AMP")
                    
#                 except Exception as e:
#                     print(f"  Error creating BE_AMP: {e}")
            
#             # Add the other 12 images
#             for i, (_, p_file) in enumerate(processed_files[:12]):
#                 if i < len(self.image_names):
#                     try:
#                         # Load the processed data
#                         mat_data = self.eng.load(p_file)
                        
#                         # Create image structure
#                         image = {
#                             'Name': self.image_names[i],
#                             'ImageType': 'PO2_pEPRI',
#                             'FileName': p_file,
#                             'isLoaded': 1,
#                             'isStore': 1,
#                             'Selected': 0,
#                             'Visible': 0
#                         }
                        
#                         # Add pO2 data if available
#                         if 'pO2' in mat_data:
#                             image['data'] = mat_data['pO2']
                        
#                         images_list.append(image)
#                         print(f"  Added {self.image_names[i]}")
                        
#                     except Exception as e:
#                         print(f"  Error creating {self.image_names[i]}: {e}")
            
#             # Create project structure
#             project_data['images'] = images_list
#             project_data['file_type'] = 'Reg_v2.0'
#             project_data['comments'] = 'Created by Python automation'
            
#             # Save the project
#             if not project_name.endswith('.mat'):
#                 project_name += '.mat'
            
#             # Use MATLAB's save function
#             self.eng.workspace['project_data'] = project_data
#             self.eng.eval(f"save('{project_name}', '-struct', 'project_data');", nargout=0)
            
#             print(f"✅ Project saved: {project_name}")
#             return True
            
#         except Exception as e:
#             print(f"Error creating manual project: {e}")
#             return False
    
#     def verify_project(self, project_name):
#         """Verify the created project"""
#         print("\\nProject Verification:")
        
#         if not project_name.endswith('.mat'):
#             project_name += '.mat'
        
#         if not os.path.exists(project_name):
#             print(f"Project file not found: {project_name}")
#             return
            
#         try:
#             # Load and examine project file
#             project_data = self.eng.load(project_name)
            
#             if 'images' in project_data:
#                 images = project_data['images']
                
#                 if hasattr(images, '__len__'):
#                     num_images = len(images)
#                     print(f"✅ Project contains {num_images} images")
                    
#                     # List images
#                     for i in range(min(num_images, 15)):  # Limit output
#                         try:
#                             img = images[i] if hasattr(images, '__getitem__') else None
#                             if img and isinstance(img, dict):
#                                 name = img.get('Name', 'Unknown')
#                                 img_type = img.get('ImageType', 'Unknown')
#                                 print(f"   {i+1:2d}. {name} ({img_type})")
#                         except:
#                             print(f"   {i+1:2d}. (Error reading image)")
#                 else:
#                     print("Images field found but structure unclear")
#             else:
#                 print("No images field found in project")
                
#         except Exception as e:
#             print(f"Error verifying project: {e}")
    
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
#         print("Direct EPRI Automation Pipeline")
#         print("=" * 40)
        
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
            
#             # Step 4: Try different approaches for project creation
#             project_name = "direct_automation_project.mat"
            
#             # First try: Use existing MATLAB script
#             if self.use_existing_matlab_script(processed_files, project_name):
#                 # Check if the script created a project file with a different name
#                 possible_names = ['arbuz_13_images_project.mat', 'direct_automation_project.mat']
#                 for name in possible_names:
#                     if os.path.exists(name):
#                         project_name = name
#                         break
#             else:
#                 # Fallback: Create project manually
#                 print("\\nFallback: Creating project manually...")
#                 self.create_simple_project_manually(processed_files, project_name)
            
#             # Step 5: Verify project
#             self.verify_project(project_name)
            
#             print(f"\\nAutomation completed!")
#             print(f"Project file: {project_name}")
            
#         except Exception as e:
#             print(f"Automation failed: {e}")
            
#         finally:
#             self.cleanup()

# def main():
#     """Main entry point"""
#     automation = DirectEPRIAutomation()
#     automation.run_automation()

# if __name__ == "__main__":
#     main()
