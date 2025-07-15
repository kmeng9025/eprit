import os
from process_raw import process_raw_file
from mat_to_3d import mat_to_3d_array
from roi_detector import detect_roi
from display_3d import display_3d_array
from train_model import train_model

def main():
    """
    The main function for the image processing pipeline.
    """
    # Define the paths
    tdms_dir = 'DATA/241202/'
    output_dir = 'pipeline'

    # Get a list of all .tdms files in the directory
    tdms_files = [f for f in os.listdir(tdms_dir) if f.endswith('.tdms')]

    for tdms_file in tdms_files:
        tdms_path = os.path.join(tdms_dir, tdms_file)

        # 1. Process the raw .tdms file
        process_raw_file(tdms_path, output_dir)

        # 2. Convert the .mat file to a 3D array
        mat_filename = os.path.splitext(tdms_file)[0] + ".mat"
        mat_path = os.path.join(output_dir, mat_filename)

        if os.path.exists(mat_path):
            array_3d = mat_to_3d_array(mat_path)

            if array_3d is not None:
                # 3. Detect the ROI
                roi_mask = detect_roi(array_3d)

                # 4. Display the ROI mask
                display_3d_array(roi_mask)
        else:
            print(f"File not found: {mat_path}")

if __name__ == '__main__':
    main()
