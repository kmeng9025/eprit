#!/usr/bin/env python3
"""
Simplified ROI Extractor for Testing
This version works without the UNet model by creating simple geometric ROIs
"""

import os
import sys
import glob
import numpy as np
import scipy.io as sio
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleEPRIExtractor:
    """Simplified EPRI extractor that works without neural network"""
    
    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or r"c:\Users\ftmen\Documents\EPRI"
        self.data_dir = os.path.join(self.base_dir, "DATA")
        
    def find_processed_files(self, data_subdir: str):
        """Find processed .mat files"""
        pattern = os.path.join(self.data_dir, data_subdir, "p*image4D_18x18_0p75gcm_file.mat")
        files = glob.glob(pattern)
        files.sort()
        logger.info(f"Found {len(files)} processed files")
        return files
    
    def create_project_file(self, processed_files, output_path: str):
        """Create project file from processed images"""
        try:
            name_mapping = ['BE1', 'BE2', 'BE3', 'BE4', 'ME1', 'ME2', 'ME3', 'ME4', 'AE1', 'AE2', 'AE3', 'AE4']
            images_list = []
            
            for i, mat_file in enumerate(processed_files[:12]):  # Max 12 files
                logger.info(f"Processing: {os.path.basename(mat_file)}")
                
                mat_data = sio.loadmat(mat_file, struct_as_record=False, squeeze_me=True)
                
                if 'fit_data' not in mat_data:
                    continue
                
                fit_data = mat_data['fit_data']
                
                if hasattr(fit_data, 'P') and hasattr(fit_data, 'Size'):
                    p_data = fit_data.P[0, :]
                    size_info = fit_data.Size
                    
                    volume_shape = (int(size_info[0]), int(size_info[1]), int(size_info[2]))
                    volume_data = np.zeros(volume_shape, dtype=np.float64)
                    
                    if hasattr(fit_data, 'Idx'):
                        idx = fit_data.Idx.astype(int) - 1
                        if np.max(idx) < volume_data.size:
                            volume_data.flat[idx] = p_data
                    
                    image_name = name_mapping[i] if i < len(name_mapping) else f"IMG{i+1}"
                    image_entry = self.create_image_struct(volume_data, image_name)
                    images_list.append(image_entry)
                    
                    # Create BE_AMP for first image
                    if i == 0:
                        be_amp_entry = self.create_image_struct(volume_data, 'BE_AMP')
                        images_list.append(be_amp_entry)
                    
                    logger.info(f"Added {image_name} with shape {volume_shape}")
            
            project_data = {
                'images': np.array(images_list, dtype=object),
                'project_info': {
                    'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'total_images': len(images_list)
                }
            }
            
            sio.savemat(output_path, project_data, do_compression=True)
            logger.info(f"Created project file: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None
    
    def create_image_struct(self, data: np.ndarray, name: str):
        """Create image structure"""
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
    
    def create_simple_roi(self, project_file: str):
        """Create simple geometric ROI"""
        try:
            mat_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            images_struct = mat_data['images']
            
            # Find BE_AMP
            be_amp_entry = None
            for entry in images_struct:
                if hasattr(entry, 'Name') and 'BE_AMP' in str(entry.Name):
                    be_amp_entry = entry
                    break
            
            if be_amp_entry is None:
                logger.error("BE_AMP not found")
                return None
            
            # Create two kidney ROIs (left and right)
            shape = be_amp_entry.data.shape
            
            # Left kidney (offset from center)
            center1 = [shape[0]//2, shape[1]//2 - shape[1]//6, shape[2]//2]
            radius1 = min(shape) // 8
            
            # Right kidney (offset from center)
            center2 = [shape[0]//2, shape[1]//2 + shape[1]//6, shape[2]//2]
            radius2 = min(shape) // 8
            
            z, y, x = np.mgrid[0:shape[0], 0:shape[1], 0:shape[2]]
            
            # Create masks
            dist1 = np.sqrt((z - center1[0])**2 + (y - center1[1])**2 + (x - center1[2])**2)
            dist2 = np.sqrt((z - center2[0])**2 + (y - center2[1])**2 + (x - center2[2])**2)
            
            roi1_mask = dist1 <= radius1
            roi2_mask = dist2 <= radius2
            
            # Create ROI structures
            roi_structs = [
                self.make_roi_struct(roi1_mask, "Kidney"),
                self.make_roi_struct(roi2_mask, "Kidney2")
            ]
            
            # Attach to all images
            for entry in images_struct:
                roi_array = np.array([roi for roi in roi_structs], dtype=object)
                setattr(entry, 'slaves', roi_array)
            
            # Save updated project
            output_path = project_file.replace('.mat', '_with_roi.mat')
            sio.savemat(output_path, mat_data, do_compression=True)
            logger.info(f"Project with ROI saved: {output_path}")
            
            return output_path
            
        except Exception as e:
            logger.error(f"Error creating ROI: {e}")
            return None
    
    def make_roi_struct(self, mask: np.ndarray, name: str):
        """Create ROI structure"""
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
    
    def extract_statistics(self, project_file: str):
        """Extract ROI statistics"""
        try:
            mat_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            images_struct = mat_data['images']
            
            results = []
            
            for entry in images_struct:
                if not hasattr(entry, 'Name') or not hasattr(entry, 'data'):
                    continue
                
                image_name = str(entry.Name)
                image_data = entry.data
                
                if hasattr(entry, 'slaves') and len(entry.slaves) > 0:
                    for roi in entry.slaves:
                        if hasattr(roi, 'data') and hasattr(roi, 'Name'):
                            roi_name = str(roi.Name)
                            roi_mask = roi.data.astype(bool)
                            roi_voxels = image_data[roi_mask]
                            
                            if len(roi_voxels) > 0:
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
                                logger.info(f"Stats for {image_name}-{roi_name}: Mean={stats['Mean']:.2f}")
            
            return pd.DataFrame(results) if results else None
            
        except Exception as e:
            logger.error(f"Error extracting statistics: {e}")
            return None
    
    def run_analysis(self, data_subdir: str = '241202'):
        """Run complete analysis"""
        try:
            output_dir = os.path.join(self.base_dir, "process", "output", 
                                    f"simple_analysis_{data_subdir}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(output_dir, exist_ok=True)
            
            # Find files
            processed_files = self.find_processed_files(data_subdir)
            if not processed_files:
                print("❌ No processed files found")
                return None
            
            # Create project
            project_file = os.path.join(output_dir, f"project_{data_subdir}.mat")
            project_file = self.create_project_file(processed_files, project_file)
            if not project_file:
                return None
            
            # Create ROI
            project_with_roi = self.create_simple_roi(project_file)
            if not project_with_roi:
                return None
            
            # Extract statistics
            stats_df = self.extract_statistics(project_with_roi)
            if stats_df is None:
                return None
            
            # Save results
            excel_file = os.path.join(output_dir, f"roi_statistics_{data_subdir}.xlsx")
            csv_file = os.path.join(output_dir, f"roi_statistics_{data_subdir}.csv")
            
            with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
                stats_df.to_excel(writer, sheet_name='ROI_Statistics', index=False)
                
                # Summary
                summary = stats_df.groupby(['Image', 'ROI']).agg({
                    'Mean': 'first', 'Median': 'first', 'Std': 'first', 'N_Voxels': 'first'
                }).reset_index()
                summary.to_excel(writer, sheet_name='Summary', index=False)
            
            stats_df.to_csv(csv_file, index=False)
            
            logger.info(f"Analysis complete! Output: {output_dir}")
            
            # Print summary
            print(f"\n📊 Analysis Summary:")
            print(f"Total images: {stats_df['Image'].nunique()}")
            print(f"Total ROIs: {stats_df['ROI'].nunique()}")
            print(f"Mean values by image:")
            for img, mean_val in stats_df.groupby('Image')['Mean'].mean().items():
                print(f"  {img}: {mean_val:.2f}")
            
            return output_dir
            
        except Exception as e:
            logger.error(f"Error in analysis: {e}")
            return None

def main():
    """Main function"""
    print("🔬 Simple EPRI ROI Analysis")
    print("="*40)
    
    extractor = SimpleEPRIExtractor()
    result = extractor.run_analysis()
    
    if result:
        print(f"\n✅ Analysis completed!")
        print(f"📁 Results saved to: {result}")
    else:
        print("\n❌ Analysis failed")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
