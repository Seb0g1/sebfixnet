# Creates InetFix-Setup-1.0.0.exe using IExpress
$ErrorActionPreference = "Stop"
$inetfixRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$releasesDir = Join-Path $inetfixRoot "server\releases"
$zipPath = Join-Path $releasesDir "InetFix-Portable-1.0.0.zip"
$setupExe = Join-Path $releasesDir "InetFix-Setup-1.0.0.exe"
$workDir = Join-Path $env:TEMP "inetfix-setup-build"

if (-not (Test-Path $zipPath)) {
    & (Join-Path $PSScriptRoot "package-portable.ps1")
}

if (Test-Path $workDir) { Remove-Item $workDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $workDir | Out-Null
Expand-Archive -Path $zipPath -DestinationPath $workDir -Force

$installPs1 = @'
$installDir = Join-Path $env:LOCALAPPDATA "InetFix"
$src = Split-Path $MyInvocation.MyCommand.Path -Parent
if (Test-Path $installDir) { Remove-Item $installDir -Recurse -Force }
Copy-Item $src $installDir -Recurse
$shortcut = (New-Object -ComObject WScript.Shell).CreateShortcut("$env:USERPROFILE\Desktop\InetFix.lnk")
$shortcut.TargetPath = Join-Path $installDir "InetFix\InetFix.bat"
$shortcut.WorkingDirectory = Join-Path $installDir "InetFix"
$shortcut.Save()
[System.Windows.Forms.MessageBox]::Show("InetFix установлен!`nЗапустите с рабочего стола.", "InetFix (By Seb0g1)")
'@

$installerDir = Join-Path $workDir "InetFix"
$installScript = Join-Path $installerDir "install.ps1"
$installBat = Join-Path $installerDir "install.bat"
Set-Content $installScript $installPs1 -Encoding UTF8
Set-Content $installBat '@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1"
pause' -Encoding ASCII

$sed = @"
[Version]
Class=IEXPRESS
SEDVersion=3
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=
DisplayLicense=
FinishMessage=InetFix установлен!
TargetName=$setupExe
FriendlyName=InetFix Setup
AppLaunched=install.bat
PostInstallCmd=
AdminQuietInstCmd=
UserQuietInstCmd=
FILE0=install.bat
[SourceFiles]
SourceFiles0=$installerDir
[SourceFiles0]
%FILE0%=
"@

$sedPath = Join-Path $env:TEMP "inetfix2.sed"
Set-Content $sedPath $sed -Encoding ASCII

& "$env:SystemRoot\System32\iexpress.exe" /N $sedPath /Q

if (Test-Path $setupExe) {
    Write-Host "Created: $setupExe"
} else {
    # Fallback: copy install.bat as setup entry point
    Copy-Item $installBat (Join-Path $releasesDir "InetFix-Setup-1.0.0.bat")
    Write-Host "IExpress failed. Use InetFix-Setup-1.0.0.bat or zip: $zipPath"
}
