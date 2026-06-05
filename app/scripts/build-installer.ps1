# Build FixInet.ez native Windows installer (Tauri NSIS)
$ErrorActionPreference = "Stop"
$appDir = Split-Path $PSScriptRoot -Parent
$inetfixRoot = Split-Path $appDir -Parent
$releasesDir = Join-Path $inetfixRoot "server\releases"
$version = "1.0.0"

Set-Location $appDir

$singbox = Join-Path $appDir "src-tauri\binaries\sing-box.exe"
if (-not (Test-Path $singbox)) {
    Write-Host "sing-box not found, downloading..."
    & (Join-Path $PSScriptRoot "download-singbox.ps1")
}

if (-not (Test-Path "src-tauri\icons\icon.ico")) {
    if (Test-Path "public\logo.png") {
        npx @tauri-apps/cli icon public/logo.png -o src-tauri/icons
    }
}

if (-not (Test-Path "node_modules")) {
    npm install
}

Write-Host "Building FixInet.ez (Tauri NSIS)..."
npm run tauri:build

New-Item -ItemType Directory -Force -Path $releasesDir | Out-Null
$built = Get-ChildItem -Path (Join-Path $appDir "src-tauri\target\release\bundle\nsis") -Filter "*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($built) {
    $target = Join-Path $releasesDir "FixInet.ez-Setup-$version.exe"
    Copy-Item $built.FullName $target -Force
    Write-Host "Native installer: $target"
} else {
    Write-Error "NSIS installer not found. Install Rust: https://rustup.rs"
}
