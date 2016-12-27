IF EXIST %~dp0windows\miniconda.exe GOTO INSTALLEREXISTS
mkdir %~dp0windows
SET "FILENAME=%~dp0windows\miniconda.exe"
SET "URL=https://repo.continuum.io/miniconda/Miniconda2-latest-Windows-x86_64.exe"
powershell "Import-Module BitsTransfer; Start-BitsTransfer '%URL%' '%FILENAME%'"
:INSTALLEREXISTS

IF EXIST %~dp0windows\miniconda GOTO INSTALLEXISTS
%~dp0windows\miniconda.exe /RegisterPython=0 /AddToPath=0 /S /D=%~dp0windows\miniconda
:INSTALLEXISTS

set np=%~dp0windows\miniconda\Lib\site-packages;%~dp0windows\miniconda\Lib\site-packages\conda_env
echo %pythonpath%|find /i "%np%">nul  || set pythonpath=%np%;%pythonpath%

set np=%~dp0windows\miniconda;%~dp0windows\miniconda\Library\bin;%~dp0windows\miniconda\Scripts
echo %path%|find /i "%np%">nul  || set path=%np%;%path%

python %~dp0conda_git_deployment\update.py %*
