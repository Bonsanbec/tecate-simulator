@echo off
rem Change directory to the root of the project
cd /d "%~dp0"

rem Activate python virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

echo Running Minecraft Importer Pipeline...
echo.

set PYTHONPATH=.
python -m src.minecraft_pipeline.importer

if %ERRORLEVEL% neq 0 (
    echo.
    echo Importer pipeline failed with error code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo Pipeline execution finished successfully!
pause
