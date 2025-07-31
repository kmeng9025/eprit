# Fiducial Detection for 3D EPR/MRI Images

This system provides automated fiducial detection in 3D EPR and MRI medical images using deep learning. It extracts fiducials from annotated .mat files, trains a 3D U-Net model, and can predict fiducials in new data.

## Overview

The system consists of three main components:

1. **Data Preprocessing** (`prep_fiducial_data.py`): Extracts fiducials from .mat files and prepares training data
2. **Model Training** (`train_fiducial_model.py`): Trains a 3D U-Net for fiducial detection
3. **Prediction** (`predict_fiducials.py`): Uses the trained model to detect fiducials in new images

## Quick Start

### Prerequisites

Install required Python packages:

```bash
pip install torch torchvision torchaudio numpy scipy matplotlib scikit-learn opencv-python
```

### Complete Pipeline

Run the entire pipeline (preprocessing + training + prediction):

```bash
python fiducial_pipeline.py --mode all
```

### Step-by-Step Usage

1. **Preprocess Data**:

   ```bash
   python fiducial_pipeline.py --mode prep
   ```

2. **Train Model**:

   ```bash
   python fiducial_pipeline.py --mode train --epochs 150
   ```

3. **Make Predictions**:
   ```bash
   python fiducial_pipeline.py --mode predict
   ```

## Data Structure

The system expects .mat files in `./DATA/MRIAlign/` with the following structure:

- `images`: Array of image entries
- Each image entry contains:
  - `Name`: Image identifier (e.g., '>MRI', '>PreExchAMP')
  - `data`: 3D image array
  - `slaves`: Array of annotation objects including fiducials

### Supported Fiducial Names

The system automatically detects fiducials with names containing:

- "FID" (e.g., FID, Side_FID, E_FID, Es_FID)
- "Fiducial" (e.g., Fiducial 1)

## Model Architecture

- **3D U-Net** with encoder-decoder structure
- **Input**: 64×64×64 normalized 3D images
- **Output**: Binary fiducial masks
- **Loss Functions**: Combination of BCE, Focal Dice, and Tversky losses
- **Optimization**: AdamW with learning rate scheduling

## Training Features

- **Data Augmentation**: Automatic resizing and normalization
- **Validation Split**: 20% of data for validation
- **Early Stopping**: Saves best model based on validation loss
- **Metrics**: Precision, Recall, F1-score, IoU
- **Checkpointing**: Resume training from saved models

## Output Files

### Preprocessing

- `./preprocessed_fiducials/X_fiducials.npy`: Input images (N, 1, 64, 64, 64)
- `./preprocessed_fiducials/Y_fiducials.npy`: Fiducial masks (N, 1, 64, 64, 64)
- `./preprocessed_fiducials/fiducial_metadata.txt`: Dataset information

### Training

- `./fiducial_model_best.pth`: Best model (recommended for inference)
- `./fiducial_model.pth`: Final model
- `./preprocessed_fiducials/training_progress.png`: Training curves

### Prediction

- `./fiducial_predictions/`: Directory containing:
  - `*_fiducial_mask.npy`: Binary prediction masks
  - `*_confidence.npy`: Confidence maps (0-1)
  - `*_prediction.png`: Visualization images

## Advanced Usage

### Individual Scripts

**Preprocessing only**:

```bash
python prep_fiducial_data.py
```

**Training with custom parameters**:

```bash
python train_fiducial_model.py
# Edit the script to modify hyperparameters
```

**Prediction on specific file**:

```bash
python predict_fiducials.py --input_file ./DATA/MRIAlign/ExchangeB6M005.mat --threshold 0.3
```

**Prediction with different threshold**:

```bash
python predict_fiducials.py --threshold 0.7 --output_dir ./custom_predictions
```

### Command Line Arguments

**fiducial_pipeline.py**:

- `--mode`: prep, train, predict, or all
- `--epochs`: Number of training epochs (default: 150)
- `--input_file`: Specific .mat file for prediction
- `--threshold`: Prediction threshold (default: 0.5)

**predict_fiducials.py**:

- `--model_path`: Path to trained model
- `--input_file`: Single file to process
- `--input_dir`: Directory of .mat files
- `--output_dir`: Output directory
- `--threshold`: Prediction threshold
- `--device`: cuda/cpu/auto

## Model Performance

The model is optimized for small fiducial objects and includes:

- **Focal Dice Loss**: Better handling of class imbalance
- **Tversky Loss**: Optimized for small object detection
- **Gradient Clipping**: Stable training
- **Learning Rate Scheduling**: Adaptive learning

## Troubleshooting

### Common Issues

1. **"No valid fiducial data found"**:

   - Check that .mat files contain fiducials with names containing "FID" or "Fiducial"
   - Verify the data structure matches expected format

2. **CUDA out of memory**:

   - Reduce batch size in training script
   - Use CPU instead: `--device cpu`

3. **Poor prediction quality**:
   - Increase training epochs
   - Adjust prediction threshold
   - Ensure sufficient training data

### Data Requirements

- **Minimum**: 5-10 annotated fiducials for training
- **Recommended**: 20+ fiducials from diverse images
- **Image Types**: Both EPR (64³) and MRI (350×350×18/40) supported
- **File Format**: MATLAB .mat files with specific structure

## Technical Details

### Image Processing

- Automatic resizing to 64×64×64 for consistency
- Intensity normalization to [0, 1] range
- Bicubic interpolation for resizing

### Model Training

- 5-fold validation split
- Mixed precision training (if available)
- Gradient clipping for stability
- Comprehensive metrics tracking

### Memory Optimization

- Batch processing for large datasets
- Efficient data loading with PyTorch DataLoader
- Automatic memory cleanup

## Citation

If you use this fiducial detection system in your research, please cite:

```
[Your paper/repository citation here]
```

## Support

For issues or questions:

1. Check the troubleshooting section
2. Review console output for error messages
3. Ensure data format matches requirements
4. Verify all dependencies are installed

## License

[Your license information here]
