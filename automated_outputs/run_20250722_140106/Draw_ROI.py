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

def get_attribute(obj, attr, default=None):
    """Safely get attribute from MATLAB structure or dict"""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    elif hasattr(obj, '__dict__') and attr in obj.__dict__:
        return obj.__dict__[attr]
    elif isinstance(obj, dict) and attr in obj:
        return obj[attr]
    else:
        return default

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
        
        # Handle both cell array and struct array formats
        if isinstance(images_struct, np.ndarray):
            images_list = images_struct.flatten().tolist()
        else:
            images_list = [images_struct] if not isinstance(images_struct, list) else images_struct
            
        # Find BE_AMP image
        be_amp_image = None
        be_amp_index = None
        
        for i, img in enumerate(images_list):
            name = get_attribute(img, 'Name', '')
            print(f"Image {i}: {name}")
            if name == '>BE_AMP':
                be_amp_image = img
                be_amp_index = i
                break

        if be_amp_image is None:
            print("BE_AMP image not found, using first image")
            be_amp_image = images_list[0]
            be_amp_index = 0

        # Get image data and reshape
        image_data = get_attribute(be_amp_image, 'data')
        box = get_attribute(be_amp_image, 'box')
        
        if image_data is None:
            raise ValueError("No image data found")
            
        if box is not None:
            if len(box) == 3:
                image_3d = image_data.reshape(box.astype(int))
            else:
                # Try to infer shape
                total_voxels = len(image_data)
                side_length = int(round(total_voxels ** (1/3)))
                image_3d = image_data.reshape(side_length, side_length, side_length)
        else:
            # Default assumption - cube
            total_voxels = len(image_data)
            side_length = int(round(total_voxels ** (1/3)))
            image_3d = image_data.reshape(side_length, side_length, side_length)

        print(f"Image shape: {image_3d.shape}")
        print(f"Image data range: {np.min(image_3d)} to {np.max(image_3d)}")

        # Normalize image
        image_min = np.min(image_3d)
        image_max = np.max(image_3d)
        if image_max > image_min:
            image_3d = (image_3d - image_min) / (image_max - image_min)
        else:
            image_3d = np.zeros_like(image_3d)

        # Resize to model input size if needed
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
        original_shape = box.astype(int) if box is not None else (64, 64, 64)
        if mask.shape != tuple(original_shape):
            mask = resize(mask.astype(float), original_shape, anti_aliasing=False) > 0.5

        print(f"ROI mask shape: {mask.shape}")
        print(f"ROI voxel count: {np.sum(mask)}")

        # Create ROI structure
        roi_struct = make_roi_struct(mask, 'kidney_roi')

        # Add ROI to BE_AMP image slaves
        current_slaves = get_attribute(be_amp_image, 'slaves', [])
        if current_slaves is None:
            current_slaves = []
        elif not isinstance(current_slaves, list):
            current_slaves = [current_slaves] if current_slaves.size > 0 else []
        
        current_slaves.append(roi_struct)
        
        # Update the slaves attribute
        if hasattr(be_amp_image, 'slaves'):
            be_amp_image.slaves = current_slaves
        else:
            be_amp_image.__dict__['slaves'] = current_slaves

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
            print(f"Successfully saved project with ROI to {output_path}")
        else:
            print("Warning: scipy.io not available, could not save file")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        import traceback
        traceback.print_exc()

# Process all files in input directory
if os.path.exists(input_dir):
    for fname in os.listdir(input_dir):
        if fname.endswith('.mat'):
            print(f"Processing {fname}")
            predict_and_save(os.path.join(input_dir, fname))
else:
    print(f"Input directory {input_dir} does not exist")
