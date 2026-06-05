# Package FixInet.ez portable distribution
$ErrorActionPreference = "Stop"
$appDir = Split-Path $PSScriptRoot -Parent
$inetfixRoot = Split-Path $appDir -Parent
$releasesDir = Join-Path $inetfixRoot "server\releases"
$packageDir = Join-Path $env:TEMP "FixInet-package"
$portableDir = Join-Path $packageDir "FixInet.ez"
$version = "1.0.0"

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
Copy-Item (Join-Path $appDir "public\logo.png") (Join-Path $portableDir "dist\logo.png") -ErrorAction SilentlyContinue
Copy-Item $singboxSrc (Join-Path $portableDir "bin\sing-box.exe")
Copy-Item (Join-Path $appDir "launcher\FixInet.ez.ps1") (Join-Path $portableDir "FixInet.ez.ps1")
Copy-Item (Join-Path $appDir "launcher\FixInet.ez.bat") (Join-Path $portableDir "FixInet.ez.bat")
Copy-Item (Join-Path $appDir "launcher\local-api.ps1") (Join-Path $portableDir "local-api.ps1")

$zipPath = Join-Path $releasesDir "FixInet.ez-Portable-$version.zip"
New-Item -ItemType Directory -Force -Path $releasesDir | Out-Null
if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
Compress-Archive -Path $portableDir -DestinationPath $zipPath -Force
Write-Host "Portable zip: $zipPath"
