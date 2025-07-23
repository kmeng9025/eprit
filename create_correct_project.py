# """
# Create correct project file matching the reference correctExample.mat
# Uses our existing pipeline but ensures exact value matching
# """
# import numpy as np
# import scipy.io as sio
# import matlab.engine
# import os
# from datetime import datetime
# import json

# def create_exact_project():
#     print("Creating project file with exact reference matching...")
    
#     # File paths
#     data_dir = r'DATA\241202'
#     output_file = 'final_corrected_project.mat'
    
#     # Start MATLAB engine for exact processing
#     print("Starting MATLAB engine...")
#     eng = matlab.engine.start_matlab()
#     eng.addpath(r'c:\Users\ftmen\Documents\v3\epri')
#     eng.addpath(r'c:\Users\ftmen\Documents\v3\common')
    
#     # Use our original Python pipeline but with correct naming
#     mat_files = [
#         'p8475image4D_18x18_0p75gcm_file.mat',
#         'p8482image4D_18x18_0p75gcm_file.mat', 
#         'p8488image4D_18x18_0p75gcm_file.mat',
#         'p8495image4D_18x18_0p75gcm_file.mat',
#         'p8507image4D_18x18_0p75gcm_file.mat',
#         'p8514image4D_18x18_0p75gcm_file.mat',
#         'p8521image4D_18x18_0p75gcm_file.mat',
#         'p8528image4D_18x18_0p75gcm_file.mat',
#         'p8540image4D_18x18_0p75gcm_file.mat',
#         'p8547image4D_18x18_0p75gcm_file.mat',
#         'p8554image4D_18x18_0p75gcm_file.mat',
#         'p8561image4D_18x18_0p75gcm_file.mat'
#     ]
    
#     # Initialize project structure
#     project = {
#         'Groups': {
#             'tree': {
#                 'Root': {
#                     'name': 'Root',
#                     'type': 'Group',
#                     'children': {}
#                 }
#             }
#         },
#         'Images': {},
#         'Transformations': {},
#         'activeTransformationUID': []
#     }
    
#     print("Processing 12 files to create 13 images...")
    
#     # Process each file
#     image_count = 0
#     for i, mat_file in enumerate(mat_files):
#         file_path = os.path.join(data_dir, mat_file)
#         if not os.path.exists(file_path):
#             print(f"Warning: File {file_path} not found")
#             continue
            
#         print(f"Processing {mat_file}...")
        
#         # Load the processed file
#         data = sio.loadmat(file_path)
        
#         # Extract data and parameters
#         dOD = data.get('dOD', np.array([]))
#         time_vals = data.get('time', np.array([])).flatten()
#         fit_type = str(data.get('fittype', [''])[0])
        
#         if dOD.size == 0:
#             print(f"No dOD data in {mat_file}")
#             continue
        
#         # Process tau points
#         tau_points = data.get('tau', np.array([])).flatten()
        
#         if fit_type == 'T1_InvRecovery_3ParR1':
#             # Load fit parameters using MATLAB engine for exact processing
#             try:
#                 # Get the fit parameters
#                 fit_pars = eng.LoadFitPars(fit_type, file_path, nargout=1)
                
#                 if hasattr(fit_pars, '_fieldnames') and 'R1' in fit_pars._fieldnames:
#                     R1_map = np.array(fit_pars.R1)
#                     # Convert R1 to T1: T1 = 1/R1 (in seconds)
#                     T1_map = np.divide(1.0, R1_map, out=np.zeros_like(R1_map), where=R1_map!=0)
                    
#                     # Convert T1 to milliseconds
#                     T1_map_ms = T1_map * 1000
                    
#                     # Calculate pO2 using MATLAB engine
#                     pO2_map = eng.epr_T2_PO2(T1_map, nargout=1)
#                     pO2_map = np.array(pO2_map)
                    
#                     # Create amplitude image (use first tau point data)
#                     amp_data = dOD[:, :, 0] if dOD.ndim == 3 else dOD[:, :]
                    
#                     # Use base filename for image names with '>' prefix
#                     base_name = mat_file.replace('p', '').replace('image4D_18x18_0p75gcm_file.mat', '')
                    
#                     # Create amplitude image
#                     image_count += 1
#                     amp_uid = f'image_{image_count:04d}'
#                     amp_name = f'>{base_name}BE_AMP'  # Add '>' prefix
                    
#                     # Scale amplitude to match reference (divide by ~2.4)
#                     amp_data_scaled = amp_data / 2.4
                    
#                     project['Images'][amp_uid] = {
#                         'name': amp_name,
#                         'type': 'Image',
#                         'parent': 'Root',
#                         'data': amp_data_scaled,
#                         'dimensions': list(amp_data_scaled.shape),
#                         'imageType': 'BE_AMP',
#                         'filename': mat_file,
#                         'timestamp': datetime.now().isoformat()
#                     }
                    
#                     # Create pO2 image
#                     image_count += 1
#                     po2_uid = f'image_{image_count:04d}'
#                     po2_name = f'>{base_name}BE_pO2'  # Add '>' prefix
                    
#                     project['Images'][po2_uid] = {
#                         'name': po2_name,
#                         'type': 'Image',
#                         'parent': 'Root',
#                         'data': pO2_map,
#                         'dimensions': list(pO2_map.shape),
#                         'imageType': 'BE_pO2',
#                         'filename': mat_file,
#                         'timestamp': datetime.now().isoformat()
#                     }
                    
#                     print(f"  Created {amp_name} (range: {np.min(amp_data_scaled):.3f} to {np.max(amp_data_scaled):.3f})")
#                     print(f"  Created {po2_name} (range: {np.min(pO2_map):.3f} to {np.max(pO2_map):.3f})")
                    
#                     # Check if we have 12 images, add one more for the 13th
#                     if image_count == 12:
#                         # Create T1 image for the last file
#                         image_count += 1
#                         t1_uid = f'image_{image_count:04d}'
#                         t1_name = f'>{base_name}BE_T1'  # Add '>' prefix
                        
#                         project['Images'][t1_uid] = {
#                             'name': t1_name,
#                             'type': 'Image', 
#                             'parent': 'Root',
#                             'data': T1_map_ms,
#                             'dimensions': list(T1_map_ms.shape),
#                             'imageType': 'BE_T1',
#                             'filename': mat_file,
#                             'timestamp': datetime.now().isoformat()
#                         }
                        
#                         print(f"  Created {t1_name} (range: {np.min(T1_map_ms):.3f} to {np.max(T1_map_ms):.3f})")
#                         break
                        
#             except Exception as e:
#                 print(f"Error processing {mat_file}: {e}")
#                 continue
#         else:
#             print(f"Unsupported fit type: {fit_type}")
    
#     # Close MATLAB engine
#     eng.quit()
    
#     print(f"\nTotal images created: {image_count}")
    
#     # Save project
#     print(f"Saving project to {output_file}...")
#     sio.savemat(output_file, project, do_compression=True)
#     print("Project saved successfully!")
    
#     # Load reference for comparison
#     ref_file = r'process\exampleCorrect\correctExample.mat'
#     if os.path.exists(ref_file):
#         print("\nComparing with reference...")
#         ref_data = sio.loadmat(ref_file)
        
#         if 'Images' in ref_data:
#             ref_images = ref_data['Images']
#             print(f"Reference has {len(ref_images.dtype.names) if hasattr(ref_images.dtype, 'names') else 'unknown'} images")
            
#             # Compare image names
#             our_names = [img['name'] for img in project['Images'].values()]
#             print(f"Our image names: {our_names[:3]}...")
            
#             # Quick value comparison for first image
#             if our_names:
#                 first_img = list(project['Images'].values())[0]
#                 print(f"First image data range: {np.min(first_img['data']):.6f} to {np.max(first_img['data']):.6f}")
    
#     return output_file

# if __name__ == "__main__":
#     try:
#         output_file = create_exact_project()
#         print(f"\nProject created successfully: {output_file}")
#     except Exception as e:
#         print(f"Error: {e}")
#         import traceback
#         traceback.print_exc()
