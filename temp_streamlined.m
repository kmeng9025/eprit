
function create_streamlined_project()
    disp('Creating streamlined ArbuzGUI project...');
    
    hGUI = ArbuzGUI();
    pause(2);
    
    if isempty(hGUI) || ~isvalid(hGUI)
        error('Failed to launch ArbuzGUI');
    end
    
    files = {
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8475image4D_18x18_0p75gcm_file.mat', 'BE_AMP', 'AMP_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8475image4D_18x18_0p75gcm_file.mat', 'BE1', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8482image4D_18x18_0p75gcm_file.mat', 'BE2', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8488image4D_18x18_0p75gcm_file.mat', 'BE3', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8495image4D_18x18_0p75gcm_file.mat', 'BE4', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8507image4D_18x18_0p75gcm_file.mat', 'ME1', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8514image4D_18x18_0p75gcm_file.mat', 'ME2', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8521image4D_18x18_0p75gcm_file.mat', 'ME3', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8528image4D_18x18_0p75gcm_file.mat', 'ME4', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8540image4D_18x18_0p75gcm_file.mat', 'AE1', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8547image4D_18x18_0p75gcm_file.mat', 'AE2', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8554image4D_18x18_0p75gcm_file.mat', 'AE3', 'PO2_pEPRI';
        'c:/Users/ftmen/Documents/v3/DATA/241202/p8561image4D_18x18_0p75gcm_file.mat', 'AE4', 'PO2_pEPRI';

    };
    
    for i = 1:size(files, 1)
        try
            add_image_safely(hGUI, files{i,1}, files{i,2}, files{i,3});
            disp(['Added: ', files{i,2}, ' [', files{i,3}, ']']);
        catch ME
            disp(['Error adding ', files{i,2}, ': ', ME.message]);
        end
        pause(0.3);
    end
    
    project_path = 'automated_outputs/complete_run_20250723_114249/streamlined_project.mat';
    arbuz_SaveProject(hGUI, project_path);
    disp(['Project saved: ', project_path]);
end

function add_image_safely(hGUI, file_path, image_name, image_type)
    try
        tmp = load(file_path);
        if isfield(tmp, 'pO2_info')
            tmp.pO2_info.AutoAccept = true;
            save(file_path, '-struct', 'tmp');
        end
    catch, end
    
    imageStruct = struct();
    imageStruct.FileName = file_path;
    imageStruct.Name = image_name;
    imageStruct.ImageType = image_type;
    imageStruct.isStore = 1;
    imageStruct.isLoaded = 0;
    
    [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
    
    imageStruct.data = imageData;
    imageStruct.data_info = imageInfo;
    imageStruct.ImageType = actualType;
    imageStruct.box = safeget(imageInfo, 'Bbox', size(imageData));
    imageStruct.Anative = safeget(imageInfo, 'Anative', eye(4));
    imageStruct.isLoaded = 1;
    
    arbuz_AddImage(hGUI, imageStruct);
    
    try
        tmp = load(file_path);
        if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
            tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
            save(file_path, '-struct', 'tmp');
        end
    catch, end
end

function val = safeget(s, field, default)
    if isfield(s, field)
        val = s.(field);
    else
        val = default;
    end
end
        