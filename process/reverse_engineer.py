#!/usr/bin/env python3
"""
Try to reverse engineer the correct pO2 calculation from reference project
"""

import scipy.io as sio
import numpy as np
from pathlib import Path

# Load the reference project to see the correct data
ref_project = sio.loadmat("exampleCorrect/correctExample.mat", struct_as_record=False, squeeze_me=True)

if 'images' in ref_project:
    images = ref_project['images']
    
    # Find BE_AMP and BE1 in reference
    be_amp_ref = None
    be1_ref = None
    
    for img in images:
        if hasattr(img, 'Name'):
            name = str(img.Name)
            if 'BE_AMP' in name:
                be_amp_ref = img
                print(f"📋 Found reference BE_AMP:")
                print(f"   Shape: {img.data.shape}")
                print(f"   Range: [{np.min(img.data):.3f}, {np.max(img.data):.3f}]")
                print(f"   Mean: {np.mean(img.data):.3f}")
                print(f"   Non-zero voxels: {np.count_nonzero(img.data)}")
            elif 'BE1' in name:
                be1_ref = img
                print(f"📋 Found reference BE1:")
                print(f"   Shape: {img.data.shape}")
                print(f"   Range: [{np.min(img.data):.3f}, {np.max(img.data):.3f}]")
                print(f"   Mean: {np.mean(img.data):.3f}")
                print(f"   Non-zero voxels: {np.count_nonzero(img.data)}")
                
                # Look at the actual distribution
                data = img.data
                mask = data != -100  # Assuming -100 is background
                if np.any(mask):
                    print(f"   Foreground range: [{np.min(data[mask]):.3f}, {np.max(data[mask]):.3f}]")
                    print(f"   Foreground mean: {np.mean(data[mask]):.3f}")

# Now let's examine how MATLAB actually loads these images by looking at epr_LoadMATFile
# with the T1_InvRecovery_3ParR1 algorithm

print(f"\n{'='*60}")
print(f"🔬 Examining MATLAB loading logic for T1_InvRecovery_3ParR1...")

# Load our source data
data_dir = Path("../DATA/241202")
p_file = data_dir / "p8475image4D_18x18_0p75gcm_file.mat"
p_mat = sio.loadmat(str(p_file), struct_as_record=False, squeeze_me=True)

fit_data = p_mat['fit_data']
po2_info = p_mat['pO2_info']

# Convert po2_info to dict
if hasattr(po2_info, '_fieldnames'):
    po2_dict = {}
    for field in po2_info._fieldnames:
        po2_dict[field] = getattr(po2_info, field)
    po2_info = po2_dict

print(f"🧮 Algorithm: {getattr(fit_data, 'Algorithm', 'Unknown')}")
print(f"📊 Fit data shapes:")
print(f"   P: {fit_data.P.shape}")
print(f"   Idx: {fit_data.Idx.shape}")
print(f"   Size: {fit_data.Size}")

# Following the MATLAB epr_LoadMATFile.m logic for T1_InvRecovery_3ParR1
print(f"\n🔄 Applying MATLAB logic:")

# Extract parameters using LoadFitPars logic
amp_3d = np.zeros(np.prod(fit_data.Size))
t1_3d = np.zeros(np.prod(fit_data.Size))
mask_3d = np.zeros(np.prod(fit_data.Size), dtype=bool)

# Parameters for T1_InvRecovery_3ParR1: [Amp, R1, Inv]
amp_3d[fit_data.Idx] = fit_data.P[0, :]  # Amplitude
r1_values = fit_data.P[1, :]             # R1 values
t1_3d[fit_data.Idx] = 1.0 / r1_values   # T1 = 1/R1

# Create mask
fit_mask = fit_data.FitMask
if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
    combined_mask = fit_mask & fit_data.Mask
else:
    combined_mask = fit_mask

mask_3d[fit_data.Idx[combined_mask]] = True

# Reshape to 3D
amp_3d = amp_3d.reshape(fit_data.Size)
t1_3d = t1_3d.reshape(fit_data.Size)
mask_3d = mask_3d.reshape(fit_data.Size)

print(f"   Valid voxels in mask: {np.sum(mask_3d)}")
print(f"   Amplitude range: [{np.min(amp_3d):.3f}, {np.max(amp_3d):.3f}]")
print(f"   T1 range: [{np.min(t1_3d[mask_3d]):.3f}, {np.max(t1_3d[mask_3d]):.3f}]")

# Apply tau correction (from MATLAB line: tau_correction = exp(2*630e-3*median(1./T1(Image.Mask(:)))))
median_r1 = np.median(1.0 / t1_3d[mask_3d])
tau_correction = np.exp(2 * 630e-3 * median_r1)
print(f"   Median R1: {median_r1:.6f}")
print(f"   Tau correction: {tau_correction:.6f}")

# Apply corrections to amplitude
Q_correction = 1  # From MATLAB
corrected_amp = amp_3d * Q_correction * tau_correction
final_amp = corrected_amp / po2_info['amp1mM']

print(f"   Corrected amplitude range: [{np.min(final_amp):.3f}, {np.max(final_amp):.3f}]")
print(f"   Mean: {np.mean(final_amp):.3f}")

# Calculate pO2 using epr_T2_PO2 logic on T1 values
po2_3d = np.zeros_like(t1_3d)
# This should actually use the T1 values for pO2 calculation, not convert to T2
# The MATLAB code shows: Image.pO2 = epr_T2_PO2(T1, Image.Amp, Image.Mask, s1.pO2_info);

print(f"\n🩸 Calculating pO2 from T1 values...")
# Based on the MATLAB, this uses T1 directly in the pO2 calculation
# Let me check what the actual calculation should be...
