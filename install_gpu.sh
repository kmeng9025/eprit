#!/bin/bash
# GPU Installation Script for Fiducial Detection Pipeline
# Run this script on your GPU computer to set up the environment

echo "🚀 Setting up Fiducial Detection Pipeline with GPU support"
echo "=========================================================="

# Check if CUDA is available
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected:"
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️  No NVIDIA GPU detected. Installing CPU-only version."
fi

# Create virtual environment (optional but recommended)
echo "📦 Creating virtual environment..."
python -m venv fiducial_env
source fiducial_env/bin/activate  # On Windows: fiducial_env\Scripts\activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install PyTorch with CUDA support (if available)
echo "🔥 Installing PyTorch..."
if command -v nvidia-smi &> /dev/null; then
    # Install CUDA version (adjust CUDA version as needed)
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
else
    # Install CPU version
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
fi

# Install other requirements
echo "📚 Installing other dependencies..."
pip install numpy scipy matplotlib scikit-learn h5py tqdm

# Verify installation
echo "✅ Verifying installation..."
python -c "
import torch
import numpy as np
import scipy
import matplotlib
import sklearn

print(f'PyTorch version: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU device: {torch.cuda.get_device_name(0)}')
print(f'NumPy version: {np.__version__}')
print(f'SciPy version: {scipy.__version__}')
print('✅ All packages installed successfully!')
"

echo ""
echo "🎯 Installation complete!"
echo "Next steps:"
echo "1. Copy your .mat files to ./DATA/MRIAlign/"
echo "2. Run: python prep_fiducial_data.py"
echo "3. Run: python train_fiducial_model.py"
echo "4. Run: python predict_fiducials.py"
