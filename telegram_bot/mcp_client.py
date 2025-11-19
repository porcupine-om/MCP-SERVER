"""
Клиент для работы с MCP сервером через HTTP
"""

import requests
from typing import Any, Dict, Optional
import config


class MCPClient:
    """Клиент для вызова MCP инструментов через HTTP"""
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.MCP_SERVER_URL
    
    def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Вызывает MCP инструмент
        
        Args:
            tool_name: Название инструмента
            arguments: Аргументы для инструмента
            
        Returns:
            Результат выполнения инструмента
        """
        if arguments is None:
            arguments = {}
        
        url = f"{self.base_url}/tools/call"
        payload = {
            "name": tool_name,
            "arguments": arguments
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Ошибка подключения к MCP серверу: {str(e)}"
            }
    
    def list_products(self) -> Dict[str, Any]:
        """Получить список всех товаров"""
        return self.call_tool("list_products", {})
    
    def find_product(self, name: str) -> Dict[str, Any]:
        """Найти товары по имени"""
        return self.call_tool("find_product", {"name": name})
    
    def find_products_by_category(self, category: str) -> Dict[str, Any]:
        """Найти товары по категории"""
        return self.call_tool("find_products_by_category", {"category": category})
    
    def find_product_by_id(self, product_id: int) -> Dict[str, Any]:
        """Найти товар по ID"""
        return self.call_tool("find_product_by_ID", {"id": product_id})
    
    def add_product(self, name: str, category: str, price: float) -> Dict[str, Any]:
        """Добавить товар"""
        return self.call_tool("add_product", {
            "name": name,
            "category": category,
            "price": price
        })
    
    def calculate(self, expression: str) -> Dict[str, Any]:
        """Вычислить математическое выражение"""
        return self.call_tool("calculate", {"expression": expression})


# Глобальный экземпляр клиента
mcp_client = MCPClient()

