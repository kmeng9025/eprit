#!/usr/bin/env python3
"""
Investigate what data should go into BE1-AE4 images
"""

import scipy.io as sio
import numpy as np
from pathlib import Path

# Load first few processed files to understand what data is available
data_dir = Path("../DATA/241202")
files_to_check = [
    "p8475image4D_18x18_0p75gcm_file.mat",  # First file
    "p8482image4D_18x18_0p75gcm_file.mat",  # Second file
]

for i, filename in enumerate(files_to_check):
    print(f"\n{'='*60}")
    print(f"🔍 Examining file {i+1}: {filename}")
    
    p_file = data_dir / filename
    if not p_file.exists():
        print(f"❌ File not found: {p_file}")
        continue
        
    p_mat = sio.loadmat(str(p_file), struct_as_record=False, squeeze_me=True)
    
    print(f"📋 Keys in file:")
    for key in p_mat.keys():
        if not key.startswith('__'):
            print(f"   {key}: {type(p_mat[key])}")
    
    # Check if we have fit_data with pO2 calculation capability
    if 'fit_data' in p_mat:
        fit_data = p_mat['fit_data']
        po2_info = p_mat.get('pO2_info', {})
        
        # Convert po2_info to dict if it's a MATLAB struct
        if hasattr(po2_info, '_fieldnames'):
            po2_dict = {}
            for field in po2_info._fieldnames:
                po2_dict[field] = getattr(po2_info, field)
            po2_info = po2_dict
            
        print(f"\n🔬 Fit data algorithm: {getattr(fit_data, 'Algorithm', 'Unknown')}")
        print(f"🩸 pO2 calibration info:")
        for key, val in po2_info.items():
            print(f"   {key}: {val}")
        
        # Try to calculate pO2 for this file
        if hasattr(fit_data, 'P') and hasattr(fit_data, 'Idx'):
            # Extract parameters
            amp_data = np.zeros(np.prod(fit_data.Size))
            r1_data = np.zeros(np.prod(fit_data.Size))
            mask = fit_data.FitMask
            
            amp_data[fit_data.Idx] = fit_data.P[0, :]  # Amplitude
            r1_data[fit_data.Idx] = fit_data.P[1, :]   # R1
            
            amp_data = amp_data.reshape(fit_data.Size)
            r1_data = r1_data.reshape(fit_data.Size)
            
            # Calculate pO2 following MATLAB logic
            t2_data = np.zeros_like(r1_data)
            t2_data[mask] = 1.0 / r1_data[mask] if np.any(mask) else 0
            
            # Convert to LLW
            llw_data = np.zeros_like(t2_data)
            llw_data[mask] = (1.0 / t2_data[mask]) / np.pi / 2 / 2.802 * 1000
            
            # Calculate pO2
            llw_zero_po2 = po2_info.get('LLW_zero_po2', 10.2)
            torr_per_mgauss = po2_info.get('Torr_per_mGauss', 1.84)
            po2_data = (llw_data - llw_zero_po2) * torr_per_mgauss
            
            print(f"\n📊 Calculated data ranges:")
            print(f"   Amplitude: [{np.min(amp_data):.3f}, {np.max(amp_data):.3f}], Mean: {np.mean(amp_data):.3f}")
            print(f"   pO2: [{np.min(po2_data):.3f}, {np.max(po2_data):.3f}], Mean: {np.mean(po2_data):.3f}")
            
            # Check against reference
            if i == 0:  # First file should match BE_AMP and BE1
                print(f"\n🎯 Reference comparison (BE_AMP):")
                print(f"   Reference BE_AMP range: [0.000, 10.552], Mean: 0.075")
                print(f"   Our calculated range: [{np.min(amp_data):.3f}, {np.max(amp_data):.3f}], Mean: {np.mean(amp_data):.3f}")
                
                print(f"\n🎯 Reference comparison (BE1 pO2):")
                print(f"   Reference BE1 range: [-100.000, 255.145], Mean: -92.713")
                print(f"   Our calculated range: [{np.min(po2_data):.3f}, {np.max(po2_data):.3f}], Mean: {np.mean(po2_data):.3f}")

print(f"\n{'='*60}")
print(f"🎯 CONCLUSION:")
print(f"   BE_AMP = Amplitude data from first file")
print(f"   BE1-AE4 = pO2 data calculated from each respective file")
print(f"   All BE1-AE4 should be PO2_pEPRI type, not 3DEPRI!")
