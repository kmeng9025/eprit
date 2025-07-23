# import scipy.io
# import numpy as np

# def check_roi_structure(project_file):
#     """Check ROI structure in project"""
#     try:
#         print(f"=== CHECKING ROI STRUCTURE: {project_file} ===")
#         data = scipy.io.loadmat(project_file)
        
#         images = data['images']
#         print(f"Found {images.shape[1]} images")
        
#         # Check each image for ROIs
#         for i in range(images.shape[1]):
#             image = images[0, i]
#             name = str(image['Name'][0][0]) if image['Name'][0].size > 0 else f"Image_{i}"
#             slaves = image['slaves']
            
#             if slaves.size > 0:
#                 # Handle different slaves structures
#                 if slaves[0].size > 0:
#                     if hasattr(slaves[0][0], 'dtype') and slaves[0][0].dtype.names:
#                         # Structure array
#                         roi_count = len(slaves[0])
#                         print(f"  {name}: {roi_count} ROIs")
                        
#                         for j in range(roi_count):
#                             roi = slaves[0][j]
#                             roi_name = str(roi['Name'][0][0]) if roi['Name'][0].size > 0 else f"ROI_{j}"
#                             roi_data = roi['data'][0]
#                             unique_vals = np.unique(roi_data)
#                             voxel_count = np.sum(roi_data > 0)
#                             print(f"    ROI {j+1}: {roi_name}, shape: {roi_data.shape}, voxels: {voxel_count}, values: {len(unique_vals)} unique")
#                     else:
#                         print(f"  {name}: slaves structure but no ROI data")
#                 else:
#                     print(f"  {name}: Empty slaves")
#             else:
#                 print(f"  {name}: No ROIs")
                
#         print("=== ROI CHECK COMPLETE ===")
        
#     except Exception as e:
#         print(f"Error checking ROI structure: {e}")
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1:
#         project_file = sys.argv[1]
#     else:
#         project_file = "automated_outputs/clean_run_20250723_133113/complete_roi_clean_project.mat"
    
#     check_roi_structure(project_file)
