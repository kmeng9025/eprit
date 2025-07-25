function [newpoints, offsets] = line_up_fiducial(pointlist, whichone)

nplanes = size(pointlist, 1);
npoints = size(pointlist, 3);

newpoints=pointlist;
target=pointlist(1,:,whichone);
%size(newpoints)

offsets=[0 0 0];
for i = 2: nplanes
    offset = squeeze(target - pointlist(i,:,whichone));
    offset(3) = 0;
    %offset
    offsets(end+1,:) = offset;
    newpoints(i,:,:) = squeeze(newpoints(i,:,:)) + repmat(offset',1,npoints);
end