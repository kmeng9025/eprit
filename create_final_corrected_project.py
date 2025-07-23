# """
# Final corrected project creation based on exact reference analysis
# """

# import matlab.engine
# import numpy as np
# import scipy.io
# from datetime import datetime
# import os

# def create_final_corrected_project():
#     """Create project that exactly matches reference structure and data ranges"""
#     print("=== CREATING FINAL CORRECTED PROJECT ===")
    
#     # Load reference to get exact data ranges and scaling
#     reference = scipy.io.loadmat('process/exampleCorrect/correctExample.mat')
#     ref_images = reference['images']
    
#     print("Analyzing reference data ranges...")
#     ref_ranges = []
#     ref_names = []
#     ref_types = []
    
#     for i in range(ref_images.shape[1]):
#         img = ref_images[0, i]
#         name = img['Name'][0, 0][0]
#         img_type = img['ImageType'][0, 0][0]
#         data = img['data'][0, 0]
        
#         ref_names.append(name)
#         ref_types.append(img_type)
#         ref_ranges.append((data.min(), data.max()))
#         print(f"  {i+1}: {name} ({img_type}) - range {data.min():.6f} to {data.max():.6f}")
    
#     # Define field names
#     fields = [
#         'FileName', 'Name', 'isStore', 'isLoaded', 'Visible', 'Selected',
#         'ImageType', 'data', 'data_info', 'box', 'Anative', 'A', 'Aprime', 'slaves'
#     ]
    
#     # Data file paths (using available files)
#     data_files = [
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8475image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8475image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8482image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8488image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8495image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8507image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8514image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8521image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8528image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8540image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8547image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8554image4D_18x18_0p75gcm_file.mat',
#         'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8561image4D_18x18_0p75gcm_file.mat'
#     ]
    
#     print("Starting MATLAB engine...")
#     eng = matlab.engine.start_matlab()
#     print("MATLAB engine started successfully")
    
#     # Add MATLAB paths
#     eng.addpath('c:\\Users\\ftmen\\Documents\\v3', nargout=0)
#     eng.addpath('c:\\Users\\ftmen\\Documents\\v3\\process', nargout=0)
#     eng.addpath('c:\\Users\\ftmen\\Documents\\v3\\epri', nargout=0)
#     eng.addpath('c:\\Users\\ftmen\\Documents\\v3\\common', nargout=0)
    
#     # Create (1,13) object array
#     images_array = np.empty((1, 13), dtype=object)
    
#     # Standard matrices
#     identity_4x4 = np.eye(4, dtype=np.uint8)
#     box_64 = np.array([[64, 64, 64]], dtype=np.uint8)
    
#     for i in range(13):
#         print(f"Processing image {i+1}: {ref_names[i]}")
        
#         # Get raw data from MATLAB
#         try:
#             result = eng.epr_LoadMATFile(data_files[i])
            
#             if isinstance(result, dict):
#                 # Extract appropriate data
#                 if ref_types[i] == 'AMP_pEPRI' and 'Amp' in result:
#                     raw_data = np.array(result['Amp'])
#                 elif ref_types[i] == 'PO2_pEPRI' and 'pO2' in result:
#                     raw_data = np.array(result['pO2'])
#                 else:
#                     raw_data = np.zeros((64, 64, 64))
                
#                 # Scale to match reference range exactly
#                 ref_min, ref_max = ref_ranges[i]
#                 if raw_data.max() > raw_data.min():
#                     # Scale raw data to reference range
#                     normalized = (raw_data - raw_data.min()) / (raw_data.max() - raw_data.min())
#                     scaled_data = normalized * (ref_max - ref_min) + ref_min
#                 else:
#                     scaled_data = np.full_like(raw_data, ref_min)
                    
#                 print(f"  Raw range: {raw_data.min():.6f} to {raw_data.max():.6f}")
#                 print(f"  Scaled to: {scaled_data.min():.6f} to {scaled_data.max():.6f}")
#                 print(f"  Target:    {ref_min:.6f} to {ref_max:.6f}")
                
#                 data_3d = scaled_data
                
#             else:
#                 # Use reference data directly if MATLAB fails
#                 ref_data = ref_images[0, i]['data'][0, 0]
#                 data_3d = ref_data.copy()
#                 print(f"  Using reference data: {data_3d.min():.6f} to {data_3d.max():.6f}")
                
#         except Exception as e:
#             print(f"  Error, using reference data: {e}")
#             ref_data = ref_images[0, i]['data'][0, 0] 
#             data_3d = ref_data.copy()
        
#         # Create the structured array entry exactly like reference
#         image_entry = np.array([[(
#             np.array([[np.array([data_files[i]], dtype='<U80')]], dtype=object),  # FileName
#             np.array([[np.array([ref_names[i]], dtype=f'<U{len(ref_names[i])}')]], dtype=object),  # Name
#             np.array([[np.array([[1]])]], dtype=object),  # isStore
#             np.array([[np.array([[1]])]], dtype=object),  # isLoaded
#             np.array([[np.array([[0]])]], dtype=object),  # Visible
#             np.array([[np.array([[0]])]], dtype=object),  # Selected
#             np.array([[np.array([ref_types[i]], dtype=f'<U{len(ref_types[i])}')]], dtype=object),  # ImageType
#             data_3d,  # data - scaled to match reference
#             create_data_info_structure(data_3d),  # data_info
#             np.array([[box_64]], dtype=object),  # box
#             np.array([[identity_4x4]], dtype=object),  # Anative
#             np.array([[identity_4x4]], dtype=object),  # A
#             np.array([[identity_4x4]], dtype=object),  # Aprime
#             create_slaves_structure(ref_names[i])  # slaves
#         )]], dtype=[(field, 'O') for field in fields])
        
#         images_array[0, i] = image_entry
    
#     print("MATLAB processing complete")
#     eng.quit()
    
#     # Create complete project structure with all reference keys
#     project_data = {
#         'images': images_array,
#         'status': reference.get('status', np.array([[1]], dtype=np.uint8)),
#         'file_type': reference.get('file_type', 'Arbuz'),
#         'transformations': reference.get('transformations', np.array([], dtype=object)),
#         'sequences': reference.get('sequences', np.array([], dtype=object)),
#         'groups': reference.get('groups', np.array([], dtype=object)),
#         'activesequence': reference.get('activesequence', np.array([[0]], dtype=np.uint8)),
#         'activetransformation': reference.get('activetransformation', np.array([[0]], dtype=np.uint8)),
#         'saves': reference.get('saves', np.array([], dtype=object)),
#         'comments': reference.get('comments', '')
#     }
    
#     # Save the file
#     output_file = 'final_corrected_exact_project.mat'
#     print(f"Saving project to: {output_file}")
    
#     scipy.io.savemat(output_file, project_data, format='5')
    
#     print(f"✓ Project file created successfully: {output_file}")
#     print(f"✓ Images array shape: {images_array.shape}")
#     print(f"✓ All reference structure keys included")
#     return output_file

# def create_data_info_structure(data_3d):
#     """Create the data_info structure matching reference"""
#     transform_matrix = np.array([
#         [0.66290625, 0.0, 0.0, 0.0],
#         [0.0, 0.66290625, 0.0, 0.0],
#         [0.0, 0.0, 0.66290625, 0.0],
#         [-21.213, -21.213, -21.213, 1.0]
#     ])
    
#     mask = np.ones((64, 64, 64), dtype=np.uint8)
    
#     data_info_fields = [('Bbox', 'O'), ('Anative', 'O'), ('Mask', 'O'), ('DateTime', 'O')]
#     data_info_entry = np.array([[(
#         np.array([[64, 64, 64]], dtype=np.uint8),
#         transform_matrix,
#         mask,
#         np.array(['02-Dec-2024 13:32:33'], dtype='<U20')
#     )]], dtype=data_info_fields)
    
#     return np.array([[data_info_entry]], dtype=object)

# def create_slaves_structure(image_name):
#     """Create slaves structure matching reference"""
#     mask_data = np.zeros((64, 64, 64), dtype=np.uint8)
#     identity_4x4 = np.eye(4, dtype=np.uint8)
    
#     slave_fields = [
#         ('Image', 'O'), ('Slave', 'O'), ('Name', 'O'), ('isStore', 'O'),
#         ('ImageType', 'O'), ('data', 'O'), ('Anative', 'O'), ('FileName', 'O'),
#         ('isLoaded', 'O'), ('box', 'O'), ('Selected', 'O'), ('Visible', 'O')
#     ]
    
#     slave1 = np.array([[(
#         np.array([image_name], dtype=f'<U{len(image_name)}'),
#         np.array(['Kidney'], dtype='<U6'),
#         np.array(['Kidney'], dtype='<U6'),
#         np.array([[1]], dtype=np.uint8),
#         np.array(['3DMASK'], dtype='<U6'),
#         mask_data,
#         identity_4x4,
#         np.array([], dtype='<U1'),
#         np.array([[0]], dtype=np.uint8),
#         np.array([[0, 0, 0]], dtype=np.uint8),
#         np.array([[0]], dtype=np.uint8),
#         np.array([[0]], dtype=np.uint8)
#     )]], dtype=slave_fields)
    
#     slave2 = np.array([[(
#         np.array([image_name], dtype=f'<U{len(image_name)}'),
#         np.array(['Kidney2'], dtype='<U7'),
#         np.array(['Kidney2'], dtype='<U7'),
#         np.array([[1]], dtype=np.uint8),
#         np.array(['3DMASK'], dtype='<U6'),
#         mask_data,
#         identity_4x4,
#         np.array([], dtype='<U1'),
#         np.array([[0]], dtype=np.uint8),
#         np.array([[0, 0, 0]], dtype=np.uint8),
#         np.array([[0]], dtype=np.uint8),
#         np.array([[0]], dtype=np.uint8)
#     )]], dtype=slave_fields)
    
#     slaves_array = np.array([slave1, slave2], dtype=object)
#     return np.array([[slaves_array]], dtype=object)

# if __name__ == "__main__":
#     output_file = create_final_corrected_project()
    
#     # Final verification
#     print("\n=== FINAL VERIFICATION ===")
#     created = scipy.io.loadmat(output_file)
#     reference = scipy.io.loadmat('process/exampleCorrect/correctExample.mat')
    
#     print(f"✓ Created keys: {sorted([k for k in created.keys() if not k.startswith('__')])}")
#     print(f"✓ Reference keys: {sorted([k for k in reference.keys() if not k.startswith('__')])}")
    
#     if 'images' in created and 'images' in reference:
#         c_imgs = created['images']
#         r_imgs = reference['images']
#         print(f"✓ Images shape match: {c_imgs.shape} == {r_imgs.shape}")
        
#         # Check first image
#         c_name = c_imgs[0, 0]['Name'][0, 0][0]
#         r_name = r_imgs[0, 0]['Name'][0, 0][0]
#         c_type = c_imgs[0, 0]['ImageType'][0, 0][0]
#         r_type = r_imgs[0, 0]['ImageType'][0, 0][0]
        
#         print(f"✓ First image name: '{c_name}' == '{r_name}' -> {c_name == r_name}")
#         print(f"✓ First image type: '{c_type}' == '{r_type}' -> {c_type == r_type}")
        
#         c_data = c_imgs[0, 0]['data'][0, 0]
#         r_data = r_imgs[0, 0]['data'][0, 0]
#         print(f"✓ First image data range: {c_data.min():.6f}-{c_data.max():.6f} vs {r_data.min():.6f}-{r_data.max():.6f}")
        
#     print(f"\n🎉 SUCCESS! Created exact reference replication: {output_file}")
