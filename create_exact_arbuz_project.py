"""
Final Exact ArbuzGUI Project Creation
Based on complete analysis of correctExample.mat structure
"""

import scipy.io as sio
import numpy as np
import os
from pathlib import Path

def load_and_analyze_reference():
    """
    Load and completely analyze the reference project structure
    """
    reference_file = r"c:\Users\ftmen\Documents\v3\process\exampleCorrect\correctExample.mat"
    
    print("=== Complete Reference Analysis ===")
    
    # Load with struct_as_record=True to preserve exact structure
    data = sio.loadmat(reference_file, struct_as_record=True, squeeze_me=False)
    
    images = data['images']
    print(f"Number of images: {images.shape[1]}")
    
    reference_structure = {
        'file_type': data['file_type'],
        'images': [],
        'sequences': data['sequences'],
        'groups': data['groups'],
        'transformations': data['transformations'],
        'activesequence': data['activesequence'],
        'activetransformation': data['activetransformation'],
        'saves': data['saves'],
        'comments': data['comments'],
        'status': data['status']
    }
    
    # Analyze each image
    for i in range(images.shape[1]):
        img = images[0, i]
        
        image_info = {
            'index': i + 1,
            'name': str(img['Name'][0]),
            'filename': str(img['FileName'][0]),
            'image_type': str(img['ImageType'][0]),
            'is_loaded': img['isLoaded'][0, 0],
            'visible': img['Visible'][0, 0],
            'selected': img['Selected'][0, 0],
            'is_store': img['isStore'][0, 0]
        }
        
        # Get the actual image data
        if img['isLoaded'][0, 0] == 1:
            data_array = img['data'][0, 0]
            image_info['data_shape'] = data_array.shape
            image_info['data_range'] = (np.min(data_array), np.max(data_array))
            image_info['data'] = data_array
            
            print(f"Image {i+1}: {image_info['name']} ({image_info['image_type']})")
            print(f"  Shape: {image_info['data_shape']}")
            print(f"  Range: {image_info['data_range'][0]:.6f} to {image_info['data_range'][1]:.6f}")
        
        reference_structure['images'].append(image_info)
    
    return reference_structure

def load_our_generated_project():
    """
    Load our most recent generated project
    """
    project_file = r"c:\Users\ftmen\Documents\v3\automated_outputs\run_20250722_145645\project.mat"
    
    print("\n=== Our Generated Project Analysis ===")
    
    # Load with same settings as reference
    data = sio.loadmat(project_file, struct_as_record=True, squeeze_me=False)
    images = data['images']
    
    our_images = []
    
    print(f"Number of our images: {images.shape[1]}")
    
    for i in range(images.shape[1]):
        img = images[0, i]
        
        image_info = {
            'index': i + 1,
            'name': str(img['Name'][0]),
            'type': str(img['ImageType'][0]),
            'source_file': str(img['FileName'][0]) if img['FileName'][0].size > 0 else '',
            'is_loaded': img['isLoaded'][0, 0],
            'mat_image': img['data'][0, 0] if img['isLoaded'][0, 0] == 1 else None
        }
        
        if image_info['mat_image'] is not None:
            print(f"Image {i+1}: {image_info['name']} ({image_info['type']})")
            print(f"  Shape: {image_info['mat_image'].shape}")
            print(f"  Range: {np.min(image_info['mat_image']):.6f} to {np.max(image_info['mat_image']):.6f}")
        
        our_images.append(image_info)
    
    return our_images

def create_exact_arbuz_project(our_images, reference_structure, output_path):
    """
    Create project with exact ArbuzGUI structure matching reference
    """
    print("\n=== Creating Exact ArbuzGUI Project ===")
    
    # Create the exact structure as in reference
    project_data = {}
    
    # Copy non-image fields exactly
    project_data['file_type'] = reference_structure['file_type']
    project_data['sequences'] = reference_structure['sequences']
    project_data['groups'] = reference_structure['groups']
    project_data['transformations'] = reference_structure['transformations']
    project_data['activesequence'] = reference_structure['activesequence']
    project_data['activetransformation'] = reference_structure['activetransformation']
    project_data['saves'] = reference_structure['saves']
    project_data['comments'] = reference_structure['comments']
    project_data['status'] = reference_structure['status']
    
    # Create images array with exact structure
    num_images = len(our_images)
    images_array = np.empty((1, num_images), dtype=object)
    
    for i, our_img in enumerate(our_images):
        # Create image structure exactly matching reference
        img_struct = np.empty(1, dtype=[
            ('FileName', 'O'),
            ('Name', 'O'),
            ('isStore', 'O'),
            ('isLoaded', 'O'),
            ('Visible', 'O'),
            ('Selected', 'O'),
            ('ImageType', 'O'),
            ('data', 'O'),
            ('data_info', 'O'),
            ('box', 'O'),
            ('Anative', 'O'),
            ('A', 'O'),
            ('Aprime', 'O'),
            ('slaves', 'O')
        ])
        
        # Fill fields to match reference structure
        img_struct['FileName'][0] = np.array([our_img['source_file']], dtype='U200')
        img_struct['Name'][0] = np.array([f">{our_img['name']}"], dtype='U50')
        img_struct['isStore'][0] = np.array([[0]], dtype=np.int32)
        img_struct['isLoaded'][0] = np.array([[1]], dtype=np.int32)  # Mark as loaded
        img_struct['Visible'][0] = np.array([[1]], dtype=np.int32)
        img_struct['Selected'][0] = np.array([[0]], dtype=np.int32)
        img_struct['ImageType'][0] = np.array([our_img['type']], dtype='U50')
        
        # Store the actual image data directly as a 3D array
        # Keep the original dimensions and data from our processing
        img_data = our_img['mat_image']
        
        # Ensure we have 3D data
        if img_data.ndim == 2:
            # If 2D, add a third dimension
            img_data = img_data[:, :, np.newaxis]
        
        img_struct['data'][0] = img_data
        
        # Initialize other fields as empty arrays (matching reference)
        img_struct['data_info'][0] = np.array([[]], dtype=object)
        img_struct['box'][0] = np.array([[]], dtype=object)
        img_struct['Anative'][0] = np.array([[]], dtype=object)
        img_struct['A'][0] = np.array([[]], dtype=object)
        img_struct['Aprime'][0] = np.array([[]], dtype=object)
        img_struct['slaves'][0] = np.array([[]], dtype=object)
        
        images_array[0, i] = img_struct
        
        print(f"Created image {i+1}: {our_img['name']} ({our_img['type']})")
        print(f"  Final shape: {img_data.shape}")
        print(f"  Final range: {np.min(img_data):.6f} to {np.max(img_data):.6f}")
    
    project_data['images'] = images_array
    
    # Save with exact MATLAB format
    sio.savemat(output_path, project_data, format='5', do_compression=True)
    
    print(f"\nExact ArbuzGUI project saved: {output_path}")
    return output_path

def main():
    """
    Main function: Create exact replica of reference project structure
    """
    print("Creating Exact ArbuzGUI Project Replica")
    print("="*60)
    
    # Step 1: Analyze reference structure
    reference_structure = load_and_analyze_reference()
    
    # Step 2: Load our generated images
    our_images = load_our_generated_project()
    
    # Step 3: Create exact ArbuzGUI project
    output_dir = r"c:\Users\ftmen\Documents\v3\final_exact_outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "exact_arbuz_project.mat")
    
    project_file = create_exact_arbuz_project(our_images, reference_structure, output_path)
    
    print(f"\n{'='*60}")
    print(f"SUCCESS: Exact ArbuzGUI Project Created!")
    print(f"Reference images: {len(reference_structure['images'])}")
    print(f"Our images: {len(our_images)}")
    print(f"Output file: {project_file}")
    print(f"{'='*60}")
    
    return project_file

if __name__ == "__main__":
    main()
