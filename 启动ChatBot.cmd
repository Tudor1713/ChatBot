@echo off
cd /d "%~dp0"
if exist "..\ChatBot\ChatBot.exe" (
  start "" "..\ChatBot\ChatBot.exe"
) else if exist "outputs\build-2.6.0\ChatBot\ChatBot.exe" (
  start "" "outputs\build-2.6.0\ChatBot\ChatBot.exe"
) else if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" "src\main.py"
) else (
  echo ChatBot is not installed. Please build it with scripts\build.ps1.
  pause
)
