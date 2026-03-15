@echo off
title Halo CME Detection
color 0A

echo ================================================
echo      HALO CME DETECTION - CMD + VENV
echo ================================================
echo.

:: Activate venv
echo [1/4] Activating virtual environment...
call cme_env\Scripts\activate
if errorlevel 1 (
    echo [ERROR] Failed to activate venv
    pause
    exit /b 1
)
echo [OK] Virtual environment activated
echo.

:: Check data file
echo [2/4] Checking data files...
if exist data\final_dataset.csv (
    echo [OK] Found data\final_dataset.csv
    dir data\final_dataset.csv | find "final_dataset"
) else (
    echo [ERROR] data\final_dataset.csv not found!
    echo Files in data folder:
    dir data
    pause
    exit /b 1
)
echo.

:: Fix paths
echo [3/4] Fixing paths in detection script...
powershell -Command "(Get-Content scripts\halo_cme_detection.py) -replace '\.\./data/', 'data/' | Set-Content scripts\halo_cme_detection.py"
if errorlevel 1 (
    echo [WARNING] Path fix may have failed
) else (
    echo [OK] Paths fixed
)
echo.

:: Run detection
echo [4/4] Running CME Detection...
echo ================================================
python scripts\halo_cme_detection.py
set DETECT_ERROR=%errorlevel%
echo ================================================
echo.

:: Check result
if %DETECT_ERROR% equ 0 (
    echo [OK] Detection completed successfully!
    
    :: Show output if exists
    if exist data\detected_halo_cmes.csv (
        echo.
        echo Output file created: data\detected_halo_cmes.csv
        echo First 3 lines:
        echo --------------------------------
        powershell -Command "Get-Content data\detected_halo_cmes.csv | Select-Object -First 3"
        echo --------------------------------
    )
) else (
    echo [ERROR] Detection failed with code %DETECT_ERROR%
    echo.
    echo Check pipeline_execution.log for details
)

echo.
echo ================================================
pause