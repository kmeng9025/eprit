"""
Diagnose and fix the array indexing issue in the project file
"""

import scipy.io as sio
import numpy as np
import os

def diagnose_project_issue(project_file):
    """Diagnose the indexing issue in the project file"""
    
    print(f"🔍 Diagnosing project file: {project_file}")
    
    try:
        # Load project
        data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
        
        print(f"✅ Project loaded successfully")
        print(f"📋 Project keys: {list(data.keys())}")
        
        if 'images' not in data:
            print("❌ No images found in project")
            return False
        
        images = data['images']
        print(f"📊 Number of images: {len(images)}")
        
        # Check each image
        issues_found = []
        
        for i, img in enumerate(images):
            img_name = getattr(img, 'Name', f'Image_{i}')
            if hasattr(img.Name, 'item'):
                img_name = str(img.Name.item())
            elif isinstance(img.Name, str):
                img_name = img.Name
            
            print(f"\\n🖼️  Checking image {i+1}: {img_name}")
            
            # Check data
            if hasattr(img, 'data'):
                print(f"   📊 Data shape: {img.data.shape}")
                print(f"   📊 Data type: {img.data.dtype}")
            else:
                print("   ❌ No data field")
                issues_found.append(f"{img_name}: Missing data field")
            
            # Check data_info and Mask
            if hasattr(img, 'data_info'):
                data_info = img.data_info
                print(f"   ✅ Has data_info")
                
                if hasattr(data_info, 'Mask'):
                    mask = data_info.Mask
                    print(f"   📊 Mask shape: {mask.shape}")
                    print(f"   📊 Mask type: {type(mask)}")
                    print(f"   📊 Mask dtype: {mask.dtype}")
                    
                    # Check if mask is compatible with data
                    if hasattr(img, 'data'):
                        data_shape = img.data.shape
                        mask_shape = mask.shape
                        
                        if len(mask_shape) == 4 and len(data_shape) == 3:
                            print(f"   ⚠️  Mask is 4D but data is 3D")
                            issues_found.append(f"{img_name}: Mask dimension mismatch (4D mask, 3D data)")
                        elif mask_shape[:3] != data_shape[:3]:
                            print(f"   ⚠️  Mask shape mismatch: {mask_shape} vs {data_shape}")
                            issues_found.append(f"{img_name}: Mask shape mismatch")
                        else:
                            print(f"   ✅ Mask compatible with data")
                            
                        # Check if mask has valid values
                        if np.all(mask == 0):
                            print(f"   ⚠️  Mask is all zeros")
                            issues_found.append(f"{img_name}: Empty mask")
                        elif not np.all((mask == 0) | (mask == 1)):
                            print(f"   ⚠️  Mask has non-boolean values")
                            issues_found.append(f"{img_name}: Non-boolean mask")
                        else:
                            print(f"   ✅ Mask has valid boolean values")
                            
                else:
                    print(f"   ❌ No Mask field in data_info")
                    issues_found.append(f"{img_name}: Missing Mask field")
            else:
                print(f"   ❌ No data_info field")
                issues_found.append(f"{img_name}: Missing data_info field")
        
        print(f"\\n📋 Summary:")
        if issues_found:
            print(f"❌ Found {len(issues_found)} issues:")
            for issue in issues_found:
                print(f"   - {issue}")
            return False
        else:
            print(f"✅ No issues found")
            return True
            
    except Exception as e:
        print(f"❌ Error diagnosing project: {e}")
        return False

def fix_project_issues(project_file, output_file=None):
    """Fix the common issues in project files"""
    
    if output_file is None:
        output_file = project_file.replace('.mat', '_fixed.mat')
    
    print(f"🔧 Fixing project file: {project_file}")
    
    try:
        # Load project
        data = sio.loadmat(project_file, struct_as_record=False, squeeze_me=True)
        images = data['images']
        
        fixed_count = 0
        
        for i, img in enumerate(images):
            img_name = getattr(img, 'Name', f'Image_{i}')
            if hasattr(img.Name, 'item'):
                img_name = str(img.Name.item())
            elif isinstance(img.Name, str):
                img_name = img.Name
            
            print(f"🔧 Fixing image: {img_name}")
            
            # Ensure data_info exists and has proper structure
            if not hasattr(img, 'data_info'):
                # Create data_info structure
                img.data_info = type('DataInfo', (), {})()
                print(f"   ✅ Created data_info")
            
            data_info = img.data_info
            
            # Fix or create Mask
            if hasattr(img, 'data'):
                data_shape = img.data.shape
                
                if not hasattr(data_info, 'Mask') or data_info.Mask is None:
                    # Create a proper mask - all True for 3D data
                    if len(data_shape) == 3:
                        mask = np.ones(data_shape, dtype=bool)
                    elif len(data_shape) == 4:
                        mask = np.ones(data_shape, dtype=bool)
                    else:
                        mask = np.ones(data_shape, dtype=bool)
                    
                    data_info.Mask = mask
                    print(f"   ✅ Created new mask with shape {mask.shape}")
                    fixed_count += 1
                    
                else:
                    # Fix existing mask
                    mask = data_info.Mask
                    
                    # Fix dimension mismatch
                    if len(mask.shape) == 4 and len(data_shape) == 3:
                        # Take first slice of 4D mask for 3D data
                        mask = mask[:, :, :, 0]
                        data_info.Mask = mask
                        print(f"   ✅ Fixed mask dimensions: {mask.shape}")
                        fixed_count += 1
                    
                    # Fix shape mismatch
                    elif mask.shape[:3] != data_shape[:3]:
                        # Create new mask with correct shape
                        if len(data_shape) == 3:
                            mask = np.ones(data_shape, dtype=bool)
                        else:
                            mask = np.ones(data_shape, dtype=bool)
                        data_info.Mask = mask
                        print(f"   ✅ Fixed mask shape: {mask.shape}")
                        fixed_count += 1
                    
                    # Fix empty mask
                    elif np.all(mask == 0):
                        mask = np.ones(mask.shape, dtype=bool)
                        data_info.Mask = mask
                        print(f"   ✅ Fixed empty mask")
                        fixed_count += 1
                    
                    # Fix non-boolean mask
                    elif not np.all((mask == 0) | (mask == 1)):
                        mask = mask.astype(bool)
                        data_info.Mask = mask
                        print(f"   ✅ Fixed mask data type")
                        fixed_count += 1
                    
                    else:
                        print(f"   ✅ Mask is OK")
            
            # Ensure other required fields exist
            if not hasattr(img, 'A'):
                img.A = np.eye(4, dtype=np.float64)
                print(f"   ✅ Added transformation matrix A")
                fixed_count += 1
            
            if not hasattr(img, 'Anative'):
                img.Anative = np.eye(4, dtype=np.float64)
                print(f"   ✅ Added transformation matrix Anative")
                fixed_count += 1
            
            if not hasattr(img, 'Aprime'):
                img.Aprime = np.eye(4, dtype=np.float64)
                print(f"   ✅ Added transformation matrix Aprime")
                fixed_count += 1
            
            if not hasattr(img, 'box'):
                if hasattr(img, 'data'):
                    img.box = np.array(img.data.shape[:3], dtype=np.float64)
                else:
                    img.box = np.array([64, 64, 64], dtype=np.float64)
                print(f"   ✅ Added box field")
                fixed_count += 1
        
        # Save fixed project
        data['images'] = images
        sio.savemat(output_file, data, do_compression=True)
        
        print(f"\\n✅ Fixed {fixed_count} issues")
        print(f"💾 Saved fixed project: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Error fixing project: {e}")
        return None

def main():
    """Main function to diagnose and fix project issues"""
    
    # Find the most recent project file
    project_files = [
        'automated_outputs/clean_run_20250723_115247/complete_roi_clean_project.mat',
        'automated_outputs/clean_run_20250723_115247/clean_project.mat',
        'automated_outputs/complete_run_20250723_110202/roi_complete_roi_annotated_streamlined_project.mat'
    ]
    
    project_file = None
    for pf in project_files:
        if os.path.exists(pf):
            project_file = pf
            break
    
    if not project_file:
        print("❌ No project file found")
        return
    
    print("🔍 MATLAB PROJECT FILE DIAGNOSTIC AND FIX")
    print("=" * 50)
    
    # Diagnose issues
    is_ok = diagnose_project_issue(project_file)
    
    if not is_ok:
        print("\\n🔧 FIXING ISSUES...")
        print("=" * 30)
        
        # Fix issues
        fixed_file = fix_project_issues(project_file)
        
        if fixed_file:
            print("\\n🔍 RE-CHECKING FIXED FILE...")
            print("=" * 35)
            
            # Re-check fixed file
            diagnose_project_issue(fixed_file)
    else:
        print("\\n✅ Project file is OK - no fixes needed")

if __name__ == "__main__":
    main()
