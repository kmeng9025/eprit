# Medical Imaging Pipeline Scripts

This folder contains the essential scripts for the automated medical imaging pipeline.

## Core Pipeline Scripts

### `clean_pipeline.py`
- **Purpose**: Main automation pipeline for processing medical images
- **Function**: Creates ArbuzGUI projects, applies ROI detection, and generates statistics
- **Usage**: Primary script for end-to-end automation
- **Status**: Working and tested

### `enhanced_draw_roi.py` / `improved_Draw_ROI.py`
- **Purpose**: Enhanced ROI detection with API wrapper
- **Function**: Wraps the original Draw_ROI.py with UNet3D model for kidney detection
- **Usage**: Called by the main pipeline for automated ROI detection
- **Status**: Working with UNet3D model

### `roi_copy_script.py`
- **Purpose**: Copy ROI masks between images
- **Function**: Propagates ROI from reference image to other images in the project
- **Usage**: Used within the pipeline for ROI propagation
- **Status**: Working

## MATLAB Compatibility Scripts

### `fix_matlab_compatibility.py`
- **Purpose**: Fix MATLAB compatibility issues with generated project files
- **Function**: Converts data types and formats for MATLAB compatibility
- **Usage**: Run when MATLAB has trouble loading Python-generated project files
- **Status**: Addresses known compatibility issues

### `create_matlab_native_project.py`
- **Purpose**: Create project files directly in MATLAB to avoid compatibility issues
- **Function**: Uses MATLAB engine to create native MATLAB project files
- **Usage**: Alternative project creation method for maximum MATLAB compatibility
- **Status**: MATLAB-native approach

## Usage Instructions

1. **Main Pipeline**: Run `clean_pipeline.py` for complete automation
2. **MATLAB Issues**: Use `fix_matlab_compatibility.py` or `create_matlab_native_project.py` if needed
3. **Manual ROI**: Use `enhanced_draw_roi.py` for standalone ROI detection

## Dependencies

- Python 3.x
- MATLAB Engine for Python
- scipy, numpy, matplotlib
- Original Draw_ROI.py with UNet3D model
- ArbuzGUI MATLAB toolbox

## Notes

- All analysis and debug scripts have been removed from the workspace
- These scripts represent the working, tested components of the pipeline
- The original Draw_ROI.py remains in the process/ folder and should not be modified
