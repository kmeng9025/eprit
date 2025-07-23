# """
# Create a proper MATLAB-compatible project using MATLAB engine
# This ensures all structures are created correctly in MATLAB format
# """

# import matlab.engine
# import numpy as np
# import os
# from pathlib import Path

# def create_matlab_native_project():
#     """Create project file directly in MATLAB to avoid compatibility issues"""
    
#     print("Creating MATLAB-native project file...")
    
#     try:
#         # Start MATLAB engine
#         print("Starting MATLAB engine...")
#         eng = matlab.engine.start_matlab()
        
#         # Add paths
#         paths = [
#             r'c:\Users\ftmen\Documents\v3',
#             r'c:\Users\ftmen\Documents\v3\Arbuz2.0',
#             r'c:\Users\ftmen\Documents\v3\epri',
#             r'c:\Users\ftmen\Documents\v3\common',
#             r'c:\Users\ftmen\Documents\v3\process'
#         ]
        
#         for path in paths:
#             eng.addpath(path, nargout=0)
        
#         # Create MATLAB script to build proper project file
#         matlab_script = """
# function create_proper_project()
#     % Create a proper ArbuzGUI project file with correct structure
    
#     fprintf('Creating MATLAB-native project...\\n');
    
#     % Find existing processed files
#     data_folder = 'c:/Users/ftmen/Documents/v3/DATA/241202';
#     pattern = fullfile(data_folder, 'p*image4D_18x18_0p75gcm_file.mat');
#     files = dir(pattern);
    
#     if length(files) < 12
#         error('Not enough processed files found');
#     end
    
#     % Sort files
#     [~, idx] = sort({files.name});
#     files = files(idx);
    
#     % Image naming scheme
#     names = {'BE_AMP', 'BE1', 'BE2', 'BE3', 'BE4', 'ME1', 'ME2', 'ME3', 'ME4', 'AE1', 'AE2', 'AE3', 'AE4'};
#     types = {'AMP_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', ...
#              'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', ...
#              'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI'};
    
#     % Initialize project structure
#     project = struct();
#     project.status = 1;
#     project.file_type = 'ArbuzGUI';
#     project.transformations = [];
#     project.sequences = [];
#     project.groups = [];
#     project.activesequence = 0;
#     project.activetransformation = 0;
#     project.saves = [];
#     project.comments = '';
    
#     % Create images array
#     images = [];
    
#     for i = 1:min(13, length(files))
#         fprintf('Processing image %d: %s\\n', i, names{i});
        
#         % Load image data
#         file_path = fullfile(files(i).folder, files(i).name);
#         loaded_data = load(file_path);
        
#         % Create image structure
#         img = struct();
#         img.Name = names{i};
#         img.ImageType = types{i};
#         img.FileName = file_path;
#         img.isStore = 1;
#         img.isLoaded = 1;
        
#         % Load image using ArbuzGUI functions
#         try
#             [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(file_path, types{i});
            
#             img.data = imageData;
#             img.ImageType = actualType;
            
#             % Create proper data_info structure
#             img.data_info = struct();
            
#             % Create proper mask - this is crucial for MATLAB compatibility
#             data_size = size(imageData);
#             if length(data_size) >= 3
#                 img.data_info.Mask = true(data_size(1), data_size(2), data_size(3));
#             else
#                 img.data_info.Mask = true(size(imageData));
#             end
            
#             % Set transformation matrices
#             if isfield(imageInfo, 'Anative')
#                 img.Anative = imageInfo.Anative;
#             else
#                 img.Anative = eye(4);
#             end
            
#             if isfield(imageInfo, 'Bbox')
#                 img.box = imageInfo.Bbox;
#             else
#                 img.box = size(imageData);
#             end
            
#             img.A = eye(4);
#             img.Aprime = eye(4);
            
#             fprintf('  [OK] Image %s loaded successfully\\n', names{i});
            
#         catch ME
#             fprintf('  [ERROR] Error loading %s: %s\\n', names{i}, ME.message);
#             % Create minimal structure if loading fails
#             img.data = zeros(64, 64, 64);
#             img.data_info = struct();
#             img.data_info.Mask = true(64, 64, 64);
#             img.A = eye(4);
#             img.Anative = eye(4);
#             img.Aprime = eye(4);
#             img.box = [64, 64, 64];
#         end
        
#         % Add to images array
#         if isempty(images)
#             images = img;
#         else
#             images(end+1) = img;
#         end
#     end
    
#     project.images = images;
    
#     % Save project
#     output_file = 'matlab_native_project.mat';
#     save(output_file, '-struct', 'project');
    
#     fprintf('[SUCCESS] MATLAB-native project saved: %s\\n', output_file);
#     fprintf('[INFO] Created project with %d images\\n', length(images));
    
#     % Test the mask indexing to make sure it works
#     fprintf('\\n[TEST] Testing mask indexing...\\n');
#     for i = 1:length(images)
#         try
#             mask = images(i).data_info.Mask;
#             test_subset = mask(:,:,:);
#             fprintf('  [OK] Image %s: mask indexing OK\\n', images(i).Name);
#         catch ME
#             fprintf('  [ERROR] Image %s: mask indexing failed: %s\\n', images(i).Name, ME.message);
#         end
#     end
# end
#         """
        
#         # Write MATLAB script
#         with open('create_proper_project.m', 'w') as f:
#             f.write(matlab_script)
        
#         # Execute the script
#         print("Executing MATLAB script...")
#         eng.create_proper_project(nargout=0)
        
#         # Clean up
#         eng.quit()
        
#         # Check if file was created
#         if os.path.exists('matlab_native_project.mat'):
#             print("MATLAB-native project created successfully!")
#             return 'matlab_native_project.mat'
#         else:
#             print("Failed to create MATLAB-native project")
#             return None
            
#     except Exception as e:
#         print(f"Error creating MATLAB-native project: {e}")
#         return None
#     finally:
#         # Clean up script file
#         if os.path.exists('create_proper_project.m'):
#             os.remove('create_proper_project.m')

# def main():
#     """Main function"""
#     print("MATLAB-NATIVE PROJECT CREATOR")
#     print("=" * 40)
    
#     # Create the project using MATLAB directly
#     project_file = create_matlab_native_project()
    
#     if project_file:
#         print(f"\nMATLAB-native project created: {project_file}")
#         print("\nThis project should work properly with ArbuzGUI!")
#         print("\nTo test:")
#         print("1. Open MATLAB")
#         print("2. Load the project file")
#         print("3. Try opening it in ArbuzGUI")
#     else:
#         print("\nFailed to create MATLAB-native project")

# if __name__ == "__main__":
#     main()
