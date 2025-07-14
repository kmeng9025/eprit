function standard_report_generator(the_list, options)

mask_stat = safeget(options, 'target', 'Kidney_EPR');

report_type = safeget(options, 'report', 1);
pars.clim_max = safeget(options, 'clim_max', 80);

experiment = the_list{options.experiment};

% loader
hFig = figure('visible','off');

arbuz_OpenProject(hFig, experiment.registration);
res   = arbuz_FindImage(hFig, 'master', 'ImageType', 'PO2_pEPRI', {'SlaveList', 'FileName'});
tumor_res = arbuz_FindImage(hFig, res{1}.SlaveList, 'InName', mask_stat, {'Data'});
tumor = tumor_res{1}.data;
tumor_res = arbuz_FindImage(hFig, res{1}.SlaveList, 'InName', 'Outline', {'Data'});
outline = tumor_res{1}.data;
delete(hFig);

[fpath, reg_name] = fileparts(experiment.registration);

% files = get_pfiles(fpath);
files = get_pfiles(fileparts(res{1}.FileName));

switch safeget(options, 'report', 1)
  case 1
    % reporter
    import mlreportgen.report.*
    import mlreportgen.dom.*

    rpt = Report(fullfile(userpath, [reg_name, '.pdf']),'pdf');
    tp = TitlePage;
    tp.Title = 'Report';
    tp.Subtitle = reg_name;
    tp.Author = '';
    append(rpt,tp);
    br = PageBreak();
    append(rpt,br);

    for ii=1:length(files)
      res = epr_LoadMATFile(files{ii}.filename, false, {'CC', 'pO2'});
      [~, image_name] = fileparts(files{ii}.filename);

      data.Data = res.pO2;
      data.Amp  = res.Amp;
      data.DataMask = res.Mask & outline;
      data.TumorMask = tumor;
      data.fig = 100+ii;
      para = Paragraph(['Image: ', image_name]);
      append(rpt,para)

      ibFIG(data, pars)
      fg = Figure();
      peaks40 = Image(getSnapshotImage(fg,rpt));
      peaks40.Width = '4.6in';
      peaks40.Height = [];
      delete(gcf);
      append(rpt,peaks40);
      para = Paragraph(' ');
      append(rpt,para)

      if mod(ii,2)==0, append(rpt,br); end
    end

    close(rpt);
    rptview(rpt);
  case 2

    nfiles = length(files);
    Data_pO2 = zeros([size(outline), nfiles]);
    Data_Amp = zeros([size(outline), nfiles]);
    Data_Mask = outline;
    for ii=1:nfiles
      res = epr_LoadMATFile(files{ii}.filename, false, {'CC', 'pO2'});
      [~, image_name] = fileparts(files{ii}.filename);

      Data_pO2(:,:,:,ii) = res.pO2;
      Data_Amp(:,:,:,ii) = res.Amp;
      Data_Mask = Data_Mask & res.Mask;
      data.Amp  = res.Amp;
      data.DataMask = res.Mask & outline;
    end
   
    Image.pO2 = Data_pO2;
    Image.Amp = Data_Amp;
    Image.Mask = Data_Mask;
    Image.Masks{1} = struct('Name', 'Tumor', 'Mask', tumor);
    Image.Masks{2} = struct('Name', 'Outline', 'Mask', outline);
    Image.Dim4Type = 'bolus';
    ibGUI(Image)
end

%-------------------------------------------------------------------------
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