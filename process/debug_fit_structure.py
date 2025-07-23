#!/usr/bin/env python3
"""
Debug script to examine fit_data structure
"""

import scipy.io as sio
import numpy as np
from pathlib import Path

# Load the first processed file to examine structure
data_dir = Path("../DATA/241202")
p_file = data_dir / "p8475image4D_18x18_0p75gcm_file.mat"

print(f"🔍 Loading: {p_file}")
p_mat = sio.loadmat(str(p_file), struct_as_record=False, squeeze_me=True)

print(f"\n📋 Keys in p_file:")
for key in p_mat.keys():
    if not key.startswith('__'):
        print(f"   {key}: {type(p_mat[key])}")

if 'fit_data' in p_mat:
    fit_data = p_mat['fit_data']
    print(f"\n🔬 fit_data attributes:")
    if hasattr(fit_data, '_fieldnames'):
        for field in fit_data._fieldnames:
            attr_val = getattr(fit_data, field)
            print(f"   {field}: {type(attr_val)} - {getattr(attr_val, 'shape', 'N/A')}")
    
    print(f"\n🧮 Algorithm: {getattr(fit_data, 'Algorithm', 'Not found')}")
    
    if hasattr(fit_data, 'P'):
        P = fit_data.P
        print(f"   P shape: {P.shape}")
        print(f"   P sample values: {P[:5, :5] if P.shape[1] > 5 else P}")
    
    if hasattr(fit_data, 'Idx'):
        Idx = fit_data.Idx
        print(f"   Idx shape: {Idx.shape}")
        print(f"   Idx sample: {Idx[:10] if len(Idx) > 10 else Idx}")
        
    if hasattr(fit_data, 'Size'):
        Size = fit_data.Size
        print(f"   Size: {Size}")

if 'pO2_info' in p_mat:
    po2_info = p_mat['pO2_info']
    print(f"\n🩸 pO2_info attributes:")
    if hasattr(po2_info, '_fieldnames'):
        for field in po2_info._fieldnames:
            attr_val = getattr(po2_info, field)
            print(f"   {field}: {attr_val}")
