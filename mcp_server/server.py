#!/usr/bin/env python3
"""
MCP Server для работы с базой данных товаров
Запуск: python server.py
"""

import json
import sys
from typing import Any, Dict, List
import db
import tools

# Инициализация БД при импорте
db.init_db()


def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """Обработка запроса initialize"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "product-mcp",
            "version": "1.0.0"
        }
    }


def handle_list_tools(params: Dict[str, Any]) -> Dict[str, Any]:
    """Обработка запроса list_tools - возвращает список доступных инструментов"""
    return {
        "tools": tools.MCP_TOOLS
    }


def handle_call_tool(params: Dict[str, Any]) -> Dict[str, Any]:
    """Обработка запроса call_tool - выполняет инструмент"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    if not tool_name:
        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps({"success": False, "error": "Имя инструмента не указано"}, ensure_ascii=False)
                }
            ],
            "isError": True
        }
    
    result = tools.execute_tool(tool_name, arguments)
    
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(result, ensure_ascii=False, indent=2)
            }
        ],
        "isError": not result.get("success", False)
    }


def process_mcp_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Обрабатывает MCP запрос и возвращает ответ"""
    method = request.get("method")
    params = request.get("params", {})
    request_id = request.get("id")
    
    response = {
        "jsonrpc": "2.0",
        "id": request_id
    }
    
    try:
        if method == "initialize":
            result = handle_initialize(params)
        elif method == "tools/list":
            result = handle_list_tools(params)
        elif method == "tools/call":
            result = handle_call_tool(params)
        else:
            result = {
                "error": {
                    "code": -32601,
                    "message": f"Метод не найден: {method}"
                }
            }
        
        response.update(result)
    
    except Exception as e:
        response["error"] = {
            "code": -32603,
            "message": f"Внутренняя ошибка: {str(e)}"
        }
    
    return response


def main():
    """Основная функция - читает JSON-RPC запросы из stdin и отправляет ответы в stdout"""
    # Инициализация БД
    db.init_db()
    
    # Читаем запросы из stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
            response = process_mcp_request(request)
            print(json.dumps(response, ensure_ascii=False))
            sys.stdout.flush()
        
        except json.JSONDecodeError as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": f"Ошибка парсинга JSON: {str(e)}"
                }
            }
            print(json.dumps(error_response, ensure_ascii=False))
            sys.stdout.flush()
        
        except Exception as e:
            error_response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32603,
                    "message": f"Внутренняя ошибка: {str(e)}"
                }
            }
            print(json.dumps(error_response, ensure_ascii=False))
            sys.stdout.flush()


if __name__ == "__main__":
    main()

