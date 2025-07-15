function [output_array, metadata] = convert_to_3d_array(mat_file_path)
    % convert_to_3d_array Converts data from a .mat file to a 3D array.
    %
    %   [output_array, metadata] = convert_to_3d_array(mat_file_path)
    %   loads the specified .mat file, extracts the relevant data, and
    %   converts it into a 3D array. It also returns metadata.

    try
        data = load(mat_file_path);

        if isfield(data, 'tdms_data')
            tdms_data = data.tdms_data;

            % Assuming the relevant data is in the 'MeasuredData' field
            if isfield(tdms_data.Data, 'MeasuredData')
                measured_data = tdms_data.Data.MeasuredData;

                % Find the first channel with data
                data_found = false;
                for i = 1:length(measured_data)
                    if isfield(measured_data(i), 'Data') && ~isempty(measured_data(i).Data)
                        %reshape the data to a 3D array
                        %The dimensions are assumed to be 64x64x64 based on the project description
                        output_array = reshape(measured_data(i).Data, [64, 64, 64]);
                        metadata = measured_data(i).Property;
                        data_found = true;
                        fprintf('Successfully converted %s to a 3D array.\n', mat_file_path);
                        return;
                    end
                end

                if ~data_found
                    error('No data found in the MAT file.');
                end

            else
                error('No "MeasuredData" field found in the MAT file.');
            end
        else
            error('No "tdms_data" field found in the MAT file.');
        end
    catch ME
        fprintf('Error converting %s to 3D array: %s\n', mat_file_path, ME.message);
        output_array = [];
        metadata = [];
    end
end
