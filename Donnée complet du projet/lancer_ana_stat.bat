@echo off
title ANA-STAT.abt - mode normal (avec connexion)
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
echo ANA-STAT.abt - MODE NORMAL : une connexion est demandee.
echo Pour tester sans connexion, utilise lancer_ana_stat_sans_connexion.bat.
echo.
set PYTHONUTF8=1
"..\.venv\Scripts\python.exe" main.py

if errorlevel 1 (
    echo.
    echo Le logiciel s'est ferme avec une erreur. Copie le message ci-dessus.
    pause
)
