import os
import torch
import numpy as np
try:
    import scipy.io as sio
except ImportError:
    sio = None
try:
    import h5py
except ImportError:
    h5py = None
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

def load_matlab_file(filepath):
    """Load MATLAB file using appropriate method"""
    try:
        # Try scipy.io first (for older formats)
        if sio is not None:
            return sio.loadmat(filepath, struct_as_record=False, squeeze_me=True)
    except (NotImplementedError, ValueError):
        pass
    
    try:
        # Try h5py for v7.3 files
        if h5py is not None:
            with h5py.File(filepath, 'r') as f:
                # Convert h5py structure to dict
                data = {}
                for key in f.keys():
                    data[key] = np.array(f[key])
                return data
    except Exception:
        pass
    
    raise ValueError(f"Could not load MATLAB file: {filepath}")

def predict_and_save(filepath):
    try:
        mat = load_matlab_file(filepath)
        if 'images' not in mat:
            raise KeyError("'images' not found")

        images_struct = mat['images']
        identity = np.eye(4, dtype=np.float64)
        
        # Handle both cell array and struct array formats
        if isinstance(images_struct, np.ndarray):
            images_list = images_struct.flatten().tolist()
        else:
            images_list = [images_struct] if not isinstance(images_struct, list) else images_struct
            
        for i, img in enumerate(images_list):
            if hasattr(img, 'data') and isinstance(img.data, np.ndarray):
                img.data = img.data.astype(np.float64)
            elif isinstance(img, dict) and 'data' in img:
                img['data'] = np.array(img['data'], dtype=np.float64)

        # Find BE_AMP image
        be_amp_image = None
        be_amp_index = None
        
        for i, img in enumerate(images_list):
            name = getattr(img, 'Name', img.get('Name', '')) if hasattr(img, 'Name') or 'Name' in img else ''
            if name == '>BE_AMP':
                be_amp_image = img
                be_amp_index = i
                break

        if be_amp_image is None:
            print("BE_AMP image not found, using first image")
            be_amp_image = images_list[0]
            be_amp_index = 0

        # Get image data and reshape
        if hasattr(be_amp_image, 'data'):
            image_data = be_amp_image.data
            box = getattr(be_amp_image, 'box', None)
        else:
            image_data = be_amp_image['data']
            box = be_amp_image.get('box', None)
            
        if box is not None:
            if len(box) == 3:
                image_3d = image_data.reshape(box.astype(int))
            else:
                # Try to infer shape
                total_voxels = len(image_data)
                side_length = int(round(total_voxels ** (1/3)))
                image_3d = image_data.reshape(side_length, side_length, side_length)
        else:
            # Default assumption
            total_voxels = len(image_data)
            side_length = int(round(total_voxels ** (1/3)))
            image_3d = image_data.reshape(side_length, side_length, side_length)

        # Normalize image
        image_3d = (image_3d - np.min(image_3d)) / (np.max(image_3d) - np.min(image_3d) + 1e-8)

        # Resize to model input size (adjust as needed)
        target_size = 64  # Adjust based on your model
        if image_3d.shape != (target_size, target_size, target_size):
            image_3d = resize(image_3d, (target_size, target_size, target_size), anti_aliasing=True)

        # Create input tensor
        input_tensor = torch.tensor(image_3d[np.newaxis, np.newaxis, ...], dtype=torch.float32).to(device)

        # Predict
        with torch.no_grad():
            prediction = model(input_tensor)
            prediction = torch.sigmoid(prediction)
            mask = (prediction.cpu().numpy()[0, 0] > 0.5).astype(np.bool_)

        # Resize mask back to original size if needed
        if hasattr(be_amp_image, 'box'):
            original_shape = be_amp_image.box.astype(int)
        else:
            original_shape = be_amp_image['box'].astype(int)
            
        if mask.shape != tuple(original_shape):
            mask = resize(mask.astype(float), original_shape, anti_aliasing=False) > 0.5

        # Create ROI structure
        roi_struct = make_roi_struct(mask, 'kidney_roi')

        # Add ROI to BE_AMP image slaves
        if hasattr(be_amp_image, 'slaves'):
            if be_amp_image.slaves is None or len(be_amp_image.slaves) == 0:
                be_amp_image.slaves = [roi_struct]
            else:
                be_amp_image.slaves.append(roi_struct)
        else:
            if 'slaves' not in be_amp_image or be_amp_image['slaves'] is None:
                be_amp_image['slaves'] = [roi_struct]
            else:
                be_amp_image['slaves'].append(roi_struct)

        # Save the updated project
        output_path = os.path.join(output_dir, "project_with_roi.mat")
        
        # Convert back to format compatible with scipy.io
        save_data = {}
        for key, value in mat.items():
            if key == 'images':
                save_data[key] = np.array(images_list, dtype=object)
            else:
                save_data[key] = value
                
        if sio is not None:
            sio.savemat(output_path, save_data, format='5')
        else:
            print("Warning: scipy.io not available, could not save file")

        print(f"Successfully processed {os.path.basename(filepath)}")
        print(f"ROI mask shape: {mask.shape}")
        print(f"ROI voxel count: {np.sum(mask)}")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()

# Process all files in input directory
if os.path.exists(input_dir):
    for fname in os.listdir(input_dir):
        if fname.endswith('.mat'):
            predict_and_save(os.path.join(input_dir, fname))
else:
    print(f"Input directory {input_dir} does not exist")
