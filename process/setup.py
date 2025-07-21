#!/usr/bin/env python3
"""
EPRI Automation Setup Script

This script sets up the Python environment and installs dependencies
for the EPRI medical scan data processing automation.
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print(f"❌ Python 3.7+ required, found {version.major}.{version.minor}")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} detected")
    return True

def install_package(package_name):
    """Install a single package using pip"""
    try:
        print(f"📦 Installing {package_name}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install {package_name}: {e}")
        return False

def check_and_install_dependencies():
    """Check and install required dependencies"""
    dependencies = [
        ("numpy", "numpy"),
        ("scipy", "scipy"),
        ("pandas", "pandas"),
        ("scikit-image", "skimage"),
        ("Pillow", "PIL"),
        ("matplotlib", "matplotlib"),
        ("openpyxl", "openpyxl"),
        ("tqdm", "tqdm")
    ]
    
    # Optional dependencies
    optional_deps = [
        ("torch", "torch"),
        ("torchvision", "torchvision")
    ]
    
    print("🔍 Checking required dependencies...")
    
    missing_deps = []
    
    for package_name, import_name in dependencies:
        try:
            spec = importlib.util.find_spec(import_name)
            if spec is None:
                missing_deps.append(package_name)
            else:
                print(f"✅ {package_name} is installed")
        except ImportError:
            missing_deps.append(package_name)
    
    if missing_deps:
        print(f"\n📦 Installing missing dependencies: {', '.join(missing_deps)}")
        for package in missing_deps:
            if not install_package(package):
                return False
    
    print("\n🔍 Checking optional dependencies...")
    
    missing_optional = []
    for package_name, import_name in optional_deps:
        try:
            spec = importlib.util.find_spec(import_name)
            if spec is None:
                missing_optional.append(package_name)
            else:
                print(f"✅ {package_name} is installed")
        except ImportError:
            missing_optional.append(package_name)
    
    if missing_optional:
        print(f"\n⚠️  Optional dependencies missing: {', '.join(missing_optional)}")
        print("   These are needed for neural network ROI generation.")
        print("   You can install them later with: pip install torch torchvision")
    
    return True

def create_directories():
    """Create necessary output directories"""
    dirs_to_create = [
        "output",
        "test_output",
        "logs"
    ]
    
    for dir_name in dirs_to_create:
        os.makedirs(dir_name, exist_ok=True)
        print(f"📁 Created directory: {dir_name}")

def test_installation():
    """Test the installation by running basic functionality"""
    print("\n🧪 Testing installation...")
    
    try:
        # Test basic imports
        import numpy as np
        import scipy.io as sio
        print("✅ Scientific computing libraries imported successfully")
        
        # Test matplotlib
        import matplotlib
        matplotlib.use('Agg')  # Use non-interactive backend for testing
        import matplotlib.pyplot as plt
        print("✅ Matplotlib imported successfully")
        
        # Test image processing
        from skimage.transform import resize
        print("✅ Image processing libraries imported successfully")
        
        # Test data handling
        import pandas as pd
        print("✅ Data handling libraries imported successfully")
        
        # Try to import torch (optional)
        try:
            import torch
            print("✅ PyTorch imported successfully")
        except ImportError:
            print("⚠️  PyTorch not available (optional for neural network ROI)")
        
        print("✅ All core libraries working correctly!")
        return True
        
    except Exception as e:
        print(f"❌ Installation test failed: {e}")
        return False

def print_usage_instructions():
    """Print usage instructions"""
    print("\n" + "="*60)
    print("🎉 EPRI Automation Setup Complete!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Ensure your .tdms files are processed using ProcessGUI.m")
    print("2. Check that processed files (starting with 'p') exist in DATA/241202/")
    print("3. Run the test script: python test_epri_data.py")
    print("4. Run the automation: python epri_roi_extractor.py")
    print("\n📂 File Overview:")
    print("  epri_roi_extractor.py      - Main automation script")
    print("  manual_roi_creator.py      - Manual ROI creation tool")
    print("  test_epri_data.py          - Test data structure and basic functionality")
    print("  run_roi_analysis.bat       - Windows batch file for easy execution")
    print("\n⚠️  Note: For neural network ROI generation, place 'unet3d_kidney.pth' in this directory")
    print("\n📖 For detailed instructions, see README.md")

def main():
    """Main setup function"""
    print("🚀 EPRI Medical Scan Data Processing Automation Setup")
    print("="*60)
    
    # Check Python version
    if not check_python_version():
        return 1
    
    # Install dependencies
    if not check_and_install_dependencies():
        print("\n❌ Dependency installation failed")
        return 1
    
    # Create directories
    print("\n📁 Creating directories...")
    create_directories()
    
    # Test installation
    if not test_installation():
        return 1
    
    # Print usage instructions
    print_usage_instructions()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
