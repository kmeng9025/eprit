"""
Fix MATLAB compatibility issues in project files
Specifically addresses the array indexing error in ibGUI
"""

import scipy.io as sio
import numpy as np
import os

def fix_matlab_compatibility(project_file):
    """Fix MATLAB compatibility issues"""
    
    print(f"🔧 Fixing MATLAB compatibility for: {project_file}")
    
    try:
        # Load project with specific settings for MATLAB compatibility
        data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
        images = data['images']
        
        fixed_count = 0
        
        for i, img in enumerate(images):
            img_name = getattr(img, 'Name', f'Image_{i}')
            if hasattr(img.Name, 'item'):
                img_name = str(img.Name.item())
            elif isinstance(img.Name, str):
                img_name = img.Name
            
            print(f"🔧 Processing image: {img_name}")
            
            # Fix data type issues
            if hasattr(img, 'data'):
                # Ensure data is double precision (float64)
                if img.data.dtype != np.float64:
                    img.data = img.data.astype(np.float64)
                    print(f"   ✅ Fixed data type to float64")
                    fixed_count += 1
            
            # Fix data_info and Mask for MATLAB compatibility
            if hasattr(img, 'data_info'):
                data_info = img.data_info
                
                if hasattr(data_info, 'Mask'):
                    mask = data_info.Mask
                    
                    # Convert mask to logical (boolean) type for MATLAB
                    if mask.dtype != bool:
                        mask = mask.astype(bool)
                        data_info.Mask = mask
                        print(f"   ✅ Converted mask to boolean type")
                        fixed_count += 1
                    
                    # Ensure mask is 3D (not 4D) for proper indexing
                    if len(mask.shape) == 4:
                        # Take first time point if 4D
                        mask = mask[:, :, :, 0].astype(bool)
                        data_info.Mask = mask
                        print(f"   ✅ Reduced mask from 4D to 3D")
                        fixed_count += 1
                    
                    # Ensure mask is C-contiguous for MATLAB
                    if not mask.flags.c_contiguous:
                        mask = np.ascontiguousarray(mask)
                        data_info.Mask = mask
                        print(f"   ✅ Made mask C-contiguous")
                        fixed_count += 1
                    
                else:
                    # Create a proper mask if missing
                    if hasattr(img, 'data'):
                        mask = np.ones(img.data.shape[:3], dtype=bool)
                        data_info.Mask = mask
                        print(f"   ✅ Created missing mask")
                        fixed_count += 1
            
            # Ensure transformation matrices are proper format
            for matrix_name in ['A', 'Anative', 'Aprime']:
                if hasattr(img, matrix_name):
                    matrix = getattr(img, matrix_name)
                    if matrix.dtype != np.float64:
                        matrix = matrix.astype(np.float64)
                        setattr(img, matrix_name, matrix)
                        print(f"   ✅ Fixed {matrix_name} data type")
                        fixed_count += 1
                else:
                    # Create identity matrix if missing
                    identity = np.eye(4, dtype=np.float64)
                    setattr(img, matrix_name, identity)
                    print(f"   ✅ Created missing {matrix_name} matrix")
                    fixed_count += 1
            
            # Fix box field
            if hasattr(img, 'box'):
                if img.box.dtype != np.float64:
                    img.box = img.box.astype(np.float64)
                    print(f"   ✅ Fixed box data type")
                    fixed_count += 1
            else:
                if hasattr(img, 'data'):
                    img.box = np.array(img.data.shape[:3], dtype=np.float64)
                    print(f"   ✅ Created missing box field")
                    fixed_count += 1
            
            # Ensure isStore and isLoaded are proper integers
            if not hasattr(img, 'isStore'):
                img.isStore = 1
                fixed_count += 1
            if not hasattr(img, 'isLoaded'):
                img.isLoaded = 1
                fixed_count += 1
        
        # Save with MATLAB v7.3 format for better compatibility
        output_file = project_file.replace('.mat', '_matlab_fixed.mat')
        
        # Save with specific options for MATLAB compatibility
        sio.savemat(output_file, data, 
                   do_compression=True,
                   format='5',  # Use MATLAB v7 format
                   oned_as='column')  # Save 1D arrays as columns
        
        print(f"\\n✅ Fixed {fixed_count} compatibility issues")
        print(f"💾 Saved MATLAB-compatible project: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error fixing MATLAB compatibility: {e}")
        return None

def create_minimal_test_project():
    """Create a minimal test project to verify MATLAB compatibility"""
    
    print("🧪 Creating minimal test project...")
    
    try:
        # Create a simple test project with one image
        test_data = {
            'status': 1,
            'file_type': 'ArbuzGUI',
            'transformations': np.array([]),
            'sequences': np.array([]),
            'groups': np.array([]),
            'activesequence': 0,
            'activetransformation': 0,
            'saves': np.array([]),
            'comments': ''
        }
        
        # Create a single test image
        test_image = type('TestImage', (), {})()
        test_image.Name = 'TEST_IMAGE'
        test_image.ImageType = 'PO2_pEPRI'
        test_image.FileName = ''
        test_image.isStore = 1
        test_image.isLoaded = 1
        
        # Create test data - simple 8x8x8 cube
        test_data_array = np.random.randn(8, 8, 8).astype(np.float64)
        test_image.data = test_data_array
        
        # Create proper data_info with mask
        test_image.data_info = type('DataInfo', (), {})()
        test_image.data_info.Mask = np.ones((8, 8, 8), dtype=bool)
        
        # Add transformation matrices
        test_image.A = np.eye(4, dtype=np.float64)
        test_image.Anative = np.eye(4, dtype=np.float64)
        test_image.Aprime = np.eye(4, dtype=np.float64)
        test_image.box = np.array([8, 8, 8], dtype=np.float64)
        
        # Create images array
        images = np.array([test_image], dtype=object)
        test_data['images'] = images
        
        # Save test project
        test_file = 'test_minimal_project.mat'
        sio.savemat(test_file, test_data, format='5', oned_as='column')
        
        print(f"✅ Created minimal test project: {test_file}")
        return test_file
        
    except Exception as e:
        print(f"❌ Error creating test project: {e}")
        return None

def main():
    """Main function"""
    
    print("🔧 MATLAB COMPATIBILITY FIXER")
    print("=" * 35)
    
    # Find project file to fix
    project_files = [
        'automated_outputs/clean_run_20250723_115247/complete_roi_clean_project.mat',
        'automated_outputs/clean_run_20250723_115247/clean_project.mat'
    ]
    
    project_file = None
    for pf in project_files:
        if os.path.exists(pf):
            project_file = pf
            break
    
    if project_file:
        # Fix the existing project
        fixed_file = fix_matlab_compatibility(project_file)
        
        if fixed_file:
            print(f"\\n🎯 Try loading this fixed file in MATLAB:")
            print(f"   {fixed_file}")
    else:
        print("⚠️  No project file found to fix")
    
    # Also create a minimal test project
    print("\\n" + "=" * 35)
    test_file = create_minimal_test_project()
    
    if test_file:
        print(f"\\n🧪 You can also test with this minimal project:")
        print(f"   {test_file}")

if __name__ == "__main__":
    main()
