$ErrorActionPreference = "Stop"
$scripts = $PSScriptRoot
$releases = Join-Path (Split-Path (Split-Path $scripts -Parent) -Parent) "server\releases"

& (Join-Path $scripts "package-portable.ps1")

$zip = Join-Path $releases "InetFix-Portable-1.0.0.zip"
$buildDir = Join-Path $env:TEMP "inetfix-pyinstaller"
if (Test-Path $buildDir) { Remove-Item $buildDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
Copy-Item $zip $buildDir
Copy-Item (Join-Path $scripts "installer.py") $buildDir

Set-Location $buildDir
python -m pip install pyinstaller --quiet 2>$null
python -m PyInstaller --onefile --windowed --name InetFix-Setup-1.0.0 `
    --add-data "InetFix-Portable-1.0.0.zip;." installer.py

$built = Join-Path $buildDir "dist\InetFix-Setup-1.0.0.exe"
if (Test-Path $built) {
    Copy-Item $built (Join-Path $releases "InetFix-Setup-1.0.0.exe") -Force
    Write-Host "Created: $(Join-Path $releases 'InetFix-Setup-1.0.0.exe')"
} else {
    Write-Host "PyInstaller build failed. Use InetFix-Setup-1.0.0.bat or zip."
}
