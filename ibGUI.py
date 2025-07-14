import scipy.io
import numpy as np

def get_oxygen_concentration(filepath):
    """
    Loads a .mat file and returns a 3D numpy array with the oxygen
    concentration levels.

    Args:
        filepath (str): The path to the .mat file.

    Returns:
        numpy.ndarray: A 3D numpy array with the oxygen concentration levels.
    """
    try:
        mat_contents = scipy.io.loadmat(filepath, squeeze_me=True)

        if 'fit_data' in mat_contents:
            fit_data = mat_contents['fit_data']

            if 'Size' in fit_data.dtype.names:
                size = fit_data['Size'].item()

            if 'P' in fit_data.dtype.names:
                p_values = fit_data['P'].item()

            if 'Idx' in fit_data.dtype.names:
                idx = fit_data['Idx'].item()

            # The pO2 values are in the second row of P
            po2_values = p_values[1,:]

            # Create the 3D array
            oxygen_concentration = np.zeros(size)
            oxygen_concentration.flat[idx-1] = po2_values

            return oxygen_concentration

    except Exception as e:
        print(f"An error occurred: {e}")
        return None

if __name__ == "__main__":
    oxygen_data = get_oxygen_concentration("p8561image4D_18x18_0p75gcm_file.mat")
    if oxygen_data is not None:
        print("Successfully extracted oxygen concentration data.")
        print(f"Shape of the 3D array: {oxygen_data.shape}")
