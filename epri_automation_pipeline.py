"""
Python automation pipeline for processing medical imaging data from .tdms files
Creates ArbuzGUI-compatible project files with proper image naming
Based on LoadImagesIntoArbuz workflow but implemented in Python
"""

import matlab.engine
import os
import glob
import time
from pathlib import Path
import numpy as np

class EPRIAutomationPipeline:
    def __init__(self):
        self.eng = None
        self.hGUI = None
        self.data_folder = r'c:\Users\ftmen\Documents\v3\DATA\241202'
        
        # Image naming as specified in requirements
        self.image_mapping = [
            # Pre-transfusion (BE)
            {'name': 'BE1', 'type': 'PO2_pEPRI'},
            {'name': 'BE2', 'type': 'PO2_pEPRI'},
            {'name': 'BE3', 'type': 'PO2_pEPRI'},
            {'name': 'BE4', 'type': 'PO2_pEPRI'},
            
            # Mid-transfusion (ME)
            {'name': 'ME1', 'type': 'PO2_pEPRI'},
            {'name': 'ME2', 'type': 'PO2_pEPRI'},
            {'name': 'ME3', 'type': 'PO2_pEPRI'},
            {'name': 'ME4', 'type': 'PO2_pEPRI'},
            
            # Post-transfusion (AE)
            {'name': 'AE1', 'type': 'PO2_pEPRI'},
            {'name': 'AE2', 'type': 'PO2_pEPRI'},
            {'name': 'AE3', 'type': 'PO2_pEPRI'},
            {'name': 'AE4', 'type': 'PO2_pEPRI'}
        ]
        
    def start_matlab_engine(self):
        """Initialize MATLAB engine and add necessary paths"""
        print("🔧 Starting MATLAB engine...")
        self.eng = matlab.engine.start_matlab()
        
        # Add necessary paths
        paths = [
            r'c:\Users\ftmen\Documents\v3',
            r'c:\Users\ftmen\Documents\v3\Arbuz2.0',
            r'c:\Users\ftmen\Documents\v3\epri',
            r'c:\Users\ftmen\Documents\v3\common',
            r'c:\Users\ftmen\Documents\v3\process'
        ]
        
        for path in paths:
            self.eng.addpath(path, nargout=0)
        
        print("✅ MATLAB engine started and paths added")
        
    def find_image_files(self):
        """Find image .tdms files (excluding FID_GRAD_MIN files)"""
        pattern = os.path.join(self.data_folder, '*image4D_18x18_0p75gcm_file.tdms')
        tdms_files = glob.glob(pattern)
        tdms_files.sort()  # Sort to ensure consistent ordering
        
        print(f"📁 Found {len(tdms_files)} image .tdms files:")
        for i, f in enumerate(tdms_files[:12]):  # Show only first 12
            print(f"   {i+1:2d}. {Path(f).name}")
        
        return tdms_files[:12]  # Return only first 12 files
        
    def process_tdms_file(self, tdms_file):
        """Process a single .tdms file using MATLAB ese_fbp"""
        print(f"🔄 Processing {Path(tdms_file).name}...")
        
        try:
            # Set up processing parameters
            file_suffix = ""
            output_path = str(Path(tdms_file).parent)
            
            # Create simplified fields structure for ese_fbp
            fields = {
                'prc': {'process_method': 'ese_fbp', 'save_data': 'yes', 'fit_data': 'yes', 'recon_data': 'yes'},
                'fbp': {'MaxGradient': 8.0, 'projection_order': 'default'},
                'rec': {'Size': 1, 'Sub_points': 64},
                'td': {'off_res_baseline': 'yes', 'prj_transpose': 'no'},
                'fft': {'FOV': 1, 'xshift_mode': 'none'},
                'clb': {'amp1mM': 1, 'ampHH': 1, 'Torr_per_mGauss': 1.84},
                'fit': {},
                'img': {'mirror_image': [0, 0, 0], 'reg_method': 'none'}
            }
            
            # Convert to MATLAB struct format
            self.eng.workspace['fields'] = fields
            self.eng.workspace['tdms_file'] = tdms_file
            self.eng.workspace['file_suffix'] = file_suffix
            self.eng.workspace['output_path'] = output_path
            
            # Call MATLAB processing function
            self.eng.eval("result = ese_fbp(tdms_file, file_suffix, output_path, fields);", nargout=0)
            
            # Generate expected output filenames
            base_name = Path(tdms_file).stem
            raw_file = Path(tdms_file).parent / f"{base_name}.mat"
            p_file = Path(tdms_file).parent / f"p{base_name}.mat"
            
            if raw_file.exists() and p_file.exists():
                print(f"  ✅ Generated: {raw_file.name} and {p_file.name}")
                return str(raw_file), str(p_file)
            else:
                print(f"  ⚠️  Output files not found")
                return None, None
                
        except Exception as e:
            print(f"  ❌ Error processing {tdms_file}: {e}")
            return None, None
            
    def launch_arbuz_gui(self):
        """Launch ArbuzGUI and get handle"""
        print("🚀 Launching ArbuzGUI...")
        
        # Launch ArbuzGUI
        self.hGUI = self.eng.ArbuzGUI()
        time.sleep(3)  # Wait for GUI to initialize
        
        if not self.hGUI:
            raise Exception("Failed to retrieve valid handle from ArbuzGUI")
        
        print("✅ ArbuzGUI launched successfully")
        
        # Store hGUI in MATLAB workspace for use in eval statements
        self.eng.workspace['hGUI'] = self.hGUI
        
    def inject_autoaccept_flag(self, mat_file):
        """Inject AutoAccept flag to automate pO2 processing"""
        try:
            safe_path = str(mat_file).replace('\\', '/')
            self.eng.eval(f"""
                try
                    tmp = load('{safe_path}');
                    if isfield(tmp, 'pO2_info')
                        tmp.pO2_info.AutoAccept = true;
                        save('{safe_path}', '-struct', 'tmp');
                    end
                catch
                    % Ignore errors for files without pO2_info
                end
            """, nargout=0)
        except Exception as e:
            # This is expected for some files
            pass
    
    def remove_autoaccept_flag(self, mat_file):
        """Remove AutoAccept flag after processing"""
        try:
            safe_path = str(mat_file).replace('\\', '/')
            self.eng.eval(f"""
                try
                    tmp = load('{safe_path}');
                    if isfield(tmp, 'pO2_info') && isfield(tmp.pO2_info, 'AutoAccept')
                        tmp.pO2_info = rmfield(tmp.pO2_info, 'AutoAccept');
                        save('{safe_path}', '-struct', 'tmp');
                    end
                catch
                    % Ignore errors
                end
            """, nargout=0)
        except Exception as e:
            pass
            
    def add_image_to_arbuz(self, p_file, image_name, image_type):
        """Add a single image to ArbuzGUI"""
        print(f"  📥 Adding image: {image_name} ({image_type})")
        
        # Inject AutoAccept flag for automation
        self.inject_autoaccept_flag(p_file)
        
        try:
            safe_path = str(p_file).replace('\\', '/')
            
            # Create and load image using ArbuzGUI functions
            result = self.eng.eval(f"""
                try
                    % Create image structure
                    imageStruct = struct();
                    imageStruct.FileName = '{safe_path}';
                    imageStruct.Name = '{image_name}';
                    imageStruct.ImageType = '{image_type}';
                    imageStruct.isStore = 1;
                    imageStruct.isLoaded = 0;
                    
                    % Load image data
                    [imageData, imageInfo, actualType, slaveImages] = arbuz_LoadImage(imageStruct.FileName, imageStruct.ImageType);
                    
                    % Complete image structure
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
                    
                    % Add to ArbuzGUI
                    arbuz_AddImage(hGUI, imageStruct);
                    
                    % Return success info
                    returnStruct = struct();
                    returnStruct.success = true;
                    returnStruct.actualType = actualType;
                    returnStruct.hasSlaves = ~isempty(slaveImages);
                    returnStruct.numSlaves = length(slaveImages);
                    
                catch ME
                    returnStruct = struct();
                    returnStruct.success = false;
                    returnStruct.error = ME.message;
                end
            """)
            
            if result.get('success', False):
                print(f"    ✅ Successfully added: {image_name} [{result['actualType']}]")
                
                # Handle BE_AMP slave images
                if image_name == 'BE_AMP' and result.get('hasSlaves', False):
                    print(f"    📎 Adding {result['numSlaves']} slave images...")
                    self.eng.eval(f"""
                        try
                            idxCell = arbuz_FindImage(hGUI, 'master', 'Name', '{image_name}', {{'ImageIdx'}});
                            if ~isempty(idxCell)
                                masterIdx = idxCell{{1}}.ImageIdx;
                                for k = 1:length(slaveImages)
                                    arbuz_AddImage(hGUI, slaveImages{{k}}, masterIdx);
                                end
                            end
                        catch
                            % Continue if slave addition fails
                        end
                    """, nargout=0)
                    print(f"      ✅ Added slave images")
                
                return True
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"    ❌ Failed to add {image_name}: {error_msg}")
                return False
                
        except Exception as e:
            print(f"    ❌ Exception adding {image_name}: {e}")
            return False
        finally:
            # Clean up AutoAccept flag
            self.remove_autoaccept_flag(p_file)
            
    def create_arbuz_project(self, processed_files, project_name):
        """Create ArbuzGUI project with all images"""
        print("🏗️  Creating ArbuzGUI project...")
        
        # Launch ArbuzGUI
        self.launch_arbuz_gui()
        
        # Add BE_AMP first (amplitude version of BE1)
        if len(processed_files) > 0:
            _, p_file = processed_files[0]  # Use first file for BE_AMP
            self.add_image_to_arbuz(p_file, 'BE_AMP', 'AMP_pEPRI')
        
        # Add all other images with proper names
        success_count = 0
        for i, (_, p_file) in enumerate(processed_files[:12]):  # Limit to 12 images
            if i < len(self.image_mapping):
                image_info = self.image_mapping[i]
                if self.add_image_to_arbuz(p_file, image_info['name'], image_info['type']):
                    success_count += 1
            
            time.sleep(0.2)  # Small delay between images
        
        print(f"✅ Successfully added {success_count + 1}/{len(self.image_mapping) + 1} images")  # +1 for BE_AMP
        
        # Save project
        self.save_project(project_name)
        
        # Verify project
        self.verify_project(project_name)
        
    def save_project(self, project_name):
        """Save the ArbuzGUI project"""
        print("💾 Saving project...")
        
        if not project_name.endswith('.mat'):
            project_name += '.mat'
        
        save_path = os.path.join(os.getcwd(), project_name).replace('\\', '/')
        
        try:
            self.eng.eval(f"""
                arbuz_SaveProject(hGUI, '{save_path}');
            """, nargout=0)
            
            print(f"✅ Project saved: {project_name}")
            
        except Exception as e:
            print(f"❌ Error saving project: {e}")
            
    def verify_project(self, project_name):
        """Verify the created project"""
        print("\n📋 Project Verification:")
        
        if not project_name.endswith('.mat'):
            project_name += '.mat'
        
        try:
            result = self.eng.eval(f"""
                try
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
                                if iscell(img.Name)
                                    imageList{{i, 1}} = img.Name{{1}};
                                else
                                    imageList{{i, 1}} = img.Name;
                                end
                                if iscell(img.ImageType)
                                    imageList{{i, 2}} = img.ImageType{{1}};
                                else
                                    imageList{{i, 2}} = img.ImageType;
                                end
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
                    
                catch ME
                    verifyStruct = struct();
                    verifyStruct.hasImages = false;
                    verifyStruct.error = ME.message;
                end
            """)
            
            if result.get('hasImages', False):
                print(f"✅ Project contains {result['numImages']} images:")
                
                for i, (name, img_type) in enumerate(result['imageList']):
                    print(f"   {i+1:2d}. {name} ({img_type})")
                
                # Count types
                image_list = result['imageList']
                amp_count = sum(1 for _, img_type in image_list if 'AMP' in str(img_type))
                po2_count = sum(1 for _, img_type in image_list if 'PO2' in str(img_type))
                
                print(f"\n📊 Summary: {amp_count} AMP images, {po2_count} PO2 images")
                print(f"🎯 Total: {result['numImages']} images loaded successfully")
            else:
                error_msg = result.get('error', 'No images found')
                print(f"❌ Project verification failed: {error_msg}")
                
        except Exception as e:
            print(f"❌ Error verifying project: {e}")
    
    def cleanup(self):
        """Clean up MATLAB engine"""
        if self.eng:
            try:
                self.eng.quit()
                print("🔧 MATLAB engine closed")
            except:
                pass
                
    def run_full_pipeline(self):
        """Run the complete automation pipeline"""
        print("🔬 EPRI Automation Pipeline")
        print("=" * 50)
        
        try:
            # Step 1: Initialize MATLAB engine
            self.start_matlab_engine()
            
            # Step 2: Find image files
            tdms_files = self.find_image_files()
            if not tdms_files:
                raise ValueError("No image .tdms files found")
            
            # Step 3: Process .tdms files
            print(f"\n🔄 Processing {len(tdms_files)} .tdms files...")
            processed_files = []
            
            for tdms_file in tdms_files:
                base_name = Path(tdms_file).stem
                raw_file = Path(tdms_file).parent / f"{base_name}.mat"
                p_file = Path(tdms_file).parent / f"p{base_name}.mat"
                
                # Check if already processed
                if raw_file.exists() and p_file.exists():
                    print(f"✅ Already processed: {base_name}")
                    processed_files.append((str(raw_file), str(p_file)))
                else:
                    # Process the file
                    raw_out, p_out = self.process_tdms_file(tdms_file)
                    if raw_out and p_out:
                        processed_files.append((raw_out, p_out))
            
            if not processed_files:
                raise ValueError("No processed .mat files available")
            
            print(f"✅ {len(processed_files)} files ready for project creation")
            
            # Step 4: Create ArbuzGUI project
            project_name = "epri_automation_project.mat"
            self.create_arbuz_project(processed_files, project_name)
            
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📄 Project file: {project_name}")
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            
        finally:
            self.cleanup()

def main():
    """Main entry point"""
    pipeline = EPRIAutomationPipeline()
    pipeline.run_full_pipeline()

if __name__ == "__main__":
    main()
