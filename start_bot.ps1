# Скрипт для запуска Telegram бота
# Использование: .\start_bot.ps1

Write-Host "Запуск Telegram бота..." -ForegroundColor Green
Set-Location "telegram_bot"
python bot.py

