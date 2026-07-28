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
pause
exit /b 1

:run_venv
set "BOOKWORKFLOW_PAUSE_ON_ERROR=1"
start "novel-workflow launcher" /D "%CD%" ".venv\Scripts\python.exe" "scripts\launch_web.py" %*
if %ERRORLEVEL% NEQ 0 goto launch_failed
exit /b 0

:run_py
set "BOOKWORKFLOW_PAUSE_ON_ERROR=1"
start "novel-workflow launcher" /D "%CD%" py -3.11 "scripts\launch_web.py" %*
if %ERRORLEVEL% NEQ 0 goto launch_failed
exit /b 0

:run_python
set "BOOKWORKFLOW_PAUSE_ON_ERROR=1"
start "novel-workflow launcher" /D "%CD%" python "scripts\launch_web.py" %*
if %ERRORLEVEL% NEQ 0 goto launch_failed
exit /b 0

:launch_failed
echo [失败] 无法创建启动器窗口。
pause
exit /b 1
