# """
# Quick test: Check image names in project file
# """

# import matlab.engine

# def test_image_names():
#     # Test the latest project file
#     project_file = "automated_outputs/fixed_run_20250723_123333/fixed_project.mat"
    
#     eng = matlab.engine.start_matlab()
    
#     script = f"""
#     try
#         data = load('{project_file.replace(chr(92), '/')}');
#         images = data.images;
        
#         fprintf('Project data type: %s\\n', class(images));
#         fprintf('Project has %d images\\n', length(images));
        
#         % Handle cell array format
#         if iscell(images)
#             fprintf('Images stored as cell array\\n');
#             for i = 1:min(3, length(images))
#                 img = images{{i}};
#                 fprintf('\\nImage %d:\\n', i);
#                 if isstruct(img)
#                     fields = fieldnames(img);
#                     for j = 1:length(fields)
#                         field_name = fields{{j}};
#                         fprintf('  %s: %s\\n', field_name, class(img.(field_name)));
                        
#                         % Show Name field content if it exists
#                         if strcmp(field_name, 'Name')
#                             try
#                                 value = img.(field_name);
#                                 if ischar(value)
#                                     fprintf('    Value: "%s"\\n', value);
#                                 elseif iscell(value)
#                                     fprintf('    Cell value: "%s"\\n', value{{1}});
#                                 else
#                                     fprintf('    Other type: %s\\n', class(value));
#                                 end
#                             catch
#                                 fprintf('    Could not display value\\n');
#                             end
#                         end
#                     end
#                 else
#                     fprintf('  Not a struct: %s\\n', class(img));
#                 end
#             end
#         else
#             fprintf('Images stored as struct array\\n');
#             for i = 1:min(3, length(images))
#                 fprintf('\\nImage %d fields:\\n', i);
#                 fields = fieldnames(images(i));
#                 for j = 1:length(fields)
#                     field_name = fields{{j}};
#                     fprintf('  %s\\n', field_name);
#                 end
#             end
#         end
        
#     catch ME
#         fprintf('Error: %s\\n', ME.message);
#     end
#     """
    
#     script_file = 'test_names.m'
#     with open(script_file, 'w') as f:
#         f.write(script)
    
#     eng.run('test_names', nargout=0)
#     eng.quit()
    
#     import os
#     if os.path.exists(script_file):
#         os.remove(script_file)

# if __name__ == "__main__":
#     test_image_names()
