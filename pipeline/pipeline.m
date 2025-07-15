function pipeline(raw_file_name, output_path, model_path)
% PIPELINE is the main pipeline that orchestrates the entire process.
%
%   PIPELINE(raw_file_name, output_path, model_path)
%
%   raw_file_name:   full name of the raw TDMS file
%   output_path:     the path where to store processed files
%   model_path:      path to the trained model

if ~exist('output_path', 'var'), output_path = ''; end
if ~exist('model_path', 'var'), model_path = 'dummy_model.mat'; end

% Process the raw data
process_raw_data(raw_file_name, output_path);

% Get the name of the processed file
fnames = epri_filename(raw_file_name, '', output_path);
processed_file_name = fnames.p_file;

% Highlight the ROI
highlighted_image = highlight_roi(processed_file_name, model_path);

% Display the result
display_3d_array(highlighted_image);

end
