# EPRI Medical Scan Data Processing Automation

This repository contains Python scripts to automate the processing workflow for EPRI (Electron Paramagnetic Resonance Imaging) medical scan data. The automation handles the entire pipeline from processed .mat files to statistical analysis with ROI (Region of Interest) extraction.

## Overview

The workflow automates the following steps:

1. **Data Organization**: Organizes processed .mat files into pre-, mid-, and post-transfusion groups
2. **Project Creation**: Creates Arbuz-compatible project files from processed images
3. **ROI Generation**: Uses neural network (UNet3D) or manual methods to create kidney ROIs
4. **ROI Transfer**: Applies ROI to all images in the project
5. **Statistics Extraction**: Calculates mean, median, standard deviation, and voxel count for each ROI
6. **Results Export**: Saves statistics to Excel and CSV files

## File Structure

```
process/
├── epri_automation.py          # Full automation script (including MATLAB ProcessGUI calls)
├── epri_roi_extractor.py       # ROI extraction from existing processed files
├── manual_roi_creator.py       # Interactive/manual ROI creation tool
├── unet3d_model.py             # UNet3D neural network model definition
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Prerequisites

### Python Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Required packages:

- numpy, scipy, pandas (scientific computing)
- scikit-image, Pillow (image processing)
- torch, torchvision (neural network)
- openpyxl, xlsxwriter (Excel support)
- matplotlib (visualization for manual ROI)

### MATLAB Dependencies (Optional)

For full automation including ProcessGUI calls:

- MATLAB with Image Processing Toolbox
- MATLAB Engine API for Python: `pip install matlabengine`

### Neural Network Model

The ROI generation requires a pre-trained UNet3D model file:

- `unet3d_kidney.pth` should be placed in the `process/` directory
- If not available, use the manual ROI creation tool instead

## Usage

### Quick Start (Recommended)

If you already have processed .mat files (starting with 'p'), use the ROI extractor:

```bash
cd process
python epri_roi_extractor.py --data-subdir 241202
```

This will:

1. Find all processed files in `DATA/241202/`
2. Create a project file
3. Generate ROI using the neural network
4. Extract statistics and save to Excel/CSV

### Manual ROI Creation

If the neural network model is not available, create ROI manually:

```bash
# First create a project file (without ROI)
python epri_roi_extractor.py --data-subdir 241202

# Then add ROI manually
python manual_roi_creator.py --project-file output/roi_analysis_241202_*/project_241202.mat
```

### Full Automation (Advanced)

For complete automation including ProcessGUI calls:

```bash
python epri_automation.py --data-subdir 241202
```

Note: This requires MATLAB Engine and proper ProcessGUI setup.

## Command Line Options

### epri_roi_extractor.py

```bash
python epri_roi_extractor.py [options]

Options:
  --data-subdir     Data subdirectory to process (default: 241202)
  --output-dir      Output directory (default: auto-generated)
  --base-dir        Base EPRI directory (default: c:\Users\ftmen\Documents\EPRI)
```

### manual_roi_creator.py

```bash
python manual_roi_creator.py --project-file PROJECT_FILE [options]

Options:
  --project-file    Path to the project .mat file (required)
  --output-file     Output file path (default: adds _with_manual_roi suffix)
  --mode           ROI creation mode: interactive or simple (default: interactive)
```

## File Organization

### Input Files

The scripts expect the following directory structure:

```
EPRI/
├── DATA/
│   └── 241202/                     # Date-based subdirectory
│       ├── p8475image4D_*.mat      # Processed files (start with 'p')
│       ├── p8482image4D_*.mat
│       └── ...
├── process/                        # This directory
│   ├── unet3d_kidney.pth          # Neural network model
│   └── *.py                       # Python scripts
└── epri/
    └── Scenario/
        ├── PulseRecon.scn         # Scenario file
        └── Local/
            └── Mouse_64pt_4D.par  # Parameter file
```

### Output Files

The scripts create the following output structure:

```
output/
└── roi_analysis_241202_20250721_143022/
    ├── project_241202.mat              # Original project file
    ├── project_241202_with_roi.mat     # Project with ROI
    ├── roi_statistics_241202.xlsx      # Excel results
    ├── roi_statistics_241202.csv       # CSV results
    └── epri_roi_extractor.log          # Log file
```

## Image Naming Convention

The scripts automatically organize images according to the EPRI naming convention:

- **Pre-transfusion**: BE1, BE2, BE3, BE4
- **Mid-transfusion**: ME1, ME2, ME3, ME4
- **Post-transfusion**: AE1, AE2, AE3, AE4
- **Amplitude reference**: BE_AMP (same as BE1 but amplitude data)

ROI is first created on BE_AMP, then transferred to all other images.

## ROI Statistics

For each image-ROI combination, the following statistics are calculated:

- **Mean**: Average value within ROI
- **Median**: Median value within ROI
- **Std**: Standard deviation within ROI
- **N_Voxels**: Number of voxels in ROI
- **Min**: Minimum value within ROI
- **Max**: Maximum value within ROI

## Interactive ROI Creation

When using manual ROI creation in interactive mode:

1. **Navigation**: Use 'n' (next) and 'p' (previous) to navigate slices
2. **ROI Creation**: Click and drag to create rectangular ROIs
3. **Reset**: Press 'r' to reset current slice ROI
4. **Save**: Press 'q' to quit and save all ROIs

## Troubleshooting

### Common Issues

1. **No processed files found**

   - Ensure .tdms files have been processed using ProcessGUI.m
   - Check that processed files start with 'p' and are in the correct directory

2. **UNet model not found**

   - Place `unet3d_kidney.pth` in the `process/` directory
   - Or use manual ROI creation as fallback

3. **MATLAB engine errors**

   - Install MATLAB Engine: `pip install matlabengine`
   - Ensure MATLAB is properly installed and licensed

4. **Memory errors with large images**
   - Close other applications to free memory
   - Process smaller batches of images

### Log Files

Check the log files for detailed error information:

- `epri_roi_extractor.log` - ROI extraction log
- `epri_automation.log` - Full automation log

## Example Output

Sample statistics output:

| Image | ROI     | Mean  | Median | Std  | N_Voxels |
| ----- | ------- | ----- | ------ | ---- | -------- |
| BE1   | Kidney  | 12.34 | 11.89  | 3.45 | 1234     |
| BE1   | Kidney2 | 13.56 | 13.01  | 2.98 | 1098     |
| BE2   | Kidney  | 11.98 | 11.45  | 3.12 | 1234     |
| ...   | ...     | ...   | ...    | ...  | ...      |

## Support

For issues or questions:

1. Check the log files for error details
2. Verify input file formats and directory structure
3. Ensure all dependencies are installed correctly

## License

This software is provided for research purposes. Please cite appropriately if used in publications.
