import scipy.io as sio
import numpy as np

# Load the fit data
mat = sio.loadmat('../DATA/241202/p8475image4D_18x18_0p75gcm_file.mat', struct_as_record=False, squeeze_me=True)

print('fit_data fields:', mat['fit_data']._fieldnames)
print('P shape:', mat['fit_data'].P.shape)
print('Parameters:', mat['fit_data'].Parameters)
print('Size:', mat['fit_data'].Size)
print('Idx min/max:', np.min(mat['fit_data'].Idx), np.max(mat['fit_data'].Idx))
print('FitMask sum:', np.sum(mat['fit_data'].FitMask))
print('P ranges:')
for i in range(mat['fit_data'].P.shape[0]):
    print(f'  P[{i}]: {np.min(mat["fit_data"].P[i,:]):.3f} to {np.max(mat["fit_data"].P[i,:]):.3f}')

# Test reconstruction
size = mat['fit_data'].Size
idx = mat['fit_data'].Idx
P = mat['fit_data'].P

print(f'\nReconstruction test:')
print(f'Total voxels: {np.prod(size)}')
print(f'Fitted voxels: {len(idx)}')

# Reconstruct amplitude image
amp_vol = np.zeros(np.prod(size))
amp_vol[idx] = P[0, :]  # First parameter is amplitude
amp_img = amp_vol.reshape(size)

print(f'Amplitude image stats:')
print(f'  Shape: {amp_img.shape}')
print(f'  Range: {np.min(amp_img):.3f} to {np.max(amp_img):.3f}')
print(f'  Non-zero voxels: {np.sum(amp_img != 0)}')
