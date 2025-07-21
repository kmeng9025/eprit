# How to Run the UNet3D AI Model - Step-by-Step Instructions

## 🎯 Quick Answer

To run the AI model on your EPRI data:

```bash
cd c:\Users\ftmen\Documents\EPRI\process
python epri_roi_extractor.py --data-subdir YOUR_DATA_FOLDER
```

Replace `YOUR_DATA_FOLDER` with the name of your data subdirectory (e.g., `241202`).

## 📁 Understanding Input File Structure

### Required File Organization

The AI model expects your files to be organized like this:

```
EPRI/
├── DATA/
│   ├── 241202/                           # ← Your data subdirectory
│   │   ├── p8475image4D_18x18_0p75gcm_file.mat    # ← Processed files (start with 'p')
│   │   ├── p8482image4D_18x18_0p75gcm_file.mat
│   │   ├── p8488image4D_18x18_0p75gcm_file.mat
│   │   └── ... (more processed files)
│   └── 250115/                           # ← Another date folder (example)
│       ├── p9001image4D_18x18_0p75gcm_file.mat
│       └── ...
└── process/
    ├── unet3d_kidney.pth                 # ← AI model file
    ├── epri_roi_extractor.py             # ← Main script
    └── ...
```

### What Files the AI Looks For

The AI model automatically finds:

- **Processed .mat files** that start with `p` and end with `image4D_18x18_0p75gcm_file.mat`
- **Example files**: `p8475image4D_18x18_0p75gcm_file.mat`, `p8561image4D_18x18_0p75gcm_file.mat`
- **Location**: Inside `DATA/YOUR_FOLDER_NAME/`

## 🚀 How to Run the AI Model

### Method 1: Basic Usage (Recommended)

```bash
# Navigate to the process directory
cd c:\Users\ftmen\Documents\EPRI\process

# Run AI analysis on data folder "241202"
python epri_roi_extractor.py --data-subdir 241202
```

### Method 2: Specify Different Data Folder

```bash
# For data in folder "250115"
python epri_roi_extractor.py --data-subdir 250115

# For data in folder "experiment_001"
python epri_roi_extractor.py --data-subdir experiment_001
```

### Method 3: Specify Custom Output Location

```bash
# Save results to a specific location
python epri_roi_extractor.py --data-subdir 241202 --output-dir "C:\MyResults\Analysis1"
```

### Method 4: Use Different Base Directory

```bash
# If your EPRI folder is in a different location
python epri_roi_extractor.py --data-subdir 241202 --base-dir "D:\Research\EPRI_Data"
```

## 📋 Command Line Options Explained

### `--data-subdir` (Required)

- **What it does**: Specifies which subfolder in DATA/ to process
- **Example**: `--data-subdir 241202` looks for files in `DATA/241202/`
- **Default**: `241202` if not specified

### `--output-dir` (Optional)

- **What it does**: Where to save the results
- **Example**: `--output-dir "C:\Results\MyAnalysis"`
- **Default**: Auto-generated folder in `process/output/`

### `--base-dir` (Optional)

- **What it does**: Location of your main EPRI directory
- **Example**: `--base-dir "D:\Research\EPRI"`
- **Default**: `c:\Users\ftmen\Documents\EPRI`

## 📊 Complete Examples

### Example 1: Analyze Today's Data

```bash
cd c:\Users\ftmen\Documents\EPRI\process
python epri_roi_extractor.py --data-subdir 250721
```

### Example 2: Analyze Specific Experiment

```bash
cd c:\Users\ftmen\Documents\EPRI\process
python epri_roi_extractor.py --data-subdir ExperimentA_Mouse1 --output-dir "C:\Results\MouseStudy"
```

### Example 3: Process Multiple Datasets

```bash
# Process first dataset
python epri_roi_extractor.py --data-subdir 241201

# Process second dataset
python epri_roi_extractor.py --data-subdir 241202

# Process third dataset
python epri_roi_extractor.py --data-subdir 241203
```

## 🔍 How to Find Your Data Subdirectory

### Step 1: Check Your DATA Folder

```bash
# List available data folders
dir c:\Users\ftmen\Documents\EPRI\DATA
```

You'll see something like:

```
241202/
250115/
ExperimentA/
```

### Step 2: Check What's Inside a Folder

```bash
# See what files are in a specific folder
dir "c:\Users\ftmen\Documents\EPRI\DATA\241202\p*.mat"
```

You should see files like:

```
p8475image4D_18x18_0p75gcm_file.mat
p8482image4D_18x18_0p75gcm_file.mat
p8488image4D_18x18_0p75gcm_file.mat
...
```

## ⚠️ Troubleshooting Input Files

### Problem: "No processed files found"

**Cause**: The AI can't find processed .mat files in your specified folder.

**Solutions**:

1. **Check folder name**: Make sure `--data-subdir` matches your actual folder name
2. **Check file names**: Files must start with `p` and end with `image4D_18x18_0p75gcm_file.mat`
3. **Check location**: Files must be in `DATA/YOUR_FOLDER/`

```bash
# Debug: List what files exist
dir "c:\Users\ftmen\Documents\EPRI\DATA\YOUR_FOLDER\*.mat"
```

### Problem: "Only found X files, need at least 4"

**Cause**: Not enough processed files for a complete analysis.

**Solutions**:

1. **Process more .tdms files** using ProcessGUI.m first
2. **Check if files are properly named** (start with `p`)

### Problem: "Error loading file"

**Cause**: Corrupted or incompatible .mat file.

**Solutions**:

1. **Re-process** the original .tdms file
2. **Check file integrity** by loading in MATLAB manually

## 📈 Expected Input/Output

### Input Requirements

- **Minimum**: 4 processed .mat files (for one complete group)
- **Optimal**: 12 processed .mat files (4 pre-, 4 mid-, 4 post-transfusion)
- **File format**: MATLAB .mat files with `fit_data` structure

### Output Generated

- **Excel file**: `roi_statistics_FOLDER_NAME.xlsx`
- **CSV file**: `roi_statistics_FOLDER_NAME.csv`
- **Project files**: Original and ROI-enhanced versions
- **Log file**: Detailed processing information

### Processing Time

- **Setup**: ~2-3 seconds
- **AI segmentation**: ~1-2 seconds per dataset
- **Statistics extraction**: ~1 second
- **Total**: Usually under 10 seconds

## 💡 Pro Tips

### Tip 1: Process Multiple Experiments

Create a batch script to process multiple datasets:

```batch
@echo off
python epri_roi_extractor.py --data-subdir 241201
python epri_roi_extractor.py --data-subdir 241202
python epri_roi_extractor.py --data-subdir 241203
echo All analyses complete!
```

### Tip 2: Test Before Full Analysis

Always test with a small dataset first:

```bash
# Test the setup
python test_unet_model.py

# Test with actual data
python epri_roi_extractor.py --data-subdir YOUR_FOLDER
```

### Tip 3: Monitor Progress

Watch the console output for:

- ✅ "Model loaded successfully"
- ✅ "Found X processed files"
- ✅ "ROI analysis completed successfully"

### Tip 4: Verify Results

After processing, check:

- **Output folder**: Contains Excel and CSV files
- **Log file**: No error messages
- **Statistics**: Values are reasonable for your data

## 🆘 Getting Help

If you encounter issues:

1. **Check the log file**: `epri_roi_extractor.log`
2. **Run diagnostics**: `python test_unet_model.py`
3. **Verify file structure**: Use the commands above to check your data organization
4. **Try simple test**: Use the working example `--data-subdir 241202`

The AI model is designed to be simple to use - just specify your data folder and let it do the work!
