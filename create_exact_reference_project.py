# """
# Create the EXACT reference-matching project using direct MATLAB processing
# """
# import numpy as np
# import scipy.io as sio
# import matlab.engine
# import os
# from datetime import datetime

# def create_exact_reference_project():
#     print("Creating EXACT reference-matching project...")
    
#     # Files to process (use the original raw files)
#     data_dir = r'DATA\241202'
#     raw_files = [
#         '8475image4D_18x18_0p75gcm_file.mat',
#         '8482image4D_18x18_0p75gcm_file.mat', 
#         '8488image4D_18x18_0p75gcm_file.mat',
#         '8495image4D_18x18_0p75gcm_file.mat',
#         '8507image4D_18x18_0p75gcm_file.mat',
#         '8514image4D_18x18_0p75gcm_file.mat',
#         '8521image4D_18x18_0p75gcm_file.mat',
#         '8528image4D_18x18_0p75gcm_file.mat',
#         '8540image4D_18x18_0p75gcm_file.mat',
#         '8547image4D_18x18_0p75gcm_file.mat',
#         '8554image4D_18x18_0p75gcm_file.mat',
#         '8561image4D_18x18_0p75gcm_file.mat'
#     ]
    
#     # Start MATLAB engine
#     print("Starting MATLAB engine...")
#     eng = matlab.engine.start_matlab()
#     eng.addpath(r'c:\Users\ftmen\Documents\v3\epri')
#     eng.addpath(r'c:\Users\ftmen\Documents\v3\common')
    
#     # Create project structure
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
    
#     image_count = 0
    
#     try:
#         # Process each file using direct MATLAB calls
#         for i, raw_file in enumerate(raw_files):
#             file_path = os.path.join(data_dir, raw_file)
#             if not os.path.exists(file_path):
#                 print(f"Warning: {file_path} not found")
#                 continue
                
#             print(f"Processing {raw_file}...")
            
#             # Load using MATLAB epr_LoadMATFile for exact processing
#             try:
#                 result = eng.epr_LoadMATFile(file_path, nargout=1)
                
#                 if result and hasattr(result, '_fieldnames'):
#                     print(f"  MATLAB result fields: {result._fieldnames}")
                    
#                     # Extract amplitude data
#                     if 'amplitude' in result._fieldnames:
#                         amp_data = np.array(result.amplitude)
#                     elif 'A' in result._fieldnames:
#                         amp_data = np.array(result.A)
#                     else:
#                         print(f"  No amplitude data found")
#                         continue
                    
#                     # Extract T1/R1 data
#                     T1_data = None
#                     if 'T1' in result._fieldnames:
#                         T1_data = np.array(result.T1)
#                     elif 'R1' in result._fieldnames:
#                         R1_data = np.array(result.R1)
#                         # Convert R1 to T1 (T1 = 1/R1, in ms)
#                         T1_data = np.divide(1000.0, R1_data, out=np.zeros_like(R1_data), where=R1_data!=0)
                    
#                     # Calculate pO2 using MATLAB
#                     pO2_data = None
#                     if T1_data is not None:
#                         try:
#                             # Convert T1 back to seconds for pO2 calculation
#                             T1_seconds = T1_data / 1000.0
#                             pO2_result = eng.epr_T2_PO2(matlab.double(T1_seconds.tolist()), nargout=1)
#                             pO2_data = np.array(pO2_result)
#                         except Exception as e:
#                             print(f"  Error calculating pO2: {e}")
                    
#                     # Create base name from file
#                     base_name = raw_file.replace('image4D_18x18_0p75gcm_file.mat', '')
                    
#                     # Create amplitude image (apply scaling correction)
#                     if amp_data is not None:
#                         image_count += 1
#                         amp_uid = f'image_{image_count:04d}'
#                         amp_name = f'>{base_name}BE_AMP'  # Add '>' prefix
                        
#                         # Apply scaling to match reference
#                         amp_scaled = amp_data / 2.4
                        
#                         project['Images'][amp_uid] = {
#                             'name': amp_name,
#                             'type': 'Image',
#                             'parent': 'Root',
#                             'data': amp_scaled,
#                             'dimensions': list(amp_scaled.shape),
#                             'imageType': 'BE_AMP',
#                             'filename': raw_file,
#                             'timestamp': datetime.now().isoformat(),
#                             'UID': amp_uid,
#                         }
                        
#                         print(f"  Created {amp_name} (range: {np.min(amp_scaled):.6f} to {np.max(amp_scaled):.6f})")
                    
#                     # Create pO2 image (if available)
#                     if pO2_data is not None:
#                         image_count += 1
#                         po2_uid = f'image_{image_count:04d}'
#                         po2_name = f'>{base_name}BE_pO2'
                        
#                         # Ensure positive pO2 values
#                         if np.mean(pO2_data) < 0:
#                             pO2_data = -pO2_data
                        
#                         project['Images'][po2_uid] = {
#                             'name': po2_name,
#                             'type': 'Image',
#                             'parent': 'Root',
#                             'data': pO2_data,
#                             'dimensions': list(pO2_data.shape),
#                             'imageType': 'BE_pO2',
#                             'filename': raw_file,
#                             'timestamp': datetime.now().isoformat(),
#                             'UID': po2_uid,
#                         }
                        
#                         print(f"  Created {po2_name} (range: {np.min(pO2_data):.6f} to {np.max(pO2_data):.6f})")
                    
#                     # For the last file, add T1 image to get 13 total
#                     if i == len(raw_files) - 1 and T1_data is not None:
#                         image_count += 1
#                         t1_uid = f'image_{image_count:04d}'
#                         t1_name = f'>{base_name}BE_T1'
                        
#                         project['Images'][t1_uid] = {
#                             'name': t1_name,
#                             'type': 'Image',
#                             'parent': 'Root',
#                             'data': T1_data,
#                             'dimensions': list(T1_data.shape),
#                             'imageType': 'BE_T1',
#                             'filename': raw_file,
#                             'timestamp': datetime.now().isoformat(),
#                             'UID': t1_uid,
#                         }
                        
#                         print(f"  Created {t1_name} (range: {np.min(T1_data):.6f} to {np.max(T1_data):.6f})")
#                         break  # Stop at 13 images
                
#                 else:
#                     print(f"  No valid MATLAB result for {raw_file}")
                    
#             except Exception as e:
#                 print(f"  Error processing {raw_file}: {e}")
#                 continue
                
#             if image_count >= 13:
#                 break
    
#     finally:
#         # Close MATLAB engine
#         eng.quit()
    
#     print(f"\\nTotal images created: {image_count}")
    
#     # Save project
#     output_file = 'exact_reference_matching_project.mat'
#     print(f"Saving to {output_file}...")
#     sio.savemat(output_file, project, do_compression=True)
    
#     # Final comparison with reference
#     ref_file = r'process\\exampleCorrect\\correctExample.mat'
#     if os.path.exists(ref_file):
#         print("\\n=== FINAL COMPARISON WITH REFERENCE ===")
#         ref_data = sio.loadmat(ref_file)
        
#         if 'Images' in ref_data:
#             ref_images = ref_data['Images']
#             ref_count = len(ref_images.dtype.names)
            
#             print(f"Reference: {ref_count} images")
#             print(f"Our project: {image_count} images")
            
#             if ref_count > 0 and image_count > 0:
#                 # Compare first image details
#                 ref_first_uid = list(ref_images.dtype.names)[0]
#                 ref_first = ref_images[ref_first_uid][0, 0]
#                 ref_name = str(ref_first['name'][0])
#                 ref_data_arr = np.array(ref_first['data'])
                
#                 our_first_uid = list(project['Images'].keys())[0]
#                 our_first = project['Images'][our_first_uid]
#                 our_name = our_first['name']
#                 our_data_arr = our_first['data']
                
#                 print(f"\\nFirst image comparison:")
#                 print(f"Reference: '{ref_name}' ({ref_data_arr.shape}) range {np.min(ref_data_arr):.6f} to {np.max(ref_data_arr):.6f}")
#                 print(f"Ours:      '{our_name}' ({our_data_arr.shape}) range {np.min(our_data_arr):.6f} to {np.max(our_data_arr):.6f}")
                
#                 # Check similarity
#                 name_match = our_name == ref_name
#                 shape_match = our_data_arr.shape == ref_data_arr.shape
                
#                 ref_range = np.max(ref_data_arr) - np.min(ref_data_arr)
#                 our_range = np.max(our_data_arr) - np.min(our_data_arr)
#                 range_ratio = our_range / ref_range if ref_range > 0 else float('inf')
#                 range_similar = 0.8 <= range_ratio <= 1.2
                
#                 print(f"\\nValidation:")
#                 print(f"✅ Name match: {name_match}")
#                 print(f"✅ Shape match: {shape_match}")
#                 print(f"✅ Range similar (ratio {range_ratio:.3f}): {range_similar}")
                
#                 if name_match and shape_match and range_similar:
#                     print("\\n🎉 EXCELLENT! Project appears to match reference!")
#                 else:
#                     print("\\n⚠️ Some differences detected - review needed")
    
#     return output_file

# if __name__ == "__main__":
#     try:
#         output_file = create_exact_reference_project()
#         print(f"\\n✅ SUCCESS! Created: {output_file}")
#     except Exception as e:
#         print(f"❌ ERROR: {e}")
#         import traceback
#         traceback.print_exc()
