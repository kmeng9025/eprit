# #!/usr/bin/env python3
# """
# ROI Copy Script for ArbuzGUI Projects
# Author: AI Assistant
# Date: July 2025

# This script copies ROI masks from one image to all other images in an ArbuzGUI project.
# Specifically designed to copy kidney ROI from BE_AMP to all other images.
# """

# import os
# import sys
# import numpy as np
# import scipy.io as sio
# from pathlib import Path

# class ROICopyProcessor:
#     def __init__(self):
#         pass
    
#     def create_roi_copy(self, source_roi, target_name="Kidney"):
#         """Create a copy of ROI structure for a target image"""
#         identity = np.eye(4, dtype=np.float64)
        
#         # Handle both dict and object types for source_roi
#         if isinstance(source_roi, dict):
#             roi_data = source_roi.get('data')
#             roi_box = source_roi.get('box', np.array(roi_data.shape if roi_data is not None else [0,0,0]))
#         else:
#             roi_data = getattr(source_roi, 'data', None)
#             roi_box = getattr(source_roi, 'box', np.array(roi_data.shape if roi_data is not None else [0,0,0]))
        
#         if roi_data is None:
#             raise ValueError("Source ROI has no data")
        
#         roi_copy = {
#             'data': roi_data.copy().astype(bool),
#             'ImageType': '3DMASK',
#             'Name': str(target_name),
#             'A': identity.copy(),
#             'Anative': identity.copy(),
#             'Aprime': identity.copy(),
#             'isStore': 1,
#             'isLoaded': 1,
#             'Selected': 0,
#             'Visible': 0,
#             'box': roi_box.copy() if isinstance(roi_box, np.ndarray) else np.array(roi_box),
#             'pars': np.array([]),
#             'FileName': ''
#         }
        
#         return roi_copy
    
#     def find_source_image_and_roi(self, images_array, source_image_name="BE_AMP"):
#         """Find the source image and extract its ROI"""
#         source_image = None
#         source_roi = None
#         source_index = None
        
#         for i, img in enumerate(images_array):
#             # Handle both dict and object types
#             if isinstance(img, dict):
#                 name = img.get('Name', '')
#                 slaves = img.get('slaves', np.array([]))
#             elif hasattr(img, 'Name'):
#                 name = str(img.Name)
#                 slaves = getattr(img, 'slaves', np.array([]))
#             else:
#                 continue
            
#             if source_image_name in str(name):
#                 source_image = img
#                 source_index = i
                
#                 # Look for ROI in slaves
#                 if len(slaves) > 0:
#                     for slave in slaves:
#                         slave_type = slave.get('ImageType') if isinstance(slave, dict) else getattr(slave, 'ImageType', '')
#                         if '3DMASK' in str(slave_type):
#                             source_roi = slave
#                             break
#                 break
        
#         return source_image, source_roi, source_index
    
#     def copy_roi_to_all_images(self, project_file, source_image_name="BE_AMP", output_file=None):
#         """Copy ROI from source image to all other images in the project"""
#         try:
#             print(f"🔄 Loading project file: {project_file}")
            
#             # Load project
#             project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
#             if 'images' not in project:
#                 raise KeyError("'images' not found in project file")
            
#             images_array = project['images']
#             print(f"📊 Project contains {len(images_array)} images")
            
#             # Find source image and ROI
#             source_image, source_roi, source_index = self.find_source_image_and_roi(images_array, source_image_name)
            
#             if source_image is None:
#                 raise ValueError(f"Source image '{source_image_name}' not found in project")
            
#             if source_roi is None:
#                 raise ValueError(f"No ROI found in source image '{source_image_name}'")
            
#             print(f"✅ Found source image '{source_image_name}' at index {source_index}")
#             print(f"✅ Found ROI in source image")
            
#             # Get ROI data info
#             roi_data = source_roi.get('data') if isinstance(source_roi, dict) else getattr(source_roi, 'data', None)
#             if roi_data is not None:
#                 print(f"📊 ROI data shape: {roi_data.shape}, total voxels: {np.sum(roi_data.astype(bool))}")
            
#             # Copy ROI to all other images
#             copied_count = 0
#             skipped_count = 0
            
#             for i, img in enumerate(images_array):
#                 # Skip the source image
#                 if i == source_index:
#                     continue
                
#                 # Get image name
#                 if isinstance(img, dict):
#                     name = img.get('Name', f'Image_{i}')
#                 elif hasattr(img, 'Name'):
#                     name = str(img.Name)
#                 else:
#                     name = f'Image_{i}'
                
#                 try:
#                     # Create ROI copy
#                     roi_copy = self.create_roi_copy(source_roi, "Kidney")
                    
#                     # Attach ROI to image
#                     if isinstance(img, dict):
#                         img['slaves'] = np.array([roi_copy], dtype=object)
#                     else:
#                         img.slaves = np.array([roi_copy], dtype=object)
                    
#                     copied_count += 1
#                     print(f"   ✅ {name}: ROI copied")
                    
#                 except Exception as e:
#                     print(f"   ⚠️  {name}: Failed to copy ROI - {e}")
#                     skipped_count += 1
            
#             print(f"\n📋 ROI Copy Summary:")
#             print(f"   ✅ Successfully copied to {copied_count} images")
#             if skipped_count > 0:
#                 print(f"   ⚠️  Skipped {skipped_count} images due to errors")
            
#             # Save updated project
#             if output_file is None:
#                 output_file = project_file  # Overwrite original
            
#             sio.savemat(output_file, project, do_compression=True)
#             print(f"✅ Updated project saved to: {output_file}")
            
#             return output_file
            
#         except Exception as e:
#             print(f"❌ Error copying ROI: {e}")
#             return None
    
#     def list_images_and_rois(self, project_file):
#         """List all images and their ROIs in the project (for debugging)"""
#         try:
#             print(f"🔍 Analyzing project file: {project_file}")
            
#             # Load project
#             project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
#             if 'images' not in project:
#                 raise KeyError("'images' not found in project file")
            
#             images_array = project['images']
            
#             # Handle case where images might be a single object or array
#             if not hasattr(images_array, '__len__'):
#                 images_array = [images_array]
            
#             print(f"\n📊 Project Analysis:")
#             print(f"   Total images: {len(images_array)}")
            
#             for i, img in enumerate(images_array):
#                 # Get image info
#                 if isinstance(img, dict):
#                     name = img.get('Name', f'Image_{i}')
#                     image_type = img.get('ImageType', 'Unknown')
#                     slaves = img.get('slaves', np.array([]))
#                     data = img.get('data')
#                 elif hasattr(img, 'Name'):
#                     name = str(img.Name)
#                     image_type = getattr(img, 'ImageType', 'Unknown')
#                     slaves = getattr(img, 'slaves', np.array([]))
#                     data = getattr(img, 'data', None)
#                 else:
#                     name = f'Image_{i}'
#                     image_type = 'Unknown'
#                     slaves = np.array([])
#                     data = None
                
#                 # Ensure slaves is iterable
#                 if not hasattr(slaves, '__len__'):
#                     slaves = [slaves] if slaves is not None else []
                
#                 # Count ROIs
#                 roi_count = 0
#                 roi_names = []
#                 for slave in slaves:
#                     if slave is None:
#                         continue
#                     slave_type = slave.get('ImageType') if isinstance(slave, dict) else getattr(slave, 'ImageType', '')
#                     if '3DMASK' in str(slave_type):
#                         roi_count += 1
#                         slave_name = slave.get('Name') if isinstance(slave, dict) else getattr(slave, 'Name', 'Unnamed')
#                         roi_names.append(str(slave_name))
                
#                 # Print info
#                 data_shape = data.shape if data is not None else 'No data'
#                 roi_info = f"{roi_count} ROIs: {', '.join(roi_names)}" if roi_count > 0 else "No ROIs"
#                 print(f"   {i+1:2d}. {name:>8s} ({image_type}) - {data_shape} - {roi_info}")
            
#             return True
            
#         except Exception as e:
#             print(f"❌ Error analyzing project: {e}")
#             import traceback
#             traceback.print_exc()
#             return False

# def main():
#     """Main entry point for command line usage"""
#     if len(sys.argv) < 2:
#         print("Usage: python roi_copy_script.py <project_file.mat> [options]")
#         print("Options:")
#         print("  --analyze             Analyze project and list images/ROIs")
#         print("  --source <name>       Source image name (default: BE_AMP)")
#         print("  --output <file>       Output file (default: overwrite input)")
#         print("")
#         print("Examples:")
#         print("  python roi_copy_script.py project.mat --analyze")
#         print("  python roi_copy_script.py project.mat")
#         print("  python roi_copy_script.py project.mat --source BE_AMP --output updated_project.mat")
#         sys.exit(1)
    
#     project_file = sys.argv[1]
    
#     if not os.path.exists(project_file):
#         print(f"❌ Project file not found: {project_file}")
#         sys.exit(1)
    
#     # Parse arguments
#     analyze_only = '--analyze' in sys.argv
#     source_name = "BE_AMP"
#     output_file = None
    
#     for i, arg in enumerate(sys.argv):
#         if arg == '--source' and i + 1 < len(sys.argv):
#             source_name = sys.argv[i + 1]
#         elif arg == '--output' and i + 1 < len(sys.argv):
#             output_file = sys.argv[i + 1]
    
#     # Create processor
#     processor = ROICopyProcessor()
    
#     if analyze_only:
#         # Just analyze and exit
#         success = processor.list_images_and_rois(project_file)
#         sys.exit(0 if success else 1)
#     else:
#         # Copy ROI
#         result = processor.copy_roi_to_all_images(project_file, source_name, output_file)
        
#         if result:
#             print(f"\n🎉 Successfully copied ROI from {source_name} to all images")
#             sys.exit(0)
#         else:
#             print(f"\n❌ Failed to copy ROI")
#             sys.exit(1)

# if __name__ == "__main__":
#     main()
