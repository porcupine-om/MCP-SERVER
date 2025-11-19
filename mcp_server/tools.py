import ast
import operator
from typing import Any, Dict
import db

# Безопасные операции для калькулятора
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_eval(expression: str) -> float:
    """
    Безопасный калькулятор, использующий AST для парсинга математических выражений.
    Запрещает использование eval() и выполняет только базовые математические операции.
    """
    try:
        # Парсим выражение в AST
        node = ast.parse(expression, mode='eval')
        
        def eval_node(node):
            if isinstance(node, ast.Constant):  # Числа
                return float(node.value)
            elif isinstance(node, ast.Num):  # Для старых версий Python
                return float(node.n)
            elif isinstance(node, ast.BinOp):  # Бинарные операции
                left = eval_node(node.left)
                right = eval_node(node.right)
                op = SAFE_OPERATORS.get(type(node.op))
                if op is None:
                    raise ValueError(f"Неподдерживаемая операция: {type(node.op)}")
                return op(left, right)
            elif isinstance(node, ast.UnaryOp):  # Унарные операции
                operand = eval_node(node.operand)
                op = SAFE_OPERATORS.get(type(node.op))
                if op is None:
                    raise ValueError(f"Неподдерживаемая операция: {type(node.op)}")
                return op(operand)
            else:
                raise ValueError(f"Неподдерживаемый тип узла: {type(node)}")
        
        result = eval_node(node.body)
        return result
    except Exception as e:
        raise ValueError(f"Ошибка вычисления: {str(e)}")


# MCP инструменты
MCP_TOOLS = [
    {
        "name": "list_products",
        "description": "Возвращает список всех товаров из базы данных",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "find_product",
        "description": "Ищет товары по имени (частичное совпадение)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Название товара для поиска"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "find_products_by_category",
        "description": "Ищет товары по категории",
        "inputSchema": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": "Категория товаров для поиска"
                }
            },
            "required": ["category"]
        }
    },
    {
        "name": "find_product_by_ID",
        "description": "Ищет товар по ID",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {
                    "type": "integer",
                    "description": "ID товара"
                }
            },
            "required": ["id"]
        }
    },
    {
        "name": "add_product",
        "description": "Добавляет новый товар в базу данных",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Название товара"
                },
                "category": {
                    "type": "string",
                    "description": "Категория товара"
                },
                "price": {
                    "type": "number",
                    "description": "Цена товара"
                }
            },
            "required": ["name", "category", "price"]
        }
    },
    {
        "name": "calculate",
        "description": "Безопасный калькулятор для вычисления математических выражений",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Математическое выражение для вычисления (например: '2+2', '10*5', '100/4')"
                }
            },
            "required": ["expression"]
        }
    }
]


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Выполняет MCP инструмент и возвращает результат"""
    try:
        if tool_name == "list_products":
            products = db.get_all_products()
            return {
                "success": True,
                "result": products,
                "count": len(products)
            }
        
        elif tool_name == "find_product":
            name = arguments.get("name")
            if not name:
                return {"success": False, "error": "Параметр 'name' обязателен"}
            products = db.find_product_by_name(name)
            return {
                "success": True,
                "result": products,
                "count": len(products)
            }
        
        elif tool_name == "find_products_by_category":
            category = arguments.get("category")
            if not category:
                return {"success": False, "error": "Параметр 'category' обязателен"}
            products = db.find_products_by_category(category)
            return {
                "success": True,
                "result": products,
                "count": len(products)
            }
        
        elif tool_name == "find_product_by_ID":
            product_id = arguments.get("id")
            if product_id is None:
                return {"success": False, "error": "Параметр 'id' обязателен"}
            product = db.find_product_by_id(product_id)
            if product:
                return {"success": True, "result": product}
            else:
                return {"success": False, "error": f"Товар с ID {product_id} не найден"}
        
        elif tool_name == "add_product":
            name = arguments.get("name")
            category = arguments.get("category")
            price = arguments.get("price")
            
            if not name or not category or price is None:
                return {"success": False, "error": "Параметры 'name', 'category' и 'price' обязательны"}
            
            try:
                price = float(price)
                if price < 0:
                    return {"success": False, "error": "Цена не может быть отрицательной"}
            except (ValueError, TypeError):
                return {"success": False, "error": "Цена должна быть числом"}
            
            product = db.add_product(name, category, price)
            return {
                "success": True,
                "result": product,
                "message": f"Товар '{name}' успешно добавлен"
            }
        
        elif tool_name == "calculate":
            expression = arguments.get("expression")
            if not expression:
                return {"success": False, "error": "Параметр 'expression' обязателен"}
            
            try:
                result = safe_eval(expression)
                return {
                    "success": True,
                    "result": result,
                    "expression": expression
                }
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        else:
            return {"success": False, "error": f"Неизвестный инструмент: {tool_name}"}
    
    except Exception as e:
        return {"success": False, "error": f"Ошибка выполнения инструмента: {str(e)}"}

