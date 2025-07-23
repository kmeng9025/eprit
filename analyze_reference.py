"""
Examine the reference file structure exactly to understand what we need to create
"""
import scipy.io as sio
import numpy as np

def analyze_reference():
    # Load the reference file and examine its EXACT structure
    ref_file = r'process\exampleCorrect\correctExample.mat'
    ref_data = sio.loadmat(ref_file)

    print('=== REFERENCE FILE ANALYSIS ===')
    print('Top-level keys:', list(ref_data.keys()))

    if 'images' in ref_data:
        images = ref_data['images']
        print(f'Images type: {type(images)}')
        print(f'Images shape: {images.shape}')
        print(f'Images dtype: {images.dtype}')
        
        if hasattr(images.dtype, 'names') and images.dtype.names:
            print(f'Number of images: {len(images.dtype.names)}')
            print('Image UIDs:', images.dtype.names[:5], '...')
            
            # Examine the first image in detail
            first_uid = images.dtype.names[0]
            first_img = images[first_uid][0, 0]
            print(f'\nFirst image UID: {first_uid}')
            print(f'First image type: {type(first_img)}')
            print(f'First image dtype: {first_img.dtype}')
            print('First image fields:', first_img.dtype.names)
            
            # Get the actual data and metadata
            for field in first_img.dtype.names:
                value = first_img[field]
                if field == 'name':
                    print(f'  {field}: "{value[0]}"')
                elif field == 'data':
                    data = np.array(value)
                    print(f'  {field}: shape {data.shape}, range {np.min(data):.6f} to {np.max(data):.6f}')
                elif hasattr(value, 'shape'):
                    print(f'  {field}: shape {value.shape}')
                else:
                    print(f'  {field}: {value}')
                    
            # Check a few more images to see the pattern
            print('\n=== PATTERN ANALYSIS ===')
            for i, uid in enumerate(images.dtype.names[:5]):
                img = images[uid][0, 0]
                name = img['name'][0]
                data = np.array(img['data'])
                print(f'{i+1}. UID: {uid}, Name: "{name}", Shape: {data.shape}, Range: {np.min(data):.3f} to {np.max(data):.3f}')

if __name__ == "__main__":
    analyze_reference()
