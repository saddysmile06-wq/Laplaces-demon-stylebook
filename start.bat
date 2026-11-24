@echo off
rem Установка и запуск одним кликом (Windows): двойной клик по этому файлу.
chcp 65001 >nul
cd /d "%~dp0"
where python >nul 2>nul && (python tools\setup.py --open) || (py -3 tools\setup.py --open)
if errorlevel 1 (
  echo.
  echo Не получилось. Нужен Python 3.9+ ^(https://www.python.org/downloads/^) и Git LFS. Подробности выше.
)
pause
