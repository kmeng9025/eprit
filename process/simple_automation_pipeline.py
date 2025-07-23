# #!/usr/bin/env python3
# """
# Simplified EPRI Automation Pipeline (No MATLAB Engine Required)
# Author: AI Assistant  
# Date: July 2025

# This script works with already processed .mat files in /DATA/241202
# to create ArbuzGUI projects, apply ROI annotations, and generate statistics.
# """

# import os
# import glob
# import numpy as np
# import scipy.io as sio
# from datetime import datetime
# from pathlib import Path
# import warnings

# # Suppress scipy warnings
# warnings.filterwarnings('ignore', category=UserWarning)

# try:
#     import pandas as pd
#     PANDAS_AVAILABLE = True
# except ImportError:
#     PANDAS_AVAILABLE = False
#     print("⚠️  pandas not available. Statistics will be saved as CSV using numpy.")

# class SimpleEPRIAutomation:
#     def __init__(self, data_dir="../DATA/241202", output_base="../automated_outputs"):
#         self.data_dir = Path(data_dir)
#         self.output_base = Path(output_base)
        
#         # Image naming according to requirements
#         self.image_names = [
#             "BE1", "BE2", "BE3", "BE4",  # Pre-transfusion
#             "ME1", "ME2", "ME3", "ME4",  # Mid-transfusion  
#             "AE1", "AE2", "AE3", "AE4"   # Post-transfusion
#         ]
    
#     def find_processed_files(self):
#         """Find all processed .mat file pairs (regular and p-prefixed)"""
#         # Find all image .mat files (not p-prefixed)
#         pattern = str(self.data_dir / "*image4D_18x18_0p75gcm_file.mat")
#         raw_files = [f for f in glob.glob(pattern) if not Path(f).name.startswith('p')]
#         raw_files.sort()
        
#         # Find corresponding p-prefixed files
#         p_files = []
#         for raw_file in raw_files:
#             base_name = Path(raw_file).name
#             p_file = self.data_dir / f"p{base_name}"
#             if p_file.exists():
#                 p_files.append(str(p_file))
#             else:
#                 p_files.append(None)
        
#         # Filter out pairs where p-file is missing
#         valid_pairs = [(r, p) for r, p in zip(raw_files, p_files) if p is not None]
        
#         print(f"📁 Found {len(valid_pairs)} valid .mat file pairs:")
#         for i, (raw_file, p_file) in enumerate(valid_pairs):
#             print(f"   {i+1:2d}. {Path(raw_file).name} + {Path(p_file).name}")
        
#         return valid_pairs
    
#     def load_fit_parameters(self, fit_data, param_name):
#         """Python implementation of MATLAB LoadFitPars functionality"""
#         if not hasattr(fit_data, 'P') or not hasattr(fit_data, 'Idx'):
#             return None
            
#         # Check algorithm and set parameter indices accordingly
#         if not hasattr(fit_data, 'Algorithm'):
#             return None
            
#         algorithm = str(fit_data.Algorithm)
        
#         if algorithm == 'T2_ExpDecay_No_Offset':
#             iAMP, iT2, iERR = 0, 1, 2
#         elif algorithm == 'T1_InvRecovery_3ParR1':
#             # For T1 inversion recovery with R1: [Amplitude, R1, Inversion]
#             # MATLAB indices are 1-based, Python 0-based
#             iAMP, iR1, iINV = 0, 1, 2  # Amplitude, R1, Inversion
#         else:
#             print(f"⚠️  Unknown algorithm: {algorithm}, assuming first parameter is amplitude")
#             iAMP, iT2, iERR = 0, 1, 2
        
#         # Create mask
#         mask = fit_data.FitMask
#         if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
#             mask = mask & fit_data.Mask
            
#         # Initialize output array
#         fit_val = np.zeros(np.prod(fit_data.Size))
        
#         if param_name.upper() == 'AMP':
#             fit_val[fit_data.Idx] = fit_data.P[iAMP, :]
#         elif param_name.upper() == 'T1':
#             if algorithm == 'T1_InvRecovery_3ParR1':
#                 # T1 = 1/R1, avoid division by zero
#                 r1_vals = fit_data.P[iR1, :]
#                 r1_vals[r1_vals == 0] = np.inf  # Avoid division by zero
#                 fit_val[fit_data.Idx] = 1.0 / r1_vals
#                 fit_val[np.isinf(fit_val)] = 0  # Set infinite values to 0
#             else:
#                 fit_val[fit_data.Idx] = fit_data.P[1, :]  # Assume second parameter
#         elif param_name.upper() == 'R1':
#             if algorithm == 'T1_InvRecovery_3ParR1':
#                 fit_val[fit_data.Idx] = fit_data.P[iR1, :]
#             else:
#                 # For T2 data, R1 = 1/T2 if available
#                 t2_vals = fit_data.P[1, :]
#                 t2_vals[t2_vals == 0] = np.inf
#                 fit_val[fit_data.Idx] = 1.0 / t2_vals
#                 fit_val[np.isinf(fit_val)] = 0
#         elif param_name.upper() == 'MASK':
#             fit_val[fit_data.Idx[mask]] = 1
#             fit_val = fit_val.astype(bool)
#         elif param_name.upper() == 'ERROR':
#             if hasattr(fit_data, 'Perr'):
#                 fit_val[fit_data.Idx] = fit_data.Perr[2, :] / fit_data.P[iAMP, :]  # Normalized error
                
#         return fit_val.reshape(fit_data.Size)
    
#     def calculate_po2_from_fit_data(self, fit_data, po2_info=None):
#         """Calculate pO2 from fit data (Python implementation of MATLAB epr_T2_PO2)"""
#         if not hasattr(fit_data, 'P') or not hasattr(fit_data, 'Idx'):
#             return None
            
#         # Extract pO2 calibration parameters
#         if po2_info is not None and hasattr(po2_info, 'LLW_zero_po2'):
#             LLW_zero_po2 = float(po2_info.LLW_zero_po2)
#             Torr_per_mGauss = float(po2_info.Torr_per_mGauss)
#         else:
#             # Default pO2 calibration parameters
#             LLW_zero_po2 = 10.2      # mG at zero pO2
#             Torr_per_mGauss = 1.84   # torr per mG
#             print("   Using default pO2 calibration parameters")
        
#         # Get R1 values
#         r1_img = self.load_fit_parameters(fit_data, 'R1')
#         if r1_img is None:
#             return None
        
#         # Convert R1 to T2 and then to LLW
#         # For EPRI: T2 = 1/R1 (but we need to be careful about units)
#         # LLW = R2/pi/2/2.8*1000 where R2 = 1/T2
#         # So LLW = R1/pi/2/2.8*1000
        
#         # Initialize pO2 image
#         po2_img = np.zeros_like(r1_img)
        
#         # Find valid voxels (where fit was performed)
#         valid_mask = r1_img > 0
        
#         if np.sum(valid_mask) > 0:
#             # Convert R1 to LLW (linewidth in mGauss)
#             # LLW = R1 / (pi * 2 * 2.8) * 1000 
#             LLW = r1_img * 1000 / (np.pi * 2 * 2.8)  # Convert to mG
            
#             # Convert LLW to pO2
#             po2_img[valid_mask] = (LLW[valid_mask] - LLW_zero_po2) * Torr_per_mGauss
            
#             # Set negative pO2 values to 0
#             po2_img[po2_img < 0] = 0
        
#         return po2_img
    
#     def create_matlab_struct_array(self, data_dict):
#         """Create a MATLAB-style struct that scipy.io can save properly"""
#         import numpy as np
#         from scipy.io.matlab.mio5_utils import VarWriter5
        
#         # Create a structured array
#         dtype_list = []
#         for key in data_dict.keys():
#             if isinstance(data_dict[key], str):
#                 dtype_list.append((key, 'U20'))
#             elif isinstance(data_dict[key], (int, float)):
#                 dtype_list.append((key, 'f8'))
#             elif isinstance(data_dict[key], np.ndarray):
#                 dtype_list.append((key, 'O'))
#             else:
#                 dtype_list.append((key, 'O'))
        
#         # Create structured array
#         struct_array = np.empty(1, dtype=dtype_list)
#         for key, value in data_dict.items():
#             struct_array[key] = value
            
#         return struct_array[0]
    
#     def create_arbuz_image_struct(self, data, name, image_type='3DEPRI'):
#         """Create an ArbuzGUI-compatible image structure"""
#         identity = np.eye(4, dtype=np.float64)
        
#         if data.ndim == 4:
#             # For 4D data, we typically want the first time point for display
#             display_data = data[:, :, :, 0]
#         else:
#             display_data = data
            
#         # Create the image structure as a dictionary first
#         image_dict = {
#             'Name': str(name),
#             'ImageType': str(image_type),
#             'data': display_data.astype(np.float64),
#             'A': identity.copy(),
#             'Anative': identity.copy(), 
#             'Aprime': identity.copy(),
#             'box': np.array(display_data.shape[:3], dtype=np.float64),
#             'isLoaded': np.array([1], dtype=np.int32),
#             'isStore': np.array([1], dtype=np.int32),
#             'Selected': np.array([0], dtype=np.int32),
#             'Visible': np.array([0], dtype=np.int32),
#             'slaves': np.array([], dtype=object),
#             'FileName': '',
#             'pars': np.array([])
#         }
        
#         return image_dict
    
#     def create_arbuz_project(self, file_pairs, output_dir):
#         """Create a complete ArbuzGUI-compatible project file"""
#         print("🏗️  Creating ArbuzGUI project...")
        
#         # Limit to 12 files and assign names
#         if len(file_pairs) > 12:
#             file_pairs = file_pairs[:12]
            
#         images = []
        
#         # Process each file pair
#         for i, (raw_file, p_file) in enumerate(file_pairs):
#             try:
#                 print(f"   Processing {i+1:2d}/12: {Path(raw_file).name}")
                
#                 # Load raw data
#                 raw_mat = sio.loadmat(raw_file, struct_as_record=False, squeeze_me=True)
#                 p_mat = sio.loadmat(p_file, struct_as_record=False, squeeze_me=True)
                
#                 # Get 4D image data
#                 if 'mat_recFXD' in raw_mat:
#                     image_data = raw_mat['mat_recFXD']
#                 else:
#                     print(f"⚠️  Warning: No mat_recFXD in {raw_file}")
#                     continue
                
#                 # Create main image with assigned name
#                 image_name = self.image_names[i]
#                 main_image = self.create_arbuz_image_struct(image_data, image_name, '3DEPRI')
#                 images.append(main_image)
                
#                 # For the first image (BE1), also create BE_AMP from amplitude data
#                 if i == 0 and 'fit_data' in p_mat:
#                     try:
#                         amp_data = self.load_fit_parameters(p_mat['fit_data'], 'AMP')
#                         if amp_data is not None:
#                             amp_image = self.create_arbuz_image_struct(amp_data, 'BE_AMP', 'AMP_pEPRI')
#                             images.append(amp_image)
#                             print(f"   ✅ Created BE_AMP from amplitude data")
                            
#                             # Also create pO2 image from the same fit data
#                             po2_info = p_mat.get('pO2_info', None)
#                             po2_data = self.calculate_po2_from_fit_data(p_mat['fit_data'], po2_info)
#                             if po2_data is not None:
#                                 po2_image = self.create_arbuz_image_struct(po2_data, 'BE_pO2', 'PO2_pEPRI')
#                                 images.append(po2_image)
#                                 print(f"   ✅ Created BE_pO2 from fit data")
#                         else:
#                             print(f"   ⚠️  Could not extract amplitude data")
#                     except Exception as e:
#                         print(f"   ⚠️  Error creating BE_AMP/pO2: {e}")
                        
#             except Exception as e:
#                 print(f"❌ Error processing {raw_file}: {e}")
#                 continue
        
#         print(f"✅ Created {len(images)} images for project")
        
#         # Create project structure
#         project = {
#             'file_type': 'Reg_v2.0',
#             'images': np.array(images, dtype=object),
#             'transformations': np.array([], dtype=object),
#             'sequences': np.array([], dtype=object),
#             'groups': np.array([], dtype=object),
#             'activesequence': np.array([-1], dtype=np.int32),
#             'activetransformation': np.array([-1], dtype=np.int32),
#             'saves': np.array([], dtype=object),
#             'comments': 'Created by Python automation pipeline',
#             'status': np.array([])
#         }
        
#         # Save project
#         project_file = output_dir / "project.mat"
#         sio.savemat(project_file, project, do_compression=True)
#         print(f"✅ Project saved to {project_file}")
        
#         return str(project_file)
    
#     def apply_roi_with_enhanced_script(self, project_file):
#         """Apply ROI using the enhanced Draw_ROI script"""
#         print("🎯 Applying ROI annotation...")
        
#         try:
#             # Import the enhanced ROI processor
#             from enhanced_draw_roi import ProjectROIProcessor
            
#             # Create processor and apply ROI
#             processor = ProjectROIProcessor()
#             result = processor.process_project_file(project_file)
            
#             if result:
#                 print(f"✅ ROI applied successfully")
#                 return result
#             else:
#                 print(f"❌ ROI application failed")
#                 return None
                
#         except ImportError:
#             print("❌ enhanced_draw_roi.py not found. Please ensure it's in the same directory.")
#             return None
#         except Exception as e:
#             print(f"❌ Error applying ROI: {e}")
#             return None
    
#     def copy_roi_to_all_images(self, project_file):
#         """Copy kidney ROI from BE_AMP to all other images"""
#         print("📋 Copying ROI to all images...")
        
#         try:
#             project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
#             # Find BE_AMP and its ROI
#             source_roi = None
#             be_amp_found = False
            
#             for img in project['images']:
#                 if isinstance(img, dict):
#                     name = img.get('Name', '')
#                 elif hasattr(img, 'Name'):
#                     name = str(img.Name)
#                 else:
#                     continue
                    
#                 if 'BE_AMP' in name:
#                     be_amp_found = True
#                     slaves = img.get('slaves') if isinstance(img, dict) else getattr(img, 'slaves', np.array([]))
#                     if len(slaves) > 0:
#                         source_roi = slaves[0]
#                         break
            
#             if not be_amp_found:
#                 print("⚠️  BE_AMP image not found")
#                 return project_file
                
#             if source_roi is None:
#                 print("⚠️  No ROI found in BE_AMP image")
#                 return project_file
            
#             print("✅ Found ROI in BE_AMP image")
            
#             # Copy ROI to all other images
#             roi_count = 0
#             for img in project['images']:
#                 if isinstance(img, dict):
#                     name = img.get('Name', '')
#                 elif hasattr(img, 'Name'):
#                     name = str(img.Name)
#                 else:
#                     continue
                    
#                 if 'BE_AMP' not in name:
#                     # Create a copy of the ROI for this image
#                     if isinstance(source_roi, dict):
#                         roi_copy = source_roi.copy()
#                     else:
#                         roi_copy = {
#                             'data': source_roi.data.copy() if hasattr(source_roi, 'data') else source_roi['data'].copy(),
#                             'ImageType': '3DMASK',
#                             'Name': 'Kidney',
#                             'A': np.eye(4, dtype=np.float64),
#                             'Anative': np.eye(4, dtype=np.float64),
#                             'Aprime': np.eye(4, dtype=np.float64),
#                             'isStore': 1,
#                             'isLoaded': 1,
#                             'Selected': 0,
#                             'Visible': 0,
#                             'box': source_roi.box.copy() if hasattr(source_roi, 'box') else source_roi['box'].copy(),
#                             'pars': np.array([]),
#                             'FileName': ''
#                         }
                    
#                     if isinstance(img, dict):
#                         img['slaves'] = np.array([roi_copy], dtype=object)
#                     else:
#                         img.slaves = np.array([roi_copy], dtype=object)
#                     roi_count += 1
            
#             print(f"✅ ROI copied to {roi_count} images")
            
#             # Save updated project
#             sio.savemat(project_file, project, do_compression=True)
            
#             return project_file
            
#         except Exception as e:
#             print(f"❌ Error copying ROI: {e}")
#             return None
    
#     def extract_statistics(self, project_file, output_dir):
#         """Extract statistics from all images with ROI masks"""
#         print("📊 Extracting statistics...")
        
#         try:
#             project = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
#             stats_data = []
#             images_array = project['images']
            
#             # Handle case where images might be a single object or array
#             if not hasattr(images_array, '__len__'):
#                 images_array = [images_array]
            
#             for img in images_array:
#                 # Handle both dict and object types
#                 if isinstance(img, dict):
#                     name = img.get('Name', 'Unknown')
#                     data = img.get('data')
#                     slaves = img.get('slaves', np.array([]))
#                 elif hasattr(img, 'Name'):
#                     name = str(img.Name)
#                     data = getattr(img, 'data', None)
#                     slaves = getattr(img, 'slaves', np.array([]))
#                 else:
#                     continue
                
#                 if data is None:
#                     continue
                
#                 # Ensure slaves is iterable
#                 if not hasattr(slaves, '__len__'):
#                     slaves = [slaves] if slaves is not None else []
                
#                 # Get ROI mask if available
#                 mask = None
#                 if len(slaves) > 0:
#                     for slave in slaves:
#                         if slave is None:
#                             continue
#                         slave_type = slave.get('ImageType') if isinstance(slave, dict) else getattr(slave, 'ImageType', '')
#                         if '3DMASK' in str(slave_type):
#                             mask_data = slave.get('data') if isinstance(slave, dict) else getattr(slave, 'data', None)
#                             if mask_data is not None:
#                                 mask = mask_data.astype(bool)
#                                 break
                
#                 if mask is not None:
#                     # Extract ROI data
#                     roi_data = data[mask]
                    
#                     if len(roi_data) > 0:
#                         # Calculate statistics
#                         stats = {
#                             'Image': str(name),
#                             'Mean': float(np.mean(roi_data)),
#                             'Median': float(np.median(roi_data)),
#                             'Std': float(np.std(roi_data)),
#                             'N_Voxels': int(len(roi_data))
#                         }
#                         stats_data.append(stats)
#                         print(f"   ✅ {name}: {len(roi_data)} voxels")
#                     else:
#                         print(f"   ⚠️  {name}: Empty ROI")
#                 else:
#                     print(f"   ⚠️  {name}: No ROI found")
            
#             # Save statistics
#             if PANDAS_AVAILABLE:
#                 # Use pandas if available
#                 df = pd.DataFrame(stats_data)
#                 excel_file = output_dir / "roi_statistics.xlsx"
#                 df.to_excel(excel_file, index=False)
#                 stats_file = str(excel_file)
#                 print(f"✅ Statistics saved to {excel_file}")
#                 print("\n📈 Summary statistics:")
#                 print(df.to_string(index=False))
#             else:
#                 # Save as CSV using basic numpy/built-in functions
#                 csv_file = output_dir / "roi_statistics.csv"
#                 with open(csv_file, 'w') as f:
#                     # Write header
#                     f.write("Image,Mean,Median,Std,N_Voxels\n")
#                     # Write data
#                     for stats in stats_data:
#                         f.write(f"{stats['Image']},{stats['Mean']:.6f},{stats['Median']:.6f},"
#                                f"{stats['Std']:.6f},{stats['N_Voxels']}\n")
#                 stats_file = str(csv_file)
#                 print(f"✅ Statistics saved to {csv_file}")
#                 print("\n📈 Summary statistics:")
#                 for stats in stats_data:
#                     print(f"{stats['Image']:>8s}: Mean={stats['Mean']:8.2f}, "
#                           f"Median={stats['Median']:8.2f}, Std={stats['Std']:8.2f}, "
#                           f"N={stats['N_Voxels']:5d}")
            
#             return stats_file
            
#         except Exception as e:
#             print(f"❌ Error extracting statistics: {e}")
#             import traceback
#             traceback.print_exc()
#             return None
    
#     def run_pipeline(self):
#         """Run the complete automation pipeline"""
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         output_dir = self.output_base / f"run_{timestamp}"
#         output_dir.mkdir(parents=True, exist_ok=True)
        
#         print(f"🚀 Starting simplified automation pipeline...")
#         print(f"📂 Output directory: {output_dir}")
        
#         try:
#             # Step 1: Find processed files
#             file_pairs = self.find_processed_files()
#             if len(file_pairs) == 0:
#                 raise ValueError("No processed .mat file pairs found")
            
#             # Step 2: Create ArbuzGUI project
#             project_file = self.create_arbuz_project(file_pairs, output_dir)
            
#             # Step 3: Apply ROI annotation
#             project_file = self.apply_roi_with_enhanced_script(project_file)
#             if not project_file:
#                 print("⚠️  ROI annotation failed, continuing without ROI...")
#                 project_file = output_dir / "project.mat"
            
#             # Step 4: Copy ROI to all images
#             project_file = self.copy_roi_to_all_images(project_file)
#             if not project_file:
#                 raise ValueError("ROI copying failed")
            
#             # Step 5: Extract statistics
#             stats_file = self.extract_statistics(project_file, output_dir)
            
#             print(f"\n🎉 Pipeline completed successfully!")
#             print(f"📁 Results saved in: {output_dir}")
#             print(f"📄 Project file: {project_file}")
#             if stats_file:
#                 print(f"📊 Statistics file: {stats_file}")
                
#             return output_dir
            
#         except Exception as e:
#             print(f"❌ Pipeline failed: {e}")
#             return None

# def main():
#     """Main entry point"""
#     print("🔬 Simple EPRI Automation Pipeline")
#     print("=" * 50)
    
#     # Create and run pipeline
#     pipeline = SimpleEPRIAutomation()
#     result = pipeline.run_pipeline()
    
#     if result:
#         print(f"\n✅ Pipeline completed. Results in: {result}")
#     else:
#         print("\n❌ Pipeline failed. Check the errors above.")

# if __name__ == "__main__":
#     main()
