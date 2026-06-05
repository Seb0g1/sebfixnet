# Build InetFix Windows installer
$ErrorActionPreference = "Stop"
$appDir = Split-Path $PSScriptRoot -Parent
$inetfixRoot = Split-Path $appDir -Parent
$releasesDir = Join-Path $inetfixRoot "server\releases"

Set-Location $appDir

# Ensure sing-box binary
$singbox = Join-Path $appDir "src-tauri\binaries\sing-box.exe"
if (-not (Test-Path $singbox)) {
    Write-Host "sing-box not found, downloading..."
    & (Join-Path $PSScriptRoot "download-singbox.ps1")
}

# Install deps
if (-not (Test-Path "node_modules")) {
    npm install
}

# Build Tauri NSIS installer
npm run tauri:build

# Copy installer to server releases
New-Item -ItemType Directory -Force -Path $releasesDir | Out-Null
$built = Get-ChildItem -Path (Join-Path $appDir "src-tauri\target\release\bundle\nsis") -Filter "*.exe" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if ($built) {
    $target = Join-Path $releasesDir "InetFix-Setup-1.0.0.exe"
    Copy-Item $built.FullName $target -Force
    Write-Host "Installer copied to: $target"
} else {
    Write-Warning "NSIS installer not found. Check Rust/Tauri toolchain."
}
