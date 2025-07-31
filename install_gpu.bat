@echo off
REM GPU Installation Script for Windows
REM Run this script on your Windows GPU computer to set up the environment

echo 🚀 Setting up Fiducial Detection Pipeline with GPU support
echo ==========================================================

REM Check if CUDA is available
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ NVIDIA GPU detected:
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
) else (
    echo ⚠️  No NVIDIA GPU detected. Installing CPU-only version.
)

REM Create virtual environment (optional but recommended)
echo 📦 Creating virtual environment...
python -m venv fiducial_env
call fiducial_env\Scripts\activate

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install PyTorch with CUDA support (if available)
echo 🔥 Installing PyTorch...
nvidia-smi >nul 2>&1
if %errorlevel% == 0 (
    REM Install CUDA version
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
) else (
    REM Install CPU version
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
)

REM Install other requirements
echo 📚 Installing other dependencies...
pip install numpy scipy matplotlib scikit-learn h5py tqdm

REM Verify installation
echo ✅ Verifying installation...
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

echo.
echo 🎯 Installation complete!
echo Next steps:
echo 1. Copy your .mat files to ./DATA/MRIAlign/
echo 2. Run: python prep_fiducial_data.py
echo 3. Run: python train_fiducial_model.py
echo 4. Run: python predict_fiducials.py

pause
