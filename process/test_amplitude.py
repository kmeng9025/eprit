import scipy.io as sio
import numpy as np
import sys
sys.path.append('.')
from simple_automation_pipeline import SimpleEPRIAutomation

# Test the updated fit parameter extraction
pipeline = SimpleEPRIAutomation()

# Load test data
p_mat = sio.loadmat('../DATA/241202/p8475image4D_18x18_0p75gcm_file.mat', struct_as_record=False, squeeze_me=True)

print("Testing amplitude extraction...")
amp_data = pipeline.load_fit_parameters(p_mat['fit_data'], 'AMP')
print(f"Amplitude data shape: {amp_data.shape}")
print(f"Amplitude range: {np.min(amp_data):.3f} to {np.max(amp_data):.3f}")
print(f"Non-zero voxels: {np.sum(amp_data > 0)}")

print("\nTesting R1 extraction...")
r1_data = pipeline.load_fit_parameters(p_mat['fit_data'], 'R1')
print(f"R1 data shape: {r1_data.shape}")
print(f"R1 range: {np.min(r1_data):.6f} to {np.max(r1_data):.6f}")
print(f"Non-zero voxels: {np.sum(r1_data > 0)}")

print("\nTesting pO2 calculation...")
po2_info = p_mat.get('pO2_info', None)
print(f"pO2_info available: {po2_info is not None}")
if po2_info is not None:
    print(f"pO2_info fields: {po2_info._fieldnames if hasattr(po2_info, '_fieldnames') else 'Not available'}")

po2_data = pipeline.calculate_po2_from_fit_data(p_mat['fit_data'], po2_info)
print(f"pO2 data shape: {po2_data.shape}")
print(f"pO2 range: {np.min(po2_data):.3f} to {np.max(po2_data):.3f}")
print(f"Non-zero voxels: {np.sum(po2_data > 0)}")
print(f"Valid pO2 voxels (>0): {np.sum(po2_data > 0)}")
