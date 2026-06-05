# Local API for sing-box control (portable mode)
param(
    [int]$ApiPort = 17421,
    [string]$SingBoxPath = "",
    [string]$ConfigDir = ""
)

$SingBoxProc = $null

function Send-Json($ctx, $obj, $code = 200) {
    $json = $obj | ConvertTo-Json -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)
    $ctx.Response.StatusCode = $code
    $ctx.Response.ContentType = "application/json"
    $ctx.Response.Headers.Add("Access-Control-Allow-Origin", "*")
    $ctx.Response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    $ctx.Response.Headers.Add("Access-Control-Allow-Headers", "Content-Type")
    $ctx.Response.ContentLength64 = $bytes.Length
    $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $ctx.Response.Close()
}

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://127.0.0.1:$ApiPort/")
$listener.Start()

while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $path = $ctx.Request.Url.LocalPath
    $method = $ctx.Request.HttpMethod

    if ($method -eq "OPTIONS") {
        Send-Json $ctx @{ ok = $true }
        continue
    }

    if ($path -eq "/status" -and $method -eq "GET") {
        $running = $SingBoxProc -and -not $SingBoxProc.HasExited
        Send-Json $ctx @{ connected = $running }
        continue
    }

    if ($path -eq "/disconnect" -and $method -eq "POST") {
        if ($SingBoxProc -and -not $SingBoxProc.HasExited) {
            $SingBoxProc.Kill()
            $SingBoxProc.WaitForExit()
        }
        $SingBoxProc = $null
        Send-Json $ctx @{ message = "Disconnected" }
        continue
    }

    if ($path -eq "/connect" -and $method -eq "POST") {
        $reader = [IO.StreamReader]::new($ctx.Request.InputStream)
        $body = $reader.ReadToEnd()
        $reader.Close()

        if ($SingBoxProc -and -not $SingBoxProc.HasExited) {
            $SingBoxProc.Kill()
            $SingBoxProc.WaitForExit()
        }

        $cfgPath = Join-Path $ConfigDir "singbox.json"
        [IO.File]::WriteAllText($cfgPath, $body)

        $SingBoxProc = Start-Process -FilePath $SingBoxPath `
            -ArgumentList "run", "-c", $cfgPath `
            -PassThru -WindowStyle Hidden

        Send-Json $ctx @{ message = "Connected" }
        continue
    }

    $ctx.Response.StatusCode = 404
    $ctx.Response.Close()
}
