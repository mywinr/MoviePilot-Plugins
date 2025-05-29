"""
示例插件 - 演示如何向MCP Server注册自定义工具
这是一个完整的示例，展示了插件开发者如何最简单地接入MCP工具注册系统
"""
from app.plugins import _PluginBase
from app.core.event import eventmanager
from app.schemas.types import EventType
from app.log import logger
import time


class McpToolExample(_PluginBase):
    """示例MCP插件"""
    
    plugin_name = "示例MCP插件"
    plugin_desc = "演示如何向MCP Server注册自定义工具"
    plugin_icon = ""
    plugin_version = "1.0"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "mcptoolexample_"
    plugin_order = 99
    auth_level = 1
    
    def init_plugin(self, config: dict = None):
        """插件初始化"""
        if self.get_state():
            logger.info("示例MCP插件已启用，注册MCP工具...")
            self._register_mcp_tools()
        else:
            logger.info("示例MCP插件已禁用")
    
    def _register_mcp_tools(self):
        """注册MCP工具"""
        tools = [
            {
                "name": "example-greeting",
                "description": "示例问候工具，可以生成个性化的问候语",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "要问候的人的姓名"
                        },
                        "language": {
                            "type": "string",
                            "description": "问候语言，支持 'zh' (中文) 或 'en' (英文)",
                            "enum": ["zh", "en"]
                        }
                    },
                    "required": ["name"]
                },
                "api_endpoint": f"/api/v1/plugin/{self.__class__.__name__}/mcp_tool_execute"
            },
            {
                "name": "example-time",
                "description": "获取当前时间信息",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "format": {
                            "type": "string",
                            "description": "时间格式，可选 'simple' 或 'detailed'",
                            "enum": ["simple", "detailed"]
                        }
                    },
                    "required": []
                },
                "api_endpoint": f"/api/v1/plugin/{self.__class__.__name__}/mcp_tool_execute"
            },
            {
                "name": "example-calculator",
                "description": "简单的计算器工具",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "operation": {
                            "type": "string",
                            "description": "运算类型",
                            "enum": ["add", "subtract", "multiply", "divide"]
                        },
                        "a": {
                            "type": "number",
                            "description": "第一个数字"
                        },
                        "b": {
                            "type": "number",
                            "description": "第二个数字"
                        }
                    },
                    "required": ["operation", "a", "b"]
                },
                "api_endpoint": f"/api/v1/plugin/{self.__class__.__name__}/mcp_tool_execute"
            }
        ]
        
        # 发送工具注册事件
        eventmanager.send_event(
            EventType.PluginAction,
            {
                "action": "mcp_tool_register",
                "plugin_id": self.__class__.__name__,
                "tools": tools
            }
        )
        
        logger.info(f"已注册 {len(tools)} 个MCP工具")

    def get_api(self) -> list:
        """注册API端点"""
        return [
            {
                "path": "/mcp_tool_execute",
                "endpoint": self._execute_mcp_tool,
                "methods": ["POST"],
                "summary": "执行MCP工具",
                "description": "执行注册的MCP工具"
            }
        ]

    def _execute_mcp_tool(self, tool_name: str, arguments: dict) -> dict:
        """MCP工具执行入口"""
        try:
            if tool_name == "example-greeting":
                return self.execute_greeting_tool(arguments)
            elif tool_name == "example-time":
                return self.execute_time_tool(arguments)
            elif tool_name == "example-calculator":
                return self.execute_calculator_tool(arguments)
            else:
                return {
                    "success": False,
                    "message": f"未知的工具: {tool_name}",
                    "data": None
                }
        except Exception as e:
            logger.error(f"执行MCP工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def execute_greeting_tool(self, arguments: dict) -> dict:
        """执行问候工具"""
        try:
            name = arguments.get("name", "朋友")
            language = arguments.get("language", "zh")
            
            if language == "en":
                greeting = f"Hello, {name}! Welcome to MoviePilot MCP Server!"
            else:
                greeting = f"你好，{name}！欢迎使用 MoviePilot MCP 服务器！"
            
            return {
                "success": True,
                "data": greeting,
                "message": "问候语生成成功"
            }
            
        except Exception as e:
            logger.error(f"执行问候工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def execute_time_tool(self, arguments: dict) -> dict:
        """执行时间工具"""
        try:
            format_type = arguments.get("format", "simple")
            current_time = time.time()
            
            if format_type == "detailed":
                import datetime
                dt = datetime.datetime.fromtimestamp(current_time)
                time_info = {
                    "timestamp": current_time,
                    "formatted": dt.strftime("%Y-%m-%d %H:%M:%S"),
                    "year": dt.year,
                    "month": dt.month,
                    "day": dt.day,
                    "hour": dt.hour,
                    "minute": dt.minute,
                    "second": dt.second,
                    "weekday": dt.strftime("%A")
                }
                message = "详细时间信息获取成功"
            else:
                import datetime
                dt = datetime.datetime.fromtimestamp(current_time)
                time_info = dt.strftime("%Y-%m-%d %H:%M:%S")
                message = "当前时间获取成功"
            
            return {
                "success": True,
                "data": time_info,
                "message": message
            }
            
        except Exception as e:
            logger.error(f"执行时间工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def execute_calculator_tool(self, arguments: dict) -> dict:
        """执行计算器工具"""
        try:
            operation = arguments.get("operation")
            a = arguments.get("a")
            b = arguments.get("b")
            
            if operation == "add":
                result = a + b
                operation_text = "加法"
            elif operation == "subtract":
                result = a - b
                operation_text = "减法"
            elif operation == "multiply":
                result = a * b
                operation_text = "乘法"
            elif operation == "divide":
                if b == 0:
                    return {
                        "success": False,
                        "message": "除数不能为零",
                        "data": None
                    }
                result = a / b
                operation_text = "除法"
            else:
                return {
                    "success": False,
                    "message": f"不支持的运算类型: {operation}",
                    "data": None
                }
            
            calculation_info = {
                "operation": operation_text,
                "operand_a": a,
                "operand_b": b,
                "result": result,
                "expression": f"{a} {operation} {b} = {result}"
            }
            
            return {
                "success": True,
                "data": calculation_info,
                "message": f"{operation_text}计算完成"
            }
            
        except Exception as e:
            logger.error(f"执行计算器工具失败: {str(e)}")
            return {
                "success": False,
                "message": f"执行失败: {str(e)}",
                "data": None
            }
    
    def stop_service(self):
        """插件停止时注销工具"""
        if self.get_state():
            logger.info("注销示例MCP工具...")
            eventmanager.send_event(
                EventType.PluginAction,
                {
                    "action": "mcp_tool_unregister",
                    "plugin_id": self.__class__.__name__
                }
            )
    
    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled
    
    @staticmethod
    def get_command() -> list:
        """获取插件命令"""
        return []
    
    def get_api(self) -> list:
        """获取插件API"""
        return []
    
    def get_form(self) -> tuple:
        """获取插件配置表单"""
        return (
            [
                {
                    'component': 'VForm',
                    'content': [
                        {
                            'component': 'VRow',
                            'content': [
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                    },
                                    'content': [
                                        {
                                            'component': 'VAlert',
                                            'props': {
                                                'type': 'info',
                                                'variant': 'tonal',
                                                'text': '这是一个示例插件，演示如何向MCP Server注册自定义工具。启用后会自动注册3个示例工具：问候工具、时间工具和计算器工具。'
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            {}
        )
    
    def get_page(self) -> list:
        """获取插件页面"""
        return []
