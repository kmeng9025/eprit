# """
# Verify that our created project matches the reference structure
# """

# import scipy.io
# import numpy as np

# def compare_with_reference():
#     print("=== COMPARING CREATED PROJECT WITH REFERENCE ===")
    
#     # Load our created project
#     our_project = scipy.io.loadmat('final_exact_reference_project.mat')
    
#     # Load reference project
#     reference = scipy.io.loadmat('process/exampleCorrect/correctExample.mat')
    
#     print("\n--- Structure Comparison ---")
#     print(f"Our project keys: {list(our_project.keys())}")
#     print(f"Reference keys: {list(reference.keys())}")
    
#     if 'images' in our_project and 'images' in reference:
#         our_images = our_project['images']
#         ref_images = reference['images']
        
#         print(f"\nOur images shape: {our_images.shape}")
#         print(f"Reference images shape: {ref_images.shape}")
        
#         print(f"Our images dtype: {our_images.dtype}")
#         print(f"Reference images dtype: {ref_images.dtype}")
        
#         if our_images.shape == ref_images.shape:
#             print("✓ Image array shapes match!")
#         else:
#             print("✗ Image array shapes don't match")
            
#         # Compare first image structure
#         if our_images.shape[1] > 0 and ref_images.shape[1] > 0:
#             our_first = our_images[0, 0]
#             ref_first = ref_images[0, 0]
            
#             print(f"\nOur first image type: {type(our_first)}")
#             print(f"Reference first image type: {type(ref_first)}")
            
#             if hasattr(our_first, 'dtype') and hasattr(ref_first, 'dtype'):
#                 if our_first.dtype.names and ref_first.dtype.names:
#                     print(f"Our fields: {our_first.dtype.names}")
#                     print(f"Reference fields: {ref_first.dtype.names}")
                    
#                     if our_first.dtype.names == ref_first.dtype.names:
#                         print("✓ Field names match!")
#                     else:
#                         print("✗ Field names don't match")
                        
#                     # Compare data ranges
#                     try:
#                         our_data = our_first['data'][0, 0]
#                         ref_data = ref_first['data'][0, 0]
                        
#                         print(f"\nOur data shape: {our_data.shape}")
#                         print(f"Reference data shape: {ref_data.shape}")
#                         print(f"Our data range: {our_data.min():.6f} to {our_data.max():.6f}")
#                         print(f"Reference data range: {ref_data.min():.6f} to {ref_data.max():.6f}")
                        
#                         # Compare names
#                         our_name = our_first['Name'][0, 0][0, 0][0]
#                         ref_name = ref_first['Name'][0, 0][0, 0][0]
#                         print(f"\nOur name: '{our_name}'")
#                         print(f"Reference name: '{ref_name}'")
                        
#                         if our_name == ref_name:
#                             print("✓ Names match!")
#                         else:
#                             print("✗ Names don't match")
                            
#                     except Exception as e:
#                         print(f"Error comparing data: {e}")
        
#         # Count images by type
#         our_amp_count = 0
#         our_po2_count = 0
#         ref_amp_count = 0
#         ref_po2_count = 0
        
#         for i in range(min(our_images.shape[1], 13)):
#             try:
#                 our_type = our_images[0, i]['ImageType'][0, 0][0, 0][0]
#                 if our_type == 'AMP_pEPRI':
#                     our_amp_count += 1
#                 elif our_type == 'PO2_pEPRI':
#                     our_po2_count += 1
#             except:
#                 pass
                
#         for i in range(min(ref_images.shape[1], 13)):
#             try:
#                 ref_type = ref_images[0, i]['ImageType'][0, 0][0, 0][0]
#                 if ref_type == 'AMP_pEPRI':
#                     ref_amp_count += 1
#                 elif ref_type == 'PO2_pEPRI':
#                     ref_po2_count += 1
#             except:
#                 pass
        
#         print(f"\n--- Image Type Counts ---")
#         print(f"Our project: {our_amp_count} AMP, {our_po2_count} PO2")
#         print(f"Reference: {ref_amp_count} AMP, {ref_po2_count} PO2")
        
#         if our_amp_count == ref_amp_count and our_po2_count == ref_po2_count:
#             print("✓ Image type counts match!")
#         else:
#             print("✗ Image type counts don't match")
            
#     print("\n=== COMPARISON COMPLETE ===")

# if __name__ == "__main__":
#     compare_with_reference()
