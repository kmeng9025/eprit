function display_3d_array(data_3d)
% DISPLAY_3D_ARRAY displays the 3D array with a color bar and a scroll bar.
%
%   DISPLAY_3D_ARRAY(data_3d)
%
%   data_3d:     a 3D array

% Create a figure
h_fig = figure;

% Create an axes for the image
h_ax = axes('Parent', h_fig, 'Position', [0.1 0.2 0.8 0.7]);

% Create a slider for scrolling through slices
h_slider = uicontrol('Parent', h_fig, 'Style', 'slider', ...
    'Position', [0.1 0.05 0.8 0.05], ...
    'Min', 1, 'Max', size(data_3d, 3), 'Value', 1, ...
    'Callback', @slider_callback);

% Display the first slice
h_img = imagesc(h_ax, data_3d(:, :, 1));
colorbar(h_ax);

% Set the callback function for the slider
    function slider_callback(src, ~)
        % Get the current slice index from the slider
        slice_idx = round(get(src, 'Value'));

        % Update the image data
        set(h_img, 'CData', data_3d(:, :, slice_idx));
    end

end
