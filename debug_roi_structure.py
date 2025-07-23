# """
# Debug: Check project structure after ROI application
# """

# import scipy.io as sio
# import matlab.engine
# import os

# def debug_project_structure():
#     # Find the latest ROI project file
#     latest_dir = "automated_outputs/matlab_safe_run_20250723_122922"
#     roi_file = os.path.join(latest_dir, "roi_matlab_safe_project.mat")
    
#     if not os.path.exists(roi_file):
#         print(f"ROI file not found: {roi_file}")
#         return
    
#     print(f"Debugging project structure: {roi_file}")
    
#     # Load with Python
#     try:
#         data = sio.loadmat(roi_file, struct_as_record=False, squeeze_me=True)
#         print("\n=== Python Load Results ===")
#         print(f"Top-level keys: {list(data.keys())}")
        
#         if 'images' in data:
#             images = data['images']
#             print(f"Images type: {type(images)}")
#             print(f"Images length: {len(images) if hasattr(images, '__len__') else 'N/A'}")
            
#             # Check first few images
#             for i in range(min(3, len(images))):
#                 img = images[i] if hasattr(images, '__getitem__') else images
#                 print(f"\nImage {i}:")
#                 if hasattr(img, 'Name'):
#                     print(f"  Name: {img.Name}")
#                 if hasattr(img, 'slaves'):
#                     print(f"  Has slaves: {img.slaves is not None}")
#                     if img.slaves is not None:
#                         print(f"  Slaves type: {type(img.slaves)}")
#                         print(f"  Slaves length: {len(img.slaves) if hasattr(img.slaves, '__len__') else 'N/A'}")
                        
#         print("\n=== MATLAB Load Test ===")
        
#         # Test with MATLAB engine
#         eng = matlab.engine.start_matlab()
        
#         # MATLAB script to check structure
#         script = f"""
#         try
#             data = load('{roi_file.replace(chr(92), '/')}');
#             fprintf('MATLAB load successful\\n');
            
#             if isfield(data, 'images')
#                 fprintf('Images field exists\\n');
#                 images = data.images;
#                 fprintf('Images type: %s\\n', class(images));
#                 fprintf('Images size: [%s]\\n', num2str(size(images)));
                
#                 for i = 1:min(3, length(images))
#                     fprintf('\\nImage %d:\\n', i);
                    
#                     if isfield(images(i), 'Name')
#                         name_field = images(i).Name;
#                         if ischar(name_field)
#                             fprintf('  Name: %s\\n', name_field);
#                         else
#                             fprintf('  Name type: %s\\n', class(name_field));
#                         end
#                     end
                    
#                     if isfield(images(i), 'slaves')
#                         slaves = images(i).slaves;
#                         if isempty(slaves)
#                             fprintf('  Slaves: empty\\n');
#                         else
#                             fprintf('  Slaves type: %s\\n', class(slaves));
#                             fprintf('  Slaves size: [%s]\\n', num2str(size(slaves)));
#                         end
#                     else
#                         fprintf('  No slaves field\\n');
#                     end
#                 end
#             else
#                 fprintf('No images field found\\n');
#             end
            
#         catch ME
#             fprintf('MATLAB error: %s\\n', ME.message);
#         end
#         """
        
#         script_file = 'debug_structure.m'
#         with open(script_file, 'w') as f:
#             f.write(script)
        
#         eng.run('debug_structure', nargout=0)
        
#         eng.quit()
        
#         if os.path.exists(script_file):
#             os.remove(script_file)
            
#     except Exception as e:
#         print(f"Error: {e}")

# if __name__ == "__main__":
#     debug_project_structure()
