import numpy as np
import pandas as pd
from scipy.io import loadmat
import os
import hashlib

# -------- Configuration --------
input_dir = "./test_outputs"
output_dir = os.path.join(input_dir, "analyzed")
os.makedirs(output_dir, exist_ok=True)

# -------- Helper: hash ROI content for uniqueness --------
def hash_roi(arr):
    return hashlib.md5(arr.astype(np.uint8).tobytes()).hexdigest()

# -------- Analyze .mat file --------
def analyze_mat_file(mat_path):
    try:
        mat_data = loadmat(mat_path, struct_as_record=False, squeeze_me=True)
        images = mat_data['images']
    except Exception as e:
        print(f"❌ Error loading '{mat_path}': {e}")
        return None

    if not isinstance(images, (list, np.ndarray)):
        images = [images]

    # Step 1: Extract all unique ROI masks
    roi_bank = {}  # {hash: (roi_name, roi_mask)}

    for img in images:
        slaves = getattr(img, 'slaves', None)
        if slaves is None:
            continue
        if not isinstance(slaves, (list, np.ndarray)):
            slaves = [slaves]
        for i, slave in enumerate(slaves):
            try:
                mask = getattr(slave, 'data') > 0
                name = getattr(slave, 'Name', f'ROI_{i}')
                h = hash_roi(mask)
                if h not in roi_bank:
                    roi_bank[h] = (name, mask)
            except Exception:
                continue

    if not roi_bank:
        print("⚠️ No valid ROIs found.")
        return None

    # Step 2: Apply each ROI to every image
    results = []
    for img in images:
        image_name = getattr(img, 'Name', 'Unnamed').lstrip('>')  # ✅ strip '>'
        image_type = getattr(img, 'ImageType', 'Unknown')
        data = getattr(img, 'data', None)
        if data is None:
            continue
        for roi_hash, (roi_name, roi_mask) in roi_bank.items():
            if roi_mask.shape != data.shape:
                continue

            # ✅ Exclude invalid voxels
            masked_vals = data[roi_mask]
            valid_vals = masked_vals[masked_vals > -99]

            # ✅ Clamp PO2_pEPRI values into [0, 80]
            if image_type == 'PO2_pEPRI':
                valid_vals = np.clip(valid_vals, 0, 80)

            if valid_vals.size == 0:
                continue

            results.append({
                'Name': image_name,
                'Image Type': image_type,
                'ROI Name': roi_name,
                'Mean': round(np.mean(valid_vals), 4),
                'Median': round(np.median(valid_vals), 4),
                'Std Dev': round(np.std(valid_vals), 4),
                'Non-zero Voxels': int(valid_vals.size)
            })

    return results

# -------- Main Loop --------
mat_files = [f for f in os.listdir(input_dir) if f.endswith('.mat')]

for filename in mat_files:
    full_path = os.path.join(input_dir, filename)
    print(f"🔍 Processing {filename}...")

    stats = analyze_mat_file(full_path)

    if stats:
        df = pd.DataFrame(stats)

        # ✅ Column order and sorting
        df = df[['Name', 'Image Type', 'ROI Name', 'Mean', 'Median', 'Std Dev', 'Non-zero Voxels']]
        df.sort_values(by=['Image Type', 'Name', 'ROI Name'], inplace=True)

        output_filename = os.path.splitext(filename)[0] + "_statistics.xlsx"
        output_path = os.path.join(output_dir, output_filename)
        df.to_excel(output_path, index=False)

        print(f"✅ Saved: {output_path}")
    else:
        print(f"⚠️ No valid stats extracted from {filename}")

print("\n🏁 Done processing all files.")
