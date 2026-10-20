@echo off
cd /d "%~dp0"
python verify_all.py
if errorlevel 1 echo Check requirements.txt and the error above.
pause
