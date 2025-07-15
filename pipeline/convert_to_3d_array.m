function data_3d = convert_to_3d_array(file_name, data_type)
% CONVERT_TO_3D_ARRAY converts the processed .mat files into a 3D array.
%
%   data_3d = CONVERT_TO_3D_ARRAY(file_name, data_type)
%
%   file_name:     full name of the file
%   data_type:     type of data to extract (e.g., 'pO2', 'Amp')

if ~exist('data_type', 'var'), data_type = 'pO2'; end

% Load the .mat file
Image = epr_LoadMATFile(file_name, false, {data_type});

% Extract the data
data_3d = Image.(data_type);

end
