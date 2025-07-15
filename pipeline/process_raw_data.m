function process_raw_data(file_name, output_path)
% PROCESS_RAW_DATA processes raw TDMS data to .mat files.
%
%   PROCESS_RAW_DATA(file_name, output_path)
%
%   file_name:     full name of the file
%   output_path:   the path where to store file, name will be preserved

if ~exist('output_path', 'var'), output_path = ''; end

% Get the file suffix from the user
file_suffix = inputdlg('Enter file suffix:', 'File Suffix', 1, {''});
if isempty(file_suffix), return; end
file_suffix = file_suffix{1};

% Get processing parameters from the user
[fields, isOk] = ProcessValueDialogDLG();
if ~isOk, return; end

% Get the processing method from the user
[process_method, isOk] = listdlg('PromptString','Select a processing method:',...
    'SelectionMode','single',...
    'ListString',{'ese_fbp'});
if ~isOk, return; end
process_method = 'ese_fbp';

% Process the data
fnames = epri_filename(file_name, file_suffix, output_path);
FinalImage = feval(process_method, file_name, file_suffix, output_path, fields);

% Save the processed data
if ~isempty(FinalImage)
    disp('Processing is finished.');
    s.file_type    = 'FitImage_v1.1';
    s.source_image = fnames.raw_file;
    s.p_image = fnames.p_file;
    s.raw_info     = FinalImage.raw_info;
    s.fit_data     = FinalImage.fit_data;
    s.rec_info     = FinalImage.rec_info;
    s.pO2_info     = fields.clb;
    save(fnames.p_file,'-struct','s');
    fprintf('File %s is saved.\n', fnames.p_file);
else
    disp('Processing failed.');
end

end
