@echo off
:: Display initial message
echo Installing, please wait...

:: Create virtual environment
python -m venv FaceRec

:: Activate the virtual environment
call FaceRec\Scripts\activate

:: Install required packages
pip install -r requirements.txt

:: Clear the screen
cls
color a
:: Display completion message
echo Installation complete.

:: Wait for user input to close
pause
