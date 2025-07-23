function load13ImagesIntoArbuz()
%LOAD13IMAGESINTOARBUZ Loads 13 images into ArbuzGUI and saves the project.
% Based on LoadImagesIntoArbuz5.m but extended for 13 images

% --- Config ---
INJECT_AUTOACCEPT = true;  % Set false to allow dialog
CLEAN_AUTOACCEPT = true;  % Remove flag after loading

% Data folder and output
folderPath = 'C:\Users\ftmen\Documents\EPRI_DATA\12\241202';
projectName = 'arbuz_13_images_project.mat';

% File mappings (file index -> [BE images, AE images])
dataFiles = {
    'p8475image4D_18x18_0p75gcm_file.mat',  % 1: BE_AMP, BE1
    'p8482image4D_18x18_0p75gcm_file.mat',  % 2: BE2  
    'p8488image4D_18x18_0p75gcm_file.mat',  % 3: BE3
    'p8495image4D_18x18_0p75gcm_file.mat',  % 4: BE4
    'p8507image4D_18x18_0p75gcm_file.mat',  % 5: BE5
    'p8514image4D_18x18_0p75gcm_file.mat',  % 6: AE_AMP
    'p8521image4D_18x18_0p75gcm_file.mat',  % 7: AE1
    'p8528image4D_18x18_0p75gcm_file.mat',  % 8: AE2
    'p8540image4D_18x18_0p75gcm_file.mat',  % 9: AE3
    'p8547image4D_18x18_0p75gcm_file.mat',  % 10: AE4
    'p8554image4D_18x18_0p75gcm_file.mat',  % 11: AE5
    'p8561image4D_18x18_0p75gcm_file.mat'   % 12: AE6
};

% Image specifications: {name, type, file_index}
imageSpecs = {
    {'BE_AMP',  'AMP_pEPRI', 1},
    {'BE1',     'PO2_pEPRI', 1},
    {'BE2',     'PO2_pEPRI', 2},
    {'BE3',     'PO2_pEPRI', 3},
    {'BE4',     'PO2_pEPRI', 4},
    {'BE5',     'PO2_pEPRI', 5},
    {'AE_AMP',  'AMP_pEPRI', 6},
    {'AE1',     'PO2_pEPRI', 7},
    {'AE2',     'PO2_pEPRI', 8},
    {'AE3',     'PO2_pEPRI', 9},
    {'AE4',     'PO2_pEPRI', 10},
    {'AE5',     'PO2_pEPRI', 11},
    {'AE6',     'PO2_pEPRI', 12}
};

% --- Start ---
disp('--- Starting load13ImagesIntoArbuz script ---');
disp(['Input folderPath: ', folderPath]);
disp(['Input projectName: ', projectName]);

% Step 1: Launch ArbuzGUI
hGUI = ArbuzGUI();
pause(2);
if isempty(hGUI) || ~isvalid(hGUI)
    error('Failed to retrieve valid handle from ArbuzGUI');
else
    disp('✅ ArbuzGUI handle received');
end

% Step 2: Retrieve handles
handles = guidata(hGUI);
if isempty(handles) || ~isstruct(handles)
    error('Could not retrieve GUI handles');
else
    disp('✅ GUI handles structure retrieved');
end

% Step 3: Load all images
for i = 1:length(imageSpecs)
    imageName = imageSpecs{i}{1};
    imageType = imageSpecs{i}{2};
    fileIdx = imageSpecs{i}{3};
    
    imagePath = fullfile(folderPath, dataFiles{fileIdx});
    
    fprintf('Loading image %d/13: %s (%s) from %s\n', i, imageName, imageType, dataFiles{fileIdx});
    
    % Check if file exists
    if ~exist(imagePath, 'file')
        fprintf('  ❌ File not found: %s\n', imagePath);
        continue;
    end
    
    % Inject AutoAccept if requested
    if INJECT_AUTOACCEPT
        inject_autoaccept_flag(imagePath);
    end
    
    % Create image structure
    imageStruct = struct();
    imageStruct.FileName = imagePath;
    imageStruct.Name = imageName;
    imageStruct.ImageType = imageType;
    imageStruct.isStore = 1;
    imageStruct.isLoaded = 0;
    
    try
        % Load using ArbuzGUI functions
        [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
        
        imageStruct.data = imageData;
        imageStruct.data_info = imageInfo;
        imageStruct.ImageType = actualType;
        imageStruct.box = safeget(imageInfo, 'Bbox', size(imageData));
        imageStruct.Anative = safeget(imageInfo, 'Anative', eye(4));
        imageStruct.isLoaded = 1;
        
        arbuz_AddImage(hGUI, imageStruct);
        arbuz_ShowMessage(hGUI, sprintf('Added image: %s [%s]', imageStruct.Name, imageStruct.ImageType));
        
        fprintf('  ✅ Added: %s [%s]\n', imageStruct.Name, imageStruct.ImageType);
        
        % Add slaves for first AMP image
        if strcmp(imageName, 'BE_AMP') && ~isempty(slaveImages)
            idxCell = arbuz_FindImage(hGUI, 'master', 'Name', imageStruct.Name, {'ImageIdx'});
            if ~isempty(idxCell)
                masterIdx = idxCell{1}.ImageIdx;
                for k = 1:length(slaveImages)
                    arbuz_AddImage(hGUI, slaveImages{k}, masterIdx);
                    arbuz_ShowMessage(hGUI, sprintf('Added slave: %s', slaveImages{k}.Name));
                    fprintf('    ✅ Added slave: %s\n', slaveImages{k}.Name);
                end
            end
        end
        
    catch ME
        fprintf('  ❌ Error loading %s: %s\n', imageName, ME.message);
    end
    
    % Clean AutoAccept flag (optional)
    if CLEAN_AUTOACCEPT
        remove_autoaccept_flag(imagePath);
    end
    
    pause(0.5);  % Small delay between images
end

% Step 4: Save project
[path, name, ext] = fileparts(projectName);
if isempty(ext), ext = '.mat'; end
savePath = fullfile(pwd, [name, ext]);

arbuz_SaveProject(hGUI, savePath);
arbuz_ShowMessage(hGUI, ['Project saved to: ', savePath]);
disp(['✅ Project saved: ', savePath]);

% Step 5: Verify project
disp('--- Verifying project ---');
try
    projectData = load(savePath);
    if isfield(projectData, 'images')
        images = projectData.images;
        fprintf('✅ Project contains %d images:\n', size(images, 2));
        for j = 1:size(images, 2)
            try
                img = images(1, j);
                imgName = img.Name{1,1}(1);
                imgType = img.ImageType{1,1}(1);
                fprintf('  %d: %s (%s)\n', j, imgName, imgType);
            catch
                fprintf('  %d: (error reading image info)\n', j);
            end
        end
    else
        fprintf('❌ No images field in project\n');
    end
catch ME
    fprintf('❌ Error verifying project: %s\n', ME.message);
end

disp('--- Script complete ---');
end

function inject_autoaccept_flag(matFile)
try
    tmp = load(matFile);
    if isfield(tmp, 'pO2_info')
        tmp.pO2_info.AutoAccept = true;
        save(matFile, '-struct', 'tmp');
    end
catch
    % Ignore errors in flag injection
end
end

function remove_autoaccept_flag(matFile)
try
    tmp = load(matFile);
    if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
        tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
        save(matFile, '-struct', 'tmp');
    end
catch
    % Ignore errors in flag removal
end
end

function value = safeget(s, field, default)
if isfield(s, field)
    value = s.(field);
else
    value = default;
end
end
