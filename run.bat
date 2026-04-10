@echo off
REM Script de démarrage de l'API en développement (Windows)

echo.
echo Demarrage API GMAO...
echo.

REM Tuer toute instance uvicorn déjà sur le port 8000
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Write-Host 'Port 8000 occupe (PID' $_.OwningProcess') - arret en cours...'; Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

REM Vérifier Python 3.12
python3.12 --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.12 non trouve. Installer depuis python.org
    exit /b 1
)

REM Créer venv si absent
if not exist ".venv\" (
    echo Création de l'environnement virtuel...
    python3.12 -m venv .venv
)

REM Activer venv
call .venv\Scripts\activate.bat

REM Installer dépendances
echo Installation des dependances...
pip install -r requirements.txt --quiet

REM Démarrer l'API
echo.
echo API en cours de demarrage sur http://localhost:8000
echo Docs Swagger: http://localhost:8000/docs
echo.

python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000 --reload

pause
