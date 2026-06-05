# FixInet.ez Portable Launcher (By Seb0g1)
$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms

$Root = Split-Path $PSScriptRoot -Parent
$Dist = Join-Path $Root "dist"
$SingBox = Join-Path $Root "bin\sing-box.exe"
$ConfigDir = Join-Path $env:APPDATA "FixInet.ez"
$UiPort = 17420
$ApiPort = 17421

if (-not (Test-Path $Dist)) {
    [System.Windows.Forms.MessageBox]::Show("dist folder not found. Reinstall FixInet.ez.", "FixInet.ez")
    exit 1
}

New-Item -ItemType Directory -Force -Path $ConfigDir | Out-Null

$apiJob = Start-Job -ScriptBlock {
    param($script, $port, $singbox, $cfg)
    & $script -ApiPort $port -SingBoxPath $singbox -ConfigDir $cfg
} -ArgumentList (Join-Path $PSScriptRoot "local-api.ps1"), $ApiPort, $SingBox, $ConfigDir

$uiListener = [System.Net.HttpListener]::new()
$uiListener.Prefixes.Add("http://127.0.0.1:$UiPort/")
$uiListener.Start()

$uiJob = Start-Job -ScriptBlock {
    param($listener, $dist)
    while ($listener.IsListening) {
        $ctx = $listener.GetContext()
        $path = $ctx.Request.Url.LocalPath
        if ($path -eq "/") { $path = "/index.html" }
        $file = Join-Path $dist $path.TrimStart("/").Replace("/", "\")
        if (Test-Path $file) {
            $bytes = [IO.File]::ReadAllBytes($file)
            $ctx.Response.ContentLength64 = $bytes.Length
            $ext = [IO.Path]::GetExtension($file).ToLower()
            $mime = switch ($ext) {
                ".html" { "text/html" }
                ".js"   { "application/javascript" }
                ".css"  { "text/css" }
                ".png"  { "image/png" }
                default { "application/octet-stream" }
            }
            $ctx.Response.ContentType = $mime
            $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
        } else {
            $ctx.Response.StatusCode = 404
        }
        $ctx.Response.Close()
    }
} -ArgumentList $uiListener, $Dist

Start-Sleep -Milliseconds 800
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe" }
if (Test-Path $edge) {
    Start-Process $edge -ArgumentList "--app=http://127.0.0.1:$UiPort/","--window-size=480,720"
} else {
    Start-Process "http://127.0.0.1:$UiPort/"
}

Write-Host "FixInet.ez UI:  http://127.0.0.1:$UiPort/"
Write-Host "FixInet.ez API: http://127.0.0.1:$ApiPort/"
try {
    while ($true) { Start-Sleep 1 }
} finally {
    $uiListener.Stop()
    Remove-Job $uiJob, $apiJob -Force -ErrorAction SilentlyContinue
}
