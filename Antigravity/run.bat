@echo off
title Face Filter Camera App
echo ========================================================
echo        Face Filter Camera App (Dog & Cat Filters)
echo ========================================================
echo.
echo Checking dependencies...
python -c "import cv2, numpy" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing opencv-python and numpy...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo.
        echo [!] Installation failed. You can also open the Web version directly:
        echo     Double-click 'web\index.html' to open in your browser!
        pause
        exit /b
    )
)

echo Starting Python Face Filter App...
python app.py
pause
