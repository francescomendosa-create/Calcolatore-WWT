# Installa Process Managed sul PC (Desktop + Menu Start), senza scaricare .bat dal browser.
# Uso: tasto destro → Esegui con PowerShell
# Oppure da PowerShell:  powershell -ExecutionPolicy Bypass -File .\Setup-Process-Managed-PC.ps1

$ErrorActionPreference = "Stop"
$appName = "Process Managed"
$url = "https://francescomendosa-create.github.io/Calcolatore-WWT/index.html?standalone=1"

$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" }
if (-not (Test-Path $edge)) {
  Write-Host "Microsoft Edge non trovato. Installa Edge e riprova."
  exit 1
}

$installDir = Join-Path $env:LOCALAPPDATA "ProcessManaged"
New-Item -ItemType Directory -Force -Path $installDir | Out-Null

$vbsPath = Join-Path $installDir "ProcessManaged.vbs"
$vbs = @"
Set sh = CreateObject("WScript.Shell")
sh.Run """$edge"" --app=""$url""", 1, False
"@
Set-Content -Path $vbsPath -Value $vbs -Encoding ASCII

$iconPath = "$edge,0"
$pngCandidates = @(
  (Join-Path $PSScriptRoot "wwt-icon-192.png"),
  (Join-Path $installDir "wwt-icon-192.png")
)
foreach ($png in $pngCandidates) {
  if (-not (Test-Path $png)) { continue }
  try {
    Add-Type -AssemblyName System.Drawing
    $ico = Join-Path $installDir "ProcessManaged.ico"
    $bmp = [System.Drawing.Bitmap]::FromFile($png)
    $icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
    $fs = [System.IO.File]::Create($ico)
    $icon.Save($fs)
    $fs.Close()
    $bmp.Dispose()
    $iconPath = $ico
    break
  } catch { }
}

$ws = New-Object -ComObject WScript.Shell

function New-AppShortcut([string]$path) {
  $s = $ws.CreateShortcut($path)
  $s.TargetPath = "wscript.exe"
  $s.Arguments = "`"$vbsPath`""
  $s.WorkingDirectory = $installDir
  $s.WindowStyle = 1
  $s.Description = $appName
  $s.IconLocation = $iconPath
  $s.Save()
}

$deskLnk = Join-Path ([Environment]::GetFolderPath("Desktop")) "$appName.lnk"
$startLnk = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\$appName.lnk"
New-AppShortcut $deskLnk
New-AppShortcut $startLnk

$unreg = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\ProcessManaged"
New-Item -Path $unreg -Force | Out-Null
New-ItemProperty -Path $unreg -Name "DisplayName" -Value $appName -PropertyType String -Force | Out-Null
New-ItemProperty -Path $unreg -Name "Publisher" -Value "Process Managed" -PropertyType String -Force | Out-Null
New-ItemProperty -Path $unreg -Name "DisplayIcon" -Value $iconPath -PropertyType String -Force | Out-Null
New-ItemProperty -Path $unreg -Name "InstallLocation" -Value $installDir -PropertyType String -Force | Out-Null
New-ItemProperty -Path $unreg -Name "NoModify" -Value 1 -PropertyType DWord -Force | Out-Null
New-ItemProperty -Path $unreg -Name "NoRepair" -Value 1 -PropertyType DWord -Force | Out-Null
$uninstallCmd = "powershell -NoProfile -Command `"Remove-Item -LiteralPath '$deskLnk','$startLnk','$installDir' -Recurse -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath '$unreg' -Recurse -Force -ErrorAction SilentlyContinue`""
New-ItemProperty -Path $unreg -Name "UninstallString" -Value $uninstallCmd -PropertyType String -Force | Out-Null

Write-Host ""
Write-Host "Installato: $appName"
Write-Host " - Desktop: $deskLnk"
Write-Host " - Menu Start: $startLnk"
Write-Host ""
Write-Host "Cerca 'Process Managed' nel menu Start, oppure usa l'icona sul Desktop."
Start-Process -FilePath "wscript.exe" -ArgumentList "`"$vbsPath`""
