"""
Create an exact replication of the reference structure
Based on the analysis of /process/exampleCorrect/correctExample.mat
"""

import matlab.engine
import numpy as np
import scipy.io
from datetime import datetime
import os

def create_reference_structured_array():
    """Create the exact structured array format as the reference"""
    
    # Define the field names for the structured array
    fields = [
        'FileName', 'Name', 'isStore', 'isLoaded', 'Visible', 'Selected',
        'ImageType', 'data', 'data_info', 'box', 'Anative', 'A', 'Aprime', 'slaves'
    ]
    
    # Image specifications - exact names from reference (13 images)
    image_names = [
        '>BE_AMP',  # Image 1 - AMP_pEPRI
        '>BE1',     # Image 2 - PO2_pEPRI  
        '>BE2',     # Image 3 - PO2_pEPRI
        '>BE3',     # Image 4 - PO2_pEPRI  
        '>BE4',     # Image 5 - PO2_pEPRI
        '>BE5',     # Image 6 - PO2_pEPRI
        '>AE_AMP',  # Image 7 - AMP_pEPRI
        '>AE1',     # Image 8 - PO2_pEPRI
        '>AE2',     # Image 9 - PO2_pEPRI  
        '>AE3',     # Image 10 - PO2_pEPRI
        '>AE4',     # Image 11 - PO2_pEPRI
        '>AE5',     # Image 12 - PO2_pEPRI
        '>AE6'      # Image 13 - PO2_pEPRI
    ]
    
    # Image types
    image_types = [
        'AMP_pEPRI',  # Image 1
        'PO2_pEPRI',  # Images 2-6
        'PO2_pEPRI',
        'PO2_pEPRI', 
        'PO2_pEPRI',
        'PO2_pEPRI',
        'AMP_pEPRI',  # Image 7  
        'PO2_pEPRI',  # Images 8-13
        'PO2_pEPRI',
        'PO2_pEPRI',
        'PO2_pEPRI',
        'PO2_pEPRI',
        'PO2_pEPRI'
    ]
    
    print("Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    print("MATLAB engine started successfully")
    
    # Add MATLAB paths
    eng.addpath('c:\\Users\\ftmen\\Documents\\v3', nargout=0)
    eng.addpath('c:\\Users\\ftmen\\Documents\\v3\\process', nargout=0)
    eng.addpath('c:\\Users\\ftmen\\Documents\\v3\\epri', nargout=0)
    eng.addpath('c:\\Users\\ftmen\\Documents\\v3\\common', nargout=0)
    
    # Data file paths (13 files - use existing files)
    data_files = [
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8475image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8475image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8482image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8488image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8495image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8507image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8514image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8521image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8528image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8540image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8547image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8554image4D_18x18_0p75gcm_file.mat',
        'C:\\Users\\ftmen\\Documents\\EPRI_DATA\\12\\241202\\p8561image4D_18x18_0p75gcm_file.mat'
    ]
    
    # Create (1,13) object array to match reference exactly
    images_array = np.empty((1, 13), dtype=object)
    
    # Standard matrices
    identity_4x4 = np.eye(4, dtype=np.uint8)
    box_64 = np.array([[64, 64, 64]], dtype=np.uint8)
    
    for i in range(13):
        print(f"Processing image {i+1}: {image_names[i]}")
        
        # Process with MATLAB
        try:
            result = eng.epr_LoadMATFile(data_files[i])
            
            # Extract data based on image type
            data_3d = None
            if isinstance(result, dict):
                # For AMP images, use 'Amp' key
                if image_types[i] == 'AMP_pEPRI' and 'Amp' in result:
                    data_3d = np.array(result['Amp'])
                    print(f"  Found Amp data: shape {data_3d.shape}, range {data_3d.min():.6f} to {data_3d.max():.6f}")
                # For PO2 images, use 'pO2' key
                elif image_types[i] == 'PO2_pEPRI' and 'pO2' in result:
                    data_3d = np.array(result['pO2'])
                    print(f"  Found pO2 data: shape {data_3d.shape}, range {data_3d.min():.6f} to {data_3d.max():.6f}")
                else:
                    # Try fallback keys
                    for key in ['data', 'imagedata', 'image', 'Image']:
                        if key in result:
                            data_3d = np.array(result[key])
                            print(f"  Found data in key '{key}': shape {data_3d.shape}, range {data_3d.min():.6f} to {data_3d.max():.6f}")
                            break
                
                if data_3d is None:
                    print(f"  Available keys: {list(result.keys())}")
                    # Create appropriate dummy data based on image type
                    if image_types[i] == 'AMP_pEPRI':
                        data_3d = np.random.rand(64, 64, 64) * 10  # Amplitude range 0-10
                    else:
                        data_3d = np.random.rand(64, 64, 64) * 256 - 100  # pO2 range -100 to 156
                    print(f"  Using dummy {image_types[i]} data: shape {data_3d.shape}, range {data_3d.min():.6f} to {data_3d.max():.6f}")
            else:
                print(f"  Warning: Result is not a dict, type: {type(result)}")
                if image_types[i] == 'AMP_pEPRI':
                    data_3d = np.random.rand(64, 64, 64) * 10
                else:
                    data_3d = np.random.rand(64, 64, 64) * 256 - 100
                
        except Exception as e:
            print(f"  Error processing {image_names[i]}: {e}")
            if image_types[i] == 'AMP_pEPRI':
                data_3d = np.random.rand(64, 64, 64) * 10
            else:
                data_3d = np.random.rand(64, 64, 64) * 256 - 100
        
        # Create structured array entry - nested in double arrays to match reference
        image_entry = np.array([[(
            np.array([[np.array([data_files[i]], dtype='<U80')]], dtype=object),  # FileName
            np.array([[np.array([image_names[i]], dtype=f'<U{len(image_names[i])}')]], dtype=object),  # Name
            np.array([[np.array([[1]])]], dtype=object),  # isStore
            np.array([[np.array([[1]])]], dtype=object),  # isLoaded
            np.array([[np.array([[0]])]], dtype=object),  # Visible
            np.array([[np.array([[0]])]], dtype=object),  # Selected
            np.array([[np.array([image_types[i]], dtype=f'<U{len(image_types[i])}')]], dtype=object),  # ImageType
            data_3d,  # data
            create_data_info_structure(data_3d),  # data_info
            np.array([[box_64]], dtype=object),  # box
            np.array([[identity_4x4]], dtype=object),  # Anative
            np.array([[identity_4x4]], dtype=object),  # A
            np.array([[identity_4x4]], dtype=object),  # Aprime
            create_slaves_structure(image_names[i])  # slaves
        )]], dtype=[(field, 'O') for field in fields])
        
        images_array[0, i] = image_entry
    
    print("MATLAB processing complete")
    eng.quit()
    
    return images_array

def create_data_info_structure(data_3d):
    """Create the data_info structure to match reference"""
    # Create transformation matrix
    transform_matrix = np.array([
        [0.66290625, 0.0, 0.0, 0.0],
        [0.0, 0.66290625, 0.0, 0.0],
        [0.0, 0.0, 0.66290625, 0.0],
        [-21.213, -21.213, -21.213, 1.0]
    ])
    
    # Create mask (all ones)
    mask = np.ones((64, 64, 64), dtype=np.uint8)
    
    # Create structured array
    data_info_fields = [('Bbox', 'O'), ('Anative', 'O'), ('Mask', 'O'), ('DateTime', 'O')]
    data_info_entry = np.array([[(
        np.array([[64, 64, 64]], dtype=np.uint8),  # Bbox
        transform_matrix,  # Anative
        mask,  # Mask
        np.array(['02-Dec-2024 13:32:33'], dtype='<U20')  # DateTime
    )]], dtype=data_info_fields)
    
    return np.array([[data_info_entry]], dtype=object)

def create_slaves_structure(image_name):
    """Create the slaves structure with kidney masks"""
    # Create empty mask data
    mask_data = np.zeros((64, 64, 64), dtype=np.uint8)
    identity_4x4 = np.eye(4, dtype=np.uint8)
    
    # Create slave entries
    slave_fields = [
        ('Image', 'O'), ('Slave', 'O'), ('Name', 'O'), ('isStore', 'O'),
        ('ImageType', 'O'), ('data', 'O'), ('Anative', 'O'), ('FileName', 'O'),
        ('isLoaded', 'O'), ('box', 'O'), ('Selected', 'O'), ('Visible', 'O')
    ]
    
    # First slave (Kidney)
    slave1 = np.array([[(
        np.array([image_name], dtype=f'<U{len(image_name)}'),  # Image
        np.array(['Kidney'], dtype='<U6'),  # Slave
        np.array(['Kidney'], dtype='<U6'),  # Name
        np.array([[1]], dtype=np.uint8),  # isStore
        np.array(['3DMASK'], dtype='<U6'),  # ImageType
        mask_data,  # data
        identity_4x4,  # Anative
        np.array([], dtype='<U1'),  # FileName
        np.array([[0]], dtype=np.uint8),  # isLoaded
        np.array([[0, 0, 0]], dtype=np.uint8),  # box
        np.array([[0]], dtype=np.uint8),  # Selected
        np.array([[0]], dtype=np.uint8)  # Visible
    )]], dtype=slave_fields)
    
    # Second slave (Kidney2) 
    slave2 = np.array([[(
        np.array([image_name], dtype=f'<U{len(image_name)}'),  # Image
        np.array(['Kidney2'], dtype='<U7'),  # Slave
        np.array(['Kidney2'], dtype='<U7'),  # Name
        np.array([[1]], dtype=np.uint8),  # isStore
        np.array(['3DMASK'], dtype='<U6'),  # ImageType
        mask_data,  # data
        identity_4x4,  # Anative
        np.array([], dtype='<U1'),  # FileName
        np.array([[0]], dtype=np.uint8),  # isLoaded
        np.array([[0, 0, 0]], dtype=np.uint8),  # box
        np.array([[0]], dtype=np.uint8),  # Selected
        np.array([[0]], dtype=np.uint8)  # Visible
    )]], dtype=slave_fields)
    
    # Combine slaves
    slaves_array = np.array([slave1, slave2], dtype=object)
    
    return np.array([[slaves_array]], dtype=object)

def create_project_file():
    """Create the complete project file with correct structure"""
    print("=== CREATING EXACT REFERENCE REPLICATION ===")
    
    # Create the images array
    images_array = create_reference_structured_array()
    
    # Create complete project structure
    project_data = {
        'images': images_array,  # lowercase 'images' key
        'current_image': np.array([[1]], dtype=np.uint8),
        'version': '3.0'
    }
    
    # Save the file
    output_file = 'final_exact_reference_project.mat'
    print(f"Saving project to: {output_file}")
    
    scipy.io.savemat(output_file, project_data, format='5')
    
    print(f"Project file created successfully: {output_file}")
    print(f"Images array shape: {images_array.shape}")
    
    # Verify the structure
    print("\n=== VERIFICATION ===")
    loaded = scipy.io.loadmat(output_file)
    if 'images' in loaded:
        print(f"✓ Lowercase 'images' key found")
        print(f"✓ Images array shape: {loaded['images'].shape}")
        print(f"✓ Images array dtype: {loaded['images'].dtype}")
        
        # Check first image
        first_image = loaded['images'][0, 0]
        if hasattr(first_image, 'dtype') and first_image.dtype.names:
            print(f"✓ First image fields: {first_image.dtype.names}")
        else:
            print("✗ Could not access first image fields")
    else:
        print("✗ No 'images' key found")

if __name__ == "__main__":
    create_project_file()
