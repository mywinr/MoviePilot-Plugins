"""
示例插件 - 演示如何向MCP Server注册自定义工具
这是一个完整的示例，展示了插件开发者如何最简单地接入MCP工具注册系统

使用方式：
- 继承MCPDecoratorMixin类
- 设置enable_tools和enable_prompts属性控制功能开关
- 使用@mcp_tool装饰器自动注册工具
- 使用@mcp_prompt装饰器自动注册提示
"""
from app.plugins import _PluginBase
from app.log import logger
import time

# 导入MCP插件助手
try:
    from app.plugins.mcpserver.dev.mcp_dev import (
        mcp_tool,
        mcp_prompt,
        MCPDecoratorMixin
    )
    MCP_DEV_AVAILABLE = True
except ImportError as e:
    logger.warning(f"MCPServer插件不可用，MCP功能将被禁用。错误详情: {str(e)}")
    MCP_DEV_AVAILABLE = False

    # 定义空的装饰器，避免语法错误
    def mcp_tool(*args, **kwargs):
        """空的MCP工具装饰器，当MCP不可用时使用"""
        def decorator(func):
            return func
        return decorator

    def mcp_prompt(*args, **kwargs):
        """空的MCP提示装饰器，当MCP不可用时使用"""
        def decorator(func):
            return func
        return decorator

    # 定义空的Mixin类
    class MCPDecoratorMixin:
        """空的MCP装饰器混入类，当MCP不可用时使用"""
        pass

class McpToolExample(_PluginBase, MCPDecoratorMixin):
    """示例MCP插件 - 演示MCP工具和提示的开发"""

    plugin_name = "MCP扩展示例"
    plugin_desc = "演示如何向MCP Server注册自定义工具和提示"
    plugin_icon = ""
    plugin_version = "1.1"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "mcptoolexample_"
    plugin_order = 99
    auth_level = 1
    _enabled = True

    def init_plugin(self, config: dict = None):
        """注销MCP功能"""
        self.stop_service()

        # 根据配置动态设置MCP功能开关
        if config and MCP_DEV_AVAILABLE:
            self._enable_tools = config.get("enable_tools", True)
            self._enable_prompts = config.get("enable_prompts", True)

        try:
            logger.info("初始化MCP功能")
            self.init_mcp_decorators()

        except Exception as e:
            logger.error(f"MCP初始化失败: {str(e)}")

    # ==================== MCP工具和提示 ====================

    @mcp_tool(
        name="greeting",
        description="问候工具，可以生成个性化的问候语",
        parameters=[
            {
                "name": "name",
                "description": "要问候的人的姓名",
                "required": True,
                "type": "string"
            },
            {
                "name": "language",
                "description": "问候语言，支持 'zh' (中文) 或 'en' (英文)",
                "required": False,
                "type": "string",
                "enum": ["zh", "en"]
            }
        ]
    )
    def greeting_tool(self, name: str, language: str = "zh") -> str:
        """问候工具"""
        if language == "en":
            return f"Hello, {name}! Welcome to MoviePilot MCP Server!"
        else:
            return f"你好，{name}！欢迎使用 MoviePilot MCP 服务器！"

    @mcp_tool(
        name="time",
        description="时间工具，获取当前时间信息",
        parameters=[
            {
                "name": "format",
                "description": "时间格式，可选 'simple' 或 'detailed'",
                "required": False,
                "type": "string",
                "enum": ["simple", "detailed"]
            }
        ]
    )
    def time_tool(self, format: str = "simple") -> dict:
        """时间工具"""
        current_time = time.time()

        if format == "detailed":
            import datetime
            dt = datetime.datetime.fromtimestamp(current_time)
            return {
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
        else:
            import datetime
            dt = datetime.datetime.fromtimestamp(current_time)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    @mcp_prompt(
        name="greeting-prompt",
        description="问候提示，生成个性化问候语的提示",
        parameters=[
            {
                "name": "name",
                "description": "要问候的人的姓名",
                "required": True
            },
            {
                "name": "occasion",
                "description": "问候场合，如生日、节日等",
                "required": False
            }
        ]
    )
    def greeting_prompt(self, name: str, occasion: str = "") -> dict:
        """问候提示"""
        if occasion:
            prompt_content = (
                f"# 个性化问候语生成\n\n"
                f"请为 **{name}** 在 **{occasion}** 场合生成一个温馨、个性化的问候语。\n\n"
                f"## 要求：\n"
                f"1. 问候语要体现{occasion}的特殊意义\n"
                f"2. 语言要温暖、真诚\n"
                f"3. 可以包含对{name}的美好祝愿\n"
                f"4. 长度适中，不要过于冗长\n\n"
                f"## 示例风格：\n"
                f"- 亲切自然的语调\n"
                f"- 体现场合特色\n"
                f"- 表达真挚的情感\n\n"
                f"请生成一个符合以上要求的问候语。"
            )
        else:
            prompt_content = (
                f"# 个性化问候语生成\n\n"
                f"请为 **{name}** 生成一个温馨、个性化的问候语。\n\n"
                f"## 要求：\n"
                f"1. 问候语要亲切自然\n"
                f"2. 语言要温暖、真诚\n"
                f"3. 可以包含对{name}的关心和祝福\n"
                f"4. 长度适中，不要过于冗长\n\n"
                f"## 示例风格：\n"
                f"- 日常友好的语调\n"
                f"- 体现关怀和友善\n"
                f"- 让人感到温暖\n\n"
                f"请生成一个符合以上要求的问候语。"
            )

        return {
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": prompt_content
                    }
                }
            ]
        }

    def stop_service(self):
        """插件停止时注销工具和提示"""
        try:
            if hasattr(self, 'stop_mcp_decorators'):
                # 停止MCP功能
                self.stop_mcp_decorators()
        except Exception as e:
            logger.error(f"停止MCP服务失败: {str(e)}")

    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled

    @staticmethod
    def get_command() -> list:
        """获取插件命令"""
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
                                                'text': '这是一个示例插件，演示如何向MCP Server注册自定义工具和提示。'
                                            }
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            'component': 'VRow',
                            'content': [
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'md': 6
                                    },
                                    'content': [
                                        {
                                            'component': 'VSwitch',
                                            'props': {
                                                'model': 'enable_tools',
                                                'label': '启用MCP工具',
                                                'hint': '启用后会注册示例工具',
                                                'persistent-hint': True
                                            }
                                        }
                                    ]
                                },
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'md': 6
                                    },
                                    'content': [
                                        {
                                            'component': 'VSwitch',
                                            'props': {
                                                'model': 'enable_prompts',
                                                'label': '启用MCP提示',
                                                'hint': '启用后会注册示例提示',
                                                'persistent-hint': True
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            {
                "enable_tools": True,
                "enable_prompts": True
            }
        )

    def get_page(self) -> list:
        """获取插件页面"""
        return []

    def get_api(self) -> list:
        """获取插件API端点"""
        api_endpoints = []

        # 添加MCP相关的API端点
        if hasattr(self, 'get_mcp_api_endpoints'):
            api_endpoints.extend(self.get_mcp_api_endpoints())

        # 在这里可以添加其他自定义的API端点
        # api_endpoints.extend([
        #     {
        #         "path": "/custom_endpoint",
        #         "endpoint": self.custom_endpoint_handler,
        #         "methods": ["GET", "POST"]
        #     }
        # ])

        return api_endpoints
