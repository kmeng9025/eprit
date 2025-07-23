function loadImagesIntoArbuz(folderPath, projectName)
%LOADIMAGESINTOARBUZ Loads AMP and BE images into ArbuzGUI and saves the project.
% Automates ibGUI behavior by injecting AutoAccept flag into pO2_info.

% --- Config ---
INJECT_AUTOACCEPT = true;  % Set false to allow dialog
CLEAN_AUTOACCEPT = true;  % Remove flag after loading

% --- Start ---
disp('--- Starting loadImagesIntoArbuz script ---');
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

% Step 3: Find p*image*.mat
pattern = 'p*image4D_18x18_0p75gcm_file.mat';
imageFiles = dir(fullfile(folderPath, pattern));
if isempty(imageFiles)
    error('No matching image files found');
end
imagePath = fullfile(folderPath, imageFiles(1).name);
disp(['✅ Found image: ', imagePath]);

% Inject AutoAccept if requested
if INJECT_AUTOACCEPT
    inject_autoaccept_flag(imagePath);
end

% Step 4: Load AMP image
ampImage = struct();
ampImage.FileName = imagePath;
ampImage.Name = 'BE_AMP';
ampImage.ImageType = 'AMP_pEPRI';
ampImage.isStore = 1;
ampImage.isLoaded = 0;

[ampData, ampInfo, ampType, slaveImages] = arbuz_LoadImage(ampImage.FileName, ampImage.ImageType);

ampImage.data = ampData;
ampImage.data_info = ampInfo;
ampImage.ImageType = ampType;
ampImage.box = safeget(ampInfo, 'Bbox', size(ampData));
ampImage.Anative = safeget(ampInfo, 'Anative', eye(4));
ampImage.isLoaded = 1;

arbuz_AddImage(hGUI, ampImage);
arbuz_ShowMessage(hGUI, sprintf('Added image: %s [%s]', ampImage.Name, ampImage.ImageType));

% Step 5: Load PO2 (BE) image
beImage = struct();
beImage.FileName = imagePath;
beImage.Name = 'BE';
beImage.ImageType = 'PO2_pEPRI';
beImage.isStore = 1;
beImage.isLoaded = 0;

[beData, beInfo, beType, ~] = arbuz_LoadImage(beImage.FileName, beImage.ImageType);

beImage.data = beData;
beImage.data_info = beInfo;
beImage.ImageType = beType;
beImage.box = safeget(beInfo, 'Bbox', size(beData));
beImage.Anative = safeget(beInfo, 'Anative', eye(4));
beImage.isLoaded = 1;

arbuz_AddImage(hGUI, beImage);
arbuz_ShowMessage(hGUI, sprintf('Added image: %s [%s]', beImage.Name, beImage.ImageType));

% Step 6: Add slaves (if any)
if ~isempty(slaveImages)
    idxCell = arbuz_FindImage(hGUI, 'master', 'Name', ampImage.Name, {'ImageIdx'});
    if ~isempty(idxCell)
        masterIdx = idxCell{1}.ImageIdx;
        for k = 1:length(slaveImages)
            arbuz_AddImage(hGUI, slaveImages{k}, masterIdx);
            arbuz_ShowMessage(hGUI, sprintf('Added slave: %s', slaveImages{k}.Name));
        end
    end
end

% Step 7: Clean AutoAccept flag (optional)
if CLEAN_AUTOACCEPT
    remove_autoaccept_flag(imagePath);
end

% Step 8: Save project
[path, name, ext] = fileparts(projectName);
if isempty(ext), ext = '.mat'; end
savePath = fullfile(path, [name, ext]);

arbuz_SaveProject(hGUI, savePath);
arbuz_ShowMessage(hGUI, ['Project saved to: ', savePath]);
disp(['✅ Project saved: ', savePath]);
disp('--- Script complete ---');
end

function inject_autoaccept_flag(matFile)
tmp = load(matFile);
if isfield(tmp, 'pO2_info')
    tmp.pO2_info.AutoAccept = true;
    save(matFile, '-struct', 'tmp');
end
end

function remove_autoaccept_flag(matFile)
tmp = load(matFile);
if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
    tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
    save(matFile, '-struct', 'tmp');
end
end
