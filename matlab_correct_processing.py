"""
Correct Project Creation - Using MATLAB Engine to replicate exact reference processing
This script will use MATLAB's epr_LoadMATFile function exactly as used in the reference
"""

import matlab.engine
import scipy.io as sio
import numpy as np
import os
from pathlib import Path

def start_matlab_engine():
    """Start MATLAB engine with proper paths"""
    print("Starting MATLAB engine...")
    eng = matlab.engine.start_matlab()
    
    # Add paths exactly as in the reference environment
    eng.addpath(r'c:\Users\ftmen\Documents\v3\epri')
    eng.addpath(r'c:\Users\ftmen\Documents\v3\common')
    eng.addpath(r'c:\Users\ftmen\Documents\v3\ibGUI')
    eng.addpath(r'c:\Users\ftmen\Documents\v3\Arbuz2.0')
    
    return eng

def load_image_with_matlab(eng, mat_file_path):
    """Use MATLAB's epr_LoadMATFile to load image exactly as reference"""
    print(f"Loading {mat_file_path} with MATLAB epr_LoadMATFile...")
    
    try:
        # Call MATLAB function exactly as used in reference
        # This is the same function that created the reference images
        result = eng.epr_LoadMATFile(mat_file_path, nargout=1)
        
        # Convert MATLAB result to Python format
        if result:
            print("Successfully loaded with MATLAB")
            return result
        else:
            print("MATLAB function returned empty result")
            return None
            
    except Exception as e:
        print(f"Error calling MATLAB function: {e}")
        return None

def create_correct_project():
    """Create project using exact MATLAB processing"""
    
    # Start MATLAB engine
    eng = start_matlab_engine()
    
    try:
        # Use the exact same source files as in reference
        source_files = [
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8475image4D_18x18_0p75gcm_file.mat',  # BE_AMP + BE1
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8482image4D_18x18_0p75gcm_file.mat',  # BE2
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8488image4D_18x18_0p75gcm_file.mat',  # BE3
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8495image4D_18x18_0p75gcm_file.mat',  # BE4
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8507image4D_18x18_0p75gcm_file.mat',  # ME1
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8514image4D_18x18_0p75gcm_file.mat',  # ME2
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8521image4D_18x18_0p75gcm_file.mat',  # ME3
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8528image4D_18x18_0p75gcm_file.mat',  # ME4
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8540image4D_18x18_0p75gcm_file.mat',  # AE1
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8547image4D_18x18_0p75gcm_file.mat',  # AE2
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8554image4D_18x18_0p75gcm_file.mat',  # AE3
            r'c:\Users\ftmen\Documents\v3\DATA\241202\p8561image4D_18x18_0p75gcm_file.mat'   # AE4
        ]
        
        # Image names exactly as in reference (with > prefix)
        image_names = [
            '>BE_AMP', '>BE1', '>BE2', '>BE3', '>BE4',
            '>ME1', '>ME2', '>ME3', '>ME4',
            '>AE1', '>AE2', '>AE3', '>AE4'
        ]
        
        # Image types
        image_types = [
            'AMP_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI',
            'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI',
            'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI', 'PO2_pEPRI'
        ]
        
        processed_images = []
        
        # Process first file to get both BE_AMP and BE1
        first_result = load_image_with_matlab(eng, source_files[0])
        
        if first_result:
            # Extract amplitude image (BE_AMP)
            if hasattr(first_result, 'Amp'):
                amp_data = np.array(first_result.Amp)
                amp_image = create_arbuz_image(amp_data, '>BE_AMP', 'AMP_pEPRI', source_files[0])
                processed_images.append(amp_image)
                print(f"Created >BE_AMP: range {np.min(amp_data):.6f} to {np.max(amp_data):.6f}")
            
            # Extract pO2 image (BE1)
            if hasattr(first_result, 'pO2'):
                po2_data = np.array(first_result.pO2)
                po2_image = create_arbuz_image(po2_data, '>BE1', 'PO2_pEPRI', source_files[0])
                processed_images.append(po2_image)
                print(f"Created >BE1: range {np.min(po2_data):.6f} to {np.max(po2_data):.6f}")
        
        # Process remaining files for BE2-AE4 (pO2 only)
        for i, (source_file, name, img_type) in enumerate(zip(source_files[1:], image_names[2:], image_types[2:]), 1):
            result = load_image_with_matlab(eng, source_file)
            
            if result and hasattr(result, 'pO2'):
                po2_data = np.array(result.pO2)
                po2_image = create_arbuz_image(po2_data, name, img_type, source_file)
                processed_images.append(po2_image)
                print(f"Created {name}: range {np.min(po2_data):.6f} to {np.max(po2_data):.6f}")
        
        # Create project structure
        project = create_project_structure(processed_images)
        
        # Save project
        output_dir = r'c:\Users\ftmen\Documents\v3\corrected_matlab_outputs'
        os.makedirs(output_dir, exist_ok=True)
        
        project_file = os.path.join(output_dir, 'corrected_project.mat')
        sio.savemat(project_file, project, do_compression=True)
        
        print(f"\nCorrect project saved: {project_file}")
        print(f"Total images: {len(processed_images)}")
        
        return project_file
        
    finally:
        eng.quit()

def create_arbuz_image(data, name, image_type, source_file):
    """Create ArbuzGUI image structure"""
    identity = np.eye(4, dtype=np.float64)
    
    return {
        'FileName': np.array([source_file], dtype='U200'),
        'Name': np.array([name], dtype='U50'),
        'isStore': np.array([[0]], dtype=np.int32),
        'isLoaded': np.array([[1]], dtype=np.int32),
        'Visible': np.array([[1]], dtype=np.int32),
        'Selected': np.array([[0]], dtype=np.int32),
        'ImageType': np.array([image_type], dtype='U50'),
        'data': data,
        'data_info': np.array([[]], dtype=object),
        'box': np.array(data.shape, dtype=np.float64),
        'Anative': identity.copy(),
        'A': identity.copy(),
        'Aprime': identity.copy(),
        'slaves': np.array([[]], dtype=object)
    }

def create_project_structure(images):
    """Create complete ArbuzGUI project structure"""
    # Create images array
    num_images = len(images)
    images_array = np.empty((1, num_images), dtype=object)
    
    for i, img in enumerate(images):
        # Create proper MATLAB struct format
        img_struct = np.empty(1, dtype=[
            ('FileName', 'O'), ('Name', 'O'), ('isStore', 'O'), ('isLoaded', 'O'),
            ('Visible', 'O'), ('Selected', 'O'), ('ImageType', 'O'), ('data', 'O'),
            ('data_info', 'O'), ('box', 'O'), ('Anative', 'O'), ('A', 'O'),
            ('Aprime', 'O'), ('slaves', 'O')
        ])
        
        for field in img_struct.dtype.names:
            img_struct[field][0] = img[field]
        
        images_array[0, i] = img_struct
    
    # Create project structure exactly matching reference
    project = {
        'file_type': np.array(['Reg_v2.0'], dtype='U10'),
        'images': images_array,
        'transformations': np.array([[]], dtype=object),
        'sequences': np.array([[]], dtype=object),
        'groups': np.array([[]], dtype=object),
        'activesequence': np.array([[-1]], dtype=np.int32),
        'activetransformation': np.array([[-1]], dtype=np.int32),
        'saves': np.array([[]], dtype=object),
        'comments': np.array([['Created with correct MATLAB processing']], dtype='U50'),
        'status': np.array([[]], dtype=object)
    }
    
    return project

def main():
    """Main function"""
    print("Creating Correct Project Using MATLAB Engine")
    print("=" * 60)
    
    project_file = create_correct_project()
    
    if project_file:
        print(f"\n✅ Success! Correct project created: {project_file}")
        print("This project should now match the reference correctExample.mat")
    else:
        print("\n❌ Failed to create correct project")

if __name__ == "__main__":
    main()
