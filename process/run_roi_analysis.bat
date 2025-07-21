@echo off
REM EPRI ROI Analysis Automation Script
REM This batch file automates the ROI analysis workflow

echo ========================================
echo EPRI ROI Analysis Automation
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and try again.
    pause
    exit /b 1
)

REM Navigate to the process directory
cd /d "%~dp0"

echo Current directory: %CD%
echo.

REM Check if required files exist
if not exist "epri_roi_extractor.py" (
    echo ERROR: epri_roi_extractor.py not found
    echo Please ensure you are running this from the correct directory.
    pause
    exit /b 1
)

if not exist "unet3d_model.py" (
    echo ERROR: unet3d_model.py not found
    echo Please ensure the UNet model file is present.
    pause
    exit /b 1
)

REM Install requirements if needed
echo Checking Python dependencies...
pip show numpy >nul 2>&1
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed.
)

echo.

REM Get data subdirectory from user
set /p DATA_SUBDIR="Enter data subdirectory (default: 241202): "
if "%DATA_SUBDIR%"=="" set DATA_SUBDIR=241202

echo.
echo Processing data from subdirectory: %DATA_SUBDIR%
echo.

REM Run the ROI extractor
echo Starting ROI analysis...
python epri_roi_extractor.py --data-subdir %DATA_SUBDIR%

if errorlevel 1 (
    echo.
    echo ========================================
    echo ROI analysis failed!
    echo Check the log file for details.
    echo ========================================
    pause
    exit /b 1
) else (
    echo.
    echo ========================================
    echo ROI analysis completed successfully!
    echo Check the output directory for results.
    echo ========================================
)

echo.
echo Opening output directory...
for /f "tokens=*" %%i in ('dir /b /ad output\roi_analysis_%DATA_SUBDIR%_* 2^>nul') do (
    explorer "output\%%i"
    goto :opened
)

echo Output directory not found. Please check manually.

:opened
echo.
echo Press any key to exit...
pause >nul
