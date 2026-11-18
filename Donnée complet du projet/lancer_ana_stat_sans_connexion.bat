@echo off
title ANA-STAT.abt - test sans connexion
cd /d "%~dp0"

if not exist "..\.venv\Scripts\python.exe" (
    echo.
    echo ERREUR : l'environnement Python est introuvable.
    echo Ouvre un terminal dans ce dossier et lance :
    echo     uv pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

echo.
echo ANA-STAT.abt - MODE TEST : aucune connexion demandee.
echo.
set PYTHONUTF8=1
"..\.venv\Scripts\python.exe" ABT.py

if errorlevel 1 (
    echo.
    echo Le logiciel s'est ferme avec une erreur. Copie le message ci-dessus.
    pause
)
