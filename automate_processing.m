function automate_processing()
% Automated processing pipeline for medical scan data
% Processes TDMS files, creates ArbuzGUI project, and extracts ROI statistics

addpath(genpath('.'));

% Configuration
data_dir = 'DATA/241202';
output_base = 'automated_outputs';
timestamp = datestr(now, 'yyyymmdd_HHMMSS');
output_dir = fullfile(output_base, ['run_' timestamp]);

% Create output directory
if ~exist(output_dir, 'dir')
    mkdir(output_dir);
end

fprintf('Starting automated processing...\n');
fprintf('Output directory: %s\n', output_dir);

% Step 1: Identify and process TDMS files
fprintf('\n=== Step 1: Identifying TDMS files ===\n');
tdms_files = identify_image_files(data_dir);
fprintf('Found %d image files to process\n', length(tdms_files));

% Step 2: Process files if needed (check if .mat files exist)
fprintf('\n=== Step 2: Processing TDMS files ===\n');
process_tdms_files(tdms_files, data_dir);

% Step 3: Build ArbuzGUI project
fprintf('\n=== Step 3: Building ArbuzGUI project ===\n');
project_file = build_arbuz_project(data_dir, output_dir);

% Step 4: Create ROI using Python script
fprintf('\n=== Step 4: Creating kidney ROI ===\n');
create_kidney_roi(project_file, output_dir);

% Step 5: Extract statistics
fprintf('\n=== Step 5: Extracting ROI statistics ===\n');
extract_roi_statistics(project_file, output_dir);

fprintf('\n=== Processing complete! ===\n');
fprintf('Results saved in: %s\n', output_dir);

end

function tdms_files = identify_image_files(data_dir)
% Identify all image4D TDMS files, excluding tuning files

files = dir(fullfile(data_dir, '*image4D_18x18_0p75gcm_file.tdms'));
tdms_files = {};

for i = 1:length(files)
    filename = files(i).name;
    % Skip tuning files
    if ~contains(filename, 'FID_GRAD_MIN')
        tdms_files{end+1} = fullfile(data_dir, filename);
    end
end

% Sort files numerically
file_numbers = [];
for i = 1:length(tdms_files)
    [~, name, ~] = fileparts(tdms_files{i});
    num_str = regexp(name, '^(\d+)', 'tokens');
    if ~isempty(num_str)
        file_numbers(i) = str2double(num_str{1}{1});
    else
        file_numbers(i) = inf;
    end
end
[~, sort_idx] = sort(file_numbers);
tdms_files = tdms_files(sort_idx);

end

function process_tdms_files(tdms_files, data_dir)
% Process TDMS files using ProcessGUI functionality

% Load required scenario and parameter files
scenario_file = 'epri/Scenario/PulseRecon.scn';
param_file = 'epri/Scenario/720MHz_JIVA5B/IRESE_64pts_mouse_STANDARD_CHIRALITY.par';

if ~exist(scenario_file, 'file') || ~exist(param_file, 'file')
    error('Required scenario or parameter files not found');
end

% Get processing fields
fields = load_processing_fields(scenario_file, param_file);

for i = 1:length(tdms_files)
    tdms_file = tdms_files{i};
    [filepath, name, ~] = fileparts(tdms_file);
    
    % Check if already processed
    mat_file = fullfile(filepath, [name '.mat']);
    p_mat_file = fullfile(filepath, ['p' name '.mat']);
    
    if exist(mat_file, 'file') && exist(p_mat_file, 'file')
        fprintf('Already processed: %s\n', name);
        continue;
    end
    
    fprintf('Processing: %s\n', name);
    
    try
        % Find corresponding cavity file
        cavity_file = find_cavity_file(tdms_file, data_dir);
        
        % Process the file
        process_single_file(tdms_file, cavity_file, fields, filepath);
        
    catch ME
        fprintf('Error processing %s: %s\n', name, ME.message);
        continue;
    end
end

end

function fields = load_processing_fields(scenario_file, param_file)
% Load processing parameters from scenario and parameter files

% This is a simplified version - in practice, you'd parse the scenario file
% For now, use default parameters that work for your data
fields = struct();
fields.fbp = struct('sequence', '2pECHO', 'nPolar', 18, 'nAz', 18);
fields.td = struct();
fields.fft = struct();
fields.rec = struct();
fields.img = struct();
fields.fit = struct();
fields.clb = struct();
fields.prc = struct('process_method', 'ese_fbp');

end

function cavity_file = find_cavity_file(tdms_file, data_dir)
% Find the appropriate cavity file for a given TDMS file

[~, name, ~] = fileparts(tdms_file);
file_num = str2double(regexp(name, '^(\d+)', 'tokens', 'once'));

% Find cavity files in the directory
cavity_files = dir(fullfile(data_dir, '*cavity_profile_file.tdms'));
cavity_nums = [];

for i = 1:length(cavity_files)
    cavity_name = cavity_files(i).name;
    num_str = regexp(cavity_name, '^(\d+)', 'tokens', 'once');
    if ~isempty(num_str)
        cavity_nums(i) = str2double(num_str{1});
    end
end

% Find the closest cavity file (should be just before the image file)
valid_cavities = cavity_nums(cavity_nums <= file_num);
if isempty(valid_cavities)
    error('No suitable cavity file found for %s', name);
end

[~, idx] = max(valid_cavities);
cavity_idx = find(cavity_nums == valid_cavities(idx), 1);
cavity_file = fullfile(data_dir, cavity_files(cavity_idx).name);

end

function process_single_file(tdms_file, cavity_file, fields, output_path)
% Process a single TDMS file using the ese_fbp method

try
    % This calls the actual processing function
    % You may need to adjust this based on the exact ese_fbp function signature
    Image = ese_fbp(tdms_file, '_file', output_path, fields);
    
    fprintf('Successfully processed: %s\n', tdms_file);
    
catch ME
    fprintf('Error in ese_fbp for %s: %s\n', tdms_file, ME.message);
    rethrow(ME);
end

end

function project_file = build_arbuz_project(data_dir, output_dir)
% Build ArbuzGUI-compatible project file

fprintf('Building ArbuzGUI project...\n');

% Get all processed files
p_files = dir(fullfile(data_dir, 'p*image4D_18x18_0p75gcm_file.mat'));
regular_files = dir(fullfile(data_dir, '*image4D_18x18_0p75gcm_file.mat'));

% Remove p-files from regular files list
regular_files_filtered = [];
for i = 1:length(regular_files)
    if ~startsWith(regular_files(i).name, 'p')
        regular_files_filtered = [regular_files_filtered; regular_files(i)];
    end
end
regular_files = regular_files_filtered;

% Sort files numerically
[p_files_sorted, p_numbers] = sort_files_numerically(p_files);
[regular_files_sorted, regular_numbers] = sort_files_numerically(regular_files);

% Define image names and groups
image_names = {'BE1', 'BE2', 'BE3', 'BE4', 'ME1', 'ME2', 'ME3', 'ME4', ...
               'AE1', 'AE2', 'AE3', 'AE4'};

if length(p_files_sorted) ~= length(image_names)
    error('Expected %d files, found %d', length(image_names), length(p_files_sorted));
end

% Initialize project structure
project = struct();
project.file_type = 'ARBUZ';
project.activesequence = int64(1);
project.activetransformation = int64(1);
project.comments = '';
project.groups = {};
project.saves = {};
project.sequences = {};
project.status = uint8([]);
project.transformations = {};

% Build images array
images = cell(1, length(image_names) + 1); % +1 for BE_AMP

% Process regular images
for i = 1:length(image_names)
    p_file = fullfile(data_dir, p_files_sorted(i).name);
    
    % Find corresponding regular file
    p_name = p_files_sorted(i).name;
    regular_name = strrep(p_name, 'p', ''); % Remove 'p' prefix
    regular_file = fullfile(data_dir, regular_name);
    
    image_name = ['>' image_names{i}];
    
    % Extract image data
    [image_data, image_info] = extract_image_data(p_file, regular_file);
    
    % Create image structure
    img_struct = create_image_structure(image_name, 'EPRI', image_data, ...
                                      image_info, p_file);
    images{i} = img_struct;
end

% Create BE_AMP image (amplitude version of BE1)
be1_file = fullfile(data_dir, p_files_sorted(1).name);
[amp_data, amp_info] = create_amplitude_image(be1_file);
amp_struct = create_image_structure('>BE_AMP', 'AMP_pEPRI', amp_data, ...
                                  amp_info, be1_file);
images{end} = amp_struct;

project.images = images;

% Save project file
project_file = fullfile(output_dir, 'project.mat');
save(project_file, '-struct', 'project', '-v7');  % Use v7 format for Python compatibility

fprintf('Project saved: %s\n', project_file);

end

function [files_sorted, numbers] = sort_files_numerically(files)
% Sort files numerically by their leading number

numbers = [];
for i = 1:length(files)
    name = files(i).name;
    num_str = regexp(name, '^p?(\d+)', 'tokens', 'once');
    if ~isempty(num_str)
        numbers(i) = str2double(num_str{1});
    else
        numbers(i) = inf;
    end
end

[numbers, sort_idx] = sort(numbers);
files_sorted = files(sort_idx);

end

function [image_data, image_info] = extract_image_data(p_file, regular_file)
% Extract image data from either p-file or regular file

% Try regular file first (contains reconstructed image data)
if ~isempty(regular_file) && exist(regular_file, 'file')
    try
        reg_data = load(regular_file);
        if isfield(reg_data, 'mat_recFXD')
            % Use reconstructed data - take first time point
            image_data = double(reg_data.mat_recFXD(:,:,:,1));
            image_info = reg_data.rec_info;
            return;
        end
    catch ME
        fprintf('Warning: Could not load regular file %s: %s\n', regular_file, ME.message);
    end
end

% Try p-file as fallback
try
    p_data = load(p_file);
    if isfield(p_data, 'fit_data') && isfield(p_data.fit_data, 'P')
        % Reshape fit data to 3D image
        P = p_data.fit_data.P;
        Size = p_data.fit_data.Size;
        Idx = p_data.fit_data.Idx;
        
        % P might have multiple parameters - use first one
        if size(P, 1) > 1
            P = P(1, :);  % Take first parameter
        end
        
        % Create full image with background
        image_data = zeros(Size);
        image_data(Idx) = P(:);
        image_data = double(image_data);
        
        image_info = p_data.rec_info;
        return;
    end
catch ME
    fprintf('Warning: Could not load p-file %s: %s\n', p_file, ME.message);
end

error('Could not extract image data from %s or %s', p_file, regular_file);

end

function [amp_data, amp_info] = create_amplitude_image(be1_file)
% Create amplitude image from BE1 data

% Get the corresponding regular file
[filepath, name, ext] = fileparts(be1_file);
regular_name = strrep(name, 'p', ''); % Remove 'p' prefix
regular_file = fullfile(filepath, [regular_name ext]);

[image_data, image_info] = extract_image_data(be1_file, regular_file);

% Calculate amplitude (magnitude)
amp_data = abs(image_data);

amp_info = image_info;

end

function img_struct = create_image_structure(name, image_type, data, info, filename)
% Create ArbuzGUI-compatible image structure

img_struct = struct();
img_struct.FileName = filename;
img_struct.Name = name;
img_struct.isStore = 1;
img_struct.isLoaded = 1;
img_struct.Visible = 0;
img_struct.Selected = 0;
img_struct.ImageType = image_type;

% Ensure data is float64 and properly sized
data = double(data);
if ndims(data) == 3
    img_struct.data = data(:);  % Flatten to 1D array
    img_struct.box = size(data);
else
    error('Image data must be 3D');
end

% Create transformation matrices
identity = eye(4, 4);
img_struct.Anative = identity;
img_struct.A = identity;
img_struct.Aprime = identity;

% Add metadata
if exist('info', 'var') && ~isempty(info)
    img_struct.data_info = info;
else
    img_struct.data_info = struct();
end

% Initialize slaves (for ROI data)
img_struct.slaves = {};

end

function create_kidney_roi(project_file, output_dir)
% Create kidney ROI using the Python script

fprintf('Creating kidney ROI...\n');

% Copy project file to test_inputs for Python script
test_inputs_dir = fullfile(output_dir, 'test_inputs');
if ~exist(test_inputs_dir, 'dir')
    mkdir(test_inputs_dir);
end

project_copy = fullfile(test_inputs_dir, 'project.mat');
copyfile(project_file, project_copy);

% Run Python ROI script
current_dir = pwd;

try
    cd(output_dir);
    
    % Copy required Python files
    copyfile(fullfile(current_dir, 'corrected_Draw_ROI.py'), 'Draw_ROI.py');
    copyfile(fullfile(current_dir, 'process', 'unet3d_model.py'), '.');
    copyfile(fullfile(current_dir, 'process', 'unet3d_kidney.pth'), '.');
    
    % Run Python script with proper executable
    python_cmd = 'C:/Users/ftmen/Documents/v3/.venv/Scripts/python.exe Draw_ROI.py';
    [status, result] = system(python_cmd);
    
    if status == 0
        fprintf('Python script executed successfully\n');
    else
        fprintf('Python script error: %s\n', result);
    end
    
    % Copy results back
    test_outputs_dir = 'test_outputs';
    if exist(test_outputs_dir, 'dir')
        roi_project = fullfile(test_outputs_dir, 'project_with_roi.mat');
        if exist(roi_project, 'file')
            copyfile(roi_project, fullfile(current_dir, output_dir, 'project_with_roi.mat'));
            fprintf('ROI creation successful\n');
        else
            warning('ROI project file not created');
        end
    else
        warning('Python script did not create output directory');
    end
    
catch ME
    warning('Error running Python ROI script: %s', ME.message);
end

cd(current_dir);

end

function extract_roi_statistics(project_file, output_dir)
% Extract ROI statistics and save to Excel

fprintf('Extracting ROI statistics...\n');

% Load project with ROI
roi_project_file = fullfile(output_dir, 'project_with_roi.mat');
if ~exist(roi_project_file, 'file')
    warning('ROI project file not found, using original project');
    roi_project_file = project_file;
end

try
    project = load(roi_project_file);
    
    % Find BE_AMP image and its ROI
    be_amp_idx = [];
    roi_mask = [];
    
    for i = 1:length(project.images)
        if strcmp(project.images{i}.Name, '>BE_AMP')
            be_amp_idx = i;
            
            % Check for ROI in slaves
            if ~isempty(project.images{i}.slaves)
                for j = 1:length(project.images{i}.slaves)
                    slave = project.images{i}.slaves{j};
                    if isfield(slave, 'ImageType') && strcmp(slave.ImageType, '3DMASK')
                        roi_mask = reshape(slave.data, slave.box);
                        break;
                    end
                end
            end
            break;
        end
    end
    
    if isempty(be_amp_idx)
        error('BE_AMP image not found in project');
    end
    
    if isempty(roi_mask)
        warning('No ROI found, creating simple mask in center');
        img_size = project.images{be_amp_idx}.box;
        roi_mask = false(img_size);
        center = round(img_size/2);
        radius = min(img_size)/4;
        [X, Y, Z] = meshgrid(1:img_size(2), 1:img_size(1), 1:img_size(3));
        distances = sqrt((X-center(2)).^2 + (Y-center(1)).^2 + (Z-center(3)).^2);
        roi_mask = distances <= radius;
    end
    
    % Extract statistics for all images
    results = {};
    
    % Define groups
    groups = {'Pre-transfusion', 'Mid-transfusion', 'Post-transfusion'};
    image_groups = {{'BE1', 'BE2', 'BE3', 'BE4'}, ...
                    {'ME1', 'ME2', 'ME3', 'ME4'}, ...
                    {'AE1', 'AE2', 'AE3', 'AE4'}};
    
    for i = 1:length(project.images)
        img = project.images{i};
        
        % Extract image name without prefix
        img_name = img.Name;
        if startsWith(img_name, '>')
            img_name = img_name(2:end);
        end
        
        % Get image data
        img_data = reshape(img.data, img.box);
        
        % Apply ROI mask and calculate statistics
        roi_data = img_data(roi_mask);
        roi_data = roi_data(roi_data > 0); % Remove zero/background voxels
        
        if ~isempty(roi_data)
            stats = struct();
            stats.ImageName = img_name;
            stats.Mean = mean(roi_data);
            stats.Median = median(roi_data);
            stats.StdDev = std(roi_data);
            stats.NumVoxels = length(roi_data);
            
            % Determine group
            stats.Group = 'Other';
            for g = 1:length(image_groups)
                if any(strcmp(img_name, image_groups{g}))
                    stats.Group = groups{g};
                    break;
                end
            end
            
            results{end+1} = stats;
        end
    end
    
    % Save to Excel
    if ~isempty(results)
        save_statistics_to_excel(results, output_dir);
    else
        warning('No valid statistics extracted');
    end
    
catch ME
    warning('Error extracting statistics: %s', ME.message);
end

end

function save_statistics_to_excel(results, output_dir)
% Save statistics to Excel spreadsheet

excel_file = fullfile(output_dir, 'roi_statistics.xlsx');

% Convert to table
data = [];
for i = 1:length(results)
    row = [string(results{i}.ImageName), string(results{i}.Group), ...
           results{i}.Mean, results{i}.Median, results{i}.StdDev, results{i}.NumVoxels];
    data = [data; row];
end

% Create table
var_names = {'ImageName', 'Group', 'Mean', 'Median', 'StdDev', 'NumVoxels'};
T = array2table(data, 'VariableNames', var_names);

% Write to Excel
try
    writetable(T, excel_file, 'Sheet', 'ROI_Statistics');
    fprintf('Statistics saved to: %s\n', excel_file);
catch
    % Fallback to CSV if Excel writing fails
    csv_file = fullfile(output_dir, 'roi_statistics.csv');
    writetable(T, csv_file);
    fprintf('Statistics saved to: %s\n', csv_file);
end

end
