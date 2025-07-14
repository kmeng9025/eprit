function standard_image_processor(the_list, options)

db = pv_processing_loader(options.path);

disp("standard_image_processor: options.fields = {'HF10', 'TCover', 'TVolume', 'TAmp', 'Amp', 'pO2'}");
disp('requirements: Tumor mask for any pO2 or MRI');
disp('requirements: Outline mask for any pO2 or MRI');

check = safeget(options, 'fields', 'HF10');
if ~iscell(check), check = {check}; end

if safeget(options, 'use_single', true)
  try
    HF = calculate(the_list{options.experiment}.registration, check);
    X = [];
    if length(db)>=options.experiment
      X = db{options.experiment};
    end
    X.Tag = the_list{options.experiment}.tag;
    flds = fieldnames(HF);
    for jj=1:length(flds), X.(flds{jj}) = HF.(flds{jj}); end
    db{options.experiment} = X;
  catch err
    disp(err);
  end
else
  for ii=1:length(the_list)
    try
      HF = calculate(the_list{ii}.registration, check);
      X = [];
      if length(db)>=ii
        X = db{ii};
      end
      X.Tag = the_list{ii}.tag;
      flds = fieldnames(HF);
      for jj=1:length(flds), X.(flds{jj}) = HF.(flds{jj}); end
      db{ii} = X;
    catch err
       disp(err);
    end
  end
end

pv_processing_loader(options.path, db);
disp('Processing is finished.');

%---------------------------------------------------------------------------------

function out = calculate(registration, check)

% loader
out = []; tumor = []; outline = [];
hFig = figure('visible','off');
fprintf('\nProcessing %s\n', registration);
arbuz_OpenProject(hFig, registration);

res_pO2   = arbuz_FindImage(hFig, 'master', 'ImageType', 'PO2_pEPRI', {'SlaveList', 'FileName'});

for jj=1:length(res_pO2)
  if isempty(tumor)
    tumor_res = arbuz_FindImage(hFig, res_pO2{jj}.SlaveList, 'InName', 'Tumor', {'Data'});
    if ~isempty(tumor_res), tumor = tumor_res{1}.data; end
  end
  if isempty(outline)
    outline_res = arbuz_FindImage(hFig, res_pO2{jj}.SlaveList, 'InName', 'Outline', {'Data'});
    if ~isempty(outline_res), outline = outline_res{1}.data; end
  end
  if ~isempty(tumor) && ~isempty(outline), break; end
end

% get masks from MRI
if isempty(tumor) || isempty(outline) 
  res   = arbuz_FindImage(hFig, 'master', 'ImageType', 'MRI', {});
  if isempty(res), error('MRI image was not found'); end
  res   = arbuz_FindImage(hFig, res, 'InName', 'MRI_ax', {'SlaveList'});
  all_masks = arbuz_FindImage(hFig, res{1}.SlaveList, 'ImageType', '3DMASK', {''});

  tumor_res = arbuz_FindImage(hFig, all_masks, 'Name', 'Tumor', {'Data'});
  outline_res = arbuz_FindImage(hFig, all_masks, 'InName', 'Outline', {'Data'});
  
  % TODO
  res = arbuz_util_transform_data(hFig, tumor_res{1}, tumor_res{1}.data, true, res_pO2{1}, []);
  tumor = res.data;
  res = arbuz_util_transform_data(hFig, outline_res{1}, outline_res{1}.data, true, res_pO2{1}, []);
  outline = res.data;
end

if isempty(tumor) || isempty(outline) 
  disp('Computational error: Masks were not found');
end

try
  if any(contains(check, 'TVolume'))
    res2   = arbuz_FindImage(hFig, 'master', 'ImageType', 'MRI', {'SlaveList', 'FileName', 'Anative'});
    if isempty(res2), error('MRI image was not found'); end
    tumor_mri = arbuz_FindImage(hFig, res2{1}.SlaveList, 'Name', 'Tumor', {});
    tumor_mri = arbuz_FindImage(hFig, tumor_mri, 'ImageType', '3DMASK', {'Data'});
    if isempty(tumor_mri), error('MRI tumor mask was not found'); end
    Anative = res2{1}.Anative;
    nvoxels = numel(find(tumor_mri{1}.data));
    vvoxel = prod(diag(Anative)) * 1e-3; % cm^3
    out.TVolumeML = nvoxels * vvoxel;
  end
catch
end
delete(hFig);

% files = get_pfiles(fpath);
files = get_pfiles(fileparts(res_pO2{1}.FileName));

for ii=1:length(files)
  res = epr_LoadMATFile(files{ii}.filename, false, {'CC', 'pO2'});
  tumor_pO2_stat = res.pO2(tumor & res.Mask);
  tumor_amp_stat = res.Amp(tumor & res.Mask);
  outline_amp_stat = res.Amp(~tumor & res.Mask & outline);
  outline_pO2_stat = res.pO2(~tumor & res.Mask & outline);
  for jj = 1: length(check)
    if contains(check{jj}, 'HF10')
      out.TumorHF10(ii) = numel(tumor_pO2_stat(tumor_pO2_stat > -25 & tumor_pO2_stat <= 10))/numel(tumor_pO2_stat);
    end
    if contains(check{jj}, 'TCover')
      out.TCover(ii) = numel(find(res.Mask & tumor)) / numel(find(tumor));
    end
    if contains(check{jj}, 'TAmp')
      out.TAmp(ii) = mean(tumor_amp_stat);
    end
    if contains(check{jj}, 'Amp')
      out.Amp(ii) = mean(outline_amp_stat);
    end
    if contains(check{jj}, 'TpO2')
      out.TpO2(ii) = mean(tumor_pO2_stat);
    end
    if contains(check{jj}, 'pO2')
      out.pO2(ii) = mean(outline_pO2_stat);
    end
  end
end

function files = get_pfiles(fpath)
k = dir(fullfile(fpath, '*.mat'));

files = {};
for ii=1:length(k)
  [~,~,c] = regexp(k(ii).name, "p(?<aaa>\d+)");
  if ~isempty(c) && c{1}(1) == 2
    files{end+1}.filename = fullfile(fpath, k(ii).name);
    files{end}.id = str2double(k(ii).name(c{1}(1):c{1}(2)));
  end
end