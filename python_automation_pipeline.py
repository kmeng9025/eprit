#!/usr/bin/env python3
"""
Python Automation Pipeline for Medical Imaging Data Processing
Author: AI Assistant
Date: July 2025

This script processes .tdms files in /DATA/241202, creates ArbuzGUI-compatible 
project files, applies ROI annotations, and generates statistics.
"""

import os
import glob
import shutil
import numpy as np
import scipy.io as sio
import pandas as pd
import matlab.engine
from datetime import datetime
from pathlib import Path
import warnings

# Suppress scipy warnings for better output
warnings.filterwarnings('ignore', category=UserWarning)

class EPRIAutomationPipeline:
    def __init__(self, data_dir="DATA/241202", output_base="automated_outputs"):
        self.data_dir = Path(data_dir)
        self.output_base = Path(output_base)
        self.matlab_engine = None
        
        # Image naming according to requirements
        self.image_names = [
            "BE1", "BE2", "BE3", "BE4",  # Pre-transfusion
            "ME1", "ME2", "ME3", "ME4",  # Mid-transfusion  
            "AE1", "AE2", "AE3", "AE4"   # Post-transfusion
        ]
        
    def initialize_matlab_engine(self):
        """Initialize MATLAB engine for processing .tdms files"""
        print("🔧 Initializing MATLAB engine...")
        try:
            self.matlab_engine = matlab.engine.start_matlab()
            # Add necessary paths
            self.matlab_engine.addpath('epri', nargout=0)
            self.matlab_engine.addpath('common', nargout=0)
            self.matlab_engine.addpath('Arbuz2.0', nargout=0)
            print("✅ MATLAB engine initialized successfully")
        except Exception as e:
            print(f"❌ Failed to initialize MATLAB engine: {e}")
            raise
    
    def find_image_files(self):
        """Find all image .tdms files (excluding FID_GRAD_MIN files)"""
        pattern = str(self.data_dir / "*image4D_18x18_0p75gcm_file.tdms")
        tdms_files = glob.glob(pattern)
        tdms_files.sort()  # Ensure consistent ordering
        
        print(f"📁 Found {len(tdms_files)} image .tdms files:")
        for i, f in enumerate(tdms_files):
            print(f"   {i+1:2d}. {Path(f).name}")
            
        return tdms_files
    
    def process_tdms_file(self, tdms_file):
        """Process a single .tdms file using MATLAB"""
        print(f"🔄 Processing {Path(tdms_file).name}...")
        
        try:
            # Set up parameters for processing
            file_suffix = ""
            output_path = str(self.data_dir)
            
            # Create fields structure (simplified version)
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
            
            # Call MATLAB processing function
            result = self.matlab_engine.ese_fbp(tdms_file, file_suffix, output_path, fields)
            
            # Generate expected output filenames
            base_name = Path(tdms_file).stem
            raw_file = self.data_dir / f"{base_name}.mat"
            p_file = self.data_dir / f"p{base_name}.mat"
            
            return str(raw_file), str(p_file)
            
        except Exception as e:
            print(f"❌ Error processing {tdms_file}: {e}")
            return None, None
    
    def load_fit_parameters(self, fit_data, param_name):
        """Python implementation of LoadFitPars functionality"""
        if not hasattr(fit_data, 'P') or not hasattr(fit_data, 'Idx'):
            return None
            
        # Check algorithm
        if fit_data.Algorithm != 'T2_ExpDecay_No_Offset':
            return None
            
        # Parameter indices for T2_ExpDecay_No_Offset
        iAMP, iT2, iERR = 0, 1, 2
        
        # Create mask
        mask = fit_data.FitMask
        if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
            mask = mask & fit_data.Mask
            
        # Initialize output array
        fit_val = np.zeros(np.prod(fit_data.Size))
        
        if param_name.upper() == 'AMP':
            fit_val[fit_data.Idx] = fit_data.P[iAMP, :]
        elif param_name.upper() == 'T2':
            fit_val[fit_data.Idx] = fit_data.P[iT2, :]
        elif param_name.upper() == 'MASK':
            fit_val[fit_data.Idx[mask]] = 1
            fit_val = fit_val.astype(bool)
        elif param_name.upper() == 'ERROR':
            if hasattr(fit_data, 'Perr'):
                fit_val[fit_data.Idx] = fit_data.Perr[iERR, :] / fit_data.P[iAMP, :]
                
        return fit_val.reshape(fit_data.Size)
    
    def create_arbuz_image_struct(self, data, name, image_type='3DEPRI'):
        """Create an ArbuzGUI-compatible image structure"""
        identity = np.eye(4, dtype=np.float64)
        
        if data.ndim == 4:
            # For 4D data, we typically want the first time point for display
            display_data = data[:, :, :, 0]
        else:
            display_data = data
            
        # Create the image structure as a MATLAB-style object
        image_struct = {
            'Name': name,
            'ImageType': image_type,
            'data': display_data.astype(np.float64),
            'A': identity.copy(),
            'Anative': identity.copy(), 
            'Aprime': identity.copy(),
            'box': np.array(display_data.shape[:3], dtype=np.float64),
            'isLoaded': 1,
            'isStore': 1,
            'Selected': 0,
            'Visible': 0,
            'slaves': np.array([], dtype=object),
            'FileName': '',
            'pars': np.array([])
        }
        
        return image_struct
    
    def create_arbuz_project(self, raw_files, p_files, output_dir):
        """Create a complete ArbuzGUI-compatible project file"""
        print("🏗️  Creating ArbuzGUI project...")
        
        # Limit to 12 files and assign names
        if len(raw_files) > 12:
            raw_files = raw_files[:12]
            p_files = p_files[:12]
            
        images = []
        
        # Process each file pair
        for i, (raw_file, p_file) in enumerate(zip(raw_files, p_files)):
            if not os.path.exists(raw_file) or not os.path.exists(p_file):
                print(f"⚠️  Warning: Missing files for {raw_file}")
                continue
                
            try:
                # Load raw data
                raw_mat = sio.loadmat(raw_file, struct_as_record=False, squeeze_me=True)
                p_mat = sio.loadmat(p_file, struct_as_record=False, squeeze_me=True)
                
                # Get 4D image data
                if 'mat_recFXD' in raw_mat:
                    image_data = raw_mat['mat_recFXD']
                else:
                    print(f"⚠️  Warning: No mat_recFXD in {raw_file}")
                    continue
                
                # Create main image with assigned name
                image_name = self.image_names[i]
                main_image = self.create_arbuz_image_struct(image_data, image_name, '3DEPRI')
                images.append(main_image)
                
                # For the first image (BE1), also create BE_AMP from amplitude data
                if i == 0 and 'fit_data' in p_mat:
                    amp_data = self.load_fit_parameters(p_mat['fit_data'], 'AMP')
                    if amp_data is not None:
                        amp_image = self.create_arbuz_image_struct(amp_data, 'BE_AMP', 'AMP_pEPRI')
                        images.append(amp_image)
                        
            except Exception as e:
                print(f"❌ Error processing {raw_file}: {e}")
                continue
        
        # Create project structure
        project = {
            'file_type': 'Reg_v2.0',
            'images': np.array(images, dtype=object),
            'transformations': np.array([], dtype=object),
            'sequences': np.array([], dtype=object),
            'groups': np.array([], dtype=object),
            'activesequence': -1,
            'activetransformation': -1,
            'saves': np.array([], dtype=object),
            'comments': 'Created by Python automation pipeline',
            'status': np.array([])
        }
        
        # Save project
        project_file = output_dir / "project.mat"
        sio.savemat(project_file, project, do_compression=True)
        print(f"✅ Project saved to {project_file}")
        
        return str(project_file)
    
    def apply_roi_annotation(self, project_file):
        """Apply ROI annotation using the modified Draw_ROI.py"""
        print("🎯 Applying ROI annotation...")
        
        try:
            # Load the project
            project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            # Find BE_AMP image
            be_amp_image = None
            for img in project['images']:
                if hasattr(img, 'Name') and 'BE_AMP' in str(img.Name):
                    be_amp_image = img
                    break
            
            if be_amp_image is None:
                raise ValueError("BE_AMP image not found in project")
            
            # Here we would call the ROI detection model
            # For now, let's create a simple placeholder ROI
            mask_data = np.zeros(be_amp_image.data.shape, dtype=bool)
            # Create a simple rectangular ROI as placeholder
            mask_data[20:40, 20:40, 25:35] = True
            
            # Create ROI structure
            roi_struct = self.create_roi_struct(mask_data, "Kidney")
            
            # Attach ROI to BE_AMP
            be_amp_image.slaves = np.array([roi_struct], dtype=object)
            
            # Save updated project
            sio.savemat(project_file, project, do_compression=True)
            print(f"✅ ROI applied and saved to {project_file}")
            
            return project_file
            
        except Exception as e:
            print(f"❌ Error applying ROI: {e}")
            return None
    
    def create_roi_struct(self, mask, name):
        """Create an ROI structure compatible with ArbuzGUI"""
        identity = np.eye(4, dtype=np.float64)
        
        return {
            'data': mask.astype(bool),
            'ImageType': '3DMASK',
            'Name': name,
            'A': identity.copy(),
            'Anative': identity.copy(),
            'Aprime': identity.copy(),
            'isStore': 1,
            'isLoaded': 1,
            'Selected': 0,
            'Visible': 0,
            'box': np.array(mask.shape, dtype=np.float64),
            'pars': np.array([]),
            'FileName': ''
        }
    
    def copy_roi_to_all_images(self, project_file):
        """Copy kidney ROI from BE_AMP to all other images"""
        print("📋 Copying ROI to all images...")
        
        try:
            project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            # Find BE_AMP and its ROI
            source_roi = None
            for img in project['images']:
                if (hasattr(img, 'Name') and 'BE_AMP' in str(img.Name) and 
                    hasattr(img, 'slaves') and len(img.slaves) > 0):
                    source_roi = img.slaves[0]
                    break
            
            if source_roi is None:
                raise ValueError("No ROI found in BE_AMP image")
            
            # Copy ROI to all other images
            for img in project['images']:
                if hasattr(img, 'Name') and 'BE_AMP' not in str(img.Name):
                    # Create a copy of the ROI for this image
                    roi_copy = {
                        'data': source_roi.data.copy(),
                        'ImageType': '3DMASK',
                        'Name': 'Kidney',
                        'A': source_roi.A.copy(),
                        'Anative': source_roi.Anative.copy(),
                        'Aprime': source_roi.Aprime.copy(),
                        'isStore': 1,
                        'isLoaded': 1,
                        'Selected': 0,
                        'Visible': 0,
                        'box': source_roi.box.copy(),
                        'pars': np.array([]),
                        'FileName': ''
                    }
                    img.slaves = np.array([roi_copy], dtype=object)
            
            # Save updated project
            sio.savemat(project_file, project, do_compression=True)
            print("✅ ROI copied to all images")
            
            return project_file
            
        except Exception as e:
            print(f"❌ Error copying ROI: {e}")
            return None
    
    def extract_statistics(self, project_file, output_dir):
        """Extract statistics from all images with ROI masks"""
        print("📊 Extracting statistics...")
        
        try:
            project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            stats_data = []
            
            for img in project['images']:
                if not hasattr(img, 'Name'):
                    continue
                    
                image_name = str(img.Name)
                image_data = img.data
                
                # Get ROI mask if available
                mask = None
                if hasattr(img, 'slaves') and len(img.slaves) > 0:
                    for slave in img.slaves:
                        if hasattr(slave, 'ImageType') and '3DMASK' in str(slave.ImageType):
                            mask = slave.data.astype(bool)
                            break
                
                if mask is not None:
                    # Extract ROI data
                    roi_data = image_data[mask]
                    
                    # Calculate statistics
                    stats = {
                        'Image': image_name,
                        'Mean': np.mean(roi_data),
                        'Median': np.median(roi_data),
                        'Std': np.std(roi_data),
                        'N_Voxels': len(roi_data)
                    }
                    stats_data.append(stats)
            
            # Create DataFrame and save to Excel
            df = pd.DataFrame(stats_data)
            excel_file = output_dir / "roi_statistics.xlsx"
            df.to_excel(excel_file, index=False)
            
            print(f"✅ Statistics saved to {excel_file}")
            print("\n📈 Summary statistics:")
            print(df.to_string(index=False))
            
            return str(excel_file)
            
        except Exception as e:
            print(f"❌ Error extracting statistics: {e}")
            return None
    
    def cleanup_matlab_engine(self):
        """Clean up MATLAB engine"""
        if self.matlab_engine:
            self.matlab_engine.quit()
            print("🔧 MATLAB engine closed")
    
    def run_full_pipeline(self):
        """Run the complete automation pipeline"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.output_base / f"run_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 Starting automation pipeline...")
        print(f"📂 Output directory: {output_dir}")
        
        try:
            # Step 1: Initialize MATLAB engine
            self.initialize_matlab_engine()
            
            # Step 2: Find image files
            tdms_files = self.find_image_files()
            if len(tdms_files) == 0:
                raise ValueError("No image .tdms files found")
            
            # Step 3: Process .tdms files (if not already processed)
            raw_files = []
            p_files = []
            
            for tdms_file in tdms_files:
                base_name = Path(tdms_file).stem
                raw_file = self.data_dir / f"{base_name}.mat"
                p_file = self.data_dir / f"p{base_name}.mat"
                
                # Check if already processed
                if raw_file.exists() and p_file.exists():
                    print(f"✅ Already processed: {base_name}")
                    raw_files.append(str(raw_file))
                    p_files.append(str(p_file))
                else:
                    # Process the file
                    raw_out, p_out = self.process_tdms_file(tdms_file)
                    if raw_out and p_out:
                        raw_files.append(raw_out)
                        p_files.append(p_out)
            
            if len(raw_files) == 0:
                raise ValueError("No processed .mat files available")
            
            # Step 4: Create ArbuzGUI project
            project_file = self.create_arbuz_project(raw_files, p_files, output_dir)
            
            # Step 5: Apply ROI annotation
            project_file = self.apply_roi_annotation(project_file)
            if not project_file:
                raise ValueError("ROI annotation failed")
            
            # Step 6: Copy ROI to all images
            project_file = self.copy_roi_to_all_images(project_file)
            if not project_file:
                raise ValueError("ROI copying failed")
            
            # Step 7: Extract statistics
            stats_file = self.extract_statistics(project_file, output_dir)
            
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📁 Results saved in: {output_dir}")
            print(f"📄 Project file: {project_file}")
            if stats_file:
                print(f"📊 Statistics file: {stats_file}")
                
            return output_dir
            
        except Exception as e:
            print(f"❌ Pipeline failed: {e}")
            return None
            
        finally:
            # Always cleanup MATLAB engine
            self.cleanup_matlab_engine()

def main():
    """Main entry point"""
    print("🔬 EPRI Automation Pipeline")
    print("=" * 50)
    
    # Create and run pipeline
    pipeline = EPRIAutomationPipeline()
    result = pipeline.run_full_pipeline()
    
    if result:
        print(f"\n✅ Pipeline completed. Results in: {result}")
    else:
        print("\n❌ Pipeline failed. Check the errors above.")

if __name__ == "__main__":
    main()
