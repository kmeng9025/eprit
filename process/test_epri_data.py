#!/usr/bin/env python3
"""
Simple test script to verify EPRI data structure and basic functionality
"""

import os
import sys
import glob
import numpy as np
import scipy.io as sio
from pathlib import Path

def test_data_access():
    """Test basic data access and structure"""
    base_dir = r"c:\Users\ftmen\Documents\EPRI"
    data_dir = os.path.join(base_dir, "DATA", "241202")
    
    print(f"Testing data access in: {data_dir}")
    
    # Check if directory exists
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    # Find processed files
    pattern = os.path.join(data_dir, "p*image4D_18x18_0p75gcm_file.mat")
    processed_files = glob.glob(pattern)
    processed_files.sort()
    
    print(f"✅ Found {len(processed_files)} processed files")
    
    if not processed_files:
        print("❌ No processed files found")
        return False
    
    # Test loading first file
    try:
        test_file = processed_files[0]
        print(f"📁 Testing file: {os.path.basename(test_file)}")
        
        mat_data = sio.loadmat(test_file, struct_as_record=False, squeeze_me=True)
        
        print("📊 File contents:")
        for key, value in mat_data.items():
            if not key.startswith('__'):
                print(f"  {key}: {type(value)}")
        
        # Check fit_data structure
        if 'fit_data' in mat_data:
            fit_data = mat_data['fit_data']
            print("\n📈 fit_data structure:")
            for attr in dir(fit_data):
                if not attr.startswith('_'):
                    try:
                        val = getattr(fit_data, attr)
                        if hasattr(val, 'shape'):
                            print(f"  {attr}: {type(val)} shape {val.shape}")
                        else:
                            print(f"  {attr}: {type(val)}")
                    except:
                        print(f"  {attr}: <unable to access>")
        
        print("\n✅ File structure test passed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing file: {e}")
        return False

def create_simple_project():
    """Create a simple project file from available data"""
    base_dir = r"c:\Users\ftmen\Documents\EPRI"
    data_dir = os.path.join(base_dir, "DATA", "241202")
    output_dir = os.path.join(base_dir, "process", "test_output")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Find processed files
    pattern = os.path.join(data_dir, "p*image4D_18x18_0p75gcm_file.mat")
    processed_files = glob.glob(pattern)
    processed_files.sort()
    
    if len(processed_files) < 4:
        print(f"❌ Need at least 4 processed files, found {len(processed_files)}")
        return None
    
    # Take first 4 files for pre-transfusion group
    pre_files = processed_files[:4]
    
    try:
        images_list = []
        
        for i, mat_file in enumerate(pre_files):
            print(f"📁 Processing: {os.path.basename(mat_file)}")
            
            # Load file
            mat_data = sio.loadmat(mat_file, struct_as_record=False, squeeze_me=True)
            
            if 'fit_data' not in mat_data:
                print(f"❌ No fit_data in {mat_file}")
                continue
            
            fit_data = mat_data['fit_data']
            
            # Extract volume data
            if hasattr(fit_data, 'P') and hasattr(fit_data, 'Size'):
                p_data = fit_data.P[0, :]  # First parameter
                size_info = fit_data.Size
                
                # Create 3D volume
                volume_shape = (int(size_info[0]), int(size_info[1]), int(size_info[2]))
                volume_data = np.zeros(volume_shape, dtype=np.float64)
                
                if hasattr(fit_data, 'Idx'):
                    idx = fit_data.Idx.astype(int) - 1  # Convert to 0-based
                    if np.max(idx) < volume_data.size:
                        volume_data.flat[idx] = p_data
                    else:
                        print(f"❌ Index out of bounds in {mat_file}")
                        continue
                
                # Create simple image structure
                image_name = f"BE{i+1}"
                
                class SimpleImage:
                    def __init__(self, data, name):
                        self.data = data
                        self.Name = name
                        self.shape = data.shape
                
                image_obj = SimpleImage(volume_data, image_name)
                images_list.append(image_obj)
                
                # Create BE_AMP for first image
                if i == 0:
                    be_amp_obj = SimpleImage(volume_data, 'BE_AMP')
                    images_list.append(be_amp_obj)
                
                print(f"✅ Created {image_name} with shape {volume_shape}")
        
        if not images_list:
            print("❌ No images could be processed")
            return None
        
        # Save simple project
        project_data = {
            'images': np.array(images_list, dtype=object),
            'num_images': len(images_list),
            'created_by': 'test_script'
        }
        
        output_file = os.path.join(output_dir, "test_project.mat")
        sio.savemat(output_file, project_data, do_compression=True)
        
        print(f"✅ Created test project: {output_file}")
        print(f"📊 Total images: {len(images_list)}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error creating project: {e}")
        return None

def test_roi_creation():
    """Test simple ROI creation"""
    print("\n🔵 Testing simple ROI creation...")
    
    # Create a simple 3D volume
    test_volume = np.random.rand(64, 64, 32) * 100
    
    # Create simple spherical ROI
    center = [32, 32, 16]
    radius = 15
    
    z, y, x = np.mgrid[0:64, 0:64, 0:32]
    distance = np.sqrt((z - center[0])**2 + (y - center[1])**2 + (x - center[2])**2)
    roi_mask = distance <= radius
    
    # Extract statistics
    roi_voxels = test_volume[roi_mask]
    stats = {
        'mean': np.mean(roi_voxels),
        'median': np.median(roi_voxels),
        'std': np.std(roi_voxels),
        'n_voxels': len(roi_voxels)
    }
    
    print(f"✅ ROI statistics:")
    print(f"  Mean: {stats['mean']:.2f}")
    print(f"  Median: {stats['median']:.2f}")
    print(f"  Std: {stats['std']:.2f}")
    print(f"  N voxels: {stats['n_voxels']}")
    
    return True

def main():
    """Main test function"""
    print("🧪 EPRI Data Structure Test")
    print("=" * 40)
    
    # Test 1: Data access
    print("\n1️⃣ Testing data access...")
    if not test_data_access():
        print("❌ Data access test failed")
        return 1
    
    # Test 2: Project creation
    print("\n2️⃣ Testing project creation...")
    project_file = create_simple_project()
    if not project_file:
        print("❌ Project creation test failed")
        return 1
    
    # Test 3: ROI creation
    print("\n3️⃣ Testing ROI creation...")
    if not test_roi_creation():
        print("❌ ROI creation test failed")
        return 1
    
    print("\n✅ All tests passed!")
    print("🚀 Ready to run the full automation scripts")
    return 0

if __name__ == "__main__":
    sys.exit(main())
