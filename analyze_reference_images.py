"""
Analyze the reference images array structure
"""
import scipy.io as sio
import numpy as np

def analyze_reference_images():
    ref_file = r'process\exampleCorrect\correctExample.mat'
    ref_data = sio.loadmat(ref_file)

    print('=== REFERENCE IMAGES ARRAY ANALYSIS ===')
    
    if 'images' in ref_data:
        images = ref_data['images']
        print(f'Images shape: {images.shape}')  # Should be (1, 13)
        print(f'Images dtype: {images.dtype}')
        
        print(f'\nExamining each of the {images.shape[1]} images:')
        
        for i in range(images.shape[1]):
            img_obj = images[0, i]
            print(f'\nImage {i+1}:')
            print(f'  Type: {type(img_obj)}')
            
            if hasattr(img_obj, 'dtype') and img_obj.dtype.names:
                print(f'  Fields: {img_obj.dtype.names}')
                
                # Extract key information
                for field in img_obj.dtype.names:
                    value = img_obj[field]
                    if field == 'name':
                        print(f'    {field}: "{value[0]}"')
                    elif field == 'data':
                        try:
                            # Handle nested array structure
                            if hasattr(value, 'shape') and value.size > 0:
                                # Try to extract actual data array
                                data = value
                                while hasattr(data, 'shape') and data.size == 1 and hasattr(data.flat[0], 'shape'):
                                    data = data.flat[0]
                                if hasattr(data, 'shape') and len(data.shape) >= 2:
                                    print(f'    {field}: shape {data.shape}, range {float(np.min(data)):.6f} to {float(np.max(data)):.6f}')
                                else:
                                    print(f'    {field}: could not extract numeric data, type {type(data)}')
                            else:
                                print(f'    {field}: empty or no shape')
                        except Exception as e:
                            print(f'    {field}: error extracting data - {e}')
                    elif field in ['type', 'imageType']:
                        print(f'    {field}: "{value[0] if hasattr(value, "__len__") and len(value) > 0 else value}"')
                    elif hasattr(value, 'shape') and value.size < 10:
                        print(f'    {field}: {value}')
                    elif hasattr(value, 'shape'):
                        print(f'    {field}: shape {value.shape}')
                    else:
                        print(f'    {field}: {value}')
            else:
                print(f'  No structured fields, raw type: {type(img_obj)}')
                if hasattr(img_obj, 'shape'):
                    print(f'  Shape: {img_obj.shape}')

if __name__ == "__main__":
    analyze_reference_images()
