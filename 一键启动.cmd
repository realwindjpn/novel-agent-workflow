@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto run_venv
where py >nul 2>&1
if %ERRORLEVEL% EQU 0 goto run_py
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 goto run_python

echo [失败] 找不到 Python 3.11。请先安装 Python，或在项目中创建 .venv。
set "EXIT_CODE=1"
goto finish

:run_venv
".venv\Scripts\python.exe" "scripts\launch_web.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:run_py
py -3.11 "scripts\launch_web.py" %*
set "EXIT_CODE=%ERRORLEVEL%"
goto finish

:run_python
python "scripts\launch_web.py" %*
set "EXIT_CODE=%ERRORLEVEL%"

:finish
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
