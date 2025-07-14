function [pos linewidth]=LwX(spectrum,sweep)

sp =zeroLine(spectrum,0.05);

N=length(sp);
n=N-1;
x=(0:n);
xn=(x-n/2)/n;


M=2000;
n=M-1;
x=(0:n);
xm=(x-n/2)/n;


if M>N
    sp=interp1(xn,sp,xm);
    
end

[mx pos]=max(sp);
pos=round(pos/M*N);
rgn=N/10;
if pos>N/2+rgn; pos=(N/2+rgn); end;
if pos<N/2-rgn; pos=(N/2-rgn); end;
pos=round(pos);
inx=sp>mx/2;

N=length(sp);
linewidth=round(1000*sum(inx)/N*sweep);

plt2(inx,sp/max(sp)); 
title(['Linewidth=' num2str(linewidth) 'mG']); 