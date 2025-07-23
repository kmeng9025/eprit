"""
Final Corrected Processing Pipeline
Implementing EXACT MATLAB corrections based on complete epr_LoadMATFile.m analysis

Key corrections needed:
1. Proper tau_correction calculation
2. Correct pO2_info parameter extraction from MATLAB files
3. Exact amplitude normalization by amp1mM
4. Proper pO2 calculation with correct calibration parameters
"""

import scipy.io as sio
import numpy as np
import os
from pathlib import Path

def load_matlab_pO2_info(mat_file_path):
    """
    Load pO2_info from the original MATLAB processed file
    """
    try:
        data = sio.loadmat(mat_file_path, struct_as_record=False, squeeze_me=True)
        
        # Look for pO2_info in the data
        if 'pO2_info' in data:
            pO2_info_struct = data['pO2_info']
            
            # Convert MATLAB struct to Python dict
            pO2_info = {}
            if hasattr(pO2_info_struct, '_fieldnames'):
                for field in pO2_info_struct._fieldnames:
                    pO2_info[field] = getattr(pO2_info_struct, field)
            
            return pO2_info
        
        # If not at top level, look in nested structures
        for key, value in data.items():
            if hasattr(value, '_fieldnames') and 'pO2_info' in value._fieldnames:
                pO2_info_struct = getattr(value, 'pO2_info')
                pO2_info = {}
                if hasattr(pO2_info_struct, '_fieldnames'):
                    for field in pO2_info_struct._fieldnames:
                        pO2_info[field] = getattr(pO2_info_struct, field)
                return pO2_info
        
        # Default values if not found
        return {
            'LLW_zero_po2': 10.2,
            'Torr_per_mGauss': 1.84,
            'mG_per_mM': 0,
            'MDNmG_per_mM': 0,
            'amp1mM': 1.0,
            'Q': 15,
            'Qcb': 15
        }
        
    except Exception as e:
        print(f"Error loading pO2_info from {mat_file_path}: {e}")
        # Return default values
        return {
            'LLW_zero_po2': 10.2,
            'Torr_per_mGauss': 1.84,
            'mG_per_mM': 0,
            'MDNmG_per_mM': 0,
            'amp1mM': 1.0,
            'Q': 15,
            'Qcb': 15
        }

def extract_fit_parameters_exact(mat_file_path):
    """
    Extract fit parameters using exact MATLAB LoadFitPars logic
    """
    print(f"Loading fit parameters from: {mat_file_path}")
    
    try:
        data = sio.loadmat(mat_file_path, struct_as_record=False, squeeze_me=True)
        
        if 'fit_data' not in data:
            print("No fit_data found")
            return None, None, None, None
        
        fit_data = data['fit_data']
        algorithm = getattr(fit_data, 'Algorithm', 'Unknown')
        
        print(f"Algorithm: {algorithm}")
        
        if algorithm != 'T1_InvRecovery_3ParR1':
            print(f"Unsupported algorithm: {algorithm}")
            return None, None, None, None
        
        # Extract parameters using exact MATLAB logic
        P = fit_data.P
        Idx = fit_data.Idx.flatten() - 1  # Convert to 0-based
        Size = fit_data.Size.flatten()
        FitMask = fit_data.FitMask.flatten()
        
        # Initialize arrays
        total_pixels = int(np.prod(Size))
        amp_flat = np.zeros(total_pixels)
        t1_flat = np.zeros(total_pixels)
        mask_flat = np.zeros(total_pixels, dtype=bool)
        
        # T1_InvRecovery_3ParR1: iAMP=0, iR1=1, iINV=2, iERR=3
        amp_flat[Idx] = P[0, :]  # Amplitude
        
        # T1 = 1./R1, with inf handling
        R1_values = P[1, :]
        T1_values = np.zeros_like(R1_values)
        valid_R1 = R1_values != 0
        T1_values[valid_R1] = 1.0 / R1_values[valid_R1]
        t1_flat[Idx] = T1_values
        
        # Mask
        mask_combined = FitMask
        if hasattr(fit_data, 'Mask') and fit_data.Mask.size > 0:
            mask_combined = mask_combined & fit_data.Mask.flatten()
        
        mask_flat[Idx[mask_combined]] = True
        
        # Reshape
        amp_image = amp_flat.reshape(Size)
        t1_image = t1_flat.reshape(Size)
        mask_image = mask_flat.reshape(Size)
        
        # Load pO2_info
        pO2_info = load_matlab_pO2_info(mat_file_path)
        
        print(f"Extracted parameters:")
        print(f"  Amplitude range: {np.min(amp_image[mask_image]):.6f} to {np.max(amp_image[mask_image]):.6f}")
        print(f"  T1 range: {np.min(t1_image[mask_image]):.6f} to {np.max(t1_image[mask_image]):.6f}")
        print(f"  Valid pixels: {np.sum(mask_image)}")
        print(f"  pO2_info keys: {list(pO2_info.keys())}")
        
        return amp_image, t1_image, mask_image, pO2_info
        
    except Exception as e:
        print(f"Error extracting parameters: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None, None

def apply_exact_matlab_corrections(amp_image, t1_image, mask_image, pO2_info):
    """
    Apply exact MATLAB corrections from epr_LoadMATFile.m lines 854-880
    """
    print("\n=== Applying Exact MATLAB Corrections ===")
    
    # Step 1: Calculate tau_correction exactly as in MATLAB
    # tau_correction = exp(2*630e-3*median(1./T1(Image.Mask(:))));
    valid_t1 = t1_image[mask_image]
    valid_t1 = valid_t1[valid_t1 > 0]
    
    if len(valid_t1) > 0:
        median_1_over_t1 = np.median(1.0 / valid_t1)
        tau_correction = np.exp(2 * 630e-3 * median_1_over_t1)
        print(f"Median 1/T1: {median_1_over_t1:.6f}")
        print(f"Tau correction: {tau_correction:.6f}")
    else:
        tau_correction = 1.0
        print("Warning: No valid T1 values for tau correction")
    
    # Step 2: Q correction (set to 1 in current MATLAB)
    Q_correction = 1.0
    print(f"Q correction: {Q_correction:.6f}")
    
    # Step 3: Apply corrections to amplitude
    # Image.Amp = Image.Amp * Q_correction .* tau_correction;
    corrected_amp = amp_image * Q_correction * tau_correction
    print(f"After corrections - Amplitude range: {np.min(corrected_amp[mask_image]):.6f} to {np.max(corrected_amp[mask_image]):.6f}")
    
    return corrected_amp, tau_correction, Q_correction

def calculate_exact_pO2(t1_image, corrected_amp, mask_image, pO2_info):
    """
    Calculate pO2 using exact MATLAB logic: epr_T2_PO2 -> epr_LLW_PO2
    """
    print("\n=== Calculating pO2 (Exact MATLAB Logic) ===")
    
    # Step 1: Calculate R2 from T1 (epr_T2_PO2.m)
    R2 = np.zeros_like(t1_image)
    valid_mask = mask_image & (t1_image > 0)
    R2[valid_mask] = 1.0 / t1_image[valid_mask]
    
    # Step 2: Convert R2 to LLW (epr_T2_PO2.m)
    # LLW = R2/pi/2/2.802*1000; % in mG
    LLW = R2 / np.pi / 2 / 2.802 * 1000
    print(f"LLW range: {np.min(LLW[valid_mask]):.6f} to {np.max(LLW[valid_mask]):.6f} mG")
    
    # Step 3: Get pO2_info parameters with defaults (epr_LLW_PO2.m)
    LLW_zero_po2 = pO2_info.get('LLW_zero_po2', 10.2)
    Torr_per_mGauss = pO2_info.get('Torr_per_mGauss', 1.84)
    mG_per_mM = pO2_info.get('mG_per_mM', 0)
    MDNmG_per_mM = pO2_info.get('MDNmG_per_mM', 0)
    amp1mM = pO2_info.get('amp1mM', np.mean(corrected_amp[valid_mask]) if np.sum(valid_mask) > 0 else 1.0)
    
    print(f"pO2 calculation parameters:")
    print(f"  LLW_zero_po2: {LLW_zero_po2:.2f} mG")
    print(f"  Torr_per_mGauss: {Torr_per_mGauss:.2f} torr/mG")
    print(f"  mG_per_mM: {mG_per_mM:.2f} mG/mM")
    print(f"  amp1mM: {amp1mM:.6f}")
    
    # Step 4: Calculate pO2 (epr_LLW_PO2.m)
    pO2 = np.zeros_like(LLW)
    
    if np.sum(valid_mask) > 0:
        # Calculate median amplitude for correction
        ampAvg = np.median(corrected_amp[valid_mask]) / amp1mM
        
        # Apply full pO2 calculation
        # pO2(mask) = (LLW(mask) - LLW_zero_po2 - Amp(mask)/amp1mM*mG_per_mM - ampAvg*MDNmG_per_mM) * Torr_per_mGauss;
        pO2[valid_mask] = (LLW[valid_mask] - LLW_zero_po2 
                          - corrected_amp[valid_mask]/amp1mM * mG_per_mM 
                          - ampAvg * MDNmG_per_mM) * Torr_per_mGauss
        
        print(f"ampAvg: {ampAvg:.6f}")
        print(f"pO2 range: {np.min(pO2[valid_mask]):.2f} to {np.max(pO2[valid_mask]):.2f} torr")
    
    return pO2, amp1mM

def normalize_amplitude_exact(corrected_amp, amp1mM):
    """
    Final amplitude normalization exactly as in MATLAB
    Image.Amp = Image.Amp / s1.pO2_info.amp1mM;
    """
    normalized_amp = corrected_amp / amp1mM
    print(f"\n=== Final Amplitude Normalization ===")
    print(f"amp1mM: {amp1mM:.6f}")
    print(f"Final amplitude range: {np.min(normalized_amp):.6f} to {np.max(normalized_amp):.6f}")
    
    return normalized_amp

def process_single_file_exact(mat_file_path):
    """
    Process a single .mat file with exact MATLAB logic
    """
    print(f"\n{'='*80}")
    print(f"Processing: {mat_file_path}")
    print(f"{'='*80}")
    
    # Extract fit parameters
    amp_image, t1_image, mask_image, pO2_info = extract_fit_parameters_exact(mat_file_path)
    
    if amp_image is None:
        return None, None
    
    # Apply exact MATLAB corrections
    corrected_amp, tau_correction, Q_correction = apply_exact_matlab_corrections(
        amp_image, t1_image, mask_image, pO2_info)
    
    # Calculate pO2 with exact MATLAB logic
    pO2_image, amp1mM = calculate_exact_pO2(t1_image, corrected_amp, mask_image, pO2_info)
    
    # Final amplitude normalization
    final_amp = normalize_amplitude_exact(corrected_amp, amp1mM)
    
    return final_amp, pO2_image

def main():
    """
    Main function: Process files with exact MATLAB corrections
    """
    print("EXACT MATLAB Processing Pipeline")
    print("="*80)
    
    # Use the actual .mat files we found with fit_data
    source_files = [
        r"DATA\241202\p8475image4D_18x18_0p75gcm_file.mat",
        r"DATA\241202\p8482image4D_18x18_0p75gcm_file.mat",
        r"DATA\241202\p8488image4D_18x18_0p75gcm_file.mat",
        r"DATA\241202\p8495image4D_18x18_0p75gcm_file.mat",
        r"DATA\241202\p8507image4D_18x18_0p75gcm_file.mat",
        r"DATA\241202\p8514image4D_18x18_0p75gcm_file.mat",
        r"DATA\241202\p8521image4D_18x18_0p75gcm_file.mat"
    ]
    
    # Convert to absolute paths
    base_dir = r"c:\Users\ftmen\Documents\v3"
    source_files = [os.path.join(base_dir, f) for f in source_files]
    
    print(f"Processing {len(source_files)} source files with fit_data")
    
    processed_images = []
    
    for i, mat_file in enumerate(source_files[:7]):  # Process first 7 to get 13+ images
        print(f"\nProcessing file {i+1}/{min(7, len(source_files))}")
        
        amp_image, pO2_image = process_single_file_exact(mat_file)
        
        if amp_image is not None:
            # Create image entries
            base_name = Path(mat_file).stem
            
            # Amplitude image
            amp_entry = {
                'name': f"{base_name}_AMP",
                'type': 'AMP_pEPRI',
                'source_file': mat_file,
                'mat_image': amp_image
            }
            processed_images.append(amp_entry)
            
            # pO2 image
            pO2_entry = {
                'name': f"{base_name}_PO2",
                'type': 'PO2_pEPRI',
                'source_file': mat_file,
                'mat_image': pO2_image
            }
            processed_images.append(pO2_entry)
    
    print(f"\n{'='*80}")
    print(f"EXACT MATLAB Processing Complete!")
    print(f"Processed images: {len(processed_images)}")
    print(f"{'='*80}")
    
    return processed_images

if __name__ == "__main__":
    main()
