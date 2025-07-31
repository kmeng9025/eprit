# GPU Setup Guide for Fiducial Detection

This guide will help you set up the fiducial detection pipeline on a GPU-enabled computer for faster training.

## Prerequisites

### Hardware Requirements

- **GPU**: NVIDIA GPU with CUDA support (GTX 1060 or better recommended)
- **RAM**: 8GB+ system RAM
- **Storage**: 2GB+ free space
- **VRAM**: 4GB+ GPU memory recommended for batch size 4

### Software Requirements

- **Python**: 3.8 or higher
- **CUDA**: 11.8 or 12.x (check with `nvidia-smi`)
- **Git**: For cloning repository (optional)

## Quick Setup

### Option 1: Automatic Installation (Recommended)

**Windows:**

```cmd
# Run the automated installer
install_gpu.bat
```

**Linux/Mac:**

```bash
# Make the script executable and run
chmod +x install_gpu.sh
./install_gpu.sh
```

### Option 2: Manual Installation

1. **Create Virtual Environment:**

```bash
python -m venv fiducial_env
source fiducial_env/bin/activate  # Windows: fiducial_env\Scripts\activate
```

2. **Install PyTorch with CUDA:**

```bash
# For CUDA 11.8
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# For CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# For CPU only (fallback)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
```

3. **Install Other Dependencies:**

```bash
pip install -r requirements.txt
```

## Verification

Test your installation:

```python
import torch
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"GPU device: {torch.cuda.get_device_name(0)}")
    print(f"GPU memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
```

## Performance Optimization

### GPU Memory Management

- **4GB VRAM**: Use batch size 2
- **6GB VRAM**: Use batch size 4
- **8GB+ VRAM**: Use batch size 6-8

### Training Speed

- **GPU**: ~2-5 minutes per epoch (depending on GPU)
- **CPU**: ~15-30 minutes per epoch

### Automatic Optimizations

The training script automatically:

- Detects GPU availability
- Uses mixed precision training (AMP) for better performance
- Adjusts batch size based on available hardware
- Enables gradient clipping for stability

## Usage

1. **Prepare Data:**

```bash
python prep_fiducial_data.py
```

2. **Train Model:**

```bash
python train_fiducial_model.py
```

3. **Make Predictions:**

```bash
python predict_fiducials.py
```

## Troubleshooting

### Common Issues

**"CUDA out of memory":**

- Reduce batch size in `train_fiducial_model.py`
- Close other GPU applications
- Use smaller model or reduce image size

**"No module named 'torch'":**

- Ensure virtual environment is activated
- Reinstall PyTorch with correct CUDA version

**"RuntimeError: No CUDA GPUs are available":**

- Check NVIDIA drivers: `nvidia-smi`
- Verify CUDA installation
- Script will automatically fall back to CPU

**Slow training on GPU:**

- Check if using CPU accidentally
- Verify mixed precision is enabled
- Monitor GPU utilization: `nvidia-smi -l 1`

### Performance Monitoring

Monitor training progress:

```bash
# GPU utilization
nvidia-smi -l 1

# Memory usage
watch -n 1 'free -h'
```

## Advanced Configuration

### Custom GPU Settings

Edit `train_fiducial_model.py` to customize:

```python
# Batch size (adjust based on GPU memory)
BATCH_SIZE = 8  # Increase for better GPU utilization

# Enable/disable mixed precision
use_amp = True  # Set to False if having issues

# Multi-GPU training (experimental)
if torch.cuda.device_count() > 1:
    model = nn.DataParallel(model)
```

### Memory Optimization

For limited GPU memory:

```python
# Gradient accumulation (simulate larger batch size)
accumulation_steps = 4
effective_batch_size = BATCH_SIZE * accumulation_steps

# Clear cache periodically
if batch_idx % 10 == 0:
    torch.cuda.empty_cache()
```

## File Transfer Tips

When moving files to/from GPU computer:

1. **Essential Files:**

   - All `.py` scripts
   - `requirements.txt`
   - `./DATA/MRIAlign/*.mat` files

2. **Compressed Transfer:**

```bash
# Create archive
tar -czf fiducial_pipeline.tar.gz *.py requirements.txt DATA/

# Extract on GPU computer
tar -xzf fiducial_pipeline.tar.gz
```

3. **Results Transfer:**
   - `./fiducial_model_best.pth` (trained model)
   - `./preprocessed_fiducials/` (processed data)
   - `./fiducial_predictions/` (prediction results)

## Expected Performance

### Training Time (150 epochs)

- **RTX 4090**: ~3-5 hours
- **RTX 3080**: ~5-8 hours
- **GTX 1080**: ~8-12 hours
- **CPU**: ~24-48 hours

### Model Quality

- **Validation Loss**: Should reach <0.1 after 100+ epochs
- **F1 Score**: Target >0.8 for good fiducial detection
- **IoU**: Target >0.7 for precise localization

## Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify GPU setup with test script
3. Try CPU fallback mode first
4. Monitor system resources during training
