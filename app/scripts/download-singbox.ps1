# Downloads sing-box Windows amd64 binary for InetFix
$ErrorActionPreference = "Stop"

$version = "1.11.7"
$url = "https://github.com/SagerNet/sing-box/releases/download/v$version/sing-box-$version-windows-amd64.zip"
$dest = Join-Path $PSScriptRoot "..\src-tauri\binaries"
$zip = Join-Path $env:TEMP "sing-box.zip"

Write-Host "Downloading sing-box v$version..."
Invoke-WebRequest -Uri $url -OutFile $zip

Expand-Archive -Path $zip -DestinationPath $env:TEMP -Force
$extracted = Get-ChildItem -Path $env:TEMP -Recurse -Filter "sing-box.exe" | Select-Object -First 1

if (-not $extracted) {
    throw "sing-box.exe not found in archive"
}

New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item $extracted.FullName (Join-Path $dest "sing-box-x86_64-pc-windows-msvc.exe") -Force
Copy-Item $extracted.FullName (Join-Path $dest "sing-box.exe") -Force

Write-Host "Done: $(Join-Path $dest 'sing-box.exe')"
