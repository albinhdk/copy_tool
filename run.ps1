Write-Host "Initializing environment..." -ForegroundColor Cyan
if (-Not (Test-Path "venv")) {
    python -m venv venv
}

# 激活虚拟环境
& ".\venv\Scripts\Activate.ps1"

Write-Host "Installing dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "Starting application..." -ForegroundColor Green
python main.py
