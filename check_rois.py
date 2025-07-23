import scipy.io
import numpy as np

def check_roi_structure(project_file):
    """Check ROI structure in project"""
    try:
        print(f"=== CHECKING ROI STRUCTURE: {project_file} ===")
        data = scipy.io.loadmat(project_file)
        
        images = data['images']
        print(f"Found {images.shape[1]} images")
        
        # Check each image for ROIs
        for i in range(images.shape[1]):
            image = images[0, i]
            name = image['Name'][0] if hasattr(image['Name'][0], '__len__') else str(image['Name'][0])
            slaves = image['slaves'][0]
            
            if slaves.size > 0 and slaves[0].size > 0:
                roi_count = len(slaves[0])
                print(f"  {name}: {roi_count} ROIs")
                
                # Check each ROI
                for j, roi in enumerate(slaves[0]):
                    roi_name = roi['Name'][0] if hasattr(roi['Name'][0], '__len__') else str(roi['Name'][0])
                    roi_data = roi['data'][0]
                    unique_vals = np.unique(roi_data)
                    print(f"    ROI {j+1}: {roi_name}, shape: {roi_data.shape}, values: {unique_vals}")
            else:
                print(f"  {name}: No ROIs")
                
        print("=== ROI CHECK COMPLETE ===")
        
    except Exception as e:
        print(f"Error checking ROI structure: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        project_file = sys.argv[1]
    else:
        project_file = "automated_outputs/clean_run_20250723_133113/complete_roi_clean_project.mat"
    
    check_roi_structure(project_file)
