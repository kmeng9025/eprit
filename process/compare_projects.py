#!/usr/bin/env python3
"""
Compare reference project file with our generated project
"""

import scipy.io as sio
import numpy as np
from pathlib import Path

# Load the reference project
ref_project_file = "exampleCorrect/correctExample.mat"
print(f"🔍 Loading reference project: {ref_project_file}")
ref_project = sio.loadmat(ref_project_file, struct_as_record=False, squeeze_me=True)

print(f"\n📋 Reference project keys:")
for key in ref_project.keys():
    if not key.startswith('__'):
        print(f"   {key}: {type(ref_project[key])}")

if 'images' in ref_project:
    images = ref_project['images']
    print(f"\n🖼️ Reference project has {len(images)} images:")
    
    for i, img in enumerate(images):
        if hasattr(img, 'Name'):
            name = str(img.Name)
            image_type = getattr(img, 'ImageType', 'Unknown')
            data_shape = getattr(img.data, 'shape', 'No data') if hasattr(img, 'data') else 'No data'
            
            print(f"   {i+1:2d}. {name} - Type: {image_type} - Shape: {data_shape}")
            
            # Check data range for first few images
            if i < 3 and hasattr(img, 'data'):
                data = img.data
                if data is not None and data.size > 0:
                    print(f"       Data range: [{np.min(data):.3f}, {np.max(data):.3f}], Mean: {np.mean(data):.3f}")

# Check our latest generated project
print(f"\n" + "="*60)
latest_dir = max(Path("../automated_outputs").glob("run_*"), key=lambda x: x.name)
our_project_file = latest_dir / "project.mat"
print(f"🔍 Loading our project: {our_project_file}")

if our_project_file.exists():
    our_project = sio.loadmat(str(our_project_file), struct_as_record=False, squeeze_me=True)
    
    if 'images' in our_project:
        our_images = our_project['images']
        print(f"\n🖼️ Our project has {len(our_images)} images:")
        
        for i, img in enumerate(our_images):
            if hasattr(img, 'Name'):
                name = str(img.Name)
                image_type = getattr(img, 'ImageType', 'Unknown')
                data_shape = getattr(img.data, 'shape', 'No data') if hasattr(img, 'data') else 'No data'
                
                print(f"   {i+1:2d}. {name} - Type: {image_type} - Shape: {data_shape}")
                
                # Check data range for first few images
                if i < 3 and hasattr(img, 'data'):
                    data = img.data
                    if data is not None and data.size > 0:
                        print(f"       Data range: [{np.min(data):.3f}, {np.max(data):.3f}], Mean: {np.mean(data):.3f}")
    
    print(f"\n📊 Comparison:")
    print(f"   Reference images: {len(ref_project['images']) if 'images' in ref_project else 0}")
    print(f"   Our images: {len(our_project['images']) if 'images' in our_project else 0}")
else:
    print(f"❌ Our project file not found: {our_project_file}")
