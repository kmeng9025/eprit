"""
Python automation script based on LoadImagesIntoArbuz5.m
Uses MATLAB engine to control ArbuzGUI and create projects with 13 images
"""

import matlab.engine
import os
import glob
import time
from pathlib import Path

class ArbuzProjectCreator:
    def __init__(self):
        self.eng = None
        self.hGUI = None
        
    def start_matlab_engine(self):
        """Start MATLAB engine and add necessary paths"""
        print("Starting MATLAB engine...")
        self.eng = matlab.engine.start_matlab()
        
        # Add paths
        paths = [
            'c:\\Users\\ftmen\\Documents\\v3',
            'c:\\Users\\ftmen\\Documents\\v3\\Arbuz2.0',
            'c:\\Users\\ftmen\\Documents\\v3\\epri',
            'c:\\Users\\ftmen\\Documents\\v3\\common'
        ]
        
        for path in paths:
            self.eng.addpath(path, nargout=0)
        
        print("✅ MATLAB engine started and paths added")
        
    def launch_arbuz_gui(self):
        """Launch ArbuzGUI and get handle"""
        print("Launching ArbuzGUI...")
        self.hGUI = self.eng.ArbuzGUI()
        
        # Wait for GUI to load
        time.sleep(3)
        
        if not self.hGUI:
            raise Exception("Failed to retrieve valid handle from ArbuzGUI")
        
        print("✅ ArbuzGUI handle received")
        
        # Test if we can access guidata (optional check)
        try:
            self.eng.eval("testHandles = guidata(hGUI);", nargout=0)
            print("✅ GUI handles accessible")
        except Exception as e:
            print(f"Warning: Could not access guidata: {e}")
            print("Continuing anyway...")
        
    def inject_autoaccept_flag(self, mat_file):
        """Inject AutoAccept flag to automate pO2 processing"""
        try:
            # Use proper escaping for Windows paths
            safe_path = mat_file.replace('\\', '/')
            self.eng.eval(f"""
                tmp = load('{safe_path}');
                if isfield(tmp, 'pO2_info')
                    tmp.pO2_info.AutoAccept = true;
                    save('{safe_path}', '-struct', 'tmp');
                end
            """, nargout=0)
        except Exception as e:
            print(f"Warning: Could not inject AutoAccept flag: {e}")
    
    def remove_autoaccept_flag(self, mat_file):
        """Remove AutoAccept flag after processing"""
        try:
            safe_path = mat_file.replace('\\', '/')
            self.eng.eval(f"""
                tmp = load('{safe_path}');
                if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
                    tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
                    save('{safe_path}', '-struct', 'tmp');
                end
            """, nargout=0)
        except Exception as e:
            print(f"Warning: Could not remove AutoAccept flag: {e}")
    
    def add_image_to_arbuz(self, image_path, image_name, image_type):
        """Add a single image to ArbuzGUI"""
        print(f"Adding image: {image_name} ({image_type}) from {os.path.basename(image_path)}")
        
        # Use proper path format for MATLAB
        safe_path = image_path.replace('\\', '/')
        
        # Inject AutoAccept flag
        self.inject_autoaccept_flag(safe_path)
        
        try:
            # Create image structure in MATLAB
            self.eng.eval(f"""
                imageStruct = struct();
                imageStruct.FileName = '{safe_path}';
                imageStruct.Name = '{image_name}';
                imageStruct.ImageType = '{image_type}';
                imageStruct.isStore = 1;
                imageStruct.isLoaded = 0;
            """, nargout=0)
            
            # Load image data
            result = self.eng.eval("""
                try
                    [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
                    
                    imageStruct.data = imageData;
                    imageStruct.data_info = imageInfo;
                    imageStruct.ImageType = actualType;
                    
                    if isfield(imageInfo, 'Bbox')
                        imageStruct.box = imageInfo.Bbox;
                    else
                        imageStruct.box = size(imageData);
                    end
                    
                    if isfield(imageInfo, 'Anative')
                        imageStruct.Anative = imageInfo.Anative;
                    else
                        imageStruct.Anative = eye(4);
                    end
                    
                    imageStruct.isLoaded = 1;
                    
                    % Return info for Python
                    returnStruct = struct();
                    returnStruct.actualType = actualType;
                    returnStruct.hasSlaves = ~isempty(slaveImages);
                    returnStruct.numSlaves = length(slaveImages);
                    returnStruct.success = true;
                catch ME
                    returnStruct = struct();
                    returnStruct.success = false;
                    returnStruct.error = ME.message;
                end
            """)
            
            if not result.get('success', False):
                print(f"  ❌ Load failed: {result.get('error', 'Unknown error')}")
                return False
            
            # Add image to ArbuzGUI
            self.eng.eval(f"""
                try
                    arbuz_AddImage(hGUI, imageStruct);
                    arbuz_ShowMessage(hGUI, sprintf('Added image: %s [%s]', imageStruct.Name, imageStruct.ImageType));
                    addSuccess = true;
                catch ME
                    addSuccess = false;
                    addError = ME.message;
                end
            """, nargout=0)
            
            # Check if add was successful
            add_result = self.eng.workspace['addSuccess']
            if not add_result:
                error_msg = self.eng.workspace.get('addError', 'Unknown error')
                print(f"  ❌ Add failed: {error_msg}")
                return False
            
            print(f"  ✅ Added: {image_name} [{result['actualType']}]")
            
            # Handle slaves for first AMP image
            if image_name == 'BE_AMP' and result['hasSlaves']:
                print(f"  Adding {result['numSlaves']} slave images...")
                self.eng.eval(f"""
                    try
                        idxCell = arbuz_FindImage(hGUI, 'master', 'Name', '{image_name}', {{'ImageIdx'}});
                        if ~isempty(idxCell)
                            masterIdx = idxCell{{1}}.ImageIdx;
                            for k = 1:length(slaveImages)
                                arbuz_AddImage(hGUI, slaveImages{{k}}, masterIdx);
                                arbuz_ShowMessage(hGUI, sprintf('Added slave: %s', slaveImages{{k}}.Name));
                            end
                        end
                        slaveSuccess = true;
                    catch ME
                        slaveSuccess = false;
                    end
                """, nargout=0)
                
                slave_success = self.eng.workspace['slaveSuccess']
                if slave_success:
                    print(f"    ✅ Added {result['numSlaves']} slaves")
                else:
                    print(f"    ⚠️  Could not add slave images")
                
        except Exception as e:
            print(f"  ❌ Error adding {image_name}: {e}")
            return False
        
        # Clean AutoAccept flag
        self.remove_autoaccept_flag(safe_path)
        
        return True
    
    def create_13_image_project(self, data_folder, project_name):
        """Create project with 13 images"""
        print("=== Creating 13-Image Project ===")
        print(f"Data folder: {data_folder}")
        print(f"Project name: {project_name}")
        
        # Data files (available in the folder)
        data_files = [
            'p8475image4D_18x18_0p75gcm_file.mat',
            'p8482image4D_18x18_0p75gcm_file.mat',
            'p8488image4D_18x18_0p75gcm_file.mat',
            'p8495image4D_18x18_0p75gcm_file.mat',
            'p8507image4D_18x18_0p75gcm_file.mat',
            'p8514image4D_18x18_0p75gcm_file.mat',
            'p8521image4D_18x18_0p75gcm_file.mat',
            'p8528image4D_18x18_0p75gcm_file.mat',
            'p8540image4D_18x18_0p75gcm_file.mat',
            'p8547image4D_18x18_0p75gcm_file.mat',
            'p8554image4D_18x18_0p75gcm_file.mat',
            'p8561image4D_18x18_0p75gcm_file.mat'
        ]
        
        # Image specifications: (name, type, file_index)
        # Using your exact naming requirements:
        # Pre-transfusion: BE1, BE2, BE3, BE4
        # Mid-transfusion: ME1, ME2, ME3, ME4  
        # Post-transfusion: AE1, AE2, AE3, AE4
        # Special: BE_AMP (amplitude version of BE1)
        image_specs = [
            ('BE_AMP', 'AMP_pEPRI', 0),  # File 1 - amplitude version
            ('BE1', 'PO2_pEPRI', 0),     # File 1 - Pre-transfusion
            ('BE2', 'PO2_pEPRI', 1),     # File 2 - Pre-transfusion
            ('BE3', 'PO2_pEPRI', 2),     # File 3 - Pre-transfusion
            ('BE4', 'PO2_pEPRI', 3),     # File 4 - Pre-transfusion
            ('ME1', 'PO2_pEPRI', 4),     # File 5 - Mid-transfusion
            ('ME2', 'PO2_pEPRI', 5),     # File 6 - Mid-transfusion
            ('ME3', 'PO2_pEPRI', 6),     # File 7 - Mid-transfusion
            ('ME4', 'PO2_pEPRI', 7),     # File 8 - Mid-transfusion
            ('AE1', 'PO2_pEPRI', 8),     # File 9 - Post-transfusion
            ('AE2', 'PO2_pEPRI', 9),     # File 10 - Post-transfusion
            ('AE3', 'PO2_pEPRI', 10),    # File 11 - Post-transfusion
            ('AE4', 'PO2_pEPRI', 11)     # File 12 - Post-transfusion
        ]
        
        # Start MATLAB and ArbuzGUI
        self.start_matlab_engine()
        self.launch_arbuz_gui()
        
        # Make hGUI available in MATLAB workspace
        self.eng.workspace['hGUI'] = self.hGUI
        
        # Add all images
        success_count = 0
        for i, (name, img_type, file_idx) in enumerate(image_specs):
            image_path = os.path.join(data_folder, data_files[file_idx])
            
            if not os.path.exists(image_path):
                print(f"❌ File not found: {data_files[file_idx]}")
                continue
                
            if self.add_image_to_arbuz(image_path, name, img_type):
                success_count += 1
            
            # Small delay between images
            time.sleep(0.5)
        
        print(f"\n✅ Successfully added {success_count}/13 images")
        
        # Save project
        self.save_project(project_name)
        
        # Verify project
        self.verify_project(project_name)
        
    def save_project(self, project_name):
        """Save the ArbuzGUI project"""
        print("Saving project...")
        
        # Ensure .mat extension
        if not project_name.endswith('.mat'):
            project_name += '.mat'
        
        save_path = os.path.join(os.getcwd(), project_name).replace('\\', '/')
        
        try:
            self.eng.eval(f"""
                arbuz_SaveProject(hGUI, '{save_path}');
                arbuz_ShowMessage(hGUI, 'Project saved to: {save_path}');
            """, nargout=0)
            
            print(f"✅ Project saved: {project_name}")
            
        except Exception as e:
            print(f"❌ Error saving project: {e}")
    
    def verify_project(self, project_name):
        """Verify the created project"""
        print("\n=== Project Verification ===")
        
        if not project_name.endswith('.mat'):
            project_name += '.mat'
        
        try:
            result = self.eng.eval(f"""
                projectData = load('{project_name}');
                verifyStruct = struct();
                
                if isfield(projectData, 'images')
                    images = projectData.images;
                    verifyStruct.hasImages = true;
                    verifyStruct.numImages = size(images, 2);
                    
                    % Get image info
                    imageList = cell(size(images, 2), 2);
                    for i = 1:size(images, 2)
                        try
                            img = images(1, i);
                            imageList{{i, 1}} = img.Name{{1,1}}(1);
                            imageList{{i, 2}} = img.ImageType{{1,1}}(1);
                        catch
                            imageList{{i, 1}} = 'Error';
                            imageList{{i, 2}} = 'Error';
                        end
                    end
                    verifyStruct.imageList = imageList;
                else
                    verifyStruct.hasImages = false;
                    verifyStruct.numImages = 0;
                end
            """)
            
            if result['hasImages']:
                print(f"✅ Project contains {result['numImages']} images:")
                
                for i, (name, img_type) in enumerate(result['imageList']):
                    print(f"  {i+1}: {name} ({img_type})")
                    
                # Count types
                amp_count = sum(1 for _, img_type in result['imageList'] if img_type == 'AMP_pEPRI')
                po2_count = sum(1 for _, img_type in result['imageList'] if img_type == 'PO2_pEPRI')
                
                print(f"\n✅ Image type summary: {amp_count} AMP, {po2_count} PO2")
                
                if result['numImages'] == 13:
                    print("🎉 SUCCESS: Project contains exactly 13 images!")
                else:
                    print(f"⚠️  Expected 13 images, got {result['numImages']}")
            else:
                print("❌ No images field found in project")
                
        except Exception as e:
            print(f"❌ Error verifying project: {e}")
    
    def cleanup(self):
        """Clean up resources"""
        if self.eng:
            try:
                self.eng.quit()
                print("✅ MATLAB engine closed")
            except:
                pass

def main():
    """Main function to create the 13-image project"""
    
    # Configuration - Updated for your exact requirements
    data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'  # Use DATA folder as specified
    project_name = 'final_automation_project.mat'
    
    creator = ArbuzProjectCreator()
    
    try:
        creator.create_13_image_project(data_folder, project_name)
        
    except Exception as e:
        print(f"❌ Script failed: {e}")
        
    finally:
        creator.cleanup()

if __name__ == "__main__":
    main()
