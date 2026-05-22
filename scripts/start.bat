@echo off
cd /d C:\Users\JUAN\SkyCast
echo Starting SkyCast server...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000