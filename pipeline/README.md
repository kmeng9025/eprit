# Python Image Processing Pipeline

This pipeline automates the process of analyzing image data, from raw `.tdms` files to ROI detection and visualization.

## Prerequisites

- Python 3.6+
- The following Python libraries:
  - `numpy`
  - `scipy`
  - `nptdms`
  - `matplotlib`

You can install these libraries using pip:

```bash
pip install numpy scipy nptdms matplotlib
```

## Usage

To run the pipeline, simply execute the `main.py` script from the root of the repository:

```bash
python pipeline/main.py
```

The pipeline will process all the `.tdms` files in the `DATA/241202` directory and save the output in the `pipeline` directory.

## Pipeline Scripts

The pipeline consists of the following scripts:

- `main.py`: The main pipeline controller.
- `process_raw.py`: Processes raw `.tdms` files into `.mat` files.
- `roi_detector.py`: Runs an AI model to detect and highlight ROIs. This is a placeholder script that should be replaced with your own AI model.
- `mat_to_3d.py`: Converts `.mat` files into a 3D NumPy array.
- `display_3d.py`: Displays the 3D array with a color bar and scroll bar.
- `train_model.py`: Trains the AI model using annotated examples. This is a placeholder script that should be replaced with your own training logic.
