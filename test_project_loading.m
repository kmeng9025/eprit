% Test script to verify the fixed project file loads properly in MATLAB
% This helps diagnose the array indexing issue

function test_project_loading()
    fprintf('Testing MATLAB project file loading...\n');
    
    % Test files to try
    test_files = {
        'automated_outputs/clean_run_20250723_115247/complete_roi_clean_project_matlab_fixed.mat',
        'test_minimal_project.mat',
        'automated_outputs/clean_run_20250723_115247/clean_project.mat'
    };
    
    for i = 1:length(test_files)
        test_file = test_files{i};
        
        if exist(test_file, 'file')
            fprintf('\n=== Testing file: %s ===\n', test_file);
            
            try
                % Try to load the project
                fprintf('Loading project file...\n');
                data = load(test_file);
                fprintf('✅ Project loaded successfully\n');
                
                % Check structure
                if isfield(data, 'images')
                    fprintf('✅ Images field found\n');
                    images = data.images;
                    fprintf('📊 Number of images: %d\n', length(images));
                    
                    % Test first image
                    if length(images) > 0
                        img = images(1);
                        fprintf('Testing first image...\n');
                        
                        if isfield(img, 'Name')
                            fprintf('✅ Image name: %s\n', img.Name);
                        end
                        
                        if isfield(img, 'data')
                            fprintf('✅ Image data size: %s\n', mat2str(size(img.data)));
                            fprintf('✅ Image data type: %s\n', class(img.data));
                        end
                        
                        if isfield(img, 'data_info') && isfield(img.data_info, 'Mask')
                            mask = img.data_info.Mask;
                            fprintf('✅ Mask size: %s\n', mat2str(size(mask)));
                            fprintf('✅ Mask type: %s\n', class(mask));
                            
                            % Test the problematic indexing that was causing errors
                            try
                                fprintf('Testing mask indexing...\n');
                                if ndims(mask) == 3
                                    test_subset = mask(:,:,:);
                                    fprintf('✅ 3D mask indexing works\n');
                                elseif ndims(mask) == 4
                                    test_subset = mask(:,:,:,1);
                                    fprintf('✅ 4D mask indexing works\n');
                                else
                                    fprintf('⚠️  Unusual mask dimensions: %d\n', ndims(mask));
                                end
                                
                                % Test if mask is logical
                                if islogical(mask)
                                    fprintf('✅ Mask is logical type\n');
                                else
                                    fprintf('⚠️  Mask is not logical type: %s\n', class(mask));
                                end
                                
                            catch ME
                                fprintf('❌ Mask indexing failed: %s\n', ME.message);
                            end
                        else
                            fprintf('⚠️  No mask found in data_info\n');
                        end
                    end
                    
                    fprintf('✅ Basic project structure test passed\n');
                    
                else
                    fprintf('❌ No images field found\n');
                end
                
            catch ME
                fprintf('❌ Error loading project: %s\n', ME.message);
                fprintf('   Stack:\n');
                for j = 1:length(ME.stack)
                    fprintf('     %s (line %d)\n', ME.stack(j).name, ME.stack(j).line);
                end
            end
        else
            fprintf('⚠️  File not found: %s\n', test_file);
        end
    end
    
    fprintf('\n=== Test Complete ===\n');
end
