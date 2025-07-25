function dM = RST9h(t,M,par)
% Bloch Equations for triangular scan
% global X Y D h f A WF;
gamma=1.7608e7; % rad s-1 G-1
B1=par.B1;
Vm=par.Vm;
hm=par.hm;
dH=par.dH;
T2=par.T2;
T1=par.T1;
% --------------------- %
%z=8/pi^2*(cos(x)+1/9*cos(3*x)+1/25*cos(5*x)+1/49*cos(7*x)+1/81*cos(9*x));
wy=0;
wx=gamma*B1;
x=2*pi*Vm*t;
%WF=sawtooth(2*pi*Vm*t,0.5);
WF=-8/pi^2*(cos(x)+1/9*cos(3*x)+1/25*cos(5*x)+1/49*cos(7*x)+1/81*cos(9*x));
A=gamma*(dH+0.5*hm*WF);
% ------------------%
dM = zeros(3,1);   % (x,y,z) a column vector
M0=1;
%!!!   dw=w-w0;
%          M1         M2         M3          M0
dM(1) = -M(1)/T2    +A*M(2)   +wy*M(3)    +0;
dM(2) = -A*M(1)    -M(2)/T2   -wx*M(3)    +0;
dM(3) = -wy*M(1)    +wx*M(2)   -M(3)/T1    +M0/T1;

% A=[-1/T2  -dw     By; ...
%     dw   -1/T2   Bx;
%    -Bx    -By   -1/T2];
% b=[0; 0 ;M0/T1];
% dM=A*M+b;
%     
