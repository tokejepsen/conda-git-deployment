:: Change the working directory to the conda-git-deployment directory.
:: "pushd" is being used so any UNC paths get mapped until a restart happens.
pushd %~dp0

:: Isolating the execution environment.
:: Powershell is needed for downloading miniconda.
set PATH=C:\WINDOWS\System32\WindowsPowerShell\v1.0

:: Create "installers" directory if it does not exist, and download miniconda into it.
IF EXIST %~dp0installers\miniconda.exe GOTO INSTALLEREXISTS
mkdir %~dp0installers
SET "FILENAME=%~dp0installers\miniconda.exe"
SET "URL=https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe"
powershell "Import-Module BitsTransfer; Start-BitsTransfer '%URL%' '%FILENAME%'"
:INSTALLEREXISTS

:: Install miniconda if the directory "%~dp0installers\miniconda" does not exist.
IF EXIST %UserProfile%\AppData\Local\Continuum\Miniconda2 GOTO INSTALLEXISTS
%~dp0installers\miniconda.exe /RegisterPython=0 /AddToPath=0 /S /D=%UserProfile%\AppData\Local\Continuum\Miniconda2
:INSTALLEXISTS

:: Set minimum PYTHONPATH for conda to function.
set PYTHONPATH=%UserProfile%\AppData\Local\Continuum\Miniconda2\Lib\site-packages;%UserProfile%\AppData\Local\Continuum\Miniconda2\Lib\site-packages\conda_env

:: Set minimum PATH for conda to function.
:: PATH has to have "C:\Windows\System32" for conda to function properly. Specifically for "cmd" and "chcp" executables.
set PATH=C:\Windows\System32;%UserProfile%\AppData\Local\Continuum\Miniconda2;%UserProfile%\AppData\Local\Continuum\Miniconda2\Library\bin;%UserProfile%\AppData\Local\Continuum\Miniconda2\Scripts

python %~dp0conda_git_deployment\update.py %*
