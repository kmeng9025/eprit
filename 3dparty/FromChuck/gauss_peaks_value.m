function yfit = gauss_peaks_value(par,xcoords)

npeaks = numel(par)/3;
yfit=xcoords*0;

for n=1:npeaks
    cent=abs(par(n,1));
    height=abs(par(n,2));
    sig=par(n,3);
    xfit=xcoords-cent;
    yfit=yfit+height*exp(-xfit.*xfit/sig/sig/2);
end
