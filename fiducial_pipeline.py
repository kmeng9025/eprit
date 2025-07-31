"""
Fiducial Detection Pipeline for 3D EPR/MRI Images

This script provides a complete pipeline for:
1. Extracting fiducial data from .mat files
2. Training a 3D U-Net model for fiducial detection  
3. Making predictions on new data

Usage:
    python fiducial_pipeline.py --mode [prep|train|predict|all]
    
Examples:
    # Run complete pipeline
    python fiducial_pipeline.py --mode all
    
    # Just preprocess data
    python fiducial_pipeline.py --mode prep
    
    # Train model (after preprocessing)
    python fiducial_pipeline.py --mode train --epochs 100
    
    # Predict on new data
    python fiducial_pipeline.py --mode predict --input_file ./DATA/MRIAlign/newfile.mat
"""

import argparse
import os
import sys
import subprocess
import time

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\\n🚀 {description}")
    print(f"Command: {command}")
    
    start_time = time.time()
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    end_time = time.time()
    
    if result.returncode == 0:
        print(f"✅ {description} completed successfully in {end_time-start_time:.1f}s")
        if result.stdout:
            print("Output:")
            print(result.stdout)
    else:
        print(f"❌ {description} failed!")
        print("Error output:")
        print(result.stderr)
        return False
    
    return True

def check_prerequisites():
    """Check if required packages are installed"""
    print("🔍 Checking prerequisites...")
    
    required_packages = ['torch', 'numpy', 'scipy', 'matplotlib', 'scikit-learn']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"  ✅ {package}")
        except ImportError:
            print(f"  ❌ {package}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\\n⚠️ Missing packages: {missing_packages}")
        print("Please install them with:")
        print("pip install torch torchvision torchaudio numpy scipy matplotlib scikit-learn")
        return False
    
    return True

def check_data_availability():
    """Check if source data is available"""
    data_dir = './DATA/MRIAlign'
    if not os.path.exists(data_dir):
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    mat_files = [f for f in os.listdir(data_dir) if f.endswith('.mat')]
    if not mat_files:
        print(f"❌ No .mat files found in {data_dir}")
        return False
    
    print(f"✅ Found {len(mat_files)} .mat files in {data_dir}")
    return True

def run_preprocessing():
    """Run the data preprocessing step"""
    if not os.path.exists('./prep_fiducial_data.py'):
        print("❌ prep_fiducial_data.py not found")
        return False
    
    command = "python prep_fiducial_data.py"
    return run_command(command, "Data preprocessing")

def run_training(epochs=150, resume=True):
    """Run the model training step"""
    if not os.path.exists('./train_fiducial_model.py'):
        print("❌ train_fiducial_model.py not found")
        return False
    
    # Check if preprocessed data exists
    if not os.path.exists('./preprocessed_fiducials/X_fiducials.npy'):
        print("❌ Preprocessed data not found. Run preprocessing first.")
        return False
    
    # Modify the training script to accept command line arguments
    command = f"python train_fiducial_model.py"
    return run_command(command, f"Model training ({epochs} epochs)")

def run_prediction(input_file=None, input_dir=None, threshold=0.5):
    """Run prediction on new data"""
    if not os.path.exists('./predict_fiducials.py'):
        print("❌ predict_fiducials.py not found")
        return False
    
    # Check if trained model exists
    model_paths = ['./fiducial_model_best.pth', './fiducial_model.pth']
    model_path = None
    for path in model_paths:
        if os.path.exists(path):
            model_path = path
            break
    
    if not model_path:
        print("❌ No trained model found. Run training first.")
        return False
    
    command = f"python predict_fiducials.py --model_path {model_path} --threshold {threshold}"
    
    if input_file:
        command += f" --input_file {input_file}"
    elif input_dir:
        command += f" --input_dir {input_dir}"
    
    return run_command(command, "Fiducial prediction")

def main():
    parser = argparse.ArgumentParser(description='Fiducial Detection Pipeline')
    parser.add_argument('--mode', type=str, choices=['prep', 'train', 'predict', 'all'], 
                        required=True, help='Pipeline mode to run')
    parser.add_argument('--epochs', type=int, default=150, 
                        help='Number of training epochs')
    parser.add_argument('--input_file', type=str, 
                        help='Specific .mat file for prediction')
    parser.add_argument('--input_dir', type=str, default='./DATA/MRIAlign',
                        help='Directory containing .mat files for prediction')
    parser.add_argument('--threshold', type=float, default=0.5,
                        help='Prediction threshold')
    parser.add_argument('--skip_checks', action='store_true',
                        help='Skip prerequisite checks')
    
    args = parser.parse_args()
    
    print("🔬 Fiducial Detection Pipeline")
    print("=" * 50)
    
    # Check prerequisites unless skipped
    if not args.skip_checks:
        if not check_prerequisites():
            print("\\n❌ Prerequisites not met. Exiting.")
            sys.exit(1)
        
        if args.mode in ['prep', 'all']:
            if not check_data_availability():
                print("\\n❌ Data not available. Exiting.")
                sys.exit(1)
    
    success = True
    
    # Run the requested pipeline steps
    if args.mode in ['prep', 'all']:
        print("\\n" + "="*20 + " PREPROCESSING " + "="*20)
        success = success and run_preprocessing()
    
    if args.mode in ['train', 'all'] and success:
        print("\\n" + "="*25 + " TRAINING " + "="*25)
        success = success and run_training(args.epochs)
    
    if args.mode in ['predict', 'all'] and success:
        print("\\n" + "="*24 + " PREDICTION " + "="*24)
        success = success and run_prediction(args.input_file, args.input_dir, args.threshold)
    
    # Final summary
    print("\\n" + "="*20 + " PIPELINE SUMMARY " + "="*20)
    if success:
        print("✅ Pipeline completed successfully!")
        
        if args.mode in ['all', 'train']:
            print("\\n📊 Trained Model Files:")
            if os.path.exists('./fiducial_model_best.pth'):
                print("  • fiducial_model_best.pth (best validation performance)")
            if os.path.exists('./fiducial_model.pth'):
                print("  • fiducial_model.pth (final model)")
        
        if args.mode in ['all', 'predict']:
            print("\\n📁 Prediction Results:")
            if os.path.exists('./fiducial_predictions'):
                print("  • ./fiducial_predictions/ (prediction outputs)")
        
        print("\\n🎯 Next Steps:")
        if args.mode == 'prep':
            print("  • Run training: python fiducial_pipeline.py --mode train")
        elif args.mode == 'train':
            print("  • Run prediction: python fiducial_pipeline.py --mode predict")
        elif args.mode in ['all', 'predict']:
            print("  • Check prediction results in ./fiducial_predictions/")
            print("  • Use the trained model for new data with predict_fiducials.py")
    else:
        print("❌ Pipeline failed. Check error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
