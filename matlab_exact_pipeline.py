# """
# Analyze and Replicate Correct Project Structure
# Based on deep MATLAB analysis of ProcessGUI.m, ArbuzGUI.m, and epr_LoadMATFile.m
# """

# import matlab
# import matlab.engine
# import numpy as np
# import scipy.io as sio
# import os

# def analyze_correct_project():
#     """
#     Analyze the reference correct project to understand exact structure
#     """
#     correct_file = r"c:\Users\ftmen\Documents\v3\process\exampleCorrect\correctExample.mat"
    
#     print("=== Analyzing Correct Reference Project ===")
    
#     try:
#         data = sio.loadmat(correct_file, struct_as_record=False, squeeze_me=True)
        
#         if 'project' in data:
#             project = data['project']
#             print(f"Project type: {type(project)}")
            
#             if hasattr(project, 'ImageList'):
#                 image_list = project.ImageList
#                 print(f"Number of images: {len(image_list)}")
                
#                 for i, img in enumerate(image_list):
#                     print(f"\nImage {i+1}:")
#                     print(f"  Type: {getattr(img, 'Type', 'N/A')}")
#                     print(f"  Name: {getattr(img, 'Name', 'N/A')}")
#                     print(f"  SourceFileName: {getattr(img, 'SourceFileName', 'N/A')}")
                    
#                     if hasattr(img, 'mat_image'):
#                         mat_img = img.mat_image
#                         print(f"  Image shape: {mat_img.shape}")
#                         print(f"  Image range: {np.min(mat_img):.6f} to {np.max(mat_img):.6f}")
                        
#                         if hasattr(img, 'Mask'):
#                             mask = img.Mask
#                             if mask.size > 0:
#                                 valid_pixels = mat_img[mask.astype(bool)]
#                                 if len(valid_pixels) > 0:
#                                     print(f"  Valid pixel range: {np.min(valid_pixels):.6f} to {np.max(valid_pixels):.6f}")
#                                     print(f"  Valid pixels: {len(valid_pixels)}")
                    
#                     if hasattr(img, 'pO2_info'):
#                         pO2_info = img.pO2_info
#                         if hasattr(pO2_info, '_fieldnames'):
#                             print(f"  pO2_info fields: {pO2_info._fieldnames}")
#                             if hasattr(pO2_info, 'amp1mM'):
#                                 print(f"  amp1mM: {pO2_info.amp1mM}")
        
#         return data
        
#     except Exception as e:
#         print(f"Error analyzing correct project: {e}")
#         return None

# def start_matlab_engine():
#     """
#     Start MATLAB engine and add necessary paths
#     """
#     print("Starting MATLAB engine...")
#     try:
#         eng = matlab.engine.start_matlab()
        
#         # Add paths
#         base_path = r'c:\Users\ftmen\Documents\v3'
#         paths_to_add = [
#             'epri',
#             'common',
#             'ibGUI',
#             'Arbuz2.0',
#             'process'
#         ]
        
#         for path in paths_to_add:
#             full_path = os.path.join(base_path, path)
#             if os.path.exists(full_path):
#                 eng.addpath(full_path)
#                 print(f"Added path: {full_path}")
        
#         return eng
#     except Exception as e:
#         print(f"Error starting MATLAB engine: {e}")
#         return None

# def process_with_matlab_engine(tdms_files, eng):
#     """
#     Process TDMS files using MATLAB engine with exact ProcessGUI logic
#     """
#     processed_files = []
    
#     for tdms_file in tdms_files[:3]:  # Process first 3
#         print(f"\n=== Processing with MATLAB Engine: {tdms_file} ===")
        
#         try:
#             # Convert to MATLAB string
#             tdms_matlab = matlab.string([tdms_file])
            
#             # Call ProcessGUI automation
#             result = eng.ProcessGUI_Automation(tdms_matlab, nargout=1)
            
#             if result and len(result) > 0:
#                 fit_file = str(result[0])
#                 print(f"MATLAB ProcessGUI created: {fit_file}")
                
#                 # Now load and process this fit file using exact epr_LoadMATFile logic
#                 processed_data = process_fit_file_exact(fit_file, eng)
#                 if processed_data:
#                     processed_files.append(processed_data)
                    
#         except Exception as e:
#             print(f"Error processing {tdms_file}: {e}")
#             import traceback
#             traceback.print_exc()
    
#     return processed_files

# def process_fit_file_exact(fit_file, eng):
#     """
#     Process fit file using exact MATLAB epr_LoadMATFile logic via engine
#     """
#     print(f"Processing fit file with exact MATLAB logic: {fit_file}")
    
#     try:
#         # Use MATLAB engine to call epr_LoadMATFile exactly as MATLAB does
#         fit_matlab = matlab.string([fit_file])
        
#         # Call the exact MATLAB function
#         result = eng.epr_LoadMATFile(fit_matlab, nargout=1)
        
#         if result:
#             print("Successfully processed with MATLAB epr_LoadMATFile")
            
#             # Convert MATLAB result to Python format for saving
#             # This will contain the exact MATLAB processing results
#             return result
#         else:
#             print("No result from MATLAB epr_LoadMATFile")
#             return None
            
#     except Exception as e:
#         print(f"Error in MATLAB processing: {e}")
#         import traceback
#         traceback.print_exc()
#         return None

# def create_exact_project(processed_images, output_path):
#     """
#     Create project file with exact structure matching reference
#     """
#     print("\n=== Creating Exact Project Structure ===")
    
#     # Initialize project structure
#     project_data = {
#         'project': {
#             'ImageList': [],
#             'Name': 'AutomatedProject',
#             'Version': 'Reg_v2.0'
#         }
#     }
    
#     # Add each processed image
#     for i, img_data in enumerate(processed_images):
#         if img_data:
#             # Create image entry with exact MATLAB structure
#             image_entry = {
#                 'Name': f'Image_{i+1:02d}',
#                 'Type': 'AMP_pEPRI' if i % 2 == 0 else 'PO2_pEPRI',
#                 'SourceFileName': getattr(img_data, 'SourceFileName', ''),
#                 'mat_image': getattr(img_data, 'Amp' if i % 2 == 0 else 'pO2', []),
#                 'Mask': getattr(img_data, 'Mask', []),
#                 'Size': getattr(img_data, 'Size', []),
#                 'pO2_info': getattr(img_data, 'pO2_info', {}),
#                 'Dim4Type': getattr(img_data, 'Dim4Type', 'Inversion')
#             }
            
#             project_data['project']['ImageList'].append(image_entry)
    
#     # Save project
#     sio.savemat(output_path, project_data)
#     print(f"Saved exact project: {output_path}")
    
#     return output_path

# def main():
#     """
#     Main function: Analyze reference and create exact replica
#     """
#     print("Starting MATLAB-Exact Pipeline with Engine Integration")
    
#     # Step 1: Analyze reference project
#     reference_data = analyze_correct_project()
    
#     # Step 2: Start MATLAB engine
#     eng = start_matlab_engine()
#     if not eng:
#         print("Failed to start MATLAB engine")
#         return
    
#     try:
#         # Step 3: Find TDMS files to process
#         tdms_files = []
#         for root, dirs, files in os.walk(r"c:\Users\ftmen\Documents\v3"):
#             for file in files:
#                 if file.endswith('.tdms'):
#                     tdms_files.append(os.path.join(root, file))
        
#         print(f"Found {len(tdms_files)} TDMS files")
        
#         # Step 4: Process with MATLAB engine
#         processed_images = process_with_matlab_engine(tdms_files, eng)
        
#         # Step 5: Create exact project
#         output_dir = r"c:\Users\ftmen\Documents\v3\matlab_exact_outputs"
#         os.makedirs(output_dir, exist_ok=True)
        
#         output_path = os.path.join(output_dir, "exact_project.mat")
#         project_file = create_exact_project(processed_images, output_path)
        
#         print(f"\n{'='*60}")
#         print(f"MATLAB-Exact Processing Complete!")
#         print(f"Reference analyzed: {reference_data is not None}")
#         print(f"Images processed: {len(processed_images)}")
#         print(f"Project created: {project_file}")
#         print(f"{'='*60}")
        
#     finally:
#         # Clean up MATLAB engine
#         eng.quit()

# if __name__ == "__main__":
#     main()
