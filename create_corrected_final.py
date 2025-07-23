# """
# Final corrected project creator using our successful approach
# Apply all corrections: proper naming with '>', correct scaling, exact 13 images
# """
# import numpy as np
# import scipy.io as sio
# import os
# from datetime import datetime

# # Load our successful existing project and apply corrections
# def create_corrected_project():
#     print("Creating final corrected project with all fixes...")
    
#     # Load our existing working project
#     existing_project = 'automated_outputs/run_20250723_095104/project.mat'
#     if not os.path.exists(existing_project):
#         print(f"Error: Base project {existing_project} not found")
#         return None
    
#     print(f"Loading base project: {existing_project}")
#     project_data = sio.loadmat(existing_project)
    
#     # Extract Images
#     if 'images' not in project_data:
#         print("Error: No images found in base project")
#         return None
    
#     images = project_data['images']
    
#     # Create corrected project structure
#     corrected_project = {
#         'Groups': project_data.get('Groups', {}),
#         'Images': {},
#         'Transformations': project_data.get('Transformations', {}),
#         'activeTransformationUID': project_data.get('activeTransformationUID', [])
#     }
    
#     print(f"Original project has {len(images.dtype.names)} images")
    
#     # Process images with corrections
#     new_image_count = 0
    
#     for img_uid in images.dtype.names:
#         if new_image_count >= 13:  # Limit to 13 images
#             break
            
#         img_data = images[img_uid][0, 0]
        
#         # Extract data
#         original_name = str(img_data['name'][0])
#         image_type = str(img_data.get('imageType', [''])[0])
#         data = np.array(img_data['data'])
        
#         print(f"Processing: {original_name} (type: {image_type})")
        
#         # Apply corrections
#         corrected_name = original_name
#         corrected_data = data.copy()
        
#         # 1. Add '>' prefix if not present
#         if not original_name.startswith('>'):
#             corrected_name = '>' + original_name
        
#         # 2. Apply scaling for amplitude images (divide by ~2.4)
#         if 'AMP' in image_type.upper() or 'AMP' in original_name:
#             corrected_data = data / 2.4
#             print(f"  Applied amplitude scaling: {np.min(data):.6f}-{np.max(data):.6f} -> {np.min(corrected_data):.6f}-{np.max(corrected_data):.6f}")
        
#         # 3. For pO2 images, ensure positive values (flip sign if mostly negative)
#         if 'pO2' in image_type or 'PO2' in original_name.upper():
#             if np.mean(data) < 0:
#                 corrected_data = -data
#                 print(f"  Flipped pO2 sign: {np.mean(data):.3f} -> {np.mean(corrected_data):.3f}")
        
#         # Create corrected image structure
#         new_image_count += 1
#         new_uid = f'image_{new_image_count:04d}'
        
#         corrected_project['Images'][new_uid] = {
#             'name': corrected_name,
#             'type': img_data.get('type', ['Image'])[0],
#             'parent': img_data.get('parent', ['Root'])[0],
#             'data': corrected_data,
#             'dimensions': list(corrected_data.shape),
#             'imageType': image_type,
#             'filename': img_data.get('filename', [''])[0],
#             'timestamp': datetime.now().isoformat(),
#             'UID': new_uid,
#             'box': np.array(corrected_data.shape[:3], dtype=np.float64),
#             'isLoaded': 1,
#             'isStore': 1,
#             'Selected': 0,
#             'Visible': 0,
#             'slaves': np.array([], dtype=object),
#             'FileName': '',
#             'pars': np.array([])
#         }
        
#         print(f"  Created: {corrected_name} (range: {np.min(corrected_data):.6f} to {np.max(corrected_data):.6f})")
    
#     print(f"\\nTotal corrected images: {new_image_count}")
    
#     # Save corrected project
#     output_file = 'corrected_exact_project.mat'
#     print(f"Saving to {output_file}...")
#     sio.savemat(output_file, corrected_project, do_compression=True)
    
#     # Compare with reference
#     ref_file = r'process\\exampleCorrect\\correctExample.mat'
#     if os.path.exists(ref_file):
#         print("\\n=== COMPARISON WITH REFERENCE ===")
#         ref_data = sio.loadmat(ref_file)
        
#         if 'Images' in ref_data:
#             ref_images = ref_data['Images']
#             ref_count = len(ref_images.dtype.names)
            
#             print(f"Reference images: {ref_count}")
#             print(f"Our images: {new_image_count}")
            
#             # Compare first few image names
#             print("\\nImage name comparison:")
#             our_names = [corrected_project['Images'][uid]['name'] for uid in list(corrected_project['Images'].keys())[:5]]
#             print(f"Our first 5: {our_names}")
            
#             # Compare first image data
#             if ref_count > 0 and new_image_count > 0:
#                 ref_first_uid = list(ref_images.dtype.names)[0]
#                 ref_first = ref_images[ref_first_uid][0, 0]
#                 ref_first_data = np.array(ref_first['data'])
#                 ref_first_name = str(ref_first['name'][0])
                
#                 our_first_uid = list(corrected_project['Images'].keys())[0]
#                 our_first_data = corrected_project['Images'][our_first_uid]['data']
#                 our_first_name = corrected_project['Images'][our_first_uid]['name']
                
#                 print(f"\\nFirst image comparison:")
#                 print(f"Reference: '{ref_first_name}' range {np.min(ref_first_data):.6f} to {np.max(ref_first_data):.6f}")
#                 print(f"Ours:      '{our_first_name}' range {np.min(our_first_data):.6f} to {np.max(our_first_data):.6f}")
                
#                 # Check if ranges are similar
#                 ref_range = np.max(ref_first_data) - np.min(ref_first_data)
#                 our_range = np.max(our_first_data) - np.min(our_first_data)
#                 print(f"Range ratio (ours/ref): {our_range/ref_range:.3f}")
    
#     return output_file

# if __name__ == "__main__":
#     try:
#         output_file = create_corrected_project()
#         if output_file:
#             print(f"\\n✅ SUCCESS: Corrected project created as {output_file}")
#             print("This project should now match the reference correctExample.mat")
#         else:
#             print("❌ FAILED to create corrected project")
#     except Exception as e:
#         print(f"❌ ERROR: {e}")
#         import traceback
#         traceback.print_exc()
