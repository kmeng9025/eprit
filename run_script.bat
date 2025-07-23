cd /d "c:\Users\ftmen\Documents\v3"
matlab -nosplash -nodesktop -r "addpath('c:\Users\ftmen\Documents\v3'); addpath('c:\Users\ftmen\Documents\v3\Arbuz2.0'); try; create_13_image_project; catch ME; fprintf('Error: %s\n', ME.message); disp(ME.stack); end; exit" -wait
pause
