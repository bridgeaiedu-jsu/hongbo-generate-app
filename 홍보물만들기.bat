@echo off
cd /d "%~dp0"
for %%f in (*.py) do python "%%f"
echo.
pause
