# UNet3D Kidney AI Model - Complete User Guide

## 🧠 What is the UNet3D Kidney Model?

The `unet3d_kidney.pth` file contains a pre-trained artificial intelligence model specifically designed to automatically identify and segment kidney regions in EPRI medical scan data. This eliminates the tedious manual process of drawing ROI boundaries.

## 🎯 How the AI Model Works

### Input Processing

1. **Image Preprocessing**: Takes your BE_AMP image (3D volume)
2. **Normalization**: Resizes to 64×64×64 and normalizes pixel values
3. **Neural Network**: Processes through 3D U-Net architecture
4. **Output**: Generates probability map for kidney regions
5. **Thresholding**: Converts probabilities to binary mask (>50% = kidney)
6. **Post-processing**: Separates into left and right kidney components

### Technical Details

- **Architecture**: 3D U-Net with encoder-decoder structure
- **Input Size**: 64×64×64 voxels (automatically resized)
- **Output**: Binary segmentation mask
- **Training**: Pre-trained on EPRI kidney data
- **Inference Time**: ~1-2 seconds on GPU, ~10-15 seconds on CPU

## 🚀 Quick Start Guide

### Step 1: Verify Setup

```bash
cd c:\Users\ftmen\Documents\EPRI\process
python test_unet_model.py
```

This will:

- ✅ Check if the model loads correctly
- ✅ Test inference on synthetic data
- ✅ Test on your actual EPRI data (if available)
- ✅ Generate visualization images

### Step 2: Run Automatic ROI Analysis

```bash
python epri_roi_extractor.py --data-subdir 241202
```

The script will automatically:

1. 🔍 Detect the UNet model
2. 📁 Load your processed .mat files
3. 🧠 Run AI segmentation on BE_AMP image
4. 🎯 Create kidney ROI masks
5. 📊 Extract statistics for all images
6. 💾 Save results to Excel/CSV

## 🔧 Advanced Usage

### Customizing the AI Model Behavior

You can modify the AI model behavior by editing the `epri_roi_extractor.py` file:

#### Adjusting Segmentation Threshold

```python
# In generate_roi_with_unet function, line ~XXX
# Default threshold is 0.5 (50% confidence)
mask = (pred > 0.5)  # Change to 0.3 for more sensitive, 0.7 for more conservative
```

#### Modifying ROI Names

```python
# In make_roi_struct function
roi_structs = [
    self.make_roi_struct(right_mask, "Right_Kidney"),  # Custom names
    self.make_roi_struct(left_mask, "Left_Kidney")
]
```

### Using the Model Programmatically

Here's how to use the UNet3D model in your own scripts:

```python
import torch
import numpy as np
from skimage.transform import resize
from unet3d_model import UNet3D

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = UNet3D().to(device)
model.load_state_dict(torch.load("unet3d_kidney.pth", map_location=device))
model.eval()

# Prepare your 3D image data (example)
your_3d_image = np.random.rand(64, 64, 64)  # Replace with your actual data

# Preprocess
img_resized = resize(your_3d_image, (64, 64, 64), preserve_range=True)
img_norm = (img_resized - img_resized.min()) / (np.ptp(img_resized) + 1e-8)
input_tensor = torch.tensor(img_norm, dtype=torch.float32).unsqueeze(0).unsqueeze(0).to(device)

# Run inference
with torch.no_grad():
    prediction = model(input_tensor).squeeze().cpu().numpy()
    kidney_mask = (prediction > 0.5)

# Use the mask for your analysis
kidney_voxels = your_3d_image[kidney_mask]
statistics = {
    'mean': np.mean(kidney_voxels),
    'std': np.std(kidney_voxels),
    'count': len(kidney_voxels)
}
```

## 🎨 Visualization and Quality Control

### Checking AI Segmentation Quality

The AI model creates visualization files to help you verify the segmentation quality:

1. **Run the test script**:

   ```bash
   python test_unet_model.py
   ```

2. **Check generated images**:

   - `unet_test_result.png` - Test on synthetic data
   - `unet_real_data_result.png` - Test on your actual data

3. **Visual inspection checklist**:
   - ✅ Are both kidneys identified?
   - ✅ Are the boundaries reasonable?
   - ✅ Is there minimal noise/artifacts?
   - ✅ Do the ROIs match anatomical expectations?

### When AI Segmentation Fails

If the AI model doesn't work well for your specific data:

1. **Use manual ROI creation**:

   ```bash
   python manual_roi_creator.py --project-file your_project.mat --mode interactive
   ```

2. **Adjust the threshold**:

   ```python
   # Try different confidence thresholds
   mask = (pred > 0.3)  # More sensitive
   # or
   mask = (pred > 0.7)  # More conservative
   ```

3. **Use geometric fallback**:
   ```bash
   python simple_roi_test.py  # Uses geometric ROI shapes
   ```

## 🔧 Troubleshooting

### Common Issues and Solutions

#### 1. "UNet model not found"

```bash
# Check if file exists
ls -la unet3d_kidney.pth

# If missing, the file should be in the process directory
# Contact your research team for the model file
```

#### 2. "CUDA out of memory"

```python
# Use CPU instead of GPU
device = torch.device("cpu")  # Force CPU usage

# Or reduce batch size (already optimized in the scripts)
```

#### 3. "Empty mask predicted"

This happens when the AI doesn't detect kidneys:

- Check input data quality
- Try lowering the threshold: `mask = (pred > 0.3)`
- Use manual ROI creation as fallback

#### 4. "Poor segmentation quality"

- Verify input data is BE_AMP (amplitude) image
- Check if image has proper contrast
- Consider manual ROI creation for problematic cases

### Performance Optimization

#### GPU vs CPU Performance

- **GPU (CUDA)**: ~1-2 seconds per image
- **CPU**: ~10-15 seconds per image

#### Memory Usage

- **GPU**: ~1-2 GB VRAM
- **CPU**: ~500 MB RAM

#### Speed Optimization Tips

```python
# Enable GPU if available
torch.backends.cudnn.benchmark = True  # Optimize for consistent input sizes
```

## 📊 Understanding the Output

### ROI Statistics Generated

For each kidney ROI, the AI extraction provides:

- **Mean**: Average signal intensity in kidney region
- **Median**: Middle value of all kidney voxels
- **Std**: Standard deviation (measure of variability)
- **N_Voxels**: Number of voxels in the kidney ROI
- **Min/Max**: Minimum and maximum values

### Expected Results

Typical kidney ROI should contain:

- **N_Voxels**: 500-3000 voxels (depending on kidney size and resolution)
- **Values**: Should reflect physiological pO2 measurements
- **Consistency**: Similar ROI sizes across time series (BE1-4, ME1-4, AE1-4)

## 🔬 Model Validation

### Quality Metrics to Check

1. **ROI Size Consistency**:

   ```python
   # Check if kidney ROI sizes are similar across images
   size_variation = std(roi_sizes) / mean(roi_sizes)
   # Should be < 0.3 for good consistency
   ```

2. **Anatomical Plausibility**:

   - Two separate kidney regions
   - Reasonable size and shape
   - Consistent positioning across time series

3. **Signal Quality**:
   - ROI values should be within expected physiological range
   - No extreme outliers or artifacts

## 🎓 Training Your Own Model (Advanced)

If you need to retrain the model for your specific data:

### Data Preparation

```python
# You would need:
# 1. Training images (3D EPRI volumes)
# 2. Manual segmentation masks (ground truth)
# 3. Validation dataset

# Typical training setup
training_data = [
    ("image1.mat", "mask1.mat"),
    ("image2.mat", "mask2.mat"),
    # ... more training pairs
]
```

### Training Script Structure

```python
# Basic training loop (simplified)
for epoch in range(num_epochs):
    for image, mask in training_loader:
        prediction = model(image)
        loss = dice_loss(prediction, mask)
        loss.backward()
        optimizer.step()
```

Note: Model retraining requires significant computational resources and expertise in deep learning.

## 📚 Additional Resources

### Research Papers

- U-Net: Convolutional Networks for Biomedical Image Segmentation
- 3D U-Net: Learning Dense Volumetric Segmentation

### Useful Tools

- **3D Slicer**: For visualizing 3D segmentation results
- **ITK-SNAP**: Medical image segmentation and visualization
- **ImageJ/Fiji**: General image analysis

## 🆘 Getting Help

If you encounter issues:

1. **Check logs**: Look at `epri_roi_extractor.log` for detailed error messages
2. **Run diagnostics**: Use `python test_unet_model.py` to isolate issues
3. **Fallback options**: Use manual or geometric ROI creation if AI fails
4. **Contact support**: Reach out to your research team for model-specific issues

## 🎉 Success Indicators

You know the AI model is working correctly when:

- ✅ Model loads without errors
- ✅ Segmentation completes in reasonable time
- ✅ ROI visualizations look anatomically correct
- ✅ Statistics are generated for all images
- ✅ Results are exported to Excel/CSV successfully

The UNet3D kidney model should dramatically speed up your ROI analysis workflow while providing consistent, reproducible results across all your EPRI medical scan data!
