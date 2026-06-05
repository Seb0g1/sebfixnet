$ErrorActionPreference = "Stop"
$scripts = $PSScriptRoot
$releases = Join-Path (Split-Path (Split-Path $scripts -Parent) -Parent) "server\releases"
$version = "1.0.0"

& (Join-Path $scripts "package-portable.ps1")

$zip = Join-Path $releases "FixInet.ez-Portable-$version.zip"
$buildDir = Join-Path $env:TEMP "fixinet-pyinstaller"
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
Copy-Item $zip $buildDir
Copy-Item (Join-Path $scripts "installer.py") $buildDir

Set-Location $buildDir
python -m pip install pyinstaller --quiet 2>$null
python -m PyInstaller --onefile --windowed --name "FixInet.ez-Setup-$version" `
    --add-data "FixInet.ez-Portable-$version.zip;." installer.py

$built = Join-Path $buildDir "dist\FixInet.ez-Setup-$version.exe"
if (Test-Path $built) {
    Copy-Item $built (Join-Path $releases "FixInet.ez-Setup-$version.exe") -Force
    Write-Host "Created: $(Join-Path $releases "FixInet.ez-Setup-$version.exe")"
} else {
    Write-Host "PyInstaller build failed."
    exit 1
}
