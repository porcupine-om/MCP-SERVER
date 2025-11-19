#!/usr/bin/env python3
"""
Telegram бот для работы с базой данных товаров через MCP сервер
Использует OpenAI для понимания запросов пользователя
Версия на aiogram (совместима с Python 3.13)
"""

import json
import re
from typing import Optional, Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode, ChatAction
import asyncio
import requests
import config
from mcp_client import mcp_client


# Промпт для LLM
SYSTEM_PROMPT = """Ты — умный помощник для работы с базой данных товаров.

Ты можешь использовать следующие инструменты:

list_products - показать все товары
find_product - найти товары по имени (требует параметр "name")
find_products_by_category - найти товары по категории (требует параметр "category")
find_product_by_ID - найти товар по ID
add_product - добавить товар (требует параметры "name", "category", "price")
calculate - вычислить математическое выражение (требует параметр "expression")

Когда пользователь просит что-то сделать, определи, какой инструмент нужен, и верни JSON в формате:

{
"tool": "название_инструмента",
"arguments": {"параметр": "значение"}
}

Если инструмент не нужен, просто ответь пользователю обычным текстом.

Примеры:

"покажи все товары" → {"tool": "list_products", "arguments": {}}
"найди чай" → {"tool": "find_product", "arguments": {"name": "чай"}}
"покажи товары в категории электроника" → {"tool": "find_products_by_category", "arguments": {"category": "Электроника"}}
"найди все товары категории одежда" → {"tool": "find_products_by_category", "arguments": {"category": "Одежда"}}
"добавь товар яблоки 120 фрукт" → {"tool": "add_product", "arguments": {"name": "яблоки", "category": "фрукт", "price": 120}}
"сколько будет 2+2" → {"tool": "calculate", "arguments": {"expression": "2+2"}}

Отвечай на русском языке, будь дружелюбным и полезным."""


def parse_tool_call(response_text: str) -> Optional[Dict]:
    """Парсит JSON из ответа LLM"""
    print(f"[DEBUG] Парсинг ответа LLM: {response_text[:200]}...")
    
    # Сначала пробуем распарсить весь ответ как JSON
    try:
        parsed = json.loads(response_text.strip())
        if isinstance(parsed, dict) and "tool" in parsed:
            print(f"[DEBUG] Найден JSON инструмент: {parsed}")
            return parsed
    except json.JSONDecodeError:
        pass
    
    # Ищем JSON объект с "tool" в тексте (улучшенное регулярное выражение)
    # Ищем от { до }, учитывая вложенные объекты
    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*"tool"[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
    json_match = re.search(json_pattern, response_text, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            if isinstance(parsed, dict) and "tool" in parsed:
                print(f"[DEBUG] Найден JSON инструмент через regex: {parsed}")
                return parsed
        except json.JSONDecodeError as e:
            print(f"[DEBUG] Ошибка парсинга JSON: {e}")
            pass
    
    # Пробуем найти JSON с помощью более простого подхода
    # Ищем от первой { до последней }
    start = response_text.find('{')
    end = response_text.rfind('}')
    if start != -1 and end != -1 and end > start:
        try:
            json_str = response_text[start:end+1]
            parsed = json.loads(json_str)
            if isinstance(parsed, dict) and "tool" in parsed:
                print(f"[DEBUG] Найден JSON инструмент через поиск скобок: {parsed}")
                return parsed
        except json.JSONDecodeError:
            pass
    
    print(f"[DEBUG] JSON инструмент не найден в ответе")
    return None


def format_products_response(products: list, count: int = None) -> str:
    """Форматирует список товаров для красивого отображения"""
    if not products:
        return "Товары не найдены."
    
    if count is None:
        count = len(products)
    
    # Ограничиваем количество товаров для отображения (чтобы не было слишком длинно)
    display_products = products[:20]
    
    result = f"📦 Найдено товаров: {count}\n\n"
    
    for product in display_products:
        result += f"🆔 ID: {product['id']}\n"
        result += f"📝 Название: {product['name']}\n"
        result += f"🏷️ Категория: {product['category']}\n"
        result += f"💰 Цена: {product['price']:.2f} ₽\n"
        result += "─" * 30 + "\n"
    
    if count > 20:
        result += f"\n... и еще {count - 20} товаров"
    
    return result


def format_single_product(product: dict) -> str:
    """Форматирует один товар для отображения"""
    return f"""📦 Товар найден!

🆔 ID: {product['id']}
📝 Название: {product['name']}
🏷️ Категория: {product['category']}
💰 Цена: {product['price']:.2f} ₽"""


async def get_llm_response(user_message: str) -> str:
    """Получает ответ от LLM"""
    try:
        print(f"[DEBUG] Отправка запроса в LLM: {user_message[:50]}...")
        print(f"[DEBUG] Используется Proxyapi URL: {config.PROXYAPI_URL}")
        print(f"[DEBUG] Модель: {config.OPENAI_MODEL}")
        
        # Используем OpenAI через Proxyapi
        headers = {
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": config.OPENAI_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ]
        }
        
        print(f"[DEBUG] Payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        
        response = requests.post(
            f"{config.PROXYAPI_URL}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        # Детальное логирование ошибок
        if response.status_code != 200:
            error_detail = response.text
            print(f"[ERROR] HTTP {response.status_code}: {error_detail}")
            try:
                error_json = response.json()
                print(f"[ERROR] Детали ошибки: {json.dumps(error_json, ensure_ascii=False, indent=2)}")
            except:
                pass
            response.raise_for_status()
        
        result = response.json()
        llm_answer = result["choices"][0]["message"]["content"].strip()
        print(f"[DEBUG] Получен ответ от LLM: {llm_answer[:100]}...")
        return llm_answer
    except requests.exceptions.HTTPError as e:
        error_msg = f"Ошибка HTTP при обращении к LLM: {str(e)}"
        if hasattr(e.response, 'text'):
            print(f"[ERROR] Ответ сервера: {e.response.text}")
        print(f"[ERROR] {error_msg}")
        return error_msg
    except Exception as e:
        error_msg = f"Ошибка при обращении к LLM: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return error_msg


async def handle_message(message: Message, bot: Bot):
    """Обрабатывает сообщения от пользователя"""
    user_message = message.text
    
    # Пропускаем команды (они обрабатываются отдельными обработчиками)
    if user_message and user_message.startswith("/"):
        return
    
    print(f"[DEBUG] Получено сообщение от пользователя: {user_message}")
    
    # Показываем, что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)
    
    # Получаем ответ от LLM
    llm_response = await get_llm_response(user_message)
    
    # Пытаемся найти вызов инструмента в ответе
    tool_call = parse_tool_call(llm_response)
    print(f"[DEBUG] Результат парсинга tool_call: {tool_call}")
    
    if tool_call and "tool" in tool_call:
        print(f"[DEBUG] Вызываем инструмент: {tool_call['tool']} с аргументами: {tool_call.get('arguments')}")
        # Нужно вызвать инструмент
        tool_name = tool_call["tool"]
        tool_args = tool_call.get("arguments", {})
        
        # Вызываем MCP инструмент
        result = mcp_client.call_tool(tool_name, tool_args)
        
        if result.get("success"):
            # Форматируем результат в зависимости от инструмента
            if tool_name == "list_products":
                products = result.get("result", [])
                response_text = format_products_response(products, result.get("count"))
            elif tool_name in ["find_product", "find_products_by_category"]:
                products = result.get("result", [])
                response_text = format_products_response(products, result.get("count"))
            elif tool_name == "find_product_by_ID":
                product = result.get("result")
                if product:
                    response_text = format_single_product(product)
                else:
                    response_text = "Товар не найден."
            elif tool_name == "add_product":
                product = result.get("result")
                if product:
                    response_text = f"✅ Товар успешно добавлен!\n\n{format_single_product(product)}"
                else:
                    response_text = result.get("message", "Товар добавлен.")
            elif tool_name == "calculate":
                calc_result = result.get("result")
                expression = result.get("expression", "")
                response_text = f"🧮 Результат: {expression} = {calc_result}"
            else:
                response_text = f"✅ Операция выполнена успешно.\n\nРезультат:\n{json.dumps(result.get('result'), ensure_ascii=False, indent=2)}"
        else:
            error_msg = result.get("error", "Неизвестная ошибка")
            response_text = f"❌ Ошибка: {error_msg}"
    else:
        # LLM ответил обычным текстом
        response_text = llm_response
    
    # Отправляем ответ пользователю
    try:
        await message.answer(response_text)
        print(f"[DEBUG] Ответ отправлен пользователю")
    except Exception as e:
        print(f"[ERROR] Ошибка при отправке ответа: {str(e)}")
        await message.answer(f"Произошла ошибка при обработке запроса. Попробуйте еще раз.")


async def start_command(message: Message):
    """Обработчик команды /start"""
    welcome_message = """👋 Привет! Я бот-помощник для работы с базой данных товаров.

Я могу помочь тебе:
• 📋 Показать все товары
• 🔍 Найти товары по имени или категории
• ➕ Добавить новый товар
• 🧮 Выполнить математические вычисления

Просто напиши мне, что ты хочешь сделать, например:
• "покажи все товары"
• "найди чай"
• "покажи товары в категории Фрукты"
• "добавь товар яблоки 120 фрукт"
• "сколько будет 2+2*3"

Начнем! 🚀"""
    
    await message.answer(welcome_message)


async def help_command(message: Message):
    """Обработчик команды /help"""
    help_message = """📖 Справка по использованию бота

Доступные команды:
/start - Начать работу с ботом
/help - Показать эту справку

Примеры запросов:
• "покажи все товары" - показать все товары в базе
• "найди молоко" - найти товары с "молоко" в названии
• "покажи товары в категории Овощи" - найти товары по категории
• "найди товар с ID 5" - найти товар по ID
• "добавь товар хлеб 50 хлеб и выпечка" - добавить новый товар
• "посчитай 100+50*2" - выполнить вычисление

Просто напиши мне свой запрос обычным языком! 😊"""
    
    await message.answer(help_message)


async def main():
    """Запуск бота"""
    print("Запуск Telegram бота (aiogram)...")
    print(f"[CONFIG] Proxyapi URL: {config.PROXYAPI_URL}")
    print(f"[CONFIG] OpenAI Model: {config.OPENAI_MODEL}")
    print(f"[CONFIG] MCP Server URL: {config.MCP_SERVER_URL}")
    print(f"[CONFIG] OpenAI API Key установлен: {'Да' if config.OPENAI_API_KEY else 'Нет'}")
    if config.OPENAI_API_KEY:
        print(f"[CONFIG] OpenAI API Key (первые 10 символов): {config.OPENAI_API_KEY[:10]}...")
    
    # Создаем бота и диспетчер
    bot = Bot(
        token=config.TELEGRAM_API_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()
    
    # Регистрируем обработчики (команды должны быть зарегистрированы первыми)
    dp.message.register(start_command, Command("start"))
    dp.message.register(help_command, Command("help"))
    # Обработчик обычных сообщений (должен быть последним, чтобы не перехватывать команды)
    dp.message.register(handle_message, F.text)
    
    # Запускаем бота
    print("Бот запущен и готов к работе!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
