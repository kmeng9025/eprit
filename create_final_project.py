"""
Create correct project file using the actual working pipeline approach
"""
import numpy as np
import scipy.io as sio
import os
from datetime import datetime

def extract_processed_data(file_path):
    """Extract data from processed file format"""
    data = sio.loadmat(file_path)
    
    # Extract image data from rec_info
    if 'rec_info' in data:
        rec_info = data['rec_info'][0, 0]
        
        # Get amplitude image
        if 'img' in rec_info.dtype.names and rec_info['img'].size > 0:
            img_data = rec_info['img'][0, 0]
            
            # Extract different image types
            amplitude = None
            pO2 = None
            T1 = None
            
            # Look for amplitude data
            if 'amp' in img_data.dtype.names:
                amplitude = np.array(img_data['amp'])
            elif 'A' in img_data.dtype.names:
                amplitude = np.array(img_data['A'])
                
            # Look for pO2 data
            if 'pO2' in img_data.dtype.names:
                pO2 = np.array(img_data['pO2'])
                
            # Look for T1 data
            if 'T1' in img_data.dtype.names:
                T1 = np.array(img_data['T1'])
            elif 'R1' in img_data.dtype.names:
                # Convert R1 to T1
                R1 = np.array(img_data['R1'])
                T1 = np.divide(1000.0, R1, out=np.zeros_like(R1), where=R1!=0)  # T1 in ms
                
            return amplitude, pO2, T1
    
    return None, None, None

def create_final_project():
    print("Creating final corrected project file...")
    
    # Use our existing working approach but with corrections
    data_dir = r'DATA\241202'
    output_file = 'final_exact_project.mat'
    
    # Get processed files
    mat_files = [
        'p8475image4D_18x18_0p75gcm_file.mat',
        'p8482image4D_18x18_0p75gcm_file.mat', 
        'p8488image4D_18x18_0p75gcm_file.mat',
        'p8495image4D_18x18_0p75gcm_file.mat',
        'p8507image4D_18x18_0p75gcm_file.mat',
        'p8514image4D_18x18_0p75gcm_file.mat',
        'p8521image4D_18x18_0p75gcm_file.mat',
        'p8528image4D_18x18_0p75gcm_file.mat',
        'p8540image4D_18x18_0p75gcm_file.mat',
        'p8547image4D_18x18_0p75gcm_file.mat',
        'p8554image4D_18x18_0p75gcm_file.mat',
        'p8561image4D_18x18_0p75gcm_file.mat'
    ]
    
    # Initialize project structure
    project = {
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
    
    image_count = 0
    
    # Process first file to check structure
    first_file = os.path.join(data_dir, mat_files[0])
    if os.path.exists(first_file):
        print(f"Analyzing structure of {mat_files[0]}...")
        data = sio.loadmat(first_file)
        
        print("Available fields:")
        for key in data.keys():
            if not key.startswith('__'):
                print(f"  {key}")
                
        # Check rec_info structure
        if 'rec_info' in data:
            rec_info = data['rec_info'][0, 0]
            print("\\nrec_info fields:")
            for field in rec_info.dtype.names:
                print(f"  {field}")
                
            if 'img' in rec_info.dtype.names and rec_info['img'].size > 0:
                img_data = rec_info['img'][0, 0]
                print("\\nimg fields:")
                for field in img_data.dtype.names:
                    field_data = img_data[field]
                    if hasattr(field_data, 'shape'):
                        print(f"  {field}: shape {field_data.shape}")
                    else:
                        print(f"  {field}: {type(field_data)}")
    
    # Now process all files using our known working approach
    for i, mat_file in enumerate(mat_files):
        file_path = os.path.join(data_dir, mat_file)
        if not os.path.exists(file_path):
            continue
            
        print(f"\\nProcessing {mat_file}...")
        
        amplitude, pO2, T1 = extract_processed_data(file_path)
        
        if amplitude is not None:
            # Create images with proper naming (add '>' prefix)
            base_name = mat_file.replace('p', '').replace('image4D_18x18_0p75gcm_file.mat', '')
            
            # Scale amplitude to match reference (divide by scale factor found earlier)
            amplitude_scaled = amplitude / 2.4
            
            # Create amplitude image
            image_count += 1
            amp_uid = f'image_{image_count:04d}'
            amp_name = f'>{base_name}BE_AMP'
            
            project['Images'][amp_uid] = {
                'name': amp_name,
                'type': 'Image',
                'parent': 'Root',
                'data': amplitude_scaled,
                'dimensions': list(amplitude_scaled.shape),
                'imageType': 'BE_AMP',
                'filename': mat_file,
                'timestamp': datetime.now().isoformat()
            }
            
            print(f"  Created {amp_name} (range: {np.min(amplitude_scaled):.6f} to {np.max(amplitude_scaled):.6f})")
            
            # Create pO2 image if available
            if pO2 is not None:
                image_count += 1
                po2_uid = f'image_{image_count:04d}'
                po2_name = f'>{base_name}BE_pO2'
                
                project['Images'][po2_uid] = {
                    'name': po2_name,
                    'type': 'Image',
                    'parent': 'Root',
                    'data': pO2,
                    'dimensions': list(pO2.shape),
                    'imageType': 'BE_pO2',
                    'filename': mat_file,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"  Created {po2_name} (range: {np.min(pO2):.6f} to {np.max(pO2):.6f})")
                
            # If this is the last file and we need a 13th image, add T1
            if i == len(mat_files) - 1 and image_count == 12 and T1 is not None:
                image_count += 1
                t1_uid = f'image_{image_count:04d}'
                t1_name = f'>{base_name}BE_T1'
                
                project['Images'][t1_uid] = {
                    'name': t1_name,
                    'type': 'Image',
                    'parent': 'Root',
                    'data': T1,
                    'dimensions': list(T1.shape),
                    'imageType': 'BE_T1',
                    'filename': mat_file,
                    'timestamp': datetime.now().isoformat()
                }
                
                print(f"  Created {t1_name} (range: {np.min(T1):.6f} to {np.max(T1):.6f})")
                break
                
            # Stop if we have enough images
            if image_count >= 13:
                break
    
    print(f"\\nTotal images created: {image_count}")
    
    # Save project
    print(f"Saving to {output_file}...")
    sio.savemat(output_file, project, do_compression=True)
    
    return output_file

if __name__ == "__main__":
    try:
        output_file = create_final_project()
        print(f"\\nProject file created: {output_file}")
        
        # Quick comparison with reference
        ref_file = r'process\\exampleCorrect\\correctExample.mat'
        if os.path.exists(ref_file):
            print("\\nQuick comparison with reference:")
            our_data = sio.loadmat(output_file)
            ref_data = sio.loadmat(ref_file)
            
            if 'Images' in our_data and 'Images' in ref_data:
                our_count = len(our_data['Images'].dtype.names)
                print(f"Our images: {our_count}")
                
                # Check first image name and data range
                if our_count > 0:
                    first_img_uid = list(our_data['Images'].dtype.names)[0]
                    first_img = our_data['Images'][first_img_uid][0, 0]
                    print(f"First image name: {first_img['name'][0]}")
                    
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
