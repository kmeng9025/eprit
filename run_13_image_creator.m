% Simple launcher for the 13-image project creation
% Run this in MATLAB after opening MATLAB manually

disp('=== 13-Image Project Creator ===');
disp('Setting up paths...');

% Add necessary paths
addpath('c:\Users\ftmen\Documents\v3');
addpath('c:\Users\ftmen\Documents\v3\Arbuz2.0');
addpath('c:\Users\ftmen\Documents\v3\epri');
addpath('c:\Users\ftmen\Documents\v3\common');

% Run the script
try
    disp('Running load13ImagesIntoArbuz...');
    load13ImagesIntoArbuz();
    disp('SUCCESS: Project created!');
catch ME
    disp(['ERROR: ' ME.message]);
    disp('Stack trace:');
    for i = 1:length(ME.stack)
        fprintf('  %s:%d in %s\n', ME.stack(i).file, ME.stack(i).line, ME.stack(i).name);
    end
end
