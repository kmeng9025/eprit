@echo off
echo ========================================
echo EPRI ROI Analysis with UNet3D AI Model
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11+ and try again
    pause
    exit /b 1
)

REM Navigate to the process directory
cd /d "c:\Users\ftmen\Documents\EPRI\process"

echo Current directory: %CD%
echo.

REM Check if main script exists
if not exist "epri_roi_extractor.py" (
    echo ERROR: epri_roi_extractor.py not found in current directory
    echo Please make sure you're in the correct folder
    pause
    exit /b 1
)

REM Check if AI model exists
if not exist "unet3d_kidney.pth" (
    echo ERROR: AI model file unet3d_kidney.pth not found
    echo Please make sure the model file is in the process directory
    pause
    exit /b 1
)

echo Available data folders:
echo.
dir "..\DATA" /b /ad 2>nul
echo.

REM Get data folder from user
set /p DATA_FOLDER="Enter the data folder name (e.g., 241202): "

if "%DATA_FOLDER%"=="" (
    echo ERROR: No data folder specified
    pause
    exit /b 1
)

REM Check if data folder exists
if not exist "..\DATA\%DATA_FOLDER%" (
    echo ERROR: Data folder '%DATA_FOLDER%' not found in DATA directory
    echo Available folders:
    dir "..\DATA" /b /ad 2>nul
    pause
    exit /b 1
)

echo.
echo Starting AI analysis on data folder: %DATA_FOLDER%
echo ========================================
echo.

REM Run the analysis
python epri_roi_extractor.py --data-subdir "%DATA_FOLDER%"

if errorlevel 1 (
    echo.
    echo ERROR: Analysis failed. Check the log file for details.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Analysis completed successfully!
echo ========================================
echo.
echo Results saved to: output\roi_analysis_%DATA_FOLDER%_%date:~-4,4%%date:~-10,2%%date:~-7,2%_*
echo.
echo Files generated:
echo - roi_statistics_%DATA_FOLDER%.xlsx (Excel spreadsheet)
echo - roi_statistics_%DATA_FOLDER%.csv (CSV file)
echo - Enhanced ArbuzGUI project files
echo - Processing log file
echo.

pause
