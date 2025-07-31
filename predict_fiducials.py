import torch
import numpy as np
import scipy.io as sio
import os
import matplotlib.pyplot as plt
from scipy import ndimage
import argparse

# Import the model class (assuming it's in the same directory)
from train_fiducial_model import FiducialUNet3D

def resize_3d_volume(volume, target_size):
    """Resize a 3D volume to target size using scipy interpolation"""
    zoom_factors = [t/s for t, s in zip(target_size, volume.shape)]
    return ndimage.zoom(volume, zoom_factors, order=1)

def normalize_image(image):
    """Normalize image to [0, 1] range"""
    image = image.astype(np.float32)
    min_val, max_val = image.min(), image.max()
    if max_val > min_val:
        return (image - min_val) / (max_val - min_val)
    return image

def load_model(model_path, device):
    """Load the trained fiducial detection model"""
    model = FiducialUNet3D()
    
    if os.path.exists(model_path):
        checkpoint = torch.load(model_path, map_location=device)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            model.load_state_dict(checkpoint['model_state_dict'])
            print(f"✅ Loaded model from {model_path}")
            if 'best_val_loss' in checkpoint:
                print(f"   Best validation loss: {checkpoint['best_val_loss']:.4f}")
        else:
            model.load_state_dict(checkpoint)
            print(f"✅ Loaded model weights from {model_path}")
    else:
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    model.to(device)
    model.eval()
    return model

def predict_fiducials(model, image_data, device, target_size=(64, 64, 64), threshold=0.5):
    """
    Predict fiducials in a 3D image
    
    Args:
        model: Trained fiducial detection model
        image_data: 3D numpy array
        device: torch device
        target_size: Target size for prediction
        threshold: Threshold for binary prediction
    
    Returns:
        predicted_mask: Binary mask of predicted fiducials
        confidence_map: Confidence map (0-1)
    """
    original_shape = image_data.shape
    
    # Resize and normalize
    resized_image = resize_3d_volume(image_data, target_size)
    normalized_image = normalize_image(resized_image)
    
    # Prepare tensor
    input_tensor = torch.tensor(normalized_image[np.newaxis, np.newaxis, ...], 
                               dtype=torch.float32).to(device)
    
    # Predict
    with torch.no_grad():
        output = model(input_tensor)
        confidence_map = output.cpu().numpy()[0, 0]  # Remove batch and channel dims
    
    # Binary prediction
    binary_prediction = (confidence_map > threshold).astype(np.uint8)
    
    # Resize back to original size
    confidence_map_resized = resize_3d_volume(confidence_map, original_shape)
    binary_prediction_resized = resize_3d_volume(binary_prediction.astype(np.float32), original_shape)
    binary_prediction_resized = (binary_prediction_resized > 0.5).astype(np.uint8)
    
    return binary_prediction_resized, confidence_map_resized

def predict_on_mat_file(mat_file_path, model, device, output_dir=None, threshold=0.5):
    """
    Predict fiducials on all images in a .mat file
    
    Args:
        mat_file_path: Path to .mat file
        model: Trained model
        device: torch device
        output_dir: Directory to save results (optional)
        threshold: Prediction threshold
    """
    print(f"\n🔍 Processing: {os.path.basename(mat_file_path)}")
    
    try:
        # Load the .mat file
        data = sio.loadmat(mat_file_path, struct_as_record=False, squeeze_me=True)
        
        if 'images' not in data:
            print("❌ No 'images' field found in the file")
            return
        
        image_entries = data['images']
        results = []
        
        for entry_idx, entry in enumerate(image_entries):
            if not hasattr(entry, 'Name') or not hasattr(entry, 'data'):
                continue
                
            entry_name = str(entry.Name)
            image_data = entry.data
            
            if not hasattr(image_data, 'shape') or len(image_data.shape) != 3:
                print(f"  ⚠️ Skipping {entry_name}: Invalid image data")
                continue
            
            print(f"  📊 Processing {entry_name} (shape: {image_data.shape})")
            
            # Predict fiducials
            predicted_mask, confidence_map = predict_fiducials(
                model, image_data, device, threshold=threshold
            )
            
            # Count detected fiducials (connected components)
            labeled_mask, num_components = ndimage.label(predicted_mask)
            
            print(f"    ✅ Detected {num_components} fiducial regions")
            print(f"    📏 Total fiducial volume: {predicted_mask.sum()} voxels")
            
            result = {
                'entry_name': entry_name,
                'original_shape': image_data.shape,
                'predicted_mask': predicted_mask,
                'confidence_map': confidence_map,
                'num_regions': num_components,
                'total_volume': predicted_mask.sum()
            }
            results.append(result)
            
            # Save results if output directory provided
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
                
                # Save predicted mask
                mask_filename = f"{os.path.splitext(os.path.basename(mat_file_path))[0]}_{entry_name}_fiducial_mask.npy"
                np.save(os.path.join(output_dir, mask_filename), predicted_mask)
                
                # Save confidence map
                conf_filename = f"{os.path.splitext(os.path.basename(mat_file_path))[0]}_{entry_name}_confidence.npy"
                np.save(os.path.join(output_dir, conf_filename), confidence_map)
                
                # Create a summary visualization (middle slice)
                mid_slice = image_data.shape[2] // 2
                
                plt.figure(figsize=(15, 5))
                
                plt.subplot(1, 3, 1)
                plt.imshow(image_data[:, :, mid_slice], cmap='gray')
                plt.title(f'Original Image\\n{entry_name}')
                plt.axis('off')
                
                plt.subplot(1, 3, 2)
                plt.imshow(confidence_map[:, :, mid_slice], cmap='hot', vmin=0, vmax=1)
                plt.title(f'Confidence Map\\n(slice {mid_slice})')
                plt.colorbar()
                plt.axis('off')
                
                plt.subplot(1, 3, 3)
                plt.imshow(image_data[:, :, mid_slice], cmap='gray', alpha=0.7)
                plt.imshow(predicted_mask[:, :, mid_slice], cmap='Reds', alpha=0.5)
                plt.title(f'Predicted Fiducials\\n({num_components} regions)')
                plt.axis('off')
                
                plt.tight_layout()
                plot_filename = f"{os.path.splitext(os.path.basename(mat_file_path))[0]}_{entry_name}_prediction.png"
                plt.savefig(os.path.join(output_dir, plot_filename), dpi=150, bbox_inches='tight')
                plt.close()
        
        return results
        
    except Exception as e:
        print(f"❌ Error processing {mat_file_path}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Predict fiducials in 3D medical images')
    parser.add_argument('--model_path', type=str, default='./fiducial_model_best.pth',
                        help='Path to the trained model')
    parser.add_argument('--input_file', type=str, 
                        help='Path to a specific .mat file to process')
    parser.add_argument('--input_dir', type=str, default='./DATA/MRIAlign',
                        help='Directory containing .mat files to process')
    parser.add_argument('--output_dir', type=str, default='./fiducial_predictions',
                        help='Directory to save prediction results')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='Prediction threshold (0-1)')
    parser.add_argument('--device', type=str, default='auto',
                        help='Device to use (cuda/cpu/auto)')
    
    args = parser.parse_args()
    
    # Set device
    if args.device == 'auto':
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    else:
        device = torch.device(args.device)
    
    print(f"🔧 Using device: {device}")
    
    # Load model
    try:
        model = load_model(args.model_path, device)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("Please make sure you have trained the model first using train_fiducial_model.py")
        return
    
    # Process files
    if args.input_file:
        # Process single file
        if os.path.exists(args.input_file):
            results = predict_on_mat_file(args.input_file, model, device, 
                                        args.output_dir, args.threshold)
        else:
            print(f"❌ File not found: {args.input_file}")
    else:
        # Process all files in directory
        if not os.path.exists(args.input_dir):
            print(f"❌ Directory not found: {args.input_dir}")
            return
        
        mat_files = [f for f in os.listdir(args.input_dir) if f.endswith('.mat')]
        
        if not mat_files:
            print(f"❌ No .mat files found in {args.input_dir}")
            return
        
        print(f"📁 Found {len(mat_files)} .mat files")
        
        all_results = []
        for mat_file in mat_files:
            mat_path = os.path.join(args.input_dir, mat_file)
            results = predict_on_mat_file(mat_path, model, device, 
                                        args.output_dir, args.threshold)
            if results:
                all_results.extend(results)
        
        # Summary statistics
        if all_results:
            total_regions = sum(r['num_regions'] for r in all_results)
            total_volume = sum(r['total_volume'] for r in all_results)
            
            print(f"\\n📊 Summary:")
            print(f"   Processed {len(all_results)} images")
            print(f"   Total detected fiducial regions: {total_regions}")
            print(f"   Total fiducial volume: {total_volume} voxels")
            print(f"   Average regions per image: {total_regions/len(all_results):.1f}")
    
    print(f"\\n✅ Prediction completed!")
    if args.output_dir:
        print(f"   Results saved to: {args.output_dir}")

if __name__ == "__main__":
    main()
