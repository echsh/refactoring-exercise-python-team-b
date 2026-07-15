@echo off
setlocal
set ROOT=%~dp0
set PYTHONPATH=%ROOT%src;%PYTHONPATH%
pushd "%ROOT%"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m unittest discover -s tests -p "test_*.py" -v
) else (
  python -m unittest discover -s tests -p "test_*.py" -v
)
set EXIT_CODE=%errorlevel%
popd
endlocal & exit /b %EXIT_CODE%
