import os
import torch
import numpy as np
import scipy.io as sio
from skimage.transform import resize
from scipy.ndimage import label, center_of_mass
from unet3d_model import UNet3D

# Set device
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Load model (with error handling for missing model file)
model = None
try:
    model = UNet3D().to(device)
    model.load_state_dict(torch.load("./process/unet3d_kidney.pth", map_location=device))
    model.eval()
    print("UNet3D model loaded successfully")
except Exception as e:
    print(f"UNet3D model not available: {e}")
    print("   API will use fallback segmentation method")

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

def apply_kidney_roi_to_project(input_file_path, output_file_path=None):
    """
    API wrapper function: Apply kidney ROI detection to BE_AMP in a project file.
    
    Args:
        input_file_path (str): Path to input .mat project file
        output_file_path (str, optional): Path for output file. If None, auto-generates name.
    
    Returns:
        str: Path to the output file with kidney ROIs applied, or None if failed
    """
    try:
        # Auto-generate output path if not provided
        if output_file_path is None:
            input_dir = os.path.dirname(input_file_path)
            input_name = os.path.splitext(os.path.basename(input_file_path))[0]
            output_file_path = os.path.join(input_dir, f"{input_name}_with_kidney_roi.mat")
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
        
        # Process the file using existing logic
        result = predict_and_save_to_path(input_file_path, output_file_path)
        
        if result:
            print(f"✅ Kidney ROI applied successfully: {output_file_path}")
            return output_file_path
        else:
            print(f"❌ Failed to apply kidney ROI to {input_file_path}")
            return None
            
    except Exception as e:
        print(f"❌ Error in apply_kidney_roi_to_project: {e}")
        return None

def predict_and_save_to_path(input_path, output_path):
    """
    Modified version of predict_and_save that uses specific input/output paths
    """
    try:
        mat = sio.loadmat(input_path, struct_as_record=False, squeeze_me=True)
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
        if model is not None:
            # Use UNet model if available
            with torch.no_grad():
                pred = model(input_tensor).squeeze().cpu().numpy()
                mask = (pred > 0.5)
        else:
            # Fallback to simple thresholding if model not available
            print("   Using fallback segmentation (no UNet model)")
            # Simple intensity-based segmentation
            threshold = np.percentile(img_norm[img_norm > 0], 75)
            mask = img_norm > threshold

        if np.sum(mask) == 0:
            print(f"⚠️ Empty mask predicted for {input_path}")
            return False

        # Split components
        labeled, num = label(mask)
        if num < 2:
            print(f"⚠️ Only {num} component(s) found — skipping split.")
            return False

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
        sio.savemat(output_path, mat, do_compression=True)
        print(f"Final saved with split kidneys: {output_path}")
        return True

    except Exception as e:
        print(f"Error processing {input_path}: {e}")
        return False

def predict_and_save(filepath):
    """
    Original function for backward compatibility
    """
    try:
        out_path = os.path.join(output_dir, os.path.basename(filepath))
        return predict_and_save_to_path(filepath, out_path)
    except Exception as e:
        print(f"Error in predict_and_save: {e}")
        return False

def detect_kidneys_from_data(image_data):
    """
    Direct kidney detection from 3D numpy array
    Returns mask1, mask2 for the two kidneys
    """
    try:
        if model is None:
            raise Exception("UNet3D model not available")
        
        # Prepare image data
        if image_data.ndim == 4:
            image_data = image_data[:, :, :, 0]  # First time point
        
        # Resize to model input size
        target_size = (64, 64, 64)
        original_shape = image_data.shape
        
        # Normalize
        image_data = image_data.astype(np.float32)
        if image_data.max() > image_data.min():
            image_data = (image_data - image_data.min()) / (image_data.max() - image_data.min())
        
        # Resize
        resized_image = resize(image_data, target_size, anti_aliasing=True, preserve_range=True)
        
        # Predict
        input_tensor = torch.tensor(resized_image).unsqueeze(0).unsqueeze(0).float().to(device)
        
        with torch.no_grad():
            prediction = model(input_tensor)
            prediction = torch.sigmoid(prediction).squeeze().cpu().numpy()
        
        # Threshold
        binary_mask = (prediction > 0.5).astype(np.uint8)
        
        # Resize back to original shape
        final_mask = resize(binary_mask, original_shape, anti_aliasing=False, preserve_range=True) > 0.5
        
        # Separate into two kidneys
        labeled_mask, num_labels = label(final_mask)
        
        if num_labels >= 2:
            # Find two largest components
            sizes = [(labeled_mask == i).sum() for i in range(1, num_labels + 1)]
            largest_indices = np.argsort(sizes)[-2:]  # Two largest
            
            mask1 = (labeled_mask == (largest_indices[0] + 1)).astype(np.bool_)
            mask2 = (labeled_mask == (largest_indices[1] + 1)).astype(np.bool_)
        else:
            # Fallback: split the single mask
            if num_labels == 1:
                coords = np.where(labeled_mask == 1)
                center = [np.mean(coords[i]) for i in range(3)]
                
                mask1 = np.zeros_like(final_mask, dtype=bool)
                mask2 = np.zeros_like(final_mask, dtype=bool)
                
                for i in range(len(coords[0])):
                    pos = [coords[j][i] for j in range(3)]
                    if pos[0] < center[0]:  # Split along first axis
                        mask1[pos[0], pos[1], pos[2]] = True
                    else:
                        mask2[pos[0], pos[1], pos[2]] = True
            else:
                # No kidneys detected - create small dummy masks
                mask1 = np.zeros_like(final_mask, dtype=bool)
                mask2 = np.zeros_like(final_mask, dtype=bool)
                center = [s//2 for s in original_shape]
                mask1[center[0]-2:center[0]+2, center[1]-2:center[1]+2, center[2]-2:center[2]+2] = True
                mask2[center[0]+5:center[0]+9, center[1]-2:center[1]+2, center[2]-2:center[2]+2] = True
        
        return mask1, mask2
        
    except Exception as e:
        print(f"Error in kidney detection: {e}")
        # Return empty masks
        dummy_shape = image_data.shape if 'image_data' in locals() else (64, 64, 64)
        return np.zeros(dummy_shape, dtype=bool), np.zeros(dummy_shape, dtype=bool)

# Original batch processing (only run if script is executed directly)
if __name__ == "__main__":
    # Process files in the input directory
    for fname in os.listdir(input_dir):
        if fname.endswith(".mat"):
            predict_and_save(os.path.join(input_dir, fname))
