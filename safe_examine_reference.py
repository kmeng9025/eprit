"""
Safer examination of reference structure
"""

import scipy.io
import numpy as np

def safe_examine_reference():
    print("=== SAFE REFERENCE EXAMINATION ===")
    
    # Load reference
    reference = scipy.io.loadmat('process/exampleCorrect/correctExample.mat')
    ref_images = reference['images']
    
    print(f"Reference images shape: {ref_images.shape}")
    
    # Examine first image
    img1 = ref_images[0, 0]
    print(f"\nFirst image shape: {img1.shape}")
    print(f"First image dtype: {img1.dtype}")
    
    # Try to access Name safely
    try:
        name_obj = img1['Name'][0, 0]
        print(f"Name object type: {type(name_obj)}")
        print(f"Name object shape: {name_obj.shape if hasattr(name_obj, 'shape') else 'no shape'}")
        
        # Try different ways to access the name
        if hasattr(name_obj, 'shape'):
            if len(name_obj.shape) == 1 and name_obj.shape[0] > 0:
                actual_name = name_obj[0]
                print(f"Name from [0]: {actual_name}")
            elif len(name_obj.shape) == 2 and name_obj.shape[0] > 0:
                actual_name = name_obj[0, 0] if name_obj.shape[1] > 0 else name_obj[0]
                print(f"Name from [0,0] or [0]: {actual_name}")
        else:
            print(f"Name direct: {name_obj}")
            
    except Exception as e:
        print(f"Name extraction error: {e}")
    
    # Try to access ImageType safely  
    try:
        type_obj = img1['ImageType'][0, 0]
        print(f"ImageType object type: {type(type_obj)}")
        print(f"ImageType object: {type_obj}")
        
        if hasattr(type_obj, 'shape'):
            if len(type_obj.shape) == 1 and type_obj.shape[0] > 0:
                actual_type = type_obj[0]
                print(f"ImageType from [0]: {actual_type}")
            elif len(type_obj.shape) == 2 and type_obj.shape[0] > 0:
                actual_type = type_obj[0, 0] if type_obj.shape[1] > 0 else type_obj[0]
                print(f"ImageType from [0,0] or [0]: {actual_type}")
        else:
            print(f"ImageType direct: {type_obj}")
            
    except Exception as e:
        print(f"ImageType extraction error: {e}")
    
    # Try to access data safely
    try:
        data_obj = img1['data'][0, 0]
        print(f"Data object type: {type(data_obj)}")
        
        if hasattr(data_obj, 'shape'):
            print(f"Data shape: {data_obj.shape}")
            if hasattr(data_obj, 'min') and hasattr(data_obj, 'max'):
                print(f"Data range: {data_obj.min():.6f} to {data_obj.max():.6f}")
        else:
            print(f"Data direct: {data_obj}")
            
    except Exception as e:
        print(f"Data extraction error: {e}")
        
    # Show raw content for debugging
    print(f"\n--- Raw Image Content ---")
    for field_name in img1.dtype.names:
        try:
            field_content = img1[field_name]
            print(f"{field_name}: shape={field_content.shape}, dtype={field_content.dtype}")
            if field_name in ['Name', 'ImageType']:
                raw_content = field_content[0, 0]
                print(f"  Raw content: {raw_content}")
                print(f"  Content type: {type(raw_content)}")
        except Exception as e:
            print(f"{field_name}: Error - {e}")

if __name__ == "__main__":
    safe_examine_reference()
