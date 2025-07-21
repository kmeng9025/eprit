#!/usr/bin/env python3
"""
EPRI ROI Statistics Extractor

This script works with already processed .mat files (starting with 'p') to:
1. Create project files from processed images
2. Generate ROI using neural network  
3. Extract statistics from ROI across all images
4. Export results to spreadsheet

This version assumes the .tdms files have already been processed using ProcessGUI.m

Usage:
    python epri_roi_extractor.py --data-subdir 241202
"""

import os
import sys
import glob
import numpy as np
import scipy.io as sio
import pandas as pd
from pathlib import Path
import torch
from skimage.transform import resize
from scipy.ndimage import label, center_of_mass
from datetime import datetime
import logging
import argparse
from typing import List, Dict, Tuple, Optional

# Add process directory to path for imports
try:
    from unet3d_model import UNet3D
except ImportError:
    print("Warning: unet3d_model.py not found. ROI generation will be disabled.")
    UNet3D = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('epri_roi_extractor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class EPRIROIExtractor:
    """EPRI ROI Statistics Extractor"""
    
    def __init__(self, base_dir: str = None):
        """Initialize the extractor with base directory"""
        self.base_dir = base_dir or r"c:\Users\ftmen\Documents\EPRI"
        self.data_dir = os.path.join(self.base_dir, "DATA")
        self.process_dir = os.path.join(self.base_dir, "process")
        self.unet_model_path = os.path.join(self.process_dir, "unet3d_kidney.pth")
        
        # Setup device for neural network
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")
        
        # Load neural network model
        self.load_unet_model()
        
    def load_unet_model(self):
        """Load the UNet3D model for ROI generation"""
        try:
            if UNet3D is None:
                logger.warning("UNet3D class not available")
                self.unet_model = None
                return
                
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
    
    def find_processed_files(self, data_subdir: str) -> List[str]:
        """Find all processed .mat files (starting with 'p') in a data subdirectory"""
        pattern = os.path.join(self.data_dir, data_subdir, "p*image4D_18x18_0p75gcm_file.mat")
        processed_files = glob.glob(pattern)
        processed_files.sort()
        logger.info(f"Found {len(processed_files)} processed files in {data_subdir}")
        return processed_files
    
    def organize_files_by_group(self, processed_files: List[str]) -> Dict[str, List[str]]:
        """Organize processed files into pre, mid, post transfusion groups"""
        # Sort by file number
        processed_files.sort(key=lambda x: int(os.path.basename(x).split('image')[0][1:]))
        
        groups = {
            'pre': processed_files[:4],
            'mid': processed_files[4:8] if len(processed_files) >= 8 else [],
            'post': processed_files[8:12] if len(processed_files) >= 12 else []
        }
        
        logger.info(f"Organized files - Pre: {len(groups['pre'])}, Mid: {len(groups['mid'])}, Post: {len(groups['post'])}")
        return groups
    
    def create_project_file(self, processed_files: Dict[str, List[str]], output_path: str) -> str:
        """Create an Arbuz-compatible project file from processed .mat files"""
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
                        logger.info(f"Loading {mat_file}")
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
                                volume_data = np.zeros(volume_shape, dtype=np.float64)
                                
                                if hasattr(fit_data, 'Idx'):
                                    idx = fit_data.Idx.astype(int) - 1  # Convert to 0-based indexing
                                    if np.max(idx) < volume_data.size:
                                        volume_data.flat[idx] = p_data
                                    else:
                                        logger.warning(f"Index out of bounds in {mat_file}")
                                        continue
                                
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
            
            if not images_list:
                logger.error("No images could be loaded")
                return None
            
            # Create project structure
            project_data = {
                'images': np.array(images_list, dtype=object),
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
                logger.error("UNet model not available - cannot generate ROI")
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
            
            logger.info(f"Processing BE_AMP image with shape: {be_amp_data.shape}")
            
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
                if hasattr(entry, 'slaves'):
                    # Handle both array and single object cases
                    slaves = entry.slaves
                    if not isinstance(slaves, (list, tuple, np.ndarray)):
                        slaves = [slaves] if slaves is not None else []
                    elif hasattr(slaves, 'size') and slaves.size == 0:
                        slaves = []
                    
                    for i, roi in enumerate(slaves):
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
    
    def process_existing_files(self, data_subdir: str, output_dir: str = None):
        """Process existing .mat files to extract ROI statistics"""
        try:
            if output_dir is None:
                output_dir = os.path.join(self.base_dir, "output", 
                                        f"roi_analysis_{data_subdir}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            
            os.makedirs(output_dir, exist_ok=True)
            
            logger.info(f"Starting ROI analysis for {data_subdir}")
            
            # Step 1: Find processed files
            processed_files = self.find_processed_files(data_subdir)
            if not processed_files:
                logger.error(f"No processed files found in {data_subdir}")
                return None
            
            # Step 2: Organize into groups
            groups = self.organize_files_by_group(processed_files)
            
            # Step 3: Create project file
            project_file = os.path.join(output_dir, f"project_{data_subdir}.mat")
            project_file = self.create_project_file(groups, project_file)
            
            if not project_file:
                logger.error("Failed to create project file")
                return None
            
            # Step 4: Generate ROI
            project_with_roi = self.generate_roi_with_unet(project_file)
            
            if not project_with_roi:
                logger.error("Failed to generate ROI")
                return None
            
            # Step 5: Extract statistics
            stats_df = self.extract_roi_statistics(project_with_roi)
            
            if stats_df is None:
                logger.error("Failed to extract statistics")
                return None
            
            # Step 6: Save results
            excel_file = os.path.join(output_dir, f"roi_statistics_{data_subdir}.xlsx")
            self.save_results_to_spreadsheet(stats_df, excel_file)
            
            # Save CSV for easy access
            csv_file = os.path.join(output_dir, f"roi_statistics_{data_subdir}.csv")
            stats_df.to_csv(csv_file, index=False)
            
            logger.info(f"ROI analysis completed successfully! Output saved to: {output_dir}")
            
            # Print summary
            print(f"\n📊 ROI Statistics Summary:")
            print(f"Total images processed: {stats_df['Image'].nunique()}")
            print(f"Total ROIs: {stats_df['ROI'].nunique()}")
            print("\nMean values by image:")
            summary = stats_df.groupby('Image')['Mean'].mean().sort_index()
            for img, mean_val in summary.items():
                print(f"  {img}: {mean_val:.2f}")
            
            return output_dir
            
        except Exception as e:
            logger.error(f"Error in ROI analysis: {e}")
            return None

def main():
    """Main function to run the ROI extractor"""
    parser = argparse.ArgumentParser(description='EPRI ROI Statistics Extractor')
    parser.add_argument('--data-subdir', type=str, default='241202',
                       help='Data subdirectory to process (default: 241202)')
    parser.add_argument('--output-dir', type=str, default=None,
                       help='Output directory (default: auto-generated)')
    parser.add_argument('--base-dir', type=str, 
                       default=r"c:\Users\ftmen\Documents\EPRI",
                       help='Base EPRI directory')
    
    args = parser.parse_args()
    
    try:
        # Create extractor
        extractor = EPRIROIExtractor(args.base_dir)
        
        # Run ROI analysis
        result = extractor.process_existing_files(args.data_subdir, args.output_dir)
        
        if result:
            print(f"\n✅ ROI analysis completed successfully!")
            print(f"📁 Output directory: {result}")
            print(f"📊 Check the Excel and CSV files for ROI statistics")
        else:
            print("\n❌ ROI analysis failed. Check the log file for details.")
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
