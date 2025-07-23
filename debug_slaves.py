# import scipy.io
# import numpy as np

# def debug_slaves_structure(project_file):
#     """Debug the slaves structure"""
#     try:
#         print(f"=== DEBUGGING SLAVES STRUCTURE: {project_file} ===")
#         data = scipy.io.loadmat(project_file)
        
#         images = data['images']
#         print(f"Found {images.shape[1]} images")
        
#         # Check first image in detail
#         image = images[0, 0]  # First image (BE_AMP)
#         name = str(image['Name'][0][0]) if image['Name'][0].size > 0 else "Unknown"
#         print(f"\nFirst image: {name}")
        
#         slaves = image['slaves']
#         print(f"Slaves type: {type(slaves)}")
#         print(f"Slaves shape: {slaves.shape}")
#         print(f"Slaves size: {slaves.size}")
        
#         if slaves.size > 0:
#             print(f"Slaves[0] type: {type(slaves[0])}")
#             print(f"Slaves[0] shape: {slaves[0].shape}")
#             print(f"Slaves[0] size: {slaves[0].size}")
            
#             if slaves[0].size > 0:
#                 print(f"Slaves[0][0] type: {type(slaves[0][0])}")
#                 if hasattr(slaves[0][0], 'dtype'):
#                     print(f"Slaves[0][0] dtype: {slaves[0][0].dtype}")
#                     if hasattr(slaves[0][0].dtype, 'names') and slaves[0][0].dtype.names:
#                         print(f"Slaves[0][0] fields: {slaves[0][0].dtype.names}")
#                     else:
#                         print("No dtype names")
#                 else:
#                     print("No dtype attribute")
        
#         print("=== DEBUG COMPLETE ===")
        
#     except Exception as e:
#         print(f"Error debugging slaves: {e}")
#         import traceback
#         traceback.print_exc()

# if __name__ == "__main__":
#     import sys
#     if len(sys.argv) > 1:
#         project_file = sys.argv[1]
#     else:
#         project_file = "automated_outputs/clean_run_20250723_133113/roi_clean_project.mat"
    
#     debug_slaves_structure(project_file)
