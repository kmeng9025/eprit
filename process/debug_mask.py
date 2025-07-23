#!/usr/bin/env python3
"""
Debug mask calculation and find correct pO2 source
"""

import scipy.io as sio
import numpy as np
from pathlib import Path

# Load our source data
data_dir = Path("../DATA/241202")
p_file = data_dir / "p8475image4D_18x18_0p75gcm_file.mat"
raw_file = data_dir / "8475image4D_18x18_0p75gcm_file.mat"

print(f"🔍 Loading files:")
print(f"   P-file: {p_file}")
print(f"   Raw file: {raw_file}")

p_mat = sio.loadmat(str(p_file), struct_as_record=False, squeeze_me=True)
raw_mat = sio.loadmat(str(raw_file), struct_as_record=False, squeeze_me=True)

# Examine the raw file to see if it has pre-calculated pO2
print(f"\n📋 Raw file keys:")
for key in raw_mat.keys():
    if not key.startswith('__'):
        val = raw_mat[key]
        print(f"   {key}: {type(val)} - {getattr(val, 'shape', 'N/A')}")

# Check fit_data details
fit_data = p_mat['fit_data']
print(f"\n🔬 Detailed fit_data analysis:")
print(f"   P shape: {fit_data.P.shape}")
print(f"   Idx shape: {fit_data.Idx.shape}")
print(f"   FitMask shape: {fit_data.FitMask.shape}")
print(f"   FitMask type: {type(fit_data.FitMask)}")

if hasattr(fit_data, 'Mask'):
    print(f"   Mask shape: {fit_data.Mask.shape}")
    print(f"   Mask type: {type(fit_data.Mask)}")
else:
    print(f"   No Mask field")

# Examine the masks in detail
print(f"\n🎭 Mask analysis:")
print(f"   FitMask sum: {np.sum(fit_data.FitMask)}")
print(f"   FitMask True values: {np.count_nonzero(fit_data.FitMask)}")

if hasattr(fit_data, 'Mask') and fit_data.Mask is not None:
    print(f"   Mask sum: {np.sum(fit_data.Mask)}")
    print(f"   Mask True values: {np.count_nonzero(fit_data.Mask)}")
    
    combined = fit_data.FitMask & fit_data.Mask
    print(f"   Combined mask True values: {np.count_nonzero(combined)}")
else:
    print(f"   Using FitMask only")
    combined = fit_data.FitMask
    print(f"   FitMask True values: {np.count_nonzero(combined)}")

# Let's see if the issue is that we should use ALL fit indices, not just masked ones
print(f"\n🎯 Testing different mask approaches:")

# Approach 1: Use all Idx (ignore mask)
all_voxels = len(fit_data.Idx)
print(f"   All fit indices: {all_voxels}")

# Create 3D arrays
amp_3d = np.zeros(np.prod(fit_data.Size))
amp_3d[fit_data.Idx] = fit_data.P[0, :]
amp_3d = amp_3d.reshape(fit_data.Size)

print(f"   Non-zero amplitude voxels: {np.count_nonzero(amp_3d)}")
print(f"   Amplitude range: [{np.min(amp_3d):.3f}, {np.max(amp_3d):.3f}]")

# Check if the ese_fbp output already has processed values
print(f"\n📊 Checking if processed values exist...")
if hasattr(raw_mat, 'Amp'):
    print(f"   Raw file has Amp field: {raw_mat.Amp.shape}")
if hasattr(raw_mat, 'pO2'):
    print(f"   Raw file has pO2 field: {raw_mat.pO2.shape}")

# Let me look for the exact pattern that the reference uses
# Maybe the reference was created using ibGUI's epr_LoadMATFile which handles this differently

print(f"\n🔍 Looking for pre-calculated values in raw file...")
for key in ['Amp', 'pO2', 'T2', 'Error', 'Mask']:
    if key in raw_mat:
        val = raw_mat[key]
        print(f"   {key}: shape {val.shape}, range [{np.min(val):.3f}, {np.max(val):.3f}]")

# Check the reference range to understand the pattern
print(f"\n🎯 Reference ranges for comparison:")
print(f"   Reference BE_AMP: [0.000, 10.552]")
print(f"   Reference BE1 pO2: [-100.000, 255.145]")
print(f"   Our amplitude: [{np.min(amp_3d):.3f}, {np.max(amp_3d):.3f}]")
