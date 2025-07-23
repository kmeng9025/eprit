% run_automation.m
% Simple script to run the automated processing pipeline

fprintf('=== EPRI Data Processing Automation ===\n');
fprintf('This script will:\n');
fprintf('1. Process TDMS files in DATA/241202\n');
fprintf('2. Build ArbuzGUI-compatible project\n');
fprintf('3. Create kidney ROI using AI\n');
fprintf('4. Extract ROI statistics\n');
fprintf('5. Save results to Excel\n\n');

try
    automate_processing();
    fprintf('\n=== Automation completed successfully! ===\n');
catch ME
    fprintf('\n=== Automation failed with error: ===\n');
    fprintf('%s\n', ME.message);
    fprintf('Stack trace:\n');
    for i = 1:length(ME.stack)
        fprintf('  File: %s, Line: %d, Function: %s\n', ...
            ME.stack(i).file, ME.stack(i).line, ME.stack(i).name);
    end
end
