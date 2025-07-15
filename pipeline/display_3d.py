import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
import numpy as np
from mat_to_3d import mat_to_3d_array
import os

class IndexTracker:
    def __init__(self, ax, X):
        self.ax = ax
        ax.set_title('use scroll wheel to navigate images')

        self.X = X
        rows, cols, self.slices = X.shape
        self.ind = self.slices // 2

        self.im = ax.imshow(self.X[:, :, self.ind])
        self.update()

    def on_scroll(self, event):
        if event.button == 'up':
            self.ind = (self.ind + 1) % self.slices
        else:
            self.ind = (self.ind - 1) % self.slices
        self.update()

    def update(self):
        self.im.set_data(self.X[:, :, self.ind])
        self.ax.set_ylabel('slice %s' % self.ind)
        self.im.axes.figure.canvas.draw()

def display_3d_array(array_3d):
    """
    Displays a 3D NumPy array with a scroll bar.

    Args:
        array_3d (np.ndarray): The 3D NumPy array to display.
    """
    fig, ax = plt.subplots(1, 1)
    tracker = IndexTracker(ax, array_3d)
    fig.canvas.mpl_connect('scroll_event', tracker.on_scroll)

    # Add a color bar
    fig.colorbar(tracker.im, ax=ax)

    # Save the plot to a file instead of displaying it
    plt.savefig('pipeline/3d_display.png')
    print("Plot saved to pipeline/3d_display.png")

if __name__ == '__main__':
    # Example usage:
    # First, run process_raw.py and mat_to_3d.py to generate the 3D array
    from process_raw import process_raw_file
    tdms_file_path = 'DATA/241202/8475image4D_18x18_0p75gcm_file.tdms'
    output_directory = 'pipeline'
    process_raw_file(tdms_file_path, output_directory)

    mat_file_path = 'pipeline/8475image4D_18x18_0p75gcm_file.mat'
    if os.path.exists(mat_file_path):
        array_3d = mat_to_3d_array(mat_file_path)
        if array_3d is not None:
            display_3d_array(array_3d)
    else:
        print(f"File not found: {mat_file_path}")
