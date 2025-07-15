function main_pipeline(data_directory)
    % main_pipeline Orchestrates the full image analysis workflow.
    %
    %   main_pipeline(data_directory) runs the entire pipeline on the
    %   data in the specified directory.

    % Add the pipeline directory to the MATLAB path
    addpath(fileparts(mfilename('fullpath')));

    % 1. Process raw data
    fprintf('--- Step 1: Processing raw data ---\n');
    tdms_files = dir(fullfile(data_directory, '*.tdms'));
    for i = 1:length(tdms_files)
        tdms_file_path = fullfile(data_directory, tdms_files(i).name);
        process_raw_data(tdms_file_path);
    end

    % 2. Convert to 3D array
    fprintf('\n--- Step 2: Converting to 3D array ---\n');
    mat_files = dir(fullfile(data_directory, 'p*.mat'));
    if ~isempty(mat_files)
        mat_file_path = fullfile(data_directory, mat_files(1).name);
        [array_3d, ~] = convert_to_3d_array(mat_file_path);
    else
        fprintf('No processed MAT files found. Skipping remaining steps.\n');
        return;
    end

    % 3. Train the AI model (placeholder)
    fprintf('\n--- Step 3: Training AI model ---\n');
    % In a real scenario, you would load your training data and annotations here
    training_data = {}; % Placeholder
    annotated_rois = {}; % Placeholder
    model = train_roi_model(training_data, annotated_rois);

    % 4. Detect ROIs
    fprintf('\n--- Step 4: Detecting ROIs ---\n');
    roi_mask = detect_roi(array_3d, model);

    % 5. Display the 3D array with ROI
    fprintf('\n--- Step 5: Displaying 3D array ---\n');
    display_3d_array_with_roi(array_3d, roi_mask);

    fprintf('\n--- Pipeline finished ---\n');
end

function display_3d_array_with_roi(array_3d, roi_mask)
    % display_3d_array_with_roi Displays a 3D array with an ROI overlay.
    %
    %   display_3d_array_with_roi(array_3d, roi_mask) displays the 3D
    %   array with the ROI mask overlaid in red.

    if ndims(array_3d) ~= 3 || ndims(roi_mask) ~= 3
        error('Input must be a 3D array and a 3D mask.');
    end

    % Create a figure and axes
    fig = figure;
    ax = axes('Parent', fig);

    % Display the first slice
    update_slice_with_roi(1, ax, array_3d, roi_mask);

    % Add a scrollbar
    num_slices = size(array_3d, 3);
    if num_slices > 1
        slider = uicontrol('Parent', fig, 'Style', 'slider', ...
            'Min', 1, 'Max', num_slices, 'Value', 1, 'SliderStep', [1/(num_slices-1) 1/(num_slices-1)], ...
            'Position', [150 10 300 20]);
        addlistener(slider, 'ContinuousValueChange', @(src, ~) update_slice_with_roi(round(src.Value), ax, array_3d, roi_mask));
    end
end

function update_slice_with_roi(slice_num, ax, array_3d, roi_mask)
    % update_slice_with_roi Callback function for the slider.

    % Create an RGB image of the slice
    slice = array_3d(:, :, slice_num);
    slice_rgb = cat(3, mat2gray(slice), mat2gray(slice), mat2gray(slice));

    % Overlay the ROI mask in red
    roi_slice = roi_mask(:, :, slice_num);
    slice_rgb(repmat(roi_slice, [1, 1, 3])) = reshape([1, 0, 0], 1, 1, 3);

    imagesc(ax, slice_rgb);
    colorbar(ax);
    title(ax, ['Slice ' num2str(slice_num)]);
end
