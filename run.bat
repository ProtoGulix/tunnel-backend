@echo off
REM Script de démarrage de l'API en développement (Windows)

echo.
echo Démarrage API GMAO...
echo.

REM Vérifier Python 3.12
python3.12 --version >nul 2>&1
if errorlevel 1 (
    echo  Python 3.12 n'est pas installé
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
echo 📥 Installation des dépendances...
pip install -r requirements.txt --quiet

REM Démarrer l'API
echo.
echo API en cours de démarrage sur http://localhost:8000
echo Docs Swagger: http://localhost:8000/docs
echo.

python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000 --reload

pause
