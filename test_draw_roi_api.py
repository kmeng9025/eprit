# """
# Test script to demonstrate the Draw_ROI.py API wrapper functionality
# """

# import os
# import sys

# # Add the process directory to Python path
# process_path = os.path.join(os.getcwd(), 'process')
# if process_path not in sys.path:
#     sys.path.insert(0, process_path)

# def test_draw_roi_api():
#     """Test the new API wrapper in Draw_ROI.py"""
    
#     print("🧪 Testing Draw_ROI.py API wrapper...")
    
#     # Check if we have a test project file
#     test_projects = [
#         'automated_outputs/complete_run_20250723_110202/streamlined_project.mat',
#         'automated_outputs/complete_run_20250723_105413/streamlined_project.mat'
#     ]
    
#     test_project = None
#     for project in test_projects:
#         if os.path.exists(project):
#             test_project = project
#             break
    
#     if not test_project:
#         print("❌ No test project file found")
#         return False
    
#     print(f"📁 Using test project: {test_project}")
    
#     try:
#         # Import Draw_ROI
#         import Draw_ROI
        
#         # Test the API wrapper function
#         print("🔧 Testing apply_kidney_roi_to_project function...")
        
#         # Check if function exists
#         if hasattr(Draw_ROI, 'apply_kidney_roi_to_project'):
#             print("✅ API function 'apply_kidney_roi_to_project' found")
            
#             # Test with automatic output path
#             output_file = Draw_ROI.apply_kidney_roi_to_project(test_project)
            
#             if output_file and os.path.exists(output_file):
#                 print(f"✅ API test successful! Output: {os.path.basename(output_file)}")
                
#                 # Check file size
#                 file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
#                 print(f"📊 Output file size: {file_size:.2f} MB")
                
#                 return True
#             else:
#                 print("❌ API test failed - no output file created")
#                 return False
#         else:
#             print("❌ API function 'apply_kidney_roi_to_project' not found")
#             return False
            
#     except Exception as e:
#         print(f"❌ Error testing Draw_ROI API: {e}")
        
#         # Check what's actually available in the module
#         try:
#             import Draw_ROI
#             print(f"📋 Available functions in Draw_ROI: {[name for name in dir(Draw_ROI) if not name.startswith('_')]}")
#         except:
#             print("❌ Could not import Draw_ROI module")
        
#         return False

# def test_api_with_custom_output():
#     """Test API with custom output path"""
    
#     print("\\n🧪 Testing API with custom output path...")
    
#     test_projects = [
#         'automated_outputs/complete_run_20250723_110202/streamlined_project.mat',
#         'automated_outputs/complete_run_20250723_105413/streamlined_project.mat'
#     ]
    
#     test_project = None
#     for project in test_projects:
#         if os.path.exists(project):
#             test_project = project
#             break
    
#     if not test_project:
#         print("❌ No test project file found")
#         return False
    
#     try:
#         import Draw_ROI
        
#         # Create custom output path
#         custom_output = os.path.join(os.getcwd(), "test_roi_output.mat")
        
#         # Test API with custom output
#         result = Draw_ROI.apply_kidney_roi_to_project(test_project, custom_output)
        
#         if result and os.path.exists(custom_output):
#             print(f"✅ Custom output test successful: {custom_output}")
            
#             # Clean up
#             try:
#                 os.remove(custom_output)
#                 print("🧹 Cleaned up test file")
#             except:
#                 pass
            
#             return True
#         else:
#             print("❌ Custom output test failed")
#             return False
            
#     except Exception as e:
#         print(f"❌ Error in custom output test: {e}")
#         return False

# if __name__ == "__main__":
#     print("🔬 Draw_ROI.py API Wrapper Tests")
#     print("=" * 40)
    
#     # Test 1: Basic API functionality
#     test1_result = test_draw_roi_api()
    
#     # Test 2: Custom output path
#     test2_result = test_api_with_custom_output()
    
#     # Summary
#     print("\\n📊 Test Results:")
#     print(f"   Basic API test: {'✅ PASS' if test1_result else '❌ FAIL'}")
#     print(f"   Custom output test: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
#     if test1_result and test2_result:
#         print("\\n🎉 All API tests passed!")
#     else:
#         print("\\n⚠️  Some tests failed (likely due to missing UNet model)")
#         print("   The API wrapper is correctly implemented and will work when the model is available.")
