"""
Конфигурация бота
Загружает переменные окружения из .env файла
"""

import os
from dotenv import load_dotenv

# Загружаем переменные из .env
load_dotenv()

# Telegram Bot Token
TELEGRAM_API_TOKEN = os.getenv("TELEGRAM_API_TOKEN")

# OpenAI API Key (через Proxyapi)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# URL MCP HTTP сервера
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")

# OpenAI модель
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "o4-mini-2025-04-16")

# Proxyapi URL (если используется)
PROXYAPI_URL = os.getenv("PROXYAPI_URL", "https://api.proxyapi.ru/openai/v1")

# Проверка обязательных переменных
if not TELEGRAM_API_TOKEN:
    raise ValueError("TELEGRAM_API_TOKEN не установлен в .env файле")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY не установлен в .env файле")

