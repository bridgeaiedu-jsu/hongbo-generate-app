@echo off
chcp 65001 >nul
cd /d "%~dp0"
python instagram_resize.py
echo.
echo 작업이 끝났습니다. 아무 키나 누르면 창이 닫힙니다.
pause >nul
