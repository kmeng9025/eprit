function display_3d_array(array_3d)
    % display_3d_array Displays a 3D array with a scrollbar.
    %
    %   display_3d_array(array_3d) displays the first slice of the 3D array
    %   and provides a scrollbar to navigate through the slices.

    if ndims(array_3d) ~= 3
        error('Input must be a 3D array.');
    end

    % Create a figure and axes
    fig = figure;
    ax = axes('Parent', fig);

    % Display the first slice
    imagesc(ax, array_3d(:, :, 1));
    colorbar(ax);
    title(ax, 'Slice 1');

    % Add a scrollbar
    num_slices = size(array_3d, 3);
    if num_slices > 1
        slider = uicontrol('Parent', fig, 'Style', 'slider', ...
            'Min', 1, 'Max', num_slices, 'Value', 1, 'SliderStep', [1/(num_slices-1) 1/(num_slices-1)], ...
            'Position', [150 10 300 20]);
        addlistener(slider, 'ContinuousValueChange', @(src, event) update_slice(src, ax, array_3d));
    end
end

function update_slice(slider, ax, array_3d)
    % update_slice Callback function for the slider.
    slice_num = round(get(slider, 'Value'));
    imagesc(ax, array_3d(:, :, slice_num));
    colorbar(ax);
    title(ax, ['Slice ' num2str(slice_num)]);
end
