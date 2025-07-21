#!/usr/bin/env python3
"""
EPRI Medical Scan Data Processing Automation Script

This script automates the entire workflow for processing medical scan data:
1. Processes .tdms files using MATLAB ProcessGUI
2. Creates project files from processed images
3. Generates ROI using neural network
4. Extracts statistics from ROI across all images
5. Exports results to spreadsheet

Author: Automated Script Generator
Date: July 2025
"""

import os
import sys
import glob
import shutil
import subprocess
import numpy as np
import scipy.io as sio
import pandas as pd
from pathlib import Path
import matlab.engine
import torch
from skimage.transform import resize
from scipy.ndimage import label, center_of_mass
from datetime import datetime
import logging
import argparse
from typing import List, Dict, Tuple, Optional

# Add process directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from unet3d_model import UNet3D

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('epri_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EPRIProcessor:
    """Main class for EPRI data processing automation"""
    
    def __init__(self, base_dir: str = None):
        """Initialize the processor with base directory"""
        self.base_dir = base_dir or r"c:\Users\ftmen\Documents\EPRI"
        self.data_dir = os.path.join(self.base_dir, "DATA")
        self.epri_dir = os.path.join(self.base_dir, "epri")
        self.process_dir = os.path.join(self.base_dir, "process")
        self.arbuz_dir = os.path.join(self.base_dir, "Arbuz2.0")
        self.ibgui_dir = os.path.join(self.base_dir, "ibGUI")
        
        # File paths
        self.scenario_file = os.path.join(self.epri_dir, "Scenario", "PulseRecon.scn")
        self.parameter_file = os.path.join(self.epri_dir, "Scenario", "Local", "Mouse_64pt_4D.par")
        self.unet_model_path = os.path.join(self.process_dir, "unet3d_kidney.pth")
        
        # Initialize MATLAB engine
        self.matlab_engine = None
        
        # Setup device for neural network
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load neural network model
        self.load_unet_model()
        
    def load_unet_model(self):
        """Load the UNet3D model for ROI generation"""
        try:
            self.unet_model = UNet3D().to(self.device)
            if os.path.exists(self.unet_model_path):
                self.unet_model.load_state_dict(torch.load(self.unet_model_path, map_location=self.device))
                self.unet_model.eval()
                logger.info("UNet3D model loaded successfully")
            else:
                logger.warning(f"UNet model not found at {self.unet_model_path}")
                self.unet_model = None
        except Exception as e:
            logger.error(f"Error loading UNet model: {e}")
            self.unet_model = None
    
    def start_matlab_engine(self):
        """Start MATLAB engine"""
        if self.matlab_engine is None:
            try:
                logger.info("Starting MATLAB engine...")
                self.matlab_engine = matlab.engine.start_matlab()
                # Add necessary paths
                self.matlab_engine.addpath(self.epri_dir, nargout=0)
                self.matlab_engine.addpath(self.arbuz_dir, nargout=0)
                self.matlab_engine.addpath(self.ibgui_dir, nargout=0)
                logger.info("MATLAB engine started successfully")
            except Exception as e:
                logger.error(f"Failed to start MATLAB engine: {e}")
                raise
    
    def stop_matlab_engine(self):
        """Stop MATLAB engine"""
        if self.matlab_engine:
            try:
                self.matlab_engine.quit()
                self.matlab_engine = None
                logger.info("MATLAB engine stopped")
            except Exception as e:
                logger.warning(f"Error stopping MATLAB engine: {e}")
    
    def find_image_files(self, data_subdir: str) -> List[str]:
        """Find all .tdms image files in a data subdirectory"""
        pattern = os.path.join(self.data_dir, data_subdir, "*image4D_18x18_0p75gcm_file.tdms")
        image_files = glob.glob(pattern)
        image_files.sort()
        logger.info(f"Found {len(image_files)} image files in {data_subdir}")
        return image_files
    
    def find_cavity_files(self, data_subdir: str) -> List[str]:
        """Find cavity profile files"""
        pattern = os.path.join(self.data_dir, data_subdir, "*cavity_profile*.tdms")
        cavity_files = glob.glob(pattern)
        cavity_files.sort()
        logger.info(f"Found {len(cavity_files)} cavity files in {data_subdir}")
        return cavity_files
    
    def process_tdms_to_mat(self, tdms_file: str, cavity_file: str) -> str:
        """Process a single .tdms file to .mat using MATLAB ProcessGUI"""
        try:
            # Start MATLAB engine if not started
            if self.matlab_engine is None:
                self.start_matlab_engine()
            
            # Extract file info
            tdms_path = Path(tdms_file)
            expected_mat_file = str(tdms_path.with_suffix('.mat'))
            expected_p_mat_file = str(tdms_path.with_name(f"p{tdms_path.stem}.mat"))
            
            # Check if already processed
            if os.path.exists(expected_p_mat_file):
                logger.info(f"File already processed: {expected_p_mat_file}")
                return expected_p_mat_file
            
            logger.info(f"Processing {tdms_file} with cavity {cavity_file}")
            
            # Call ProcessGUI through MATLAB
            # This is a simplified approach - in practice, you might need to 
            # implement the actual ProcessGUI workflow or call it programmatically
            result = self.matlab_engine.eval(f"""
                try
                    % Set up processing parameters
                    tdms_file = '{tdms_file.replace(os.sep, '/')}';
                    cavity_file = '{cavity_file.replace(os.sep, '/')}';
                    scenario_file = '{self.scenario_file.replace(os.sep, '/')}';
                    parameter_file = '{self.parameter_file.replace(os.sep, '/')}';
                    
                    % This would be replaced with actual ProcessGUI call
                    % For now, we assume the processing is done manually
                    % and we just check for the output file
                    fprintf('Would process: %s\\n', tdms_file);
                    result = 'success';
                catch ME
                    fprintf('Error: %s\\n', ME.message);
                    result = 'error';
                end
            """)
            
            # Wait for processing to complete and check for output
            if os.path.exists(expected_p_mat_file):
                logger.info(f"Successfully processed: {expected_p_mat_file}")
                return expected_p_mat_file
            else:
                logger.warning(f"Processing may have failed - output file not found: {expected_p_mat_file}")
                return None
                
        except Exception as e:
            logger.error(f"Error processing {tdms_file}: {e}")
            return None
    
    def organize_images_by_group(self, image_files: List[str]) -> Dict[str, List[str]]:
        """Organize images into pre, mid, post transfusion groups"""
        # Sort by file number
        image_files.sort(key=lambda x: int(os.path.basename(x).split('image')[0]))
        
        groups = {
            'pre': image_files[:4],
            'mid': image_files[4:8] if len(image_files) >= 8 else [],
            'post': image_files[8:12] if len(image_files) >= 12 else []
        }
        
        logger.info(f"Organized images - Pre: {len(groups['pre'])}, Mid: {len(groups['mid'])}, Post: {len(groups['post'])}")
        return groups
    
    def create_project_file(self, processed_files: Dict[str, List[str]], output_path: str) -> str:
        """Create an Arbuz project file from processed .mat files"""
        try:
            # Image naming convention
            name_mapping = {
                'pre': ['BE1', 'BE2', 'BE3', 'BE4'],
                'mid': ['ME1', 'ME2', 'ME3', 'ME4'],
                'post': ['AE1', 'AE2', 'AE3', 'AE4']
            }
            
            images_list = []
            
            # Process each group
            for group, files in processed_files.items():
                if not files:
                    continue
                    
                for i, mat_file in enumerate(files):
                    if i >= 4:  # Only process first 4 files per group
                        break
                        
                    # Load the processed .mat file
                    try:
                        mat_data = sio.loadmat(mat_file, struct_as_record=False, squeeze_me=True)
                        
                        # Extract the image data and reconstruct 3D volume
                        if 'fit_data' in mat_data:
                            fit_data = mat_data['fit_data']
                            
                            # Reconstruct 3D volume from fit_data
                            if hasattr(fit_data, 'P') and hasattr(fit_data, 'Size'):
                                p_data = fit_data.P[0, :]  # First parameter (amplitude)
                                size_info = fit_data.Size
                                
                                # Create 3D volume
                                volume_shape = (int(size_info[0]), int(size_info[1]), int(size_info[2]))
                                volume_data = np.zeros(volume_shape)
                                
                                if hasattr(fit_data, 'Idx'):
                                    idx = fit_data.Idx.astype(int) - 1  # Convert to 0-based indexing
                                    volume_data.flat[idx] = p_data
                                
                                # Create image entry
                                image_name = name_mapping[group][i]
                                image_entry = self.create_image_struct(volume_data, image_name)
                                images_list.append(image_entry)
                                
                                # Create BE_AMP (amplitude version of BE1)
                                if group == 'pre' and i == 0:
                                    be_amp_entry = self.create_image_struct(volume_data, 'BE_AMP')
                                    images_list.append(be_amp_entry)
                                
                                logger.info(f"Added image {image_name} from {mat_file}")
                    
                    except Exception as e:
                        logger.error(f"Error processing {mat_file}: {e}")
                        continue
            
            # Create project structure
            project_data = {
                'images': np.array(images_list, dtype=object) if images_list else np.array([]),
                'project_info': {
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'script_version': '1.0',
                    'total_images': len(images_list)
                }
            }
            
            # Save project file
            sio.savemat(output_path, project_data, do_compression=True)
            logger.info(f"Created project file: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating project file: {e}")
            return None
    
    def create_image_struct(self, data: np.ndarray, name: str) -> object:
        """Create an image structure compatible with Arbuz"""
        class ImageStruct:
            def __init__(self, data, name):
                self.data = data.astype(np.float64)
                self.Name = name
                self.ImageType = '3DIMAGE'
                self.A = np.eye(4, dtype=np.float64)
                self.Anative = np.eye(4, dtype=np.float64)
                self.Aprime = np.eye(4, dtype=np.float64)
                self.box = np.array(data.shape, dtype=np.float64)
                self.isStore = 1
                self.isLoaded = 0
                self.Selected = 0
                self.Visible = 0
                self.pars = np.array([])
                self.FileName = np.array('', dtype='U')
                self.slaves = np.array([])
                
        return ImageStruct(data, name)
    
    def generate_roi_with_unet(self, project_file: str) -> str:
        """Generate ROI using UNet3D model on BE_AMP image"""
        try:
            if self.unet_model is None:
                logger.error("UNet model not available")
                return None
            
            # Load project file
            mat_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in mat_data:
                logger.error("No images found in project file")
                return None
            
            images_struct = mat_data['images']
            
            # Find BE_AMP image
            be_amp_data = None
            image_entry = None
            
            for entry in images_struct:
                if hasattr(entry, 'Name') and 'BE_AMP' in str(entry.Name):
                    be_amp_data = entry.data
                    image_entry = entry
                    break
            
            if be_amp_data is None:
                logger.error("BE_AMP image not found")
                return None
            
            if be_amp_data.ndim != 3:
                logger.error(f"Invalid BE_AMP data dimensions: {be_amp_data.shape}")
                return None
            
            # Normalize and resize input
            img_resized = resize(be_amp_data, (64, 64, 64), preserve_range=True)
            img_norm = (img_resized - img_resized.min()) / (np.ptp(img_resized) + 1e-8)
            input_tensor = torch.tensor(img_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
            
            # Run prediction
            with torch.no_grad():
                pred = self.unet_model(input_tensor).squeeze().cpu().numpy()
                mask = (pred > 0.5)
            
            if np.sum(mask) == 0:
                logger.warning("Empty mask predicted")
                return None
            
            # Resize mask back to original size
            mask_resized = resize(mask.astype(float), be_amp_data.shape, preserve_range=True) > 0.5
            
            # Split into left and right kidney components
            labeled, num = label(mask_resized)
            if num < 2:
                logger.warning(f"Only {num} component(s) found - using single ROI")
                roi_structs = [self.make_roi_struct(mask_resized, "Kidney")]
            else:
                # Find two largest components
                sizes = [(labeled == i).sum() for i in range(1, num + 1)]
                largest = np.argsort(sizes)[-2:][::-1]
                comp1 = (labeled == (largest[0] + 1))
                comp2 = (labeled == (largest[1] + 1))
                
                # Determine left/right based on center of mass
                com1 = center_of_mass(comp1)
                com2 = center_of_mass(comp2)
                
                if com1[0] > com2[0]:
                    right_mask, left_mask = comp1, comp2
                else:
                    right_mask, left_mask = comp2, comp1
                
                roi_structs = [
                    self.make_roi_struct(right_mask, "Kidney"),
                    self.make_roi_struct(left_mask, "Kidney2")
                ]
            
            # Attach ROI to BE_AMP image
            roi_array = np.array(roi_structs, dtype=object)
            setattr(image_entry, 'slaves', roi_array)
            
            # Transfer ROI to all other images
            self.transfer_roi_to_all_images(images_struct, roi_structs)
            
            # Save updated project file
            output_path = project_file.replace('.mat', '_with_roi.mat')
            sio.savemat(output_path, mat_data, do_compression=True)
            logger.info(f"Project file with ROI saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating ROI: {e}")
            return None
    
    def make_roi_struct(self, mask: np.ndarray, name: str) -> object:
        """Create ROI structure compatible with Arbuz"""
        class ROIStruct:
            def __init__(self, mask, name):
                self.data = mask.astype(bool)
                self.ImageType = '3DMASK'
                self.Name = name
                self.A = np.eye(4, dtype=np.float64)
                self.Anative = np.eye(4, dtype=np.float64)
                self.Aprime = np.eye(4, dtype=np.float64)
                self.isStore = 1
                self.isLoaded = 0
                self.Selected = 0
                self.Visible = 0
                self.box = np.array(mask.shape, dtype=np.float64)
                self.pars = np.array([])
                self.FileName = np.array('', dtype='U')
        
        return ROIStruct(mask, name)
    
    def transfer_roi_to_all_images(self, images_struct, roi_structs):
        """Transfer ROI from BE_AMP to all other images"""
        try:
            for entry in images_struct:
                if hasattr(entry, 'Name') and 'BE_AMP' not in str(entry.Name):
                    # Copy ROI structures to each image
                    roi_array = np.array([roi for roi in roi_structs], dtype=object)
                    setattr(entry, 'slaves', roi_array)
            
            logger.info("ROI transferred to all images")
            
        except Exception as e:
            logger.error(f"Error transferring ROI: {e}")
    
    def extract_roi_statistics(self, project_file: str) -> pd.DataFrame:
        """Extract statistics from ROI for each image"""
        try:
            # Load project file
            mat_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in mat_data:
                logger.error("No images found in project file")
                return None
            
            images_struct = mat_data['images']
            
            results = []
            
            for entry in images_struct:
                if not hasattr(entry, 'Name') or not hasattr(entry, 'data'):
                    continue
                
                image_name = str(entry.Name)
                image_data = entry.data
                
                # Get ROI masks
                if hasattr(entry, 'slaves') and len(entry.slaves) > 0:
                    for i, roi in enumerate(entry.slaves):
                        if hasattr(roi, 'data') and hasattr(roi, 'Name'):
                            roi_name = str(roi.Name)
                            roi_mask = roi.data.astype(bool)
                            
                            # Extract voxels within ROI
                            roi_voxels = image_data[roi_mask]
                            
                            if len(roi_voxels) > 0:
                                # Calculate statistics
                                stats = {
                                    'Image': image_name,
                                    'ROI': roi_name,
                                    'Mean': np.mean(roi_voxels),
                                    'Median': np.median(roi_voxels),
                                    'Std': np.std(roi_voxels),
                                    'N_Voxels': len(roi_voxels),
                                    'Min': np.min(roi_voxels),
                                    'Max': np.max(roi_voxels)
                                }
                                results.append(stats)
                                
                                logger.info(f"Extracted stats for {image_name} - {roi_name}: "
                                          f"Mean={stats['Mean']:.2f}, N={stats['N_Voxels']}")
            
            if results:
                df = pd.DataFrame(results)
                logger.info(f"Extracted statistics for {len(results)} ROI-image combinations")
                return df
            else:
                logger.warning("No ROI statistics extracted")
                return None
                
        except Exception as e:
            logger.error(f"Error extracting ROI statistics: {e}")
            return None
    
    def save_results_to_spreadsheet(self, df: pd.DataFrame, output_path: str):
        """Save results to Excel spreadsheet"""
        try:
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # Main results
                df.to_excel(writer, sheet_name='ROI_Statistics', index=False)
                
                # Summary by image
                summary = df.groupby(['Image', 'ROI']).agg({
                    'Mean': 'first',
                    'Median': 'first',
                    'Std': 'first',
                    'N_Voxels': 'first'
                }).reset_index()
                summary.to_excel(writer, sheet_name='Summary', index=False)
                
                # Pivot table for easy comparison
                pivot = df.pivot_table(
                    index='Image',
                    columns='ROI',
                    values=['Mean', 'Median', 'Std', 'N_Voxels'],
                    aggfunc='first'
                )
                pivot.to_excel(writer, sheet_name='Pivot_View')
            
            logger.info(f"Results saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Error saving results: {e}")
    
    def process_full_workflow(self, data_subdir: str, output_dir: str = None):
        """Execute the complete processing workflow"""
        try:
            if output_dir is None:
                output_dir = os.path.join(self.base_dir, "output", 
                                        f"processed_{data_subdir}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Starting full workflow for {data_subdir}")
            
            # Step 1: Find image files
            image_files = self.find_image_files(data_subdir)
            if not image_files:
                logger.error(f"No image files found in {data_subdir}")
                return None
            
            # Step 2: Find cavity files
            cavity_files = self.find_cavity_files(data_subdir)
            
            # Step 3: Process .tdms files to .mat (if needed)
            processed_files = []
            for i, tdms_file in enumerate(image_files):
                # Find corresponding cavity file
                cavity_file = cavity_files[min(i // 4, len(cavity_files) - 1)] if cavity_files else None
                
                # Check if .mat file already exists
                mat_file = tdms_file.replace('.tdms', '.mat')
                p_mat_file = os.path.join(os.path.dirname(mat_file), f"p{os.path.basename(mat_file)}")
                
                if os.path.exists(p_mat_file):
                    processed_files.append(p_mat_file)
                    logger.info(f"Using existing processed file: {p_mat_file}")
                else:
                    logger.warning(f"Processed file not found: {p_mat_file}")
                    logger.info("Please run ProcessGUI.m manually to process the .tdms files first")
                    # In a complete implementation, you would call ProcessGUI here
                    processed_files.append(None)
            
            # Filter out None values
            processed_files = [f for f in processed_files if f is not None]
            
            if not processed_files:
                logger.error("No processed .mat files available")
                return None
            
            # Step 4: Organize into groups
            groups = self.organize_images_by_group(processed_files)
            
            # Step 5: Create project file
            project_file = os.path.join(output_dir, f"project_{data_subdir}.mat")
            project_file = self.create_project_file(groups, project_file)
            
            if not project_file:
                logger.error("Failed to create project file")
                return None
            
            # Step 6: Generate ROI
            project_with_roi = self.generate_roi_with_unet(project_file)
            
            if not project_with_roi:
                logger.error("Failed to generate ROI")
                return None
            
            # Step 7: Extract statistics
            stats_df = self.extract_roi_statistics(project_with_roi)
            
            if stats_df is None:
                logger.error("Failed to extract statistics")
                return None
            
            # Step 8: Save results
            excel_file = os.path.join(output_dir, f"roi_statistics_{data_subdir}.xlsx")
            self.save_results_to_spreadsheet(stats_df, excel_file)
            
            # Save CSV for easy access
            csv_file = os.path.join(output_dir, f"roi_statistics_{data_subdir}.csv")
            stats_df.to_csv(csv_file, index=False)
            
            logger.info(f"Workflow completed successfully! Output saved to: {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"Error in full workflow: {e}")
            return None
        
        finally:
            # Clean up MATLAB engine
            self.stop_matlab_engine()

def main():
    """Main function to run the automation script"""
    parser = argparse.ArgumentParser(description='EPRI Medical Scan Data Processing Automation')
    parser.add_argument('--data-subdir', type=str, default='241202',
                       help='Data subdirectory to process (default: 241202)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: auto-generated)')
    parser.add_argument('--base-dir', type=str, 
                       default=r"c:\Users\ftmen\Documents\EPRI",
                       help='Base EPRI directory')
    
    args = parser.parse_args()
    
    try:
        # Create processor
        processor = EPRIProcessor(args.base_dir)
        
        # Run full workflow
        result = processor.process_full_workflow(args.data_subdir, args.output_dir)
        
        if result:
            print(f"\n✅ Processing completed successfully!")
            print(f"📁 Output directory: {result}")
            print(f"📊 Check the Excel and CSV files for ROI statistics")
        else:
            print("\n❌ Processing failed. Check the log file for details.")
            return 1
        
    except KeyboardInterrupt:
        print("\n⏸️ Processing interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
