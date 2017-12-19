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

:: Get installation directory.
set directory=%UserProfile%\miniconda

set argc=0
FOR %%A IN (%*) DO (
    set /A argc+=1
    IF "%%A"=="--repository-install" SET directory=%~dp0\installation\win
)

:: Install miniconda if the directory %directory% does not exist.
IF EXIST %directory% GOTO INSTALLATIONEXISTS
%~dp0installers\miniconda.exe /RegisterPython=0 /AddToPath=0 /S /D=%directory%
:INSTALLATIONEXISTS

:: Set minimum PATH for conda to function.
:: PATH has to have "C:\Windows\System32" for conda to function properly. Specifically for "cmd" and "chcp" executables.
set PATH=C:\Windows\System32;%directory%\Scripts

call activate root
python %~dp0conda_git_deployment\update.py %*
