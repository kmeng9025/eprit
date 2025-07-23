# EPRI Automation Pipeline

This folder contains the complete Python automation pipeline for processing medical imaging data stored in .tdms files.

## Files Description

### Main Scripts

- **`simple_automation_pipeline.py`** - Main automation script (recommended)
- **`python_automation_pipeline.py`** - Full pipeline with MATLAB engine support
- **`enhanced_draw_roi.py`** - ROI detection and annotation script
- **`roi_copy_script.py`** - Utility to copy ROI between images

### Models and Data

- **`unet3d_kidney.pth`** - Trained UNet3D model for kidney segmentation
- **`unet3d_model.py`** - UNet3D model architecture
- **`Draw_ROI.py`** - Original ROI drawing script
- **`exampleCorrect/`** - Reference example files

## Usage

### Quick Start (Recommended)

```bash
cd process
python simple_automation_pipeline.py
```

This will:

1. Find all processed .mat files in `../DATA/241202/`
2. Create an ArbuzGUI-compatible project with 12 images + BE_AMP + BE_pO2
3. Extract proper amplitude and pO2 images from fit data using correct algorithms
4. Apply kidney ROI detection using the UNet3D model on BE_AMP
5. Copy ROI to all images
6. Extract statistics (Mean, Median, Std, N_Voxels) for each image
7. Save results to `../automated_outputs/run_TIMESTAMP/`

### Output Files

- **`project.mat`** - ArbuzGUI-compatible project file with all images and ROIs
- **`roi_statistics.xlsx`** - Excel file with statistics for each image

### Image Naming Convention

The pipeline automatically assigns these names to the 14 images:

- **Pre-transfusion**: BE1, BE2, BE3, BE4
- **Mid-transfusion**: ME1, ME2, ME3, ME4
- **Post-transfusion**: AE1, AE2, AE3, AE4
- **Special**: BE_AMP (amplitude version of BE1), BE_pO2 (pO2 map from BE1 fit data)

### Individual Script Usage

#### Enhanced ROI Detection

```bash
python enhanced_draw_roi.py project.mat [output.mat]
```

#### ROI Copying

```bash
python roi_copy_script.py project.mat [--analyze] [--source BE_AMP] [--output updated.mat]
```

#### Full Pipeline with MATLAB Engine

```bash
python python_automation_pipeline.py
```

_Note: Requires MATLAB Engine for Python and processes .tdms files directly_

## Requirements

### Python Packages

- numpy
- scipy
- torch (PyTorch)
- scikit-image
- pandas (optional, for Excel output)

### Optional

- MATLAB Engine for Python (for full pipeline)

## Data Structure

### Input Requirements

- Processed .mat files in `../DATA/241202/`
- Files ending in `image4D_18x18_0p75gcm_file.mat` (regular files)
- Corresponding `p`-prefixed files with fitting results

### Output Structure

```
../automated_outputs/run_TIMESTAMP/
├── project.mat           # ArbuzGUI project file
└── roi_statistics.xlsx   # Statistics spreadsheet
```

## Technical Notes

### ArbuzGUI Compatibility

The generated project files are fully compatible with ArbuzGUI and include:

- Proper image structures with transformation matrices
- ROI masks as 'slaves' attached to images
- Correct metadata and project structure

### ROI Detection

- Uses trained UNet3D model for kidney segmentation on properly reconstructed amplitude images
- Automatically splits detected regions into left/right kidneys
- Falls back to spatial splitting if only one component found
- Creates placeholder ROI if model unavailable
- Works with correct T1_InvRecovery_3ParR1 fit parameters for accurate amplitude reconstruction

### Statistics Extraction

For each image with ROI, calculates:

- **Mean**: Average intensity within ROI
- **Median**: Median intensity within ROI
- **Std**: Standard deviation of intensities
- **N_Voxels**: Number of voxels in ROI

## Troubleshooting

### Common Issues

1. **No .mat files found**: Ensure processed files exist in `../DATA/241202/`
2. **Model not found**: Check that `unet3d_kidney.pth` exists in current directory
3. **Import errors**: Install required Python packages
4. **MATLAB errors**: Ensure MATLAB Engine for Python is installed (full pipeline only)

### Debug Mode

Use the analyze option to inspect project contents:

```bash
python roi_copy_script.py project.mat --analyze
```

## Version History

- **v1.0** - Initial release with full automation pipeline
- **v1.1** - Added UNet3D model integration and improved ROI handling
- **v1.2** - Moved to process folder and optimized for existing processed files
