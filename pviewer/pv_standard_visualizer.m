function res = pv_standard_visualizer(the_item)
if ~isempty(the_item)
  res = '';
  flds = fieldnames(the_item);
  for ii=1:length(flds)
    fld = flds{ii};
    if contains(fld, 'Tag'), continue; end
    val = the_item.(fld);
    str = sprintf('%.3f, ',val);
    res = [res, newline, fld, ':', str];
  end
else
  res = '';
end