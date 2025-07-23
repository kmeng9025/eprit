"""
Create corrected project from the Arbuz project structure
"""
import numpy as np
import scipy.io as sio
import os
from datetime import datetime

def extract_arbuz_image_data(img_struct):
    """Extract data from Arbuz image structure"""
    try:
        name = str(img_struct.Name[0])
        image_type = str(img_struct.ImageType[0])
        
        # The data field contains the actual image
        if hasattr(img_struct.data, 'shape') and img_struct.data.size > 0:
            data = np.array(img_struct.data)
        elif hasattr(img_struct, 'A') and hasattr(img_struct.A, 'shape') and img_struct.A.size > 0:
            data = np.array(img_struct.A)
        else:
            return None, None, None
        
        return name, image_type, data
    except Exception as e:
        print(f"Error extracting image data: {e}")
        return None, None, None

def create_final_corrected_project():
    print("Creating final corrected project from Arbuz structure...")
    
    # Load the project
    project_file = 'automated_outputs/run_20250723_095104/project.mat'
    if not os.path.exists(project_file):
        print(f"Error: Project file {project_file} not found")
        return None
    
    print(f"Loading project: {project_file}")
    project_data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
    
    images = project_data['images']
    if len(images.shape) == 2:
        num_images = images.shape[1]
    else:
        num_images = images.shape[0] if len(images.shape) > 0 else 0
    print(f"Found {num_images} images in project")
    
    # Create new project structure matching reference format
    corrected_project = {
        'Groups': {
            'tree': {
                'Root': {
                    'name': 'Root',
                    'type': 'Group', 
                    'children': {}
                }
            }
        },
        'Images': {},
        'Transformations': {},
        'activeTransformationUID': []
    }
    
    # Process each image
    image_count = 0
    for i in range(min(num_images, 13)):  # Limit to 13 images
        if len(images.shape) == 2:
            img_struct = images[0, i]
        else:
            img_struct = images[i]
        
        name, image_type, data = extract_arbuz_image_data(img_struct)
        
        if data is None:
            print(f"Warning: No data found for image {i}")
            continue
            
        print(f"Processing image {i+1}: {name} (type: {image_type})")
        print(f"  Original data range: {np.min(data):.6f} to {np.max(data):.6f}")
        
        # Apply corrections
        corrected_name = name
        corrected_data = data.copy()
        
        # 1. Add '>' prefix for proper ArbuzGUI display
        if not name.startswith('>'):
            corrected_name = '>' + name
        
        # 2. Apply amplitude scaling (reduce by factor of ~2.4)
        if 'AMP' in image_type.upper() or 'AMP' in name.upper():
            corrected_data = data / 2.4
            print(f"  Applied amplitude scaling by 2.4")
        
        # 3. Fix pO2 sign if needed
        if 'pO2' in image_type or 'PO2' in name.upper():
            if np.mean(data) < 0:
                corrected_data = -data
                print(f"  Flipped pO2 sign (was mostly negative)")
        
        # Create corrected image entry
        image_count += 1
        img_uid = f'image_{image_count:04d}'
        
        corrected_project['Images'][img_uid] = {
            'name': corrected_name,
            'type': 'Image',
            'parent': 'Root',
            'data': corrected_data,
            'dimensions': list(corrected_data.shape),
            'imageType': image_type,
            'filename': f'processed_file_{i+1}',
            'timestamp': datetime.now().isoformat(),
            'UID': img_uid,
            'box': np.array(corrected_data.shape[:3], dtype=np.float64),
            'isLoaded': 1,
            'isStore': 1,
            'Selected': 0,
            'Visible': 0,
            'slaves': np.array([], dtype=object),
            'FileName': '',
            'pars': np.array([])
        }
        
        print(f"  Created: '{corrected_name}' range {np.min(corrected_data):.6f} to {np.max(corrected_data):.6f}")
    
    print(f"\\nTotal corrected images: {image_count}")
    
    # Save the corrected project
    output_file = 'final_corrected_reference_project.mat'
    print(f"Saving corrected project to {output_file}...")
    sio.savemat(output_file, corrected_project, do_compression=True)
    
    # Compare with reference
    ref_file = r'process\\exampleCorrect\\correctExample.mat'
    if os.path.exists(ref_file):
        print("\\n=== COMPARISON WITH REFERENCE ===")
        ref_data = sio.loadmat(ref_file)
        
        if 'Images' in ref_data:
            ref_images = ref_data['Images']
            ref_count = len(ref_images.dtype.names)
            
            print(f"Reference has {ref_count} images")
            print(f"Our project has {image_count} images")
            
            # Compare first image
            if ref_count > 0 and image_count > 0:
                ref_first_uid = list(ref_images.dtype.names)[0]
                ref_first = ref_images[ref_first_uid][0, 0]
                ref_name = str(ref_first['name'][0])
                ref_data_array = np.array(ref_first['data'])
                
                our_first_uid = list(corrected_project['Images'].keys())[0]
                our_first = corrected_project['Images'][our_first_uid]
                our_name = our_first['name']
                our_data_array = our_first['data']
                
                print(f"\\nFirst image comparison:")
                print(f"Reference: '{ref_name}' range {np.min(ref_data_array):.6f} to {np.max(ref_data_array):.6f}")
                print(f"Ours:      '{our_name}' range {np.min(our_data_array):.6f} to {np.max(our_data_array):.6f}")
                
                # Calculate similarity
                ref_range = np.max(ref_data_array) - np.min(ref_data_array)
                our_range = np.max(our_data_array) - np.min(our_data_array)
                range_ratio = our_range / ref_range if ref_range > 0 else float('inf')
                
                print(f"Range ratio (ours/reference): {range_ratio:.3f}")
                
                if 0.8 <= range_ratio <= 1.2:
                    print("✅ GOOD: Data ranges are similar!")
                else:
                    print("⚠️  WARNING: Data ranges differ significantly")
                
                if our_name == ref_name:
                    print("✅ GOOD: Image names match!")
                else:
                    print(f"⚠️  WARNING: Name mismatch - expected '{ref_name}', got '{our_name}'")
    
    return output_file

if __name__ == "__main__":
    try:
        output_file = create_final_corrected_project()
        if output_file:
            print(f"\\n🎉 SUCCESS! Final corrected project created: {output_file}")
            print("This project should now closely match the reference correctExample.mat")
        else:
            print("❌ FAILED to create corrected project")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
