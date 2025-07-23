# EPRI Data Processing Automation

This automated pipeline processes medical scan data from TDMS files and creates ArbuzGUI-compatible projects with ROI analysis.

## Overview

The automation pipeline:

1. **Identifies TDMS files** in `DATA/241202` (excludes tuning files ending in `FID_GRAD_MIN_file.tdms`)
2. **Processes image files** ending in `image4D_18x18_0p75gcm_file.tdms` using ProcessGUI.m functionality
3. **Builds ArbuzGUI project** with proper image names and metadata:
   - Pre-transfusion: BE1, BE2, BE3, BE4
   - Mid-transfusion: ME1, ME2, ME3, ME4
   - Post-transfusion: AE1, AE2, AE3, AE4
   - Special amplitude image: BE_AMP (from BE1)
4. **Creates kidney ROI** on BE_AMP image using AI model (Draw_ROI.py)
5. **Extracts statistics** from all images within the ROI:
   - Mean, Median, Standard deviation, Number of voxels
6. **Saves results** to Excel spreadsheet

## Required Files

- `epri/Scenario/PulseRecon.scn` - Processing scenario
- `epri/Scenario/720MHz_JIVA5B/IRESE_64pts_mouse_STANDARD_CHIRALITY.par` - Parameters
- `process/unet3d_model.py` - AI model definition
- `process/unet3d_kidney.pth` - Trained AI model weights
- `corrected_Draw_ROI.py` - ROI creation script

## Usage

### Simple Usage

```matlab
run_automation
```

### Advanced Usage

```matlab
automate_processing
```

## Output Structure

Each run creates a timestamped folder in `automated_outputs/` containing:

- `project.mat` - ArbuzGUI-compatible project file
- `project_with_roi.mat` - Project file with kidney ROI
- `roi_statistics.xlsx` - Excel file with ROI statistics
- Supporting files and debug information

## Results

The Excel file contains statistics for each image:

- ImageName: BE1, BE2, etc.
- Group: Pre-transfusion, Mid-transfusion, Post-transfusion
- Mean: Average signal in ROI
- Median: Median signal in ROI
- StdDev: Standard deviation of signal in ROI
- NumVoxels: Number of voxels in ROI

## Data Structure Compatibility

The generated project files are fully compatible with:

- ArbuzGUI (Arbuz2.0/ArbuzGUI.m)
- ibGUI (ibGUI/ibGUI.m)

Image data is stored as:

- float64 format
- Proper transformation matrices (A, Anative, Aprime)
- Correct ImageType values (EPRI, AMP_pEPRI)
- Initialized ROI structures

## Requirements

### MATLAB Dependencies

- Image Processing Toolbox
- Signal Processing Toolbox
- All EPRI toolbox functions

### Python Dependencies

- torch, torchvision
- numpy, scipy
- scikit-image
- h5py

## Troubleshooting

### Common Issues

1. **"Could not extract image data"**

   - Check that both .mat and p\*.mat files exist
   - Verify file permissions

2. **"ROI creation failed"**

   - Ensure Python environment is configured
   - Check that AI model file exists
   - Verify image data format

3. **"Statistics extraction failed"**
   - Check that ROI was created successfully
   - Verify Excel writing permissions

### File Locations

- TDMS files: `DATA/241202/*image4D_18x18_0p75gcm_file.tdms`
- Processed files: `DATA/241202/*.mat` and `DATA/241202/p*.mat`
- Output: `automated_outputs/run_YYYYMMDD_HHMMSS/`

## Technical Details

### Image Processing

- Uses reconstructed image data from `mat_recFXD` field (first time point)
- Falls back to fitted data from p-files if needed
- Handles multiple parameter fits (uses first parameter)

### ROI Creation

- AI model trained on kidney segmentation
- Processes BE_AMP (amplitude) image
- Creates 3D binary mask
- Saves as ArbuzGUI-compatible ROI structure

### Statistics Calculation

- Applies ROI mask to each image
- Excludes zero/background voxels
- Calculates standard descriptive statistics
- Groups results by experimental phase

## Notes

- Each run creates a unique output directory to avoid overwrites
- Processing skips files that are already processed
- Compatible with both v7 and v7.3 MATLAB file formats
- Handles MATLAB structure arrays and cell arrays properly
- Maintains full metadata and transformation information
