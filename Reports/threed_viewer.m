function threed_viewer(app, hh)

%% Load registration
hGUI = figure(22);
reg = app.pathToRegistration; 
arbuz_OpenProject(hGUI, reg)
image_name = app.txtImageName.Value;
mask_name = app.txtMaskName.Value;

acq = arbuz_FindImage(hGUI, 'master', 'Name', image_name, {'data', 'SlaveList'});
mask = arbuz_FindImage(hGUI, acq{1}.SlaveList, 'Name', mask_name, {'data'});
mask = logical(mask{1}.data);
acqQ = acq{1}.data;
outline = acqQ >-100;
acqQ(acqQ==-100)=nan; acq_masked = acqQ;
acq_masked(~mask) = nan;
acq_masked = permute(acq_masked,[3 2 1]);
outline = permute(outline,[3 2 1]);
acqQ = permute(acqQ,[3 2 1]);

if app.ckboxUseMask.Value
  volume = acq_masked;
else
  volume = acqQ;
end

%% Variables
if app.ROImin > size(volume,1) || app.ROImin <= 0 || app.ROImax > size(volume,1) || app.ROImax <= 0
  ROI_limits = NaN;
else
  ROI_limits = app.ROImin:app.ROImax;
  if app.projections.Value
      % AXIAL
      X = meshgrid(1:size(volume,1))'; Y = meshgrid(1:size(volume,2)); Z = ones(size(volume,2),size(volume,2));
      C = squeeze(volume(:,ROI_limits(end),:));
      hold(hh, 'on')
      s = surf(Z,X,Y, C, 'Parent', hh); s.EdgeColor = 'none'; s.FaceColor = 'interp'; 
  end
end

if app.saggittalCut > size(volume,1) || app.saggittalCut <= 0 || isnan(app.saggittalCut)
  app.saggittalCut = NaN;
else
  if app.projections.Value
      % SAGGITTAL
      X = meshgrid(1:size(volume,1))'; Y = meshgrid(1:size(volume,2)); Z = ones(size(volume,2),size(volume,2));
      C = squeeze(volume(app.saggittalCut,:,:));
      hold(hh, 'on')
      s = surf(X,Z,Y, C, 'Parent', hh); s.EdgeColor = 'none'; s.FaceColor = 'interp'; 
  end
end

if app.coronalCut > size(volume,1) || app.coronalCut <= 0 || isnan(app.coronalCut)
  app.coronalCut = NaN; 
else
  if app.projections.Value
      % CORONAL
      X = meshgrid(1:size(volume,1))'; Y = meshgrid(1:size(volume,2)); Z = ones(size(volume,2),size(volume,2));
      C = squeeze(volume(:,:,app.coronalCut));
      hold(hh, 'on')
      sc = surf(Y,X,Z, C, 'Parent', hh); sc.EdgeColor = 'none'; sc.FaceColor = 'interp';
  end
end

p=1; 
while p <= length(ROI_limits)

  % Limits: [start_axial end_axial start_sagittal end_sagittal(left-right) start_coronal end_coronal (up-down)]
  outlineLimits = [NaN NaN NaN NaN NaN NaN];
  [x, y, z, outlineSub] = subvolume(outline, outlineLimits);   
  isovalue_outlineMask = 0.5;
  [fo,vo] = isosurface(x,y,z,outlineSub,isovalue_outlineMask); 
  p1 = patch('Faces', fo, 'Vertices', vo, 'Parent', hh); 
  %vo_colors = isocolors(x,y,z,acqQsub,vo-1);
  %p1.CData = vo_colors;
  p1.FaceColor = 'blue';
  p1.EdgeColor = 'none';
  p1.FaceAlpha = app.txtAlphaValue.Value;
  
  % Draw cuts
  kidneysLims_ax = [NaN ROI_limits(p) NaN NaN NaN NaN];
  kidneysLims_sg = [NaN NaN NaN app.saggittalCut NaN NaN];
  kidneysLims_cr = [NaN NaN NaN NaN NaN app.coronalCut];
  [x_ax,y_ax,z_ax, acqSub_ax] = subvolume(volume, kidneysLims_ax);
  [x_sg, y_sg, z_sg, acqSub_sg] = subvolume(volume, kidneysLims_sg);
  [x_cr, y_cr, z_cr, acqSub_cr] = subvolume(volume, kidneysLims_cr);
  isovalue_ROI = -10; 
  [fe_ax,ve_ax,ce_ax] = isocaps(x_ax,y_ax,z_ax,acqSub_ax,isovalue_ROI);
  [fe_sg,ve_sg,ce_sg] = isocaps(x_sg, y_sg, z_sg,acqSub_sg,isovalue_ROI);
  [fe_cr,ve_cr,ce_cr] = isocaps(x_cr, y_cr, z_cr,acqSub_cr,isovalue_ROI);
  hold(hh, 'on')
  % AXIAL
  p_ax = patch('Faces', fe_ax, 'Vertices', ve_ax, 'FaceVertexCData', ce_ax,'Parent', hh);
  p_ax.FaceColor = 'interp';
  p_ax.EdgeColor = 'none';
  if ~isempty(ve_ax) && app.projectionsLines.Value
      % Find vertex for projections lines
      [~, idxs_min] = min(ve_ax); [~, idxs_max] = max(ve_ax); 
      plot3([1, ve_ax(idxs_min(2),1)], [ve_ax(idxs_min(2),2), ve_ax(idxs_min(2),2)], [ve_ax(idxs_min(2),3), ve_ax(idxs_min(2),3)], ...
          'black', 'LineStyle', '--', 'Parent', hh);
      plot3([1, ve_ax(idxs_max(2),1)], [ve_ax(idxs_max(2),2), ve_ax(idxs_max(2),2)], [ve_ax(idxs_max(2),3), ve_ax(idxs_max(2),3)], ...
          'black', 'LineStyle', '--', 'Parent', hh);
  end
  
  % SAGGITTAL
  p_sg = patch('Faces', fe_sg, 'Vertices', ve_sg, 'FaceVertexCData', ce_sg,'Parent', hh);
  p_sg.FaceColor = 'interp';
  p_sg.EdgeColor = 'none';
  if ~isempty(ve_sg) && app.projectionsLines.Value
      % Find vertex for projections lines
      [~, idxs_min] = min(ve_sg); [~, idxs_max] = max(ve_sg); 
      plot3([ve_sg(idxs_min(1),1), ve_sg(idxs_min(1),1)],[1, ve_sg(idxs_min(1),2)], [ve_sg(idxs_min(1),3), ve_sg(idxs_min(1),3)], ...
          'black', 'LineStyle', '--', 'Parent', hh);
      plot3([ve_sg(idxs_max(1),1), ve_sg(idxs_max(1),1)], [1, ve_sg(idxs_max(1),2)],[ve_sg(idxs_max(1),3), ve_sg(idxs_max(1),3)], ...
          'black', 'LineStyle', '--', 'Parent', hh);
  end

  % CORONAL
  p_cr = patch('Faces', fe_cr, 'Vertices', ve_cr, 'FaceVertexCData', ce_cr, 'Parent', hh);
  p_cr.FaceColor = 'interp';
  p_cr.EdgeColor = 'none';
  if ~isempty(ve_cr) && app.projectionsLines.Value
      % Find vertex for projections lines
      [~, idxs_min] = min(ve_cr); [~, idxs_max] = max(ve_cr); 
      plot3([ve_cr(idxs_min(2),1), ve_cr(idxs_min(2),1)], [ve_cr(idxs_min(2),2), ve_cr(idxs_min(2),2)],[1, ve_cr(idxs_min(2),3)], ...
          'black', 'LineStyle', '--', 'Parent', hh);
      plot3([ve_cr(idxs_max(2),1), ve_cr(idxs_max(2),1)], [ve_cr(idxs_max(2),2), ve_cr(idxs_max(2),2)],[1, ve_cr(idxs_max(2),3)], ...
          'black', 'LineStyle', '--', 'Parent', hh);
  end

  p = p+2;

  % Intersection lines
  if ~isempty(ve_cr) && ~isempty(ve_ax) && app.projectionsLines.Value
      [commonRows_axcr, ~, ~] = intersect(ve_ax, ve_cr, 'rows');
      plot3([commonRows_axcr(1,1) commonRows_axcr(1,1)], [min(commonRows_axcr(:,2)), max(commonRows_axcr(:,2))], [commonRows_axcr(1,3), commonRows_axcr(1,3)], ...
          'black', 'LineWidth', 1.5, 'Parent', hh);
  end
  
  if ~isempty(ve_sg) && ~isempty(ve_ax) && app.projectionsLines.Value
      [commonRows_axsg, ~, ~] = intersect(ve_ax, ve_sg, 'rows');
      plot3([commonRows_axsg(1,1) commonRows_axsg(1,1)], [commonRows_axsg(1,2), commonRows_axsg(1,2)],[min(commonRows_axsg(:,3)), max(commonRows_axsg(:,3))], ...
          'black','LineWidth', 1.5 ,'Parent', hh);
  end

  if ~isempty(ve_sg) && ~isempty(ve_cr) && app.projectionsLines.Value
      [commonRows_sgcr, ~, ~] = intersect(ve_sg, ve_cr, 'rows');
      plot3([min(commonRows_sgcr(:,1)) max(commonRows_sgcr(:,1))], [commonRows_sgcr(1,2), commonRows_sgcr(1,2)], [commonRows_sgcr(1,3), commonRows_sgcr(1,3)], ...
          'black', 'LineWidth', 1.5, 'Parent', hh);
  end
end

% How to make this settings for plot inside the GUI?
view(hh, [55,55,10])  
colormap(hh, jet)
clim(hh, [app.txtColorMIN.Value, app.txtColorMAX.Value])
hh.Box = 'on';

axis(hh, 'equal');

%light(hh, 'Position', [1 0 1], 'Style', 'infinite');  % Light from the right
%light(hh, 'Position', [-1 0 1], 'Style', 'infinite'); % Light from the left
lighting(hh, 'gouraud'); % or flat

