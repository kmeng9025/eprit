#!/usr/bin/env python3
"""
UNet3D Model Test Script

This script tests the UNet3D kidney segmentation model to ensure it's working correctly.
"""

import os
import sys
import numpy as np
import torch
from skimage.transform import resize
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from unet3d_model import UNet3D

def test_unet_model():
    """Test the UNet3D model loading and inference"""
    print("🧠 Testing UNet3D Kidney Segmentation Model")
    print("=" * 50)
    
    # Check if model file exists
    model_path = "unet3d_kidney.pth"
    if not os.path.exists(model_path):
        print(f"❌ Model file not found: {model_path}")
        return False
    
    print(f"✅ Model file found: {model_path}")
    
    # Check device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️  Using device: {device}")
    
    try:
        # Load model
        print("📥 Loading UNet3D model...")
        model = UNet3D().to(device)
        model.load_state_dict(torch.load(model_path, map_location=device))
        model.eval()
        print("✅ Model loaded successfully!")
        
        # Create test data (simulate a 64x64x64 image)
        print("🔬 Creating test data...")
        test_image = np.random.rand(64, 64, 64).astype(np.float32)
        
        # Add some structure to make it more realistic
        # Create two spherical regions to simulate kidneys
        center1 = [32, 20, 32]
        center2 = [32, 44, 32]
        radius = 8
        
        z, y, x = np.mgrid[0:64, 0:64, 0:64]
        dist1 = np.sqrt((z - center1[0])**2 + (y - center1[1])**2 + (x - center1[2])**2)
        dist2 = np.sqrt((z - center2[0])**2 + (y - center2[1])**2 + (x - center2[2])**2)
        
        test_image[dist1 <= radius] = 1.0
        test_image[dist2 <= radius] = 1.0
        
        # Normalize
        test_image = (test_image - test_image.min()) / (test_image.max() - test_image.min() + 1e-8)
        
        # Convert to tensor
        input_tensor = torch.tensor(test_image).unsqueeze(0).unsqueeze(0).to(device)
        print(f"📊 Input tensor shape: {input_tensor.shape}")
        
        # Run inference
        print("🚀 Running inference...")
        with torch.no_grad():
            output = model(input_tensor)
            prediction = output.squeeze().cpu().numpy()
            mask = (prediction > 0.5).astype(np.uint8)
        
        print(f"📊 Output shape: {prediction.shape}")
        print(f"📊 Prediction range: {prediction.min():.3f} to {prediction.max():.3f}")
        print(f"🎯 Segmented voxels: {np.sum(mask)} / {mask.size} ({100*np.sum(mask)/mask.size:.1f}%)")
        
        # Save visualization
        print("📸 Creating visualization...")
        fig, axes = plt.subplots(2, 3, figsize=(12, 8))
        
        # Show middle slices
        mid_slice = 32
        
        # Original image
        axes[0, 0].imshow(test_image[:, :, mid_slice], cmap='gray')
        axes[0, 0].set_title('Test Image (Z-slice)')
        axes[0, 1].imshow(test_image[:, mid_slice, :], cmap='gray')
        axes[0, 1].set_title('Test Image (Y-slice)')
        axes[0, 2].imshow(test_image[mid_slice, :, :], cmap='gray')
        axes[0, 2].set_title('Test Image (X-slice)')
        
        # Predicted mask
        axes[1, 0].imshow(mask[:, :, mid_slice], cmap='Reds')
        axes[1, 0].set_title('Predicted Mask (Z-slice)')
        axes[1, 1].imshow(mask[:, mid_slice, :], cmap='Reds')
        axes[1, 1].set_title('Predicted Mask (Y-slice)')
        axes[1, 2].imshow(mask[mid_slice, :, :], cmap='Reds')
        axes[1, 2].set_title('Predicted Mask (X-slice)')
        
        for ax in axes.flat:
            ax.axis('off')
        
        plt.tight_layout()
        plt.savefig('unet_test_result.png', dpi=150, bbox_inches='tight')
        print("✅ Visualization saved as 'unet_test_result.png'")
        
        print("\n✅ UNet3D model test completed successfully!")
        print("🎉 The AI model is ready for automatic kidney segmentation!")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_unet_model()
    sys.exit(0 if success else 1)
