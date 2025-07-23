import os
import torch
import numpy as np
import scipy.io as sio
from skimage.transform import resize
from scipy.ndimage import label, center_of_mass
from unet3d_model import UNet3D

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model
model = UNet3D().to(device)
model.load_state_dict(torch.load("./unet3d_kidney.pth", map_location=device))
model.eval()

# Input and output paths
input_dir = "./test_inputs"
output_dir = "./test_outputs"
os.makedirs(output_dir, exist_ok=True)

def make_roi_struct(mask, name):
    identity_matrix = np.eye(4, dtype=np.float64)
    return {
        'data': mask.astype(np.bool_),
        'ImageType': '3DMASK',
        'Name': name,
        'A': identity_matrix.copy(),
        'Anative': identity_matrix.copy(),
        'Aprime': identity_matrix.copy(),
        'isStore': 1,
        'isLoaded': 0,
        'Selected': 0,
        'Visible': 0,
        'box': np.array(mask.shape, dtype=np.float64),
        'pars': np.array([]),
        'FileName': np.array('', dtype='U')
    }

def predict_and_save(filepath):
    try:
        mat = sio.loadmat(filepath, struct_as_record=False, squeeze_me=True)
        if 'images' not in mat:
            raise KeyError("'images' not found")

        images_struct = mat['images']
        identity = np.eye(4, dtype=np.float64)
        for img in images_struct:
            if hasattr(img, 'data') and isinstance(img.data, np.ndarray):
                img.data = img.data.astype(np.float64)
                img.A = identity.copy()
                img.Anative = identity.copy()
                img.Aprime = identity.copy()
                img.box = np.array(img.data.shape[:3], dtype=np.float64)

                if hasattr(img, 'data_info'):
                    # Make sure 'Mask' field is logical
                    if hasattr(img.data_info, 'Mask'):
                        img.data_info.Mask = img.data_info.Mask.astype(bool)
                    else:
                        img.data_info.Mask = np.ones(img.data.shape, dtype=bool)

                if hasattr(img, 'slaves') and isinstance(img.slaves, np.ndarray):
                    for slave in img.slaves:
                        if hasattr(slave, 'data'):
                            slave.data = slave.data.astype(bool)
                            slave.A = identity.copy()
                            slave.Anative = identity.copy()
                            slave.Aprime = identity.copy()
                            slave.box = np.array(slave.data.shape[:3], dtype=np.float64)

        # Find BE_AMP
        be_amp_data = None
        image_entry = None
        for entry in images_struct:
            if hasattr(entry, 'Name') and 'BE_AMP' in str(entry.Name):
                be_amp_data = entry.data
                image_entry = entry
                break

        if be_amp_data is None or be_amp_data.ndim != 3:
            raise ValueError("Invalid or missing BE_AMP data")

        # Normalize input
        img_resized = resize(be_amp_data, (64, 64, 64), preserve_range=True)
        img_norm = (img_resized - img_resized.min()) / (np.ptp(img_resized) + 1e-8)
        input_tensor = torch.tensor(img_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)

        # Run prediction
        with torch.no_grad():
            pred = model(input_tensor).squeeze().cpu().numpy()
            mask = (pred > 0.5)

        if np.sum(mask) == 0:
            print(f"\u26a0\ufe0f Empty mask predicted for {filepath}")
            return

        # Split components
        labeled, num = label(mask)
        if num < 2:
            print(f"\u26a0\ufe0f Only {num} component(s) found — skipping split.")
            return

        # Find two largest components
        sizes = [(labeled == i).sum() for i in range(1, num + 1)]
        largest = np.argsort(sizes)[-2:][::-1]
        comp1 = (labeled == (largest[0] + 1))
        comp2 = (labeled == (largest[1] + 1))

        # Determine left/right
        com1 = center_of_mass(comp1)
        com2 = center_of_mass(comp2)

        if com1[0] > com2[0]:
            right_mask, left_mask = comp1, comp2
        else:
            right_mask, left_mask = comp2, comp1

        # Create ROI structs
        roi1 = make_roi_struct(right_mask, "Kidney")
        roi2 = make_roi_struct(left_mask, "Kidney2")

        # Attach both ROIs
        roi_array = np.empty((2,), dtype=object)
        roi_array[0] = roi1
        roi_array[1] = roi2
        setattr(image_entry, 'slaves', roi_array)

        # Save output
        out_path = os.path.join(output_dir, os.path.basename(filepath))
        sio.savemat(out_path, mat, do_compression=True)
        print(f"\u2705 Final saved with split kidneys: {out_path}")

    except Exception as e:
        print(f"❌ Error processing {filepath}: {e}")

# Process files
for fname in os.listdir(input_dir):
    if fname.endswith(".mat"):
        predict_and_save(os.path.join(input_dir, fname))
