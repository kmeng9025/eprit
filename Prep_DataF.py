import os
import numpy as np
import scipy.io as sio
from glob import glob

# Set your input and output directories
INPUT_DIR = './DATA/MRIAlign'  # Folder where your .mat files are stored
OUTPUT_DIR = './preprocessed'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# These are the image and ROI field names
IMG_KEY = '>MRI'
ROI_KEYS = ['FID', 'Side_FID']

# Lists to hold data
images = []
roi_masks = []

# Search for .mat files in the input directory
mat_files = glob(os.path.join(INPUT_DIR, '*.mat'))

for file in mat_files:
    try:
        data = sio.loadmat(file, struct_as_record=False, squeeze_me=True)
        image_entries = data['images']

        # Extract BE_AMP image
        be_amp = None
        for entry in image_entries:
            if hasattr(entry, 'Name') and IMG_KEY in str(entry.Name):
                be_amp = entry.data
                slaves = entry.slaves[0] if hasattr(entry, 'slaves') else []
                break

        if be_amp is None or not slaves:
            print(f"Skipping {file} — missing image or ROIs")
            continue

        # Extract ROIs by name
        roi1 = roi2 = None
        for slave in slaves:
            if hasattr(slave, 'Name'):
                if 'Kidney' == str(slave.Name):
                    roi1 = slave.data.astype(np.uint8)
                elif 'Kidney2' == str(slave.Name):
                    roi2 = slave.data.astype(np.uint8)

        if roi1 is None or roi2 is None:
            print(f"Skipping {file} — missing one or both ROIs")
            continue

        # Normalize image
        norm_img = (be_amp - np.mean(be_amp)) / (np.std(be_amp) + 1e-5)
        images.append(norm_img[np.newaxis, ...])  # shape (1, 64, 64, 64)

        stacked_rois = np.stack([roi1, roi2], axis=0)  # shape (2, 64, 64, 64)
        roi_masks.append(stacked_rois)

        print(f"Processed {file}")

    except Exception as e:
        print(f"Error processing {file}: {e}")

# Final dataset arrays
X = np.stack(images)
Y = np.stack(roi_masks)

np.save(os.path.join(OUTPUT_DIR, 'X.npy'), X)
np.save(os.path.join(OUTPUT_DIR, 'Y.npy'), Y)
print("✅ Preprocessing complete. Saved X.npy and Y.npy")
