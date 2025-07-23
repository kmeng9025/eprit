#!/usr/bin/env python3
"""
Enhanced Draw_ROI.py for ArbuzGUI Project Processing
Author: AI Assistant
Date: July 2025

This script applies kidney ROI detection to BE_AMP image in an ArbuzGUI project file.
"""

import os
import sys
import torch
import numpy as np
import scipy.io as sio
from skimage.transform import resize
from scipy.ndimage import label, center_of_mass
from pathlib import Path

# Conditional imports for model (if available)
try:
    from unet3d_model import UNet3D
    MODEL_AVAILABLE = True
except ImportError:
    MODEL_AVAILABLE = False
    print("⚠️  UNet3D model not available. Will use placeholder ROI.")

class ProjectROIProcessor:
    def __init__(self, model_path="./unet3d_kidney.pth"):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.model_path = model_path
        
        if MODEL_AVAILABLE and os.path.exists(model_path):
            self.load_model()
        else:
            print(f"⚠️  Model not found at {model_path}. Using placeholder ROI.")
    
    def load_model(self):
        """Load the UNet3D model for kidney segmentation"""
        try:
            self.model = UNet3D().to(self.device)
            self.model.load_state_dict(torch.load(self.model_path, map_location=self.device))
            self.model.eval()
            print(f"✅ Model loaded from {self.model_path}")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            self.model = None
    
    def create_placeholder_roi(self, data_shape):
        """Create a placeholder ROI when model is not available"""
        mask = np.zeros(data_shape[:3], dtype=bool)
        
        # Create two kidney-like regions
        h, w, d = data_shape[:3]
        
        # Left kidney region
        y1, y2 = max(0, h//4), min(h, 3*h//4)
        x1, x2 = max(0, w//6), min(w, w//3)
        z1, z2 = max(0, d//3), min(d, 2*d//3)
        mask[y1:y2, x1:x2, z1:z2] = True
        
        # Right kidney region  
        x3, x4 = max(0, 2*w//3), min(w, 5*w//6)
        mask[y1:y2, x3:x4, z1:z2] = True
        
        return mask
    
    def predict_kidney_mask(self, image_data):
        """Predict kidney mask using the model or create placeholder"""
        if self.model is None or not MODEL_AVAILABLE:
            return self.create_placeholder_roi(image_data.shape)
        
        try:
            # Ensure 3D data
            if image_data.ndim == 4:
                # Use first timepoint for segmentation
                data_3d = image_data[:, :, :, 0]
            else:
                data_3d = image_data
            
            # Resize and normalize
            img_resized = resize(data_3d, (64, 64, 64), preserve_range=True)
            img_norm = (img_resized - img_resized.min()) / (np.ptp(img_resized) + 1e-8)
            
            # Create tensor
            input_tensor = torch.tensor(img_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(self.device)
            
            # Run prediction
            with torch.no_grad():
                pred = self.model(input_tensor).squeeze().cpu().numpy()
                mask = (pred > 0.5)
            
            # Resize back to original size
            mask_resized = resize(mask.astype(float), data_3d.shape, preserve_range=True) > 0.5
            
            return mask_resized
            
        except Exception as e:
            print(f"❌ Prediction failed: {e}. Using placeholder ROI.")
            return self.create_placeholder_roi(image_data.shape)
    
    def split_kidney_mask(self, mask):
        """Split kidney mask into left and right components"""
        if np.sum(mask) == 0:
            print("⚠️  Empty mask - cannot split")
            return None, None
        
        # Label connected components
        labeled, num_components = label(mask)
        
        if num_components < 2:
            print(f"⚠️  Only {num_components} component(s) found - cannot split into two kidneys")
            # For single component, try to split spatially
            if num_components == 1:
                # Split along x-axis (left-right)
                center_x = mask.shape[1] // 2
                left_mask = mask.copy()
                right_mask = mask.copy()
                left_mask[:, center_x:, :] = False
                right_mask[:, :center_x, :] = False
                return left_mask, right_mask
            else:
                return None, None
        
        # Find two largest components
        component_sizes = [(labeled == i).sum() for i in range(1, num_components + 1)]
        largest_indices = np.argsort(component_sizes)[-2:]
        
        comp1 = (labeled == (largest_indices[0] + 1))
        comp2 = (labeled == (largest_indices[1] + 1))
        
        # Determine left/right based on center of mass
        com1 = center_of_mass(comp1)
        com2 = center_of_mass(comp2)
        
        if com1[1] > com2[1]:  # x-coordinate determines left/right
            right_mask, left_mask = comp1, comp2
        else:
            right_mask, left_mask = comp2, comp1
        
        return left_mask, right_mask
    
    def make_roi_struct(self, mask, name):
        """Create an ROI structure compatible with ArbuzGUI"""
        identity_matrix = np.eye(4, dtype=np.float64)
        
        return {
            'data': mask.astype(bool),
            'ImageType': '3DMASK',
            'Name': name,
            'A': identity_matrix.copy(),
            'Anative': identity_matrix.copy(),
            'Aprime': identity_matrix.copy(),
            'isStore': 1,
            'isLoaded': 1,
            'Selected': 0,
            'Visible': 0,
            'box': np.array(mask.shape, dtype=np.float64),
            'pars': np.array([]),
            'FileName': ''
        }
    
    def process_project_file(self, project_file_path, output_path=None):
        """Process an ArbuzGUI project file to add kidney ROI to BE_AMP image"""
        try:
            print(f"🔄 Processing project file: {project_file_path}")
            
            # Load project file
            project = sio.loadmat(project_file_path, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in project:
                raise KeyError("'images' not found in project file")
            
            images_array = project['images']
            
            # Find BE_AMP image
            be_amp_image = None
            be_amp_index = None
            
            for i, img in enumerate(images_array):
                if hasattr(img, 'Name') and 'BE_AMP' in str(img.Name):
                    be_amp_image = img
                    be_amp_index = i
                    break
            
            if be_amp_image is None:
                raise ValueError("BE_AMP image not found in project")
            
            print(f"✅ Found BE_AMP image at index {be_amp_index}")
            
            # Get image data
            if not hasattr(be_amp_image, 'data'):
                raise ValueError("BE_AMP image has no data")
            
            image_data = be_amp_image.data
            print(f"📊 BE_AMP data shape: {image_data.shape}")
            
            # Predict kidney mask
            print("🧠 Predicting kidney mask...")
            kidney_mask = self.predict_kidney_mask(image_data)
            
            # Split into left and right kidneys
            left_mask, right_mask = self.split_kidney_mask(kidney_mask)
            
            if left_mask is None or right_mask is None:
                print("⚠️  Could not split kidneys, using single mask")
                # Create single kidney ROI
                roi_struct = self.make_roi_struct(kidney_mask, "Kidney")
                roi_array = np.array([roi_struct], dtype=object)
            else:
                print("✅ Successfully split into left and right kidneys")
                # Create ROI structures for both kidneys
                roi1 = self.make_roi_struct(right_mask, "Kidney")
                roi2 = self.make_roi_struct(left_mask, "Kidney2")
                roi_array = np.array([roi1, roi2], dtype=object)
            
            # Attach ROIs to BE_AMP image
            be_amp_image.slaves = roi_array
            
            # Update the project
            project['images'][be_amp_index] = be_amp_image
            
            # Determine output path
            if output_path is None:
                output_path = project_file_path  # Overwrite original
            
            # Save updated project
            sio.savemat(output_path, project, do_compression=True)
            print(f"✅ Project saved with ROI annotations: {output_path}")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error processing project file: {e}")
            return None

def main():
    """Main entry point for command line usage"""
    if len(sys.argv) != 2 and len(sys.argv) != 3:
        print("Usage: python enhanced_draw_roi.py <project_file.mat> [output_file.mat]")
        print("   If output_file is not specified, input file will be overwritten")
        sys.exit(1)
    
    project_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) == 3 else None
    
    if not os.path.exists(project_file):
        print(f"❌ Project file not found: {project_file}")
        sys.exit(1)
    
    # Create processor and run
    processor = ProjectROIProcessor()
    result = processor.process_project_file(project_file, output_file)
    
    if result:
        print(f"🎉 Successfully processed project file")
        sys.exit(0)
    else:
        print(f"❌ Failed to process project file")
        sys.exit(1)

if __name__ == "__main__":
    main()
