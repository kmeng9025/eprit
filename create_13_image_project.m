function create_13_image_project()
%CREATE_13_IMAGE_PROJECT Creates a project with 13 images using ArbuzGUI properly
% Based on LoadImagesIntoArbuz5.m approach

% --- Config ---
INJECT_AUTOACCEPT = true;  % Automate pO2 processing
CLEAN_AUTOACCEPT = true;   % Clean up afterwards

% Data folder and files
dataFolder = 'C:\Users\ftmen\Documents\EPRI_DATA\12\241202';
dataFiles = {
    'p8475image4D_18x18_0p75gcm_file.mat',  % BE_AMP, BE1
    'p8482image4D_18x18_0p75gcm_file.mat',  % BE2  
    'p8488image4D_18x18_0p75gcm_file.mat',  % BE3
    'p8495image4D_18x18_0p75gcm_file.mat',  % BE4
    'p8507image4D_18x18_0p75gcm_file.mat',  % BE5
    'p8514image4D_18x18_0p75gcm_file.mat',  % AE_AMP
    'p8521image4D_18x18_0p75gcm_file.mat',  % AE1
    'p8528image4D_18x18_0p75gcm_file.mat',  % AE2
    'p8540image4D_18x18_0p75gcm_file.mat',  % AE3
    'p8547image4D_18x18_0p75gcm_file.mat',  % AE4
    'p8554image4D_18x18_0p75gcm_file.mat',  % AE5
    'p8561image4D_18x18_0p75gcm_file.mat'   % AE6
};

% Image definitions (matching reference exactly)
imageSpecs = {
    {'BE_AMP',  'AMP_pEPRI', 1},   % File 1
    {'BE1',     'PO2_pEPRI', 1},   % File 1  
    {'BE2',     'PO2_pEPRI', 2},   % File 2
    {'BE3',     'PO2_pEPRI', 3},   % File 3
    {'BE4',     'PO2_pEPRI', 4},   % File 4
    {'BE5',     'PO2_pEPRI', 5},   % File 5
    {'AE_AMP',  'AMP_pEPRI', 6},   % File 6
    {'AE1',     'PO2_pEPRI', 7},   % File 7
    {'AE2',     'PO2_pEPRI', 8},   % File 8
    {'AE3',     'PO2_pEPRI', 9},   % File 9
    {'AE4',     'PO2_pEPRI', 10},  % File 10
    {'AE5',     'PO2_pEPRI', 11},  % File 11
    {'AE6',     'PO2_pEPRI', 12}   % File 12
};

disp('=== Creating 13-Image Project Using ArbuzGUI ===');

% Step 1: Launch ArbuzGUI
disp('Launching ArbuzGUI...');
hGUI = ArbuzGUI();
pause(3);  % Allow GUI to fully load

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

% Step 3: Process each image
for i = 1:length(imageSpecs)
    imageName = imageSpecs{i}{1};
    imageType = imageSpecs{i}{2};
    fileIdx = imageSpecs{i}{3};
    
    imagePath = fullfile(dataFolder, dataFiles{fileIdx});
    
    fprintf('Processing image %d/%d: %s (%s)\n', i, length(imageSpecs), imageName, imageType);
    
    % Check if file exists
    if ~exist(imagePath, 'file')
        fprintf('  ⚠️  File not found: %s\n', imagePath);
        continue;
    end
    
    % Inject AutoAccept flag for automated processing
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
        % Load image data using ArbuzGUI's loader
        [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
        
        % Complete the image structure
        imageStruct.data = imageData;
        imageStruct.data_info = imageInfo;
        imageStruct.ImageType = actualType;
        imageStruct.box = safeget(imageInfo, 'Bbox', size(imageData));
        imageStruct.Anative = safeget(imageInfo, 'Anative', eye(4));
        imageStruct.isLoaded = 1;
        
        % Add to ArbuzGUI
        arbuz_AddImage(hGUI, imageStruct);
        arbuz_ShowMessage(hGUI, sprintf('Added image: %s [%s]', imageStruct.Name, imageStruct.ImageType));
        
        fprintf('  ✅ Added: %s [%s]\n', imageStruct.Name, imageStruct.ImageType);
        
        % Add slaves if this is the first AMP image
        if strcmp(imageName, 'BE_AMP') && ~isempty(slaveImages)
            fprintf('  Adding %d slave images...\n', length(slaveImages));
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
        continue;
    end
    
    % Clean AutoAccept flag
    if CLEAN_AUTOACCEPT
        remove_autoaccept_flag(imagePath);
    end
    
    % Small pause between images
    pause(0.5);
end

% Step 4: Save the project
projectName = 'arbuz_13_images_project.mat';
projectPath = fullfile(pwd, projectName);

disp('Saving project...');
try
    arbuz_SaveProject(hGUI, projectPath);
    arbuz_ShowMessage(hGUI, ['Project saved to: ', projectPath]);
    fprintf('✅ Project saved: %s\n', projectPath);
catch ME
    fprintf('❌ Error saving project: %s\n', ME.message);
end

% Step 5: Verify the project
disp('=== Project Verification ===');
try
    projectData = load(projectPath);
    if isfield(projectData, 'images')
        images = projectData.images;
        fprintf('✅ Project contains %d images\n', size(images, 2));
        
        % List all images
        for i = 1:size(images, 2)
            try
                img = images(1, i);
                name = img.Name{1,1}(1);
                type = img.ImageType{1,1}(1);
                fprintf('  %d: %s (%s)\n', i, name, type);
            catch
                fprintf('  %d: (error reading)\n', i);
            end
        end
    else
        fprintf('❌ No images field found in project\n');
    end
catch ME
    fprintf('❌ Error verifying project: %s\n', ME.message);
end

disp('=== Script Complete ===');
end

function inject_autoaccept_flag(matFile)
% Inject AutoAccept flag to automate pO2 processing
try
    tmp = load(matFile);
    if isfield(tmp, 'pO2_info')
        tmp.pO2_info.AutoAccept = true;
        save(matFile, '-struct', 'tmp');
    end
catch
    % Ignore errors
end
end

function remove_autoaccept_flag(matFile)
% Remove AutoAccept flag after processing
try
    tmp = load(matFile);
    if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
        tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
        save(matFile, '-struct', 'tmp');
    end
catch
    % Ignore errors
end
end

function value = safeget(s, field, default)
% Safely get field value with default
if isfield(s, field)
    value = s.(field);
else
    value = default;
end
end
