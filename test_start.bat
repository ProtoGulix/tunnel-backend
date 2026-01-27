@echo off
echo Testing API on port 8001...
call .venv\Scripts\activate.bat
python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8001
