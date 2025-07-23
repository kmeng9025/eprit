function test_arbuzgui()
%TEST_ARBUZGUI Simple test to see if ArbuzGUI works

disp('Testing ArbuzGUI launch...');

try
    % Add paths
    addpath('c:\Users\ftmen\Documents\v3');
    addpath('c:\Users\ftmen\Documents\v3\Arbuz2.0');
    
    % Try to launch
    disp('Attempting to launch ArbuzGUI...');
    hGUI = ArbuzGUI();
    
    if isempty(hGUI)
        disp('ERROR: ArbuzGUI returned empty handle');
    else
        disp(['SUCCESS: ArbuzGUI handle: ' class(hGUI)]);
        
        % Try to get handles
        try
            handles = guidata(hGUI);
            disp(['SUCCESS: Got handles structure with ' num2str(length(fieldnames(handles))) ' fields']);
        catch ME
            disp(['ERROR getting handles: ' ME.message]);
        end
        
        % Close GUI
        try
            close(hGUI);
            disp('SUCCESS: Closed GUI');
        catch
            disp('WARNING: Could not close GUI');
        end
    end
    
catch ME
    disp(['ERROR: ' ME.message]);
    disp('Stack trace:');
    for i = 1:length(ME.stack)
        disp(['  ' ME.stack(i).file ':' num2str(ME.stack(i).line) ' - ' ME.stack(i).name]);
    end
end

disp('Test complete.');
end
