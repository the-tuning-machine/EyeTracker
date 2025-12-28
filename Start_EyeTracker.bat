@echo off
echo ========================================
echo   Eye Tracker - Projet OraDys 3TT
echo   Universite Paris 8
echo ========================================
echo.

REM Activation de l'environnement virtuel
echo Activation de l'environnement virtuel...
call .venv\Scripts\activate.bat

if errorlevel 1 (
    echo ERREUR: Impossible d'activer l'environnement virtuel .venv
    echo Verifiez que le dossier .venv existe.
    pause
    exit /b 1
)

echo Environnement virtuel active avec succes.
echo.

REM Lancement du script Eye Tracker
echo Lancement de Eye Tracker...
echo.
python eye_tracker.py

REM En cas d'erreur, garder la fenêtre ouverte
if errorlevel 1 (
    echo.
    echo ERREUR: Le script s'est termine avec une erreur.
    pause
)
