:: Isolating the execution environment.
:: Powershell is needed for downloading miniconda.
set PATH=C:\WINDOWS\System32\WindowsPowerShell\v1.0

:: Create "windows" directory if it does not exist, and download miniconda into it.
IF EXIST %~dp0windows\miniconda.exe GOTO INSTALLEREXISTS
mkdir %~dp0windows
SET "FILENAME=%~dp0windows\miniconda.exe"
SET "URL=https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe"
powershell "Import-Module BitsTransfer; Start-BitsTransfer '%URL%' '%FILENAME%'"
:INSTALLEREXISTS

:: Install miniconda if the directory "windows\miniconda" does not exist.
IF EXIST %~dp0windows\miniconda GOTO INSTALLEXISTS
%~dp0windows\miniconda.exe /RegisterPython=0 /AddToPath=0 /S /D=%~dp0windows\miniconda
:INSTALLEXISTS

:: Set minimum PYTHONPATH for conda to function.
set PYTHONPATH=%~dp0windows\miniconda\Lib\site-packages;%~dp0windows\miniconda\Lib\site-packages\conda_env

:: Set minimum PATH for conda to function.
:: PATH has to have "C:\Windows\System32" for conda to function properly. Specifically for "cmd" and "chcp" executables.
set PATH=C:\Windows\System32;%~dp0windows\miniconda;%~dp0windows\miniconda\Library\bin;%~dp0windows\miniconda\Scripts

python %~dp0conda_git_deployment\update.py %*
