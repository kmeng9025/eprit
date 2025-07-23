% Test the MATLAB-native project file
% This script verifies the project can be loaded and used in ArbuzGUI

fprintf('Testing MATLAB-native project file...\n');

% Load the project
project_file = 'matlab_native_project.mat';
if ~exist(project_file, 'file')
    error('Project file not found: %s', project_file);
end

fprintf('Loading project: %s\n', project_file);
project_data = load(project_file);

% Check project structure
fprintf('\n=== PROJECT STRUCTURE ===\n');
fprintf('Status: %d\n', project_data.status);
fprintf('File type: %s\n', project_data.file_type);
fprintf('Number of images: %d\n', length(project_data.images));

% Test each image
fprintf('\n=== IMAGE DETAILS ===\n');
for i = 1:length(project_data.images)
    img = project_data.images(i);
    fprintf('Image %d: %s\n', i, img.Name);
    fprintf('  Type: %s\n', img.ImageType);
    fprintf('  Data size: %s\n', mat2str(size(img.data)));
    
    % Test mask access - this is what was failing before
    try
        mask = img.data_info.Mask;
        mask_subset = mask(:,:,:);
        fprintf('  Mask: OK (size: %s)\n', mat2str(size(mask)));
    catch ME
        fprintf('  Mask: ERROR - %s\n', ME.message);
    end
    
    % Test transformation matrices
    if isfield(img, 'A') && ~isempty(img.A)
        fprintf('  Transform A: OK\n');
    else
        fprintf('  Transform A: Missing\n');
    end
    
    fprintf('\n');
end

% Test if this can be used with ArbuzGUI functions
fprintf('=== ARBUZGUI COMPATIBILITY TEST ===\n');
try
    % Try to use with ibGUI-like operations
    test_img = project_data.images(1);
    
    % Test the specific operation that was failing
    if isfield(test_img, 'data_info') && isfield(test_img.data_info, 'Mask')
        DataMask = test_img.data_info.Mask;
        
        % This is the line that was causing "Array indices must be positive integers"
        test_access = DataMask(:,:,:,1);  % This should work now
        fprintf('DataMask indexing: PASSED\n');
        
        % Also test the 4D indexing that might be used
        if size(DataMask, 4) >= 1
            test_4d = DataMask(:,:,:,1);
            fprintf('4D mask indexing: PASSED\n');
        else
            fprintf('3D mask only (no 4th dimension)\n');
        end
        
    else
        fprintf('No mask found in data_info structure\n');
    end
    
    fprintf('\n✅ Project appears compatible with ArbuzGUI!\n');
    
catch ME
    fprintf('❌ Compatibility issue: %s\n', ME.message);
end

fprintf('\n=== TEST COMPLETE ===\n');
