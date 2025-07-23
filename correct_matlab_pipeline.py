"""
MATLAB-Exact Image Processing Pipeline
Based on deep analysis of ProcessGUI.m, ArbuzGUI.m, and epr_LoadMATFile.m

Key discoveries from MATLAB code analysis:
1. T1_InvRecovery_3ParR1 algorithm: Uses R1 (not T1) for processing
2. Tau correction: exp(2*630e-3*median(1./T1(mask))) for T1_InvRecovery
3. Q correction: Currently set to 1 in MATLAB
4. pO2 calculation: Uses epr_T2_PO2 -> epr_LLW_PO2 chain
5. Amplitude normalization: Divided by pO2_info.amp1mM after corrections
6. LoadFitPars: T1_InvRecovery_3ParR1 case uses T1 = 1./R1 conversion
"""

import matlab
import matlab.engine
import numpy as np
import os
import scipy.io as sio
from pathlib import Path

def extract_matlab_processing_exact(fit_data, pO2_info, algorithm):
    """
    Exact replication of epr_LoadMATFile.m processing for T1_InvRecovery_3ParR1
    """
    print(f"\n=== MATLAB-Exact Processing for {algorithm} ===")
    
    # Extract fitting parameters using exact MATLAB logic
    if 'P' not in fit_data or fit_data['P'].size == 0:
        print("No fit results found!")
        return None, None, None
        
    # T1_InvRecovery_3ParR1 case: iAMP=1, iR1=2, iINV=3, iERR=4
    if algorithm == 'T1_InvRecovery_3ParR1':
        print("Processing T1_InvRecovery_3ParR1 algorithm")
        
        # Extract parameters from fit_data.P
        P = fit_data['P']  # Parameter matrix
        Idx = fit_data['Idx'].flatten() - 1  # Convert MATLAB 1-based to Python 0-based
        Size = fit_data['Size'].flatten()
        FitMask = fit_data['FitMask'].flatten()
        
        print(f"P shape: {P.shape}")
        print(f"Idx length: {len(Idx)}")
        print(f"Image size: {Size}")
        print(f"FitMask sum: {np.sum(FitMask)}")
        
        # Initialize output arrays
        total_pixels = int(np.prod(Size))
        amp_flat = np.zeros(total_pixels)
        t1_flat = np.zeros(total_pixels)
        mask_flat = np.zeros(total_pixels, dtype=bool)
        
        # Extract parameters according to LoadFitPars.m T1_InvRecovery_3ParR1 case
        iAMP = 0  # Python 0-based indexing
        iR1 = 1
        
        # Load amplitude: fit_val(mat_fit.Idx) = mat_fit.P(iAMP,:)
        amp_flat[Idx] = P[iAMP, :]
        
        # Load T1: fit_val(mat_fit.Idx) = 1./mat_fit.P(iR1,:)
        R1_values = P[iR1, :]
        T1_values = np.zeros_like(R1_values)
        valid_R1 = R1_values != 0
        T1_values[valid_R1] = 1.0 / R1_values[valid_R1]
        t1_flat[Idx] = T1_values
        
        # Create mask: combine FitMask with any additional mask
        mask_combined = FitMask
        if 'Mask' in fit_data and fit_data['Mask'].size > 0:
            mask_combined = mask_combined & fit_data['Mask'].flatten()
        
        mask_flat[Idx[mask_combined]] = True
        
        # Reshape to image dimensions
        amp_image = amp_flat.reshape(Size)
        t1_image = t1_flat.reshape(Size)
        mask_image = mask_flat.reshape(Size)
        
        print(f"Amplitude range: {np.min(amp_image[mask_image]):.6f} to {np.max(amp_image[mask_image]):.6f}")
        print(f"T1 range: {np.min(t1_image[mask_image]):.6f} to {np.max(t1_image[mask_image]):.6f}")
        print(f"Mask pixels: {np.sum(mask_image)}")
        
        return amp_image, t1_image, mask_image
    
    else:
        print(f"Algorithm {algorithm} not implemented yet")
        return None, None, None

def apply_matlab_corrections_exact(amp_image, t1_image, mask_image, pO2_info):
    """
    Apply exact MATLAB corrections from epr_LoadMATFile.m T1_InvRecovery cases
    """
    print("\n=== Applying MATLAB-Exact Corrections ===")
    
    # Step 1: Tau correction (exact from MATLAB)
    # tau_correction = exp(2*630e-3*median(1./T1(Image.Mask(:))));
    valid_t1 = t1_image[mask_image]
    valid_t1 = valid_t1[valid_t1 > 0]  # Remove zeros
    
    if len(valid_t1) > 0:
        median_1_over_t1 = np.median(1.0 / valid_t1)
        tau_correction = np.exp(2 * 630e-3 * median_1_over_t1)
        print(f"Median 1/T1: {median_1_over_t1:.6f}")
        print(f"Tau correction: {tau_correction:.6f}")
    else:
        tau_correction = 1.0
        print("Warning: No valid T1 values for tau correction")
    
    # Step 2: Q correction (set to 1 in current MATLAB code)
    # Q_correction = sqrt(s1.pO2_info.Qcb/s1.pO2_info.Q);
    # Q_correction = 1; % Currently hardcoded to 1
    Q_correction = 1.0
    print(f"Q correction: {Q_correction:.6f}")
    
    # Step 3: Apply corrections to amplitude
    # Image.Amp = Image.Amp * Q_correction .* tau_correction;
    corrected_amp = amp_image * Q_correction * tau_correction
    print(f"Corrected amplitude range: {np.min(corrected_amp[mask_image]):.6f} to {np.max(corrected_amp[mask_image]):.6f}")
    
    return corrected_amp, tau_correction, Q_correction

def calculate_pO2_exact(t1_image, corrected_amp, mask_image, pO2_info):
    """
    Calculate pO2 using exact MATLAB logic: epr_T2_PO2 -> epr_LLW_PO2
    """
    print("\n=== Calculating pO2 (MATLAB-Exact) ===")
    
    # Step 1: Convert T1 to R2 (from epr_T2_PO2.m)
    # R2 = zeros(size(T2)); R2(mask) = 1.0 ./ T2(mask);
    R2 = np.zeros_like(t1_image)
    valid_mask = mask_image & (t1_image > 0)
    R2[valid_mask] = 1.0 / t1_image[valid_mask]
    
    # Step 2: Convert R2 to LLW (from epr_T2_PO2.m)
    # LLW = R2/pi/2/2.802*1000; % in mG
    LLW = R2 / np.pi / 2 / 2.802 * 1000  # Convert to mG
    print(f"LLW range: {np.min(LLW[valid_mask]):.6f} to {np.max(LLW[valid_mask]):.6f} mG")
    
    # Step 3: Calculate pO2 from LLW (from epr_LLW_PO2.m)
    # Extract pO2_info parameters with MATLAB defaults
    LLW_zero_po2 = pO2_info.get('LLW_zero_po2', 10.2)
    Torr_per_mGauss = pO2_info.get('Torr_per_mGauss', 1.84)
    mG_per_mM = pO2_info.get('mG_per_mM', 0)
    MDNmG_per_mM = pO2_info.get('MDNmG_per_mM', 0)
    amp1mM = pO2_info.get('amp1mM', np.mean(corrected_amp[valid_mask]) if np.sum(valid_mask) > 0 else 1.0)
    
    print(f"pO2 parameters:")
    print(f"  LLW_zero_po2: {LLW_zero_po2:.2f} mG")
    print(f"  Torr_per_mGauss: {Torr_per_mGauss:.2f} torr/mG")
    print(f"  mG_per_mM: {mG_per_mM:.2f} mG/mM")
    print(f"  amp1mM: {amp1mM:.6f}")
    
    # Calculate pO2 with amplitude correction
    # pO2(mask) = (LLW(mask) - LLW_zero_po2 - Amp(mask)/amp1mM*mG_per_mM - ampAvg*MDNmG_per_mM) * Torr_per_mGauss;
    pO2 = np.zeros_like(LLW)
    
    if np.sum(valid_mask) > 0:
        ampAvg = np.median(corrected_amp[valid_mask]) / amp1mM
        
        pO2[valid_mask] = (LLW[valid_mask] - LLW_zero_po2 
                          - corrected_amp[valid_mask]/amp1mM * mG_per_mM 
                          - ampAvg * MDNmG_per_mM) * Torr_per_mGauss
        
        print(f"ampAvg: {ampAvg:.6f}")
        print(f"pO2 range: {np.min(pO2[valid_mask]):.2f} to {np.max(pO2[valid_mask]):.2f} torr")
    
    return pO2

def normalize_amplitude_exact(corrected_amp, pO2_info):
    """
    Final amplitude normalization exactly as in MATLAB
    """
    # Image.Amp = Image.Amp / s1.pO2_info.amp1mM;
    amp1mM = pO2_info.get('amp1mM', 1.0)
    normalized_amp = corrected_amp / amp1mM
    
    print(f"\n=== Final Amplitude Normalization ===")
    print(f"amp1mM: {amp1mM:.6f}")
    print(f"Final amplitude range: {np.min(normalized_amp):.6f} to {np.max(normalized_amp):.6f}")
    
    return normalized_amp

def process_mat_file_exact(mat_file_path, output_dir):
    """
    Process a single .mat file using exact MATLAB processing logic
    """
    print(f"\n{'='*60}")
    print(f"Processing: {mat_file_path}")
    print(f"{'='*60}")
    
    try:
        # Load the .mat file
        data = sio.loadmat(mat_file_path, struct_as_record=False, squeeze_me=True)
        
        # Extract main data structure
        if 'fit_data' in data:
            fit_data = data['fit_data']
            pO2_info = data.get('pO2_info', {})
            
            # Convert MATLAB struct to dict if needed
            if hasattr(fit_data, '_fieldnames'):
                fit_dict = {}
                for field in fit_data._fieldnames:
                    fit_dict[field] = getattr(fit_data, field)
                fit_data = fit_dict
            
            if hasattr(pO2_info, '_fieldnames'):
                pO2_dict = {}
                for field in pO2_info._fieldnames:
                    pO2_dict[field] = getattr(pO2_info, field)
                pO2_info = pO2_dict
            
            # Get algorithm
            algorithm = fit_data.get('Algorithm', 'Unknown')
            print(f"Algorithm: {algorithm}")
            
            # Extract fitting parameters using exact MATLAB logic
            amp_image, t1_image, mask_image = extract_matlab_processing_exact(fit_data, pO2_info, algorithm)
            
            if amp_image is not None:
                # Apply exact MATLAB corrections
                corrected_amp, tau_correction, Q_correction = apply_matlab_corrections_exact(
                    amp_image, t1_image, mask_image, pO2_info)
                
                # Calculate pO2 using exact MATLAB logic
                pO2_image = calculate_pO2_exact(t1_image, corrected_amp, mask_image, pO2_info)
                
                # Final amplitude normalization
                final_amp = normalize_amplitude_exact(corrected_amp, pO2_info)
                
                # Create output structure
                base_name = Path(mat_file_path).stem
                
                # Save amplitude image
                amp_output = {
                    'mat_image': final_amp,
                    'Size': fit_data['Size'],
                    'Mask': mask_image,
                    'Type': 'AMP_pEPRI',
                    'Dim4Type': 'Inversion',
                    'pO2_info': pO2_info,
                    'corrections': {
                        'tau_correction': tau_correction,
                        'Q_correction': Q_correction,
                        'amp1mM': pO2_info.get('amp1mM', 1.0)
                    }
                }
                amp_file = os.path.join(output_dir, f"{base_name}_AMP.mat")
                sio.savemat(amp_file, amp_output)
                print(f"Saved amplitude: {amp_file}")
                
                # Save pO2 image
                pO2_output = {
                    'mat_image': pO2_image,
                    'Size': fit_data['Size'],
                    'Mask': mask_image,
                    'Type': 'PO2_pEPRI',
                    'Dim4Type': 'Inversion',
                    'pO2_info': pO2_info
                }
                pO2_file = os.path.join(output_dir, f"{base_name}_PO2.mat")
                sio.savemat(pO2_file, pO2_output)
                print(f"Saved pO2: {pO2_file}")
                
                return amp_file, pO2_file
                
        else:
            print("No fit_data found in .mat file")
            return None, None
            
    except Exception as e:
        print(f"Error processing {mat_file_path}: {e}")
        import traceback
        traceback.print_exc()
        return None, None

def main():
    """
    Main processing function using exact MATLAB logic
    """
    base_dir = r"c:\Users\ftmen\Documents\v3"
    output_dir = os.path.join(base_dir, "exact_matlab_outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all _fit.mat files
    fit_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith('_fit.mat'):
                fit_files.append(os.path.join(root, file))
    
    print(f"Found {len(fit_files)} _fit.mat files")
    
    processed_files = []
    for fit_file in fit_files[:3]:  # Process first 3 for testing
        print(f"\nProcessing: {fit_file}")
        amp_file, pO2_file = process_mat_file_exact(fit_file, output_dir)
        if amp_file and pO2_file:
            processed_files.extend([amp_file, pO2_file])
    
    print(f"\n{'='*60}")
    print(f"MATLAB-Exact Processing Complete!")
    print(f"Total files processed: {len(processed_files)}")
    print(f"Output directory: {output_dir}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
