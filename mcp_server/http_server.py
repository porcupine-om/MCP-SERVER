#!/usr/bin/env python3
"""
HTTP обертка для MCP сервера
Позволяет подключаться к MCP инструментам через HTTP API
Запуск: python http_server.py
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Any, Dict, Optional
import uvicorn
import db
import tools

# Инициализация БД
db.init_db()

app = FastAPI(title="Product MCP HTTP Server", version="1.0.0")


class ToolCallRequest(BaseModel):
    name: str
    arguments: Dict[str, Any] = {}


class ToolCallResponse(BaseModel):
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    count: Optional[int] = None
    message: Optional[str] = None


@app.get("/")
async def root():
    """Информация о сервере"""
    return {
        "name": "product-mcp",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/tools")
async def list_tools():
    """Возвращает список доступных инструментов"""
    return {"tools": tools.MCP_TOOLS}


@app.post("/tools/call", response_model=ToolCallResponse)
async def call_tool(request: ToolCallRequest):
    """Вызывает MCP инструмент"""
    try:
        result = tools.execute_tool(request.name, request.arguments)
        return ToolCallResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    print("Запуск HTTP сервера MCP на http://localhost:8000")
    print("Документация API: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)

