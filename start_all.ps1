# Скрипт для запуска обоих сервисов параллельно
# Использование: .\start_all.ps1

Write-Host "Запуск MCP HTTP сервера и Telegram бота..." -ForegroundColor Cyan

# Запускаем HTTP сервер в новом окне
Write-Host "Запуск HTTP сервера в новом окне..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\mcp_server'; python http_server.py"

# Ждем немного, чтобы сервер успел запуститься
Start-Sleep -Seconds 3

# Запускаем бота в новом окне
Write-Host "Запуск Telegram бота в новом окне..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\telegram_bot'; python bot.py"

Write-Host "`nОба сервиса запущены в отдельных окнах!" -ForegroundColor Green
Write-Host "HTTP сервер: http://localhost:8000" -ForegroundColor Cyan
Write-Host "Telegram бот: запущен и ожидает сообщения" -ForegroundColor Cyan
Write-Host "`nДля остановки закройте соответствующие окна PowerShell" -ForegroundColor Yellow

