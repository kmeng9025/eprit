"""
Examine reference structure in detail to understand exact format
"""

import scipy.io
import numpy as np

def examine_reference_details():
    print("=== DETAILED REFERENCE EXAMINATION ===")
    
    # Load reference
    reference = scipy.io.loadmat('process/exampleCorrect/correctExample.mat')
    ref_images = reference['images']
    
    print(f"Reference images shape: {ref_images.shape}")
    print(f"Reference images dtype: {ref_images.dtype}")
    
    # Examine first few images in detail
    for i in range(min(3, ref_images.shape[1])):
        print(f"\n--- Image {i+1} ---")
        img = ref_images[0, i]
        
        print(f"Image type: {type(img)}")
        print(f"Image dtype: {img.dtype}")
        print(f"Image shape: {img.shape}")
        
        if hasattr(img, 'dtype') and img.dtype.names:
            print(f"Fields: {img.dtype.names}")
            
            # Extract Name
            try:
                name_field = img['Name']
                print(f"Name field shape: {name_field.shape}")
                print(f"Name field type: {type(name_field)}")
                print(f"Name field dtype: {name_field.dtype}")
                
                # Navigate the nested structure
                name_data = name_field[0, 0]
                print(f"Name data shape: {name_data.shape}")
                print(f"Name data type: {type(name_data)}")
                
                if hasattr(name_data, 'shape') and len(name_data.shape) > 0:
                    if name_data.shape[0] > 0:
                        actual_name = name_data[0, 0]
                        print(f"Actual name shape: {actual_name.shape}")
                        print(f"Actual name type: {type(actual_name)}")
                        if hasattr(actual_name, 'shape') and len(actual_name) > 0:
                            print(f"Name value: '{actual_name[0]}'")
                        else:
                            print(f"Name value: '{actual_name}'")
                            
            except Exception as e:
                print(f"Error extracting name: {e}")
            
            # Extract ImageType
            try:
                type_field = img['ImageType']
                print(f"ImageType field shape: {type_field.shape}")
                
                type_data = type_field[0, 0]
                print(f"ImageType data shape: {type_data.shape}")
                
                if hasattr(type_data, 'shape') and len(type_data.shape) > 0:
                    if type_data.shape[0] > 0:
                        actual_type = type_data[0, 0]
                        if hasattr(actual_type, 'shape') and len(actual_type) > 0:
                            print(f"ImageType value: '{actual_type[0]}'")
                        else:
                            print(f"ImageType value: '{actual_type}'")
                            
            except Exception as e:
                print(f"Error extracting image type: {e}")
                
            # Extract data info
            try:
                data_field = img['data']
                print(f"Data shape: {data_field.shape}")
                print(f"Data range: {data_field.min():.6f} to {data_field.max():.6f}")
                
            except Exception as e:
                print(f"Error extracting data: {e}")

if __name__ == "__main__":
    examine_reference_details()
