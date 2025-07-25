function outputParams=GetMATLAB(inputParams)
% Example function that returns the minimum and maximum voxel value in a volume
% and performs thresholding operation on the volume.
%
% Parameters:
%  inputParams.threshold: threshold value
%  inputParams.inputvolume: input image filename
%  inputParams.outputvolume: output image filename, result of the processing
%  outputParams.min: image minimum value
%  outputParams.max: image maximum value
%

clc
disp('MATLAB: GetMATLAB');


% find arbuzgui
h = arbuz_FindGUI();

if isfield(inputParams, 'image') && ~isempty(h)
  disp('Load an image.');

  % find master image
  res = arbuz_FindImage(h, 'master', 'Name', inputParams.image, {'data', 'Anative'});
  
  if ~isempty(res)
    % store ready mask
    if isfield(inputParams, 'mask')  && isfield(inputParams, 'maskvolume')
      img=cli_imageread(inputParams.maskvolume);
      new_image.ImageType = 'MRI';
      new_image.Name = inputParams.mask;
      new_image.data = img.pixelData > 0.5;

      arbuz_AddImage(h, new_image, res{1}.Image);
      arbuz_UpdateInterface(h);
    end
  
    img.pixelData = res{1}.data;
    img.ijkToLpsTransform = res{1}.Anative;
  else
    disp('A random data image.');
    img.pixelData = rand(100,100,100);
    img.ijkToLpsTransform = eye(4);
  end
  
  cli_imagewrite(inputParams.imagevolume, img);
end

%% Help for reading/writing parameters
%
% Reading input parameters
%
%  integer, integer-vector, float, float-vector, double, double-vector, string, string-enumeration, file:
%    value=inputParams.name;
%  string-vector:
%    value=cli_stringvectordecode(inputParams.name);
%  point-vector:
%    value=cli_pointvectordecode(inputParams.name);
%  boolean:
%    value=isfield(inputParams,'name');
%  image:
%    value=cli_imageread(inputParams.name);
%  transform:
%    value=cli_lineartransformread(inputParams.name);
%   or (for generic transforms):
%    value=cli_transformread(inputParams.name);
%  measurement:
%    value=cli_measurementread(inputParams.name);
%  geometry:
%    value=cli_geometryread(inputParams.name);
%    Important: in the CLI definition file the following attribute shall be added to the geometry element: fileExtensions=".stl"
%    See https://subversion.assembla.com/svn/slicerrt/trunk/MatlabBridge/src/Examples/MeshScale/ for a complete example.
%
%  Notes:
%    - Input and file (image, transform, measurement, geometry) parameter names are defined by the <longflag> element in the XML file
%    - Output parameter names are defined by the <name> element in the XML file
%    - For retrieving index-th unnamed parameter use inputParams.unnamed{index+1} instead of inputParams.name
%
%
% Writing output parameters
%
%  integer, integer-vector, float, float-vector, double, double-vector, string, string-enumeration, file:
%    outputParams.name=value;
%  image:
%    cli_imagewrite(inputParams.name, value);
%  transform:
%    cli_lineartransformwrite(inputParams.name, value);
%   or (for generic transforms):
%    cli_transformwrite(inputParams.name, value);
%  measurement:
%    cli_measurementwrite(inputParams.name, value);
%  geometry:
%    cli_geometrywrite(inputParams.name, value);
%    Important: in the CLI definition file the following attribute shall be added to the geometry element: fileExtensions=".stl"
%    See https://subversion.assembla.com/svn/slicerrt/trunk/MatlabBridge/src/Examples/MeshScale/ for a complete example.
%
