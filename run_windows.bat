@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo     EcoLingua-TN V24 Reliable Fast
echo ==========================================

rem Windows can fail on very long paths. Warn early.
set "PROJECT_PATH=%CD%"
if not "%PROJECT_PATH:~120,1%"=="" (
    echo.
    echo ERREUR : le chemin du projet est trop long.
    echo Deplacez le dossier vers C:\EcoLingua puis relancez ce fichier.
    echo Chemin actuel : %PROJECT_PATH%
    echo.
    pause
    exit /b 1
)

where py >nul 2>nul
if errorlevel 1 (
    echo Python Launcher ^(py^) est introuvable.
    echo Installez Python 3.11 ou 3.12 depuis python.org.
    pause
    exit /b 1
)

if not exist venv\Scripts\python.exe (
    echo Creation de l'environnement virtuel...
    py -3 -m venv venv
    if errorlevel 1 goto :error
)

echo Mise a jour de pip...
venv\Scripts\python.exe -m pip install --upgrade pip
if errorlevel 1 goto :error

echo Installation des dependances...
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto :error

echo Lancement de EcoLingua-TN V24...
venv\Scripts\python.exe -m streamlit run app\dashboard.py
exit /b 0

:error
echo.
echo L'installation a echoue. Copiez le projet dans C:\EcoLingua,
echo supprimez le dossier venv puis relancez run_windows.bat.
pause
exit /b 1
