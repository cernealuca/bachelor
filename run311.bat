@echo off
REM Activate the Python 3.11 virtual environment and run the specified script
REM Usage: run311.bat script.py [args]

echo Activating Python 3.11 virtual environment...
call "%~dp0venv311\Scripts\activate.bat"

echo Running: python %*
python %*
