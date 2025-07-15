import scipy.io as sio
import numpy as np
import os

def mat_to_3d_array(mat_path):
    """
    Converts a .mat file to a 3D NumPy array.

    Args:
        mat_path (str): The path to the .mat file.

    Returns:
        np.ndarray: The 3D NumPy array.
    """
    try:
        mat_contents = sio.loadmat(mat_path)

        if 'processed_data' in mat_contents:
            processed_data = mat_contents['processed_data']

            if 'Re' in processed_data.dtype.names and 'Im' in processed_data.dtype.names:
                real_part = processed_data['Re'][0, 0]
                imag_part = processed_data['Im'][0, 0]

                # Combine real and imaginary parts to form a complex array
                complex_array = real_part + 1j * imag_part

                # Compute the magnitude of the complex array
                magnitude_array = np.abs(complex_array)

                # Reshape the array to 64x64xN
                num_elements = magnitude_array.size
                n_slices = num_elements // (64 * 64)
                if n_slices > 0:
                    new_size = 64 * 64 * n_slices
                    return magnitude_array.flatten()[:new_size].reshape((64, 64, n_slices))
                else:
                    print("Not enough data to form a single 64x64 slice.")
                    return None


        print(f"No 'Re' and 'Im' fields found in {mat_path}")
        return None

    except Exception as e:
        print(f"Error processing {mat_path}: {e}")
        return None

if __name__ == '__main__':
    # Example usage:
    # First, run process_raw.py to generate the .mat file
    from process_raw import process_raw_file
    tdms_file_path = 'DATA/241202/8475image4D_18x18_0p75gcm_file.tdms'
    output_directory = 'pipeline'
    process_raw_file(tdms_file_path, output_directory)

    mat_file_path = 'pipeline/8475image4D_18x18_0p75gcm_file.mat'
    if os.path.exists(mat_file_path):
      array_3d = mat_to_3d_array(mat_file_path)
      if array_3d is not None:
          print(f"Successfully converted {mat_file_path} to a 3D array with shape: {array_3d.shape}")
    else:
        print(f"File not found: {mat_file_path}")
