function process_raw_data(tdms_file_path)
    % process_raw_data Converts a TDMS file to a MAT file.
    %
    %   process_raw_data(tdms_file_path) converts the specified TDMS file
    %   to a MAT file, saving it in the same directory with a 'p' prefix.

    [file_path, file_name, ~] = fileparts(tdms_file_path);

    % Check if the file already has a 'p' prefix
    if startsWith(file_name, 'p')
        fprintf('File %s is already processed. Skipping.\n', file_name);
        return;
    end

    mat_file_name = ['p' file_name '.mat'];
    mat_file_path = fullfile(file_path, mat_file_name);

    if isfile(mat_file_path)
        fprintf('MAT file %s already exists. Skipping.\n', mat_file_name);
        return;
    end

    try
        tdms_data = convertTDMS(false, tdms_file_path);
        save(mat_file_path, 'tdms_data');
        fprintf('Successfully converted %s to %s\n', tdms_file_path, mat_file_path);
    catch ME
        fprintf('Error converting %s: %s\n', tdms_file_path, ME.message);
    end
end
