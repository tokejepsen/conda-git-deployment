REM Reset deployment by deleting repositories and conda directory, then reinstall.
cd %~dp0
cd ..
@RD /S /Q windows
startup.bat
