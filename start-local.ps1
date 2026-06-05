# Start InetFix stack locally for development
$Root = $PSScriptRoot
$envFile = Join-Path $Root ".env"

if (-not (Test-Path $envFile)) {
    Copy-Item (Join-Path $Root ".env.example") $envFile
    Write-Host "Created .env from example — fill BOT_TOKEN and API_SECRET"
}

Write-Host "Starting backend on :8080..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\backend'; .\.venv\Scripts\uvicorn main:app --reload --port 8080"

Start-Sleep 2

Write-Host "Starting Telegram bot..."
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$Root\bot'; .\.venv\Scripts\python main.py"

Write-Host "Done. API: http://localhost:8080/docs"
