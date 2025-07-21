#!/usr/bin/env python3
"""
Manual ROI Creation Script for EPRI Data

This script provides an interactive interface to manually create ROI
when the UNet model is not available.

Usage:
    python manual_roi_creator.py --project-file path/to/project.mat
"""

import os
import sys
import numpy as np
import scipy.io as sio
import matplotlib.pyplot as plt
from matplotlib.widgets import RectangleSelector, EllipseSelector
import argparse
from pathlib import Path

class ManualROICreator:
    """Interactive ROI creation tool"""
    
    def __init__(self):
        self.roi_masks = []
        self.current_slice = 0
        self.image_data = None
        self.image_shape = None
        
    def load_project_file(self, project_file: str):
        """Load project file and find BE_AMP image"""
        try:
            mat_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
            
            if 'images' not in mat_data:
                print("❌ No images found in project file")
                return None
            
            images_struct = mat_data['images']
            
            # Find BE_AMP image
            for entry in images_struct:
                if hasattr(entry, 'Name') and 'BE_AMP' in str(entry.Name):
                    self.image_data = entry.data
                    self.image_shape = self.image_data.shape
                    print(f"✅ Found BE_AMP image with shape: {self.image_shape}")
                    return mat_data, entry
            
            print("❌ BE_AMP image not found")
            return None
            
        except Exception as e:
            print(f"❌ Error loading project file: {e}")
            return None
    
    def create_roi_interactive(self, output_file: str):
        """Create ROI interactively using matplotlib"""
        if self.image_data is None:
            print("❌ No image data loaded")
            return None
        
        print("\n🖱️  Interactive ROI Creation")
        print("Instructions:")
        print("1. Use the slider to navigate through slices")
        print("2. Click and drag to create rectangular ROIs")
        print("3. Press 'r' to reset current slice ROI")
        print("4. Press 'n' for next slice, 'p' for previous slice")
        print("5. Press 'q' to quit and save")
        
        # Initialize the plot
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # Show current slice
        self.current_slice = self.image_shape[2] // 2  # Start at middle slice
        im1 = ax1.imshow(self.image_data[:, :, self.current_slice], cmap='gray')
        ax1.set_title(f'BE_AMP - Slice {self.current_slice + 1}/{self.image_shape[2]}')
        
        # Initialize ROI mask
        roi_mask_3d = np.zeros(self.image_shape, dtype=bool)
        im2 = ax2.imshow(roi_mask_3d[:, :, self.current_slice], cmap='Reds', alpha=0.7)
        ax2.set_title('ROI Mask')
        
        # Rectangle selector for ROI creation
        def onselect(eclick, erelease):
            x1, y1 = int(eclick.xdata), int(eclick.ydata)
            x2, y2 = int(erelease.xdata), int(erelease.ydata)
            
            # Ensure coordinates are within bounds
            x1, x2 = max(0, min(x1, x2)), min(self.image_shape[1], max(x1, x2))
            y1, y2 = max(0, min(y1, y2)), min(self.image_shape[0], max(y1, y2))
            
            # Create ROI on current slice
            roi_mask_3d[y1:y2, x1:x2, self.current_slice] = True
            
            # Update display
            im2.set_array(roi_mask_3d[:, :, self.current_slice])
            fig.canvas.draw()
            
            print(f"✅ ROI created on slice {self.current_slice + 1}: ({x1},{y1}) to ({x2},{y2})")
        
        selector = RectangleSelector(ax1, onselect, useblit=True)
        
        def on_key(event):
            nonlocal roi_mask_3d
            
            if event.key == 'n':  # Next slice
                self.current_slice = min(self.current_slice + 1, self.image_shape[2] - 1)
                update_display()
            elif event.key == 'p':  # Previous slice
                self.current_slice = max(self.current_slice - 1, 0)
                update_display()
            elif event.key == 'r':  # Reset current slice
                roi_mask_3d[:, :, self.current_slice] = False
                update_display()
                print(f"🔄 Reset ROI on slice {self.current_slice + 1}")
            elif event.key == 'q':  # Quit and save
                plt.close()
                return roi_mask_3d
        
        def update_display():
            im1.set_array(self.image_data[:, :, self.current_slice])
            ax1.set_title(f'BE_AMP - Slice {self.current_slice + 1}/{self.image_shape[2]}')
            im2.set_array(roi_mask_3d[:, :, self.current_slice])
            fig.canvas.draw()
        
        fig.canvas.mpl_connect('key_press_event', on_key)
        
        plt.tight_layout()
        plt.show()
        
        return roi_mask_3d
    
    def create_simple_roi(self):
        """Create a simple spherical ROI in the center of the image"""
        if self.image_data is None:
            return None
        
        print("🔵 Creating simple spherical ROI in image center")
        
        # Create spherical ROI in center
        center = [s // 2 for s in self.image_shape]
        radius = min(self.image_shape) // 6
        
        roi_mask = np.zeros(self.image_shape, dtype=bool)
        
        z, y, x = np.mgrid[0:self.image_shape[0], 0:self.image_shape[1], 0:self.image_shape[2]]
        distance = np.sqrt((z - center[0])**2 + (y - center[1])**2 + (x - center[2])**2)
        roi_mask = distance <= radius
        
        print(f"✅ Created spherical ROI with radius {radius} at center {center}")
        return roi_mask
    
    def make_roi_struct(self, mask: np.ndarray, name: str) -> object:
        """Create ROI structure compatible with Arbuz"""
        class ROIStruct:
            def __init__(self, mask, name):
                self.data = mask.astype(bool)
                self.ImageType = '3DMASK'
                self.Name = name
                self.A = np.eye(4, dtype=np.float64)
                self.Anative = np.eye(4, dtype=np.float64)
                self.Aprime = np.eye(4, dtype=np.float64)
                self.isStore = 1
                self.isLoaded = 0
                self.Selected = 0
                self.Visible = 0
                self.box = np.array(mask.shape, dtype=np.float64)
                self.pars = np.array([])
                self.FileName = np.array('', dtype='U')
        
        return ROIStruct(mask, name)
    
    def save_project_with_roi(self, mat_data, be_amp_entry, roi_masks: list, output_file: str):
        """Save project file with ROI attached to all images"""
        try:
            # Create ROI structures
            roi_structs = []
            for i, mask in enumerate(roi_masks):
                roi_name = f"Kidney{i+1}" if i > 0 else "Kidney"
                roi_struct = self.make_roi_struct(mask, roi_name)
                roi_structs.append(roi_struct)
            
            # Attach ROI to BE_AMP
            roi_array = np.array(roi_structs, dtype=object)
            setattr(be_amp_entry, 'slaves', roi_array)
            
            # Transfer ROI to all other images
            images_struct = mat_data['images']
            for entry in images_struct:
                if hasattr(entry, 'Name') and 'BE_AMP' not in str(entry.Name):
                    roi_array_copy = np.array([roi for roi in roi_structs], dtype=object)
                    setattr(entry, 'slaves', roi_array_copy)
            
            # Save updated project file
            sio.savemat(output_file, mat_data, do_compression=True)
            print(f"✅ Project file with ROI saved: {output_file}")
            return output_file
            
        except Exception as e:
            print(f"❌ Error saving project file: {e}")
            return None

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Manual ROI Creator for EPRI Data')
    parser.add_argument('--project-file', type=str, required=True,
                       help='Path to the project .mat file')
    parser.add_argument('--output-file', type=str, default=None,
                       help='Output file path (default: adds _with_manual_roi suffix)')
    parser.add_argument('--mode', type=str, choices=['interactive', 'simple'], default='interactive',
                       help='ROI creation mode: interactive or simple (default: interactive)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.project_file):
        print(f"❌ Project file not found: {args.project_file}")
        return 1
    
    # Set output file
    if args.output_file is None:
        project_path = Path(args.project_file)
        args.output_file = str(project_path.with_name(f"{project_path.stem}_with_manual_roi.mat"))
    
    try:
        # Create ROI creator
        creator = ManualROICreator()
        
        # Load project file
        result = creator.load_project_file(args.project_file)
        if result is None:
            return 1
        
        mat_data, be_amp_entry = result
        
        # Create ROI
        if args.mode == 'interactive':
            print("\n🖱️  Starting interactive ROI creation...")
            roi_mask = creator.create_roi_interactive(args.output_file)
        else:
            print("\n🔵 Creating simple ROI...")
            roi_mask = creator.create_simple_roi()
        
        if roi_mask is None:
            print("❌ ROI creation failed")
            return 1
        
        # Save project with ROI
        result = creator.save_project_with_roi(mat_data, be_amp_entry, [roi_mask], args.output_file)
        
        if result:
            print(f"\n✅ Manual ROI creation completed!")
            print(f"📁 Output file: {result}")
            print(f"💡 You can now use this file with the ROI extractor script")
        else:
            print("\n❌ Failed to save project file")
            return 1
        
    except KeyboardInterrupt:
        print("\n⏸️ ROI creation interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
