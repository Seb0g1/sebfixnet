# Package InetFix portable distribution and create installer exe
$ErrorActionPreference = "Stop"
$appDir = Split-Path $PSScriptRoot -Parent
$inetfixRoot = Split-Path $appDir -Parent
$releasesDir = Join-Path $inetfixRoot "server\releases"
$packageDir = Join-Path $env:TEMP "InetFix-package"
$portableDir = Join-Path $packageDir "InetFix"

Write-Host "Building frontend..."
Set-Location $appDir
if (-not (Test-Path "node_modules")) { npm install }
npm run build

$singboxSrc = Join-Path $appDir "src-tauri\binaries\sing-box.exe"
if (-not (Test-Path $singboxSrc)) {
    & (Join-Path $PSScriptRoot "download-singbox.ps1")
}

Write-Host "Packaging portable..."
if (Test-Path $packageDir) { Remove-Item $packageDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path (Join-Path $portableDir "bin") | Out-Null

Copy-Item (Join-Path $appDir "dist") (Join-Path $portableDir "dist") -Recurse
Copy-Item $singboxSrc (Join-Path $portableDir "bin\sing-box.exe")
Copy-Item (Join-Path $appDir "launcher\InetFix.ps1") (Join-Path $portableDir "InetFix.ps1")
Copy-Item (Join-Path $appDir "launcher\InetFix.bat") (Join-Path $portableDir "InetFix.bat")
Copy-Item (Join-Path $appDir "launcher\local-api.ps1") (Join-Path $portableDir "local-api.ps1")

# Create zip
$zipPath = Join-Path $releasesDir "InetFix-Portable-1.0.0.zip"
New-Item -ItemType Directory -Force -Path $releasesDir | Out-Null
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $portableDir -DestinationPath $zipPath -Force

# Create IExpress self-extractor
$sedPath = Join-Path $env:TEMP "inetfix.sed"
$setupExe = Join-Path $releasesDir "InetFix-Setup-1.0.0.exe"
$batLauncher = Join-Path $portableDir "InetFix.bat"

@"
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
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=Установить InetFix (By Seb0g1)?
DisplayLicense=
FinishMessage=InetFix установлен. Запустите InetFix.bat из папки установки.
TargetName=$setupExe
FriendlyName=InetFix Setup 1.0.0
AppLaunched=cmd /c InetFix.bat
PostInstallCmd=<None>
AdminQuietInstCmd=
UserQuietInstCmd=
FILE0="$batLauncher"
[SourceFiles]
SourceFiles0=$portableDir
[SourceFiles0]
%FILE0%=
"@ | Set-Content $sedPath -Encoding ASCII

$iexpress = Join-Path $env:SystemRoot "System32\iexpress.exe"
if (Test-Path $iexpress) {
    & $iexpress /N $sedPath /Q
    if (Test-Path $setupExe) {
        Write-Host "Installer created: $setupExe"
    } else {
        Write-Warning "IExpress did not produce exe. Zip available: $zipPath"
    }
} else {
    Write-Warning "IExpress not found. Portable zip: $zipPath"
}

Write-Host "Done."
