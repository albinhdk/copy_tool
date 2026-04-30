@echo off
chcp 65001 >nul
echo Initializing environment...
if not exist "venv" (
    python -m venv venv
)
call venv\Scripts\activate.bat
echo Installing dependencies...
pip install -r requirements.txt
echo Starting application...
python main.py
pause
