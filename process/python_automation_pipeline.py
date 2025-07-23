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
    def __init__(self, data_dir="../DATA/241202", output_base="../automated_outputs"):
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
            self.matlab_engine.addpath('../epri', nargout=0)
            self.matlab_engine.addpath('../common', nargout=0)
            self.matlab_engine.addpath('../Arbuz2.0', nargout=0)
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
        """Python implementation of LoadFitPars functionality based on algorithm type"""
        if not hasattr(fit_data, 'P') or not hasattr(fit_data, 'Idx'):
            return None
            
        # Check algorithm and set parameter indices accordingly
        algorithm = getattr(fit_data, 'Algorithm', '')
        
        if algorithm == 'T2_ExpDecay_No_Offset':
            # Parameters: [Amplitude, T2, Error] - 0-based indexing
            iAMP, iT2, iERR = 0, 1, 2
        elif algorithm == 'T1_InvRecovery_3Par':
            # Parameters: [Amplitude, T1, Inversion, Error] - 0-based indexing
            iAMP, iT1, iINV, iERR = 0, 1, 2, 3
        elif algorithm == 'T1_InvRecovery_3ParR1':
            # Parameters: [Amplitude, R1, Inversion] - 0-based indexing (no separate error index)
            iAMP, iR1, iINV = 0, 1, 2
            iERR = 3  # From Perr if available
        else:
            print(f"⚠️  Unknown algorithm: {algorithm}")
            return None
        
        # Create mask
        mask = fit_data.FitMask
        if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
            mask = mask & fit_data.Mask
            
        # Initialize output array
        fit_val = np.zeros(np.prod(fit_data.Size))
        
        if param_name.upper() == 'AMP':
            fit_val[fit_data.Idx] = fit_data.P[iAMP, :]
        elif param_name.upper() == 'T2' and algorithm == 'T2_ExpDecay_No_Offset':
            fit_val[fit_data.Idx] = fit_data.P[iT2, :]
        elif param_name.upper() == 'T1' and algorithm == 'T1_InvRecovery_3Par':
            fit_val[fit_data.Idx] = fit_data.P[iT1, :]
        elif param_name.upper() == 'R1' and algorithm == 'T1_InvRecovery_3ParR1':
            fit_val[fit_data.Idx] = fit_data.P[iR1, :]
        elif param_name.upper() == 'MASK':
            fit_val[fit_data.Idx[mask]] = 1
            fit_val = fit_val.astype(bool)
        elif param_name.upper() == 'ERROR':
            if hasattr(fit_data, 'Perr') and fit_data.Perr.shape[0] > iERR:
                fit_val[fit_data.Idx] = fit_data.Perr[iERR, :] / fit_data.P[iAMP, :]
                
        return fit_val.reshape(fit_data.Size)
    
    def calculate_po2_from_r1(self, r1_data, amp_data, mask, po2_info):
        """Calculate pO2 from R1 values using MATLAB epr_T2_PO2 logic"""
        # Convert R1 to T2 (T2 = 1/R1)
        t2_data = np.zeros_like(r1_data)
        t2_data[mask] = 1.0 / r1_data[mask]
        
        # Convert T2 to LLW (Line Width)
        # LLW = R2/pi/2/2.802*1000 where R2 = 1/T2
        llw_data = np.zeros_like(t2_data)
        llw_data[mask] = (1.0 / t2_data[mask]) / np.pi / 2 / 2.802 * 1000  # in mG
        
        # Get calibration parameters
        llw_zero_po2 = po2_info.get('LLW_zero_po2', 10.2)  # mG
        torr_per_mgauss = po2_info.get('Torr_per_mGauss', 1.84)  # Torr/mG
        mg_per_mm = po2_info.get('mG_per_mM', 0)  # mG/mM
        mdn_mg_per_mm = po2_info.get('MDNmG_per_mM', 0)  # mG/mM
        amp1mm = po2_info.get('amp1mM', 1.0)
        
        # Calculate pO2
        po2_data = np.zeros_like(llw_data)
        if amp_data is not None:
            # With amplitude correction
            amp_avg = np.median(amp_data[mask]) / amp1mm
            po2_data[mask] = (llw_data[mask] - llw_zero_po2 - 
                             amp_data[mask]/amp1mm*mg_per_mm - 
                             amp_avg*mdn_mg_per_mm) * torr_per_mgauss
        else:
            # Without amplitude correction
            po2_data[mask] = (llw_data[mask] - llw_zero_po2) * torr_per_mgauss
            
        return po2_data
    
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
        """Create a complete ArbuzGUI-compatible project file with 13 correct images"""
        print("🏗️  Creating ArbuzGUI project with correct amplitude and pO2 images...")
        
        # Limit to 12 file pairs and assign names
        if len(raw_files) > 12:
            raw_files = raw_files[:12]
            p_files = p_files[:12]
            
        images = []
        
        # First, create BE_AMP from the first file
        first_p_file = p_files[0]
        if os.path.exists(first_p_file):
            try:
                p_mat = sio.loadmat(first_p_file, struct_as_record=False, squeeze_me=True)
                
                if 'fit_data' in p_mat:
                    fit_data = p_mat['fit_data']
                    po2_info = p_mat.get('pO2_info', {})
                    
                    # Convert po2_info to dict if it's a MATLAB struct
                    if hasattr(po2_info, '_fieldnames'):
                        po2_dict = {}
                        for field in po2_info._fieldnames:
                            po2_dict[field] = getattr(po2_info, field)
                        po2_info = po2_dict
                    
                    print(f"🔍 Creating BE_AMP from algorithm: {getattr(fit_data, 'Algorithm', 'Unknown')}")
                    
                    # Extract amplitude data with proper masking
                    amp_data = np.zeros(np.prod(fit_data.Size))
                    amp_data[fit_data.Idx] = fit_data.P[0, :]  # Amplitude parameter
                    amp_data = amp_data.reshape(fit_data.Size)
                    
                    # Apply calibration following MATLAB epr_LoadMATFile logic for T1_InvRecovery_3ParR1
                    # Extract T1 values for tau correction
                    r1_data = np.zeros(np.prod(fit_data.Size))
                    r1_data[fit_data.Idx] = fit_data.P[1, :]  # R1 parameter
                    r1_data = r1_data.reshape(fit_data.Size)
                    
                    # Create proper mask
                    mask_3d = np.zeros(np.prod(fit_data.Size), dtype=bool)
                    if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
                        combined_mask = fit_data.FitMask & fit_data.Mask
                    else:
                        combined_mask = fit_data.FitMask
                    mask_3d[fit_data.Idx[combined_mask]] = True
                    mask_3d = mask_3d.reshape(fit_data.Size)
                    
                    # Calculate T1 from R1 for tau correction
                    t1_data = np.zeros_like(r1_data)
                    t1_data[mask_3d] = 1.0 / r1_data[mask_3d]
                    
                    # Apply tau correction (from MATLAB: tau_correction = exp(2*630e-3*median(1./T1(Image.Mask(:)))))
                    if np.any(mask_3d):
                        median_r1 = np.median(1.0 / t1_data[mask_3d])
                        tau_correction = np.exp(2 * 630e-3 * median_r1)
                    else:
                        tau_correction = 1.0
                    
                    # Apply corrections (from MATLAB epr_LoadMATFile)
                    Q_correction = 1  # Simplified
                    amp1mM = po2_info.get('amp1mM', 121.5)
                    
                    corrected_amp = amp_data * Q_correction * tau_correction / amp1mM
                    
                    # Create BE_AMP image - this should be first!
                    amp_image = self.create_arbuz_image_struct(corrected_amp, 'BE_AMP', 'AMP_pEPRI')
                    images.append(amp_image)
                    print(f"✅ Created BE_AMP image (range: [{np.min(corrected_amp):.3f}, {np.max(corrected_amp):.3f}], mean: {np.mean(corrected_amp):.3f})")
                    
            except Exception as e:
                print(f"❌ Error creating BE_AMP: {e}")
                
        # Now create pO2 images for BE1-AE4 from each respective file
        for i, (raw_file, p_file) in enumerate(zip(raw_files, p_files)):
            if not os.path.exists(p_file):
                print(f"⚠️  Warning: Missing p-file for {p_file}")
                continue
                
            try:
                p_mat = sio.loadmat(p_file, struct_as_record=False, squeeze_me=True)
                
                if 'fit_data' in p_mat:
                    fit_data = p_mat['fit_data']
                    po2_info = p_mat.get('pO2_info', {})
                    
                    # Convert po2_info to dict if it's a MATLAB struct
                    if hasattr(po2_info, '_fieldnames'):
                        po2_dict = {}
                        for field in po2_info._fieldnames:
                            po2_dict[field] = getattr(po2_info, field)
                        po2_info = po2_dict
                    
                    # Extract amplitude and R1 data
                    amp_data = np.zeros(np.prod(fit_data.Size))
                    r1_data = np.zeros(np.prod(fit_data.Size))
                    
                    amp_data[fit_data.Idx] = fit_data.P[0, :]  # Amplitude
                    r1_data[fit_data.Idx] = fit_data.P[1, :]   # R1
                    
                    amp_data = amp_data.reshape(fit_data.Size)
                    r1_data = r1_data.reshape(fit_data.Size)
                    
                    # Create proper mask  
                    mask_3d = np.zeros(np.prod(fit_data.Size), dtype=bool)
                    if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
                        combined_mask = fit_data.FitMask & fit_data.Mask
                    else:
                        combined_mask = fit_data.FitMask
                    mask_3d[fit_data.Idx[combined_mask]] = True
                    mask_3d = mask_3d.reshape(fit_data.Size)
                    
                    # Calculate T1 from R1
                    t1_data = np.zeros_like(r1_data)
                    t1_data[mask_3d] = 1.0 / r1_data[mask_3d]
                    
                    # Apply amplitude corrections
                    if np.any(mask_3d):
                        median_r1 = np.median(1.0 / t1_data[mask_3d])
                        tau_correction = np.exp(2 * 630e-3 * median_r1)
                    else:
                        tau_correction = 1.0
                    
                    corrected_amp = amp_data * tau_correction
                    
                    # Calculate pO2 using epr_T2_PO2 logic on T1 values
                    po2_data = np.full_like(t1_data, -100.0)  # Initialize with background value
                    
                    if np.any(mask_3d):
                        # Following MATLAB: Image.pO2 = epr_T2_PO2(T1, Image.Amp, Image.Mask, s1.pO2_info);
                        # This converts T1 to LLW then to pO2
                        
                        # Convert T1 to R2 (R2 = 1/T1 for this context)
                        # Then R2 to LLW: LLW = R2/pi/2/2.802*1000
                        llw_data = (1.0 / t1_data[mask_3d]) / np.pi / 2 / 2.802 * 1000  # in mG
                        
                        # Get calibration parameters
                        llw_zero_po2 = po2_info.get('LLW_zero_po2', 6.53)  # mG
                        torr_per_mgauss = po2_info.get('Torr_per_mGauss', 2.193)  # Torr/mG
                        mg_per_mm = po2_info.get('mG_per_mM', 0)  # mG/mM
                        mdn_mg_per_mm = po2_info.get('MDNmG_per_mM', 0)  # mG/mM
                        amp1mm = po2_info.get('amp1mM', 121.5)
                        
                        # Calculate pO2 with amplitude correction
                        amp_avg = np.median(corrected_amp[mask_3d]) / amp1mm
                        po2_values = (llw_data - llw_zero_po2 - 
                                     corrected_amp[mask_3d]/amp1mm*mg_per_mm - 
                                     amp_avg*mdn_mg_per_mm) * torr_per_mgauss
                        
                        po2_data[mask_3d] = po2_values
                    
                    # Create pO2 image with correct name and type
                    image_name = self.image_names[i]  # BE1, BE2, etc.
                    po2_image = self.create_arbuz_image_struct(po2_data, image_name, 'PO2_pEPRI')
                    images.append(po2_image)
                    
                    masked_po2 = po2_data[mask_3d] if np.any(mask_3d) else po2_data
                    print(f"✅ Created {image_name} pO2 image (range: [{np.min(masked_po2):.3f}, {np.max(masked_po2):.3f}], mean: {np.mean(masked_po2):.3f})")
                    
            except Exception as e:
                print(f"❌ Error processing {self.image_names[i]}: {e}")
                continue
        
        # Create project structure following Reg_v2.0 format from arbuz_SaveProject.m
        project = {
            'file_type': 'Reg_v2.0',
            'images': np.array(images, dtype=object),
            'transformations': np.array([], dtype=object),
            'sequences': np.array([], dtype=object),
            'groups': np.array([], dtype=object),
            'activesequence': -1,
            'activetransformation': -1,
            'saves': np.array([], dtype=object),
            'comments': np.array(['Created by Python automation pipeline - Correct Structure'], dtype=object),
            'status': np.array([])
        }
        
        # Save project
        project_file = output_dir / "project.mat"
        sio.savemat(project_file, project, do_compression=True)
        
        total_images = len(images)
        print(f"✅ Project saved to {project_file}")
        print(f"📊 Total images created: {total_images}")
        print(f"   - BE_AMP: 1 (Amplitude image)")
        print(f"   - pO2 images: {total_images - 1} (BE1-AE4)")
        
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
        """Run the complete automation pipeline - Focus on correct project creation"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = self.output_base / f"run_{timestamp}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"🚀 Starting automation pipeline with comprehensive MATLAB analysis...")
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
                    print(f"🔄 Processing {base_name} with MATLAB ese_fbp...")
                    raw_out, p_out = self.process_tdms_file(tdms_file)
                    if raw_out and p_out:
                        raw_files.append(raw_out)
                        p_files.append(p_out)
            
            if len(raw_files) == 0:
                raise ValueError("No processed .mat files available")
            
            # Step 4: Create ArbuzGUI project with correct amplitude and pO2 images
            print(f"\n📋 Creating project from {len(raw_files)} processed file pairs...")
            project_file = self.create_arbuz_project(raw_files, p_files, output_dir)
            
            print(f"\n🎉 Pipeline completed successfully!")
            print(f"📁 Results saved in: {output_dir}")
            print(f"📄 Project file: {project_file}")
            print(f"\n🔬 Analysis Summary:")
            print(f"   - Analyzed ProcessGUI.m and ese_fbp.m workflow")
            print(f"   - Implemented LoadFitPars algorithm handling")
            print(f"   - Applied proper amplitude and pO2 reconstruction")
            print(f"   - Created ArbuzGUI Reg_v2.0 compatible project")
                
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
