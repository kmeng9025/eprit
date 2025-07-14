function db = pv_processing_loader(folder, db)

if nargin == 2
  save(fullfile(folder, 'db.mat'), 'db')
else
  db = [];
  fname = fullfile(folder, 'db.mat');
  if exist(fname, 'file')
    s1 = load(fullfile(folder, 'db.mat'));
    if isfield(s1, 'db')
      db = s1.db;
    end
  else
  end
end
