import scipy.io
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from matplotlib.colors import LinearSegmentedColormap

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

def display_slices(data_3d):
    """
    Displays a 3D numpy array as a series of 2D slices with a scrollbar.

    Args:
        data_3d (numpy.ndarray): The 3D data to display.
    """
    fig, ax = plt.subplots()
    plt.subplots_adjust(bottom=0.25)

    # Create a custom colormap from blue to red
    colors = [(0, 0, 1), (1, 0, 0)]  # Blue to Red
    cmap_name = 'blue_red'
    cm = LinearSegmentedColormap.from_list(cmap_name, colors, N=100)


    initial_slice = 0
    img = ax.imshow(data_3d[:, :, initial_slice], cmap=cm)
    ax.set_title(f"Slice {initial_slice}")
    fig.colorbar(img, ax=ax)


    ax_slider = plt.axes([0.25, 0.1, 0.65, 0.03])
    slider = Slider(
        ax=ax_slider,
        label='Slice',
        valmin=0,
        valmax=data_3d.shape[2] - 1,
        valinit=initial_slice,
        valstep=1
    )

    def update(val):
        slice_index = int(slider.val)
        img.set_data(data_3d[:, :, slice_index])
        ax.set_title(f"Slice {slice_index}")
        fig.canvas.draw_idle()

    slider.on_changed(update)

    plt.show()


if __name__ == "__main__":
    oxygen_data = get_oxygen_concentration("p8561image4D_18x18_0p75gcm_file.mat")
    if oxygen_data is not None:
        print("Successfully extracted oxygen concentration data.")
        print(f"Shape of the 3D array: {oxygen_data.shape}")
        display_slices(oxygen_data)
