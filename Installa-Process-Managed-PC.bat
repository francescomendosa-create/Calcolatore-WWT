@echo off
REM Process Managed — apre l'app in finestra dedicata (Edge o Chrome)
set "URL=https://francescomendosa-create.github.io/Calcolatore-WWT/index.html?standalone=1"

where msedge >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" msedge --app="%URL%"
  exit /b 0
)

if exist "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe" --app="%URL%"
  exit /b 0
)
if exist "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" (
  start "" "%ProgramFiles%\Microsoft\Edge\Application\msedge.exe" --app="%URL%"
  exit /b 0
)

where chrome >nul 2>&1
if %ERRORLEVEL%==0 (
  start "" chrome --app="%URL%"
  exit /b 0
)

if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
  start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" --app="%URL%"
  exit /b 0
)
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" (
  start "" "%LocalAppData%\Google\Chrome\Application\chrome.exe" --app="%URL%"
  exit /b 0
)

echo Edge/Chrome non trovati. Apro nel browser predefinito...
start "" "%URL%"
pause
