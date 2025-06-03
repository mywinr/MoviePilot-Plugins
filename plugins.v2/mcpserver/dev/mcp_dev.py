import logging
import threading
from typing import List, Dict, Any, Optional, Callable
from pathlib import Path
from logging.handlers import RotatingFileHandler

from app.core.event import eventmanager
from app.schemas.types import EventType


class MCPGlobalLogger:
    """
    MCP 全局日志器，完全独立于 MoviePilot 的日志系统
    根据传入的插件实例自动确定日志文件路径
    """

    _loggers: Dict[str, logging.Logger] = {}
    _lock = threading.Lock()

    def __init__(self):
        self._current_plugin_name = None

    def set_plugin_from_instance(self, plugin_instance):
        """从插件实例中提取插件名称并设置为当前目标"""
        plugin_name = self._extract_plugin_name_from_instance(plugin_instance)
        self._current_plugin_name = plugin_name
        return plugin_name

    def _extract_plugin_name_from_instance(self, plugin_instance) -> Optional[str]:
        """从插件实例中提取插件名称"""
        try:
            if hasattr(plugin_instance, '__module__'):
                module_path = plugin_instance.__module__
                parts = module_path.split('.')
                if 'plugins' in parts:
                    plugins_index = parts.index('plugins')
                    if plugins_index + 2 < len(parts):
                        return parts[plugins_index + 2]  # 跳过 plugins.v2
                    elif plugins_index + 1 < len(parts):
                        return parts[plugins_index + 1]

            # 如果无法从模块路径提取，使用类名的小写形式
            return plugin_instance.__class__.__name__.lower()
        except Exception:
            return None

    def _get_logger_for_plugin(self, plugin_name: str) -> logging.Logger:
        """获取或创建指定插件的 logger"""
        if not plugin_name:
            plugin_name = "mcp_dev_default"

        with MCPGlobalLogger._lock:
            if plugin_name not in MCPGlobalLogger._loggers:
                # 创建新的 logger
                logger = logging.getLogger(f"mcp_dev_{plugin_name}")
                logger.setLevel(self._get_log_level())

                # 清除已有的处理器
                for handler in logger.handlers[:]:
                    logger.removeHandler(handler)

                # 确定日志文件路径
                log_file = self._get_log_file_path(plugin_name)

                # 确保日志目录存在
                log_file.parent.mkdir(parents=True, exist_ok=True)

                # 创建文件处理器
                file_handler = RotatingFileHandler(
                    filename=log_file,
                    mode="a",
                    maxBytes=5 * 1024 * 1024,  # 5MB
                    backupCount=3,
                    encoding="utf-8"
                )

                # 设置日志格式（与 MoviePilot 保持一致）
                formatter = logging.Formatter("【%(levelname)s】%(asctime)s - %(message)s")
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)

                # 防止日志传播到根 logger
                logger.propagate = False

                MCPGlobalLogger._loggers[plugin_name] = logger

            return MCPGlobalLogger._loggers[plugin_name]

    def _get_log_file_path(self, plugin_name: str) -> Path:
        """获取插件对应的日志文件路径"""
        try:
            # 尝试获取 MoviePilot 的日志路径配置
            from app.log import log_settings
            base_log_path = log_settings.LOG_PATH
        except ImportError:
            # 如果无法导入，使用默认路径
            base_log_path = Path("config/logs")

        if plugin_name == "mcp_dev_default":
            return base_log_path / "mcp_dev.log"
        else:
            return base_log_path / "plugins" / f"{plugin_name}.log"

    def _get_log_level(self) -> int:
        """获取当前日志级别"""
        try:
            from app.log import log_settings
            return logging.DEBUG if log_settings.DEBUG else getattr(logging, log_settings.LOG_LEVEL.upper(), logging.INFO)
        except ImportError:
            return logging.INFO

    def _log_with_plugin(self, level: str, msg: str, plugin_name: str = None, *args, **kwargs):
        """使用指定插件名称记录日志"""
        target_plugin = plugin_name or self._current_plugin_name
        logger = self._get_logger_for_plugin(target_plugin)

        # 添加 mcp_dev.py 前缀来标识日志来源
        prefixed_msg = f"mcp_dev.py - {msg}"

        log_method = getattr(logger, level, None)
        if log_method:
            log_method(prefixed_msg, *args, **kwargs)

    def debug(self, msg: str, plugin_name: str = None, *args, **kwargs):
        """输出调试级别日志"""
        self._log_with_plugin("debug", msg, plugin_name, *args, **kwargs)

    def info(self, msg: str, plugin_name: str = None, *args, **kwargs):
        """输出信息级别日志"""
        self._log_with_plugin("info", msg, plugin_name, *args, **kwargs)

    def warning(self, msg: str, plugin_name: str = None, *args, **kwargs):
        """输出警告级别日志"""
        self._log_with_plugin("warning", msg, plugin_name, *args, **kwargs)

    def error(self, msg: str, plugin_name: str = None, *args, **kwargs):
        """输出错误级别日志"""
        self._log_with_plugin("error", msg, plugin_name, *args, **kwargs)

    def critical(self, msg: str, plugin_name: str = None, *args, **kwargs):
        """输出严重错误级别日志"""
        self._log_with_plugin("critical", msg, plugin_name, *args, **kwargs)


# 创建全局的 MCP logger 实例
logger = MCPGlobalLogger()


class MCPToolInfo:
    """MCP工具信息类"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any],
                 handler: Callable, validate_params: bool = True):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.validate_params = validate_params

    def to_config(self, plugin_class_name: str) -> Dict[str, Any]:
        """转换为工具配置格式"""
        # 处理参数格式，统一转换为 JSON Schema 格式
        parameters = {"type": "object", "properties": {}, "required": []}

        if isinstance(self.parameters, list):
            # 简化格式：参数列表格式
            # 格式：[{"name": "param1", "description": "描述", "required": True, "type": "string", "enum": [...] }, ...]
            properties = {}
            required = []

            for param_def in self.parameters:
                param_name = param_def.get("name")
                if param_name:
                    # 构建参数 schema
                    param_schema = {
                        "description": param_def.get("description", "")
                    }

                    # 添加类型信息（如果有）
                    if "type" in param_def:
                        param_schema["type"] = param_def["type"]

                    # 添加枚举值（如果有）
                    if "enum" in param_def:
                        param_schema["enum"] = param_def["enum"]

                    # 添加其他验证规则
                    for key in ["minimum", "maximum", "minLength", "maxLength", "pattern"]:
                        if key in param_def:
                            param_schema[key] = param_def[key]

                    properties[param_name] = param_schema

                    # 处理必需参数
                    if param_def.get("required", False):
                        required.append(param_name)

            parameters = {
                "type": "object",
                "properties": properties,
                "required": required
            }

        elif isinstance(self.parameters, dict):
            # JSON Schema格式（向后兼容）
            parameters = self.parameters.copy()
            # 确保有 type: object
            if "type" not in parameters:
                parameters["type"] = "object"

        return {
            "name": self.name,
            "description": self.description,
            "parameters": parameters,
            "api_endpoint": f"/api/v1/plugin/{plugin_class_name}/mcp_tool_execute"
        }


class MCPPromptInfo:
    """MCP提示信息类"""

    def __init__(self, name: str, description: str, parameters: Dict[str, Any],
                 handler: Callable, validate_params: bool = True):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
        self.validate_params = validate_params

    def to_config(self, plugin_class_name: str) -> Dict[str, Any]:
        """转换为提示配置格式"""
        arguments = []

        if isinstance(self.parameters, list):
            # 简化格式：直接传递参数列表
            # 格式：[{"name": "param1", "description": "描述", "required": True}, ...]
            arguments = self.parameters
        elif isinstance(self.parameters, dict):
            if "properties" in self.parameters:
                # JSON Schema格式（向后兼容）
                properties = self.parameters["properties"]
                required_fields = self.parameters.get("required", [])

                for param_name, param_schema in properties.items():
                    arguments.append({
                        "name": param_name,
                        "description": param_schema.get("description", ""),
                        "required": param_name in required_fields
                    })
            # 如果是空字典或其他格式，arguments 保持为空列表

        return {
            "name": self.name,
            "description": self.description,
            "arguments": arguments,
            "api_endpoint": f"/api/v1/plugin/{plugin_class_name}/mcp_prompt_execute"
        }


class MCPPluginRegistry:
    """MCP插件注册表，管理装饰器注册的工具和提示"""

    def __init__(self, plugin_instance):
        self.plugin_instance = plugin_instance
        self.plugin_class_name = plugin_instance.__class__.__name__
        self.tools: Dict[str, MCPToolInfo] = {}
        self.prompts: Dict[str, MCPPromptInfo] = {}
        self._mcp_helper = None

        # 从插件实例中提取真实的插件名称并设置全局 logger
        self.target_plugin_name = logger.set_plugin_from_instance(plugin_instance)

        # 设置日志器
        self._setup_logger()

    def _extract_plugin_name(self) -> Optional[str]:
        """从插件实例中提取真实的插件名称"""
        try:
            if hasattr(self.plugin_instance, '__module__'):
                module_path = self.plugin_instance.__module__
                parts = module_path.split('.')
                if 'plugins' in parts:
                    plugins_index = parts.index('plugins')
                    if plugins_index + 2 < len(parts):
                        return parts[plugins_index + 2]  # 跳过 plugins.v2
                    elif plugins_index + 1 < len(parts):
                        return parts[plugins_index + 1]

            # 如果无法从模块路径提取，使用类名的小写形式
            return self.plugin_class_name.lower()
        except Exception:
            return None

    def _setup_logger(self):
        """设置日志器"""
        try:
            logger.debug(f"MCP 注册表已初始化，插件: {self.plugin_class_name}, 目标日志: {self.target_plugin_name}", self.target_plugin_name)
        except Exception as e:
            # 如果日志记录失败，使用 print 作为备用
            print(f"MCP 日志设置失败: {str(e)}")

    def register_tool(self, tool_info: MCPToolInfo):
        """注册工具"""
        self.tools[tool_info.name] = tool_info
        logger.debug(f"注册工具: {tool_info.name}", self.target_plugin_name)

    def register_prompt(self, prompt_info: MCPPromptInfo):
        """注册提示"""
        self.prompts[prompt_info.name] = prompt_info
        logger.debug(f"注册提示: {prompt_info.name}", self.target_plugin_name)

    def get_tools_config(self) -> List[Dict[str, Any]]:
        """获取所有工具的配置"""
        return [tool.to_config(self.plugin_class_name) for tool in self.tools.values()]

    def get_prompts_config(self) -> List[Dict[str, Any]]:
        """获取所有提示的配置"""
        return [prompt.to_config(self.plugin_class_name) for prompt in self.prompts.values()]

    def execute_tool(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具 - 接收完整的请求数据"""
        try:
            # 从请求数据中提取工具名称和参数
            tool_name = request_data.get("tool_name")
            arguments = request_data.get("arguments", {})

            if not tool_name:
                return {
                    "success": False,
                    "message": "缺少工具名称",
                    "data": None
                }

            if tool_name not in self.tools:
                return {
                    "success": False,
                    "message": f"未知的工具: {tool_name}",
                    "data": None
                }

            tool_info = self.tools[tool_name]

            # 参数验证
            if tool_info.validate_params:
                validated_args = self._validate_parameters(arguments, tool_info.parameters)
                if validated_args is None:
                    return {
                        "success": False,
                        "message": "参数验证失败",
                        "data": None
                    }
                arguments = validated_args

            # 执行工具处理函数
            result = tool_info.handler(self.plugin_instance, **arguments)

            # 统一的返回格式处理
            return self._standardize_response(result, "工具执行成功")

        except Exception as e:
            logger.error(f"工具执行失败: {str(e)}", self.target_plugin_name)
            return {
                "success": False,
                "message": f"工具执行失败: {str(e)}",
                "data": None
            }

    def execute_prompt(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """执行提示 - 接收完整的请求数据"""
        try:
            # 从请求数据中提取提示名称和参数
            prompt_name = request_data.get("prompt_name")
            arguments = request_data.get("arguments", {})

            if not prompt_name:
                return {
                    "success": False,
                    "message": "缺少提示名称",
                    "data": None
                }

            if prompt_name not in self.prompts:
                return {
                    "success": False,
                    "message": f"未知的提示: {prompt_name}",
                    "data": None
                }

            prompt_info = self.prompts[prompt_name]

            # 参数验证
            if prompt_info.validate_params:
                validated_args = self._validate_parameters(arguments, prompt_info.parameters)
                if validated_args is None:
                    return {
                        "success": False,
                        "message": "参数验证失败",
                        "data": None
                    }
                arguments = validated_args

            # 执行提示处理函数
            result = prompt_info.handler(self.plugin_instance, **arguments)

            # 统一的返回格式处理
            return self._standardize_response(result, "提示执行成功")

        except Exception as e:
            logger.error(f"提示执行失败: {str(e)}", self.target_plugin_name)
            return {
                "success": False,
                "message": f"提示执行失败: {str(e)}",
                "data": None
            }

    def _standardize_response(self, result: Any, default_message: str) -> Dict[str, Any]:
        """统一的响应格式处理"""
        if isinstance(result, dict) and "success" in result:
            return result
        else:
            return {
                "success": True,
                "data": result,
                "message": default_message
            }

    def _validate_parameters(self, arguments: Dict[str, Any],
                           parameters) -> Optional[Dict[str, Any]]:
        """验证参数"""
        try:
            if isinstance(parameters, list):
                # 简化格式：参数列表格式
                # 格式：[{"name": "param1", "description": "描述", "required": True}, ...]
                validated = {}

                # 检查必需参数
                for param_def in parameters:
                    param_name = param_def.get("name")
                    is_required = param_def.get("required", False)

                    if is_required and param_name not in arguments:
                        logger.error(f"缺少必需参数: {param_name}", self.target_plugin_name)
                        return None

                # 简化格式下只做基本的必需参数检查，不做类型验证
                for param_name, param_value in arguments.items():
                    validated[param_name] = param_value

                return validated

            elif isinstance(parameters, dict):
                # JSON Schema格式（向后兼容）
                if "properties" not in parameters:
                    return arguments

                properties = parameters["properties"]
                required = parameters.get("required", [])
                validated = {}

                # 检查必需参数
                for req_param in required:
                    if req_param not in arguments:
                        logger.error(f"缺少必需参数: {req_param}", self.target_plugin_name)
                        return None

                # 验证参数类型
                for param_name, param_value in arguments.items():
                    if param_name in properties:
                        param_schema = properties[param_name]
                        param_type = param_schema.get("type")

                        # 基本类型验证
                        if param_type == "string" and not isinstance(param_value, str):
                            logger.error(f"参数 {param_name} 应为字符串类型", self.target_plugin_name)
                            return None
                        elif param_type == "integer" and not isinstance(param_value, int):
                            logger.error(f"参数 {param_name} 应为整数类型", self.target_plugin_name)
                            return None
                        elif param_type == "number" and not isinstance(param_value, (int, float)):
                            logger.error(f"参数 {param_name} 应为数字类型", self.target_plugin_name)
                            return None
                        elif param_type == "boolean" and not isinstance(param_value, bool):
                            logger.error(f"参数 {param_name} 应为布尔类型", self.target_plugin_name)
                            return None

                        # 枚举值验证
                        if "enum" in param_schema and param_value not in param_schema["enum"]:
                            logger.error(f"参数 {param_name} 值不在允许范围内", self.target_plugin_name)
                            return None

                    validated[param_name] = param_value

                return validated
            else:
                # 其他格式，直接返回参数
                return arguments

        except Exception as e:
            logger.error(f"参数验证异常: {str(e)}", self.target_plugin_name)
            return None

    def initialize_with_helper(self, enable_tools: bool = True, enable_prompts: bool = True):
        """使用MCP助手初始化注册"""
        try:
            self._mcp_helper = create_mcp_helper(self.plugin_instance, self.plugin_class_name)

            tools_config = self.get_tools_config() if enable_tools else []
            prompts_config = self.get_prompts_config() if enable_prompts else []

            if tools_config or prompts_config:
                self._mcp_helper.register_with_retry(
                    tools=tools_config,
                    prompts=prompts_config,
                    enable_tools=enable_tools,
                    enable_prompts=enable_prompts
                )

        except Exception as e:
            logger.error(f"初始化失败: {str(e)}", self.target_plugin_name)

    def stop(self):
        """停止并注销所有注册的工具和提示"""
        if self._mcp_helper:
            self._mcp_helper.handle_plugin_stop()


class MCPPluginHelper:
    """MCP插件助手类，简化版本"""

    def __init__(self, plugin_instance, plugin_class_name: str = None):
        self.plugin_instance = plugin_instance
        self.plugin_class_name = plugin_class_name or plugin_instance.__class__.__name__

        # 从插件实例中提取真实的插件名称并设置全局 logger
        self.target_plugin_name = logger.set_plugin_from_instance(plugin_instance)

    def _extract_plugin_name(self) -> Optional[str]:
        """从插件实例中提取真实的插件名称"""
        try:
            if hasattr(self.plugin_instance, '__module__'):
                module_path = self.plugin_instance.__module__
                parts = module_path.split('.')
                if 'plugins' in parts:
                    plugins_index = parts.index('plugins')
                    if plugins_index + 2 < len(parts):
                        return parts[plugins_index + 2]  # 跳过 plugins.v2
                    elif plugins_index + 1 < len(parts):
                        return parts[plugins_index + 1]

            # 如果无法从模块路径提取，使用类名的小写形式
            return self.plugin_class_name.lower()
        except Exception:
            return None

    def register_with_retry(self, tools: List[Dict[str, Any]] = None,
                          prompts: List[Dict[str, Any]] = None,
                          enable_tools: bool = True, enable_prompts: bool = True):
        """带重试机制的注册方法"""
        try:
            if enable_tools and tools:
                self.register_tools(tools)
            if enable_prompts and prompts:
                self.register_prompts(prompts)
            logger.info(f"MCP注册完成", self.target_plugin_name)
        except Exception as e:
            logger.error(f"MCP注册失败: {str(e)}", self.target_plugin_name)

    def register_tools(self, tools: List[Dict[str, Any]]):
        """注册工具"""
        try:

            event_data = {
                "action": "mcp_tool_register",
                "plugin_id": self.plugin_class_name,
                "tools": tools
            }

            eventmanager.send_event(EventType.PluginAction, event_data)
            logger.info(f"已注册 {len(tools)} 个工具", self.target_plugin_name)

        except Exception as e:
            logger.error(f"注册工具失败: {str(e)}", self.target_plugin_name)

    def register_prompts(self, prompts: List[Dict[str, Any]]):
        """注册提示"""
        try:
            event_data = {
                "action": "mcp_prompt_register",
                "plugin_id": self.plugin_class_name,
                "prompts": prompts
            }

            eventmanager.send_event(EventType.PluginAction, event_data)
            logger.info(f"已注册 {len(prompts)} 个提示", self.target_plugin_name)

        except Exception as e:
            logger.error(f"注册提示失败: {str(e)}", self.target_plugin_name)

    def handle_plugin_stop(self):
        """处理插件停止"""
        try:
            # 直接注销所有工具和提示，MCPServer会处理不存在的情况
            self.unregister_tools()
            self.unregister_prompts()
        except Exception as e:
            logger.error(f"停止处理失败: {str(e)}", self.target_plugin_name)

    def unregister_tools(self):
        """注销工具"""
        try:
            event_data = {
                "action": "mcp_tool_unregister",
                "plugin_id": self.plugin_class_name
            }

            eventmanager.send_event(EventType.PluginAction, event_data)
            logger.info(f"已注销工具", self.target_plugin_name)

        except Exception as e:
            logger.error(f"注销工具失败: {str(e)}", self.target_plugin_name)

    def unregister_prompts(self):
        """注销提示"""
        try:
            event_data = {
                "action": "mcp_prompt_unregister",
                "plugin_id": self.plugin_class_name
            }

            eventmanager.send_event(EventType.PluginAction, event_data)
            logger.info(f"已注销提示", self.target_plugin_name)

        except Exception as e:
            logger.error(f"注销提示失败: {str(e)}", self.target_plugin_name)

    def get_mcp_api_endpoints(self) -> List[Dict[str, Any]]:
        """获取MCP API端点"""
        # 创建包装函数来处理FastAPI请求
        def mcp_tool_wrapper(request_data: dict) -> dict:
            """MCP工具执行包装函数"""
            return self.plugin_instance._execute_mcp_tool(request_data)

        def mcp_prompt_wrapper(request_data: dict) -> dict:
            """MCP提示执行包装函数"""
            return self.plugin_instance._execute_mcp_prompt(request_data)

        return [
            {
                "path": "/mcp_tool_execute",
                "endpoint": mcp_tool_wrapper,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行MCP工具"
            },
            {
                "path": "/mcp_prompt_execute",
                "endpoint": mcp_prompt_wrapper,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "执行MCP提示"
            }
        ]


def create_mcp_helper(plugin_instance, plugin_class_name: str = None):
    """创建MCP助手实例"""
    try:
        return MCPPluginHelper(plugin_instance, plugin_class_name)
    except Exception as e:
        # 这里使用全局 logger，先设置插件名称
        plugin_name = logger.set_plugin_from_instance(plugin_instance)
        logger.error(f"创建MCP助手失败: {str(e)}", plugin_name)
        return None


def auto_discover_mcp_methods(plugin_instance) -> MCPPluginRegistry:
    """自动发现插件中的MCP方法"""
    registry = MCPPluginRegistry(plugin_instance)

    # 扫描插件实例的所有方法
    for attr_name in dir(plugin_instance):
        attr = getattr(plugin_instance, attr_name)

        # 检查是否有MCP工具装饰器
        if hasattr(attr, '_mcp_tool_info'):
            tool_info = attr._mcp_tool_info
            registry.register_tool(tool_info)

        # 检查是否有MCP提示装饰器
        if hasattr(attr, '_mcp_prompt_info'):
            prompt_info = attr._mcp_prompt_info
            registry.register_prompt(prompt_info)

    return registry


def mcp_tool(name: str, description: str, parameters = None,
             validate_params: bool = True):
    """MCP工具装饰器

    Args:
        name: 工具名称
        description: 工具描述
        parameters: 参数定义，支持两种格式：
            1. 简化格式（推荐）：[{"name": "param1", "description": "描述", "required": True, "type": "string", "enum": [...] }, ...]
            2. JSON Schema格式：{"type": "object", "properties": {...}, "required": [...]}
        validate_params: 是否验证参数
    """
    if parameters is None:
        parameters = []

    def decorator(func: Callable) -> Callable:
        # 创建工具信息对象
        tool_info = MCPToolInfo(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
            validate_params=validate_params
        )

        # 将工具信息附加到函数上
        func._mcp_tool_info = tool_info

        return func

    return decorator


def mcp_prompt(name: str, description: str, parameters = None,
               validate_params: bool = True):
    """MCP提示装饰器

    Args:
        name: 提示名称
        description: 提示描述
        parameters: 参数定义，支持两种格式：
            1. 简化格式（推荐）：[{"name": "param1", "description": "描述", "required": True}, ...]
            2. JSON Schema格式：{"type": "object", "properties": {...}, "required": [...]}
        validate_params: 是否验证参数
    """
    if parameters is None:
        parameters = []

    def decorator(func: Callable) -> Callable:
        # 创建提示信息对象
        prompt_info = MCPPromptInfo(
            name=name,
            description=description,
            parameters=parameters,
            handler=func,
            validate_params=validate_params
        )

        # 将提示信息附加到函数上
        func._mcp_prompt_info = prompt_info

        return func

    return decorator


class MCPDecoratorMixin:
    """MCP装饰器混入类，为插件提供装饰器支持"""

    # MCP功能开关，插件可以直接设置这些属性
    _enable_tools: bool = True
    _enable_prompts: bool = True

    def init_mcp_decorators(self):
        """初始化MCP装饰器支持"""
        try:
            # 自动发现装饰器标记的方法
            self.mcp_registry = auto_discover_mcp_methods(self)

            # 设置执行方法
            self._execute_mcp_tool = self.mcp_registry.execute_tool
            self._execute_mcp_prompt = self.mcp_registry.execute_prompt

            # 注册事件监听器
            self._register_mcp_event_listener()

            # 异步尝试立即注册（如果MCPServer已经就绪）
            self._async_register_mcp()

            logger.info(f"MCP装饰器初始化完成")

        except Exception as e:
            logger.error(f"MCP装饰器初始化失败: {str(e)}")

    def _register_mcp_event_listener(self):
        """注册MCP事件监听器"""
        try:
            if eventmanager and EventType:
                # 创建一个动态的事件处理器，其__qualname__包含插件类名
                plugin_class_name = self.__class__.__name__

                # 创建一个动态函数，其__qualname__会被识别为插件方法
                def dynamic_handler(event):
                    return self._handle_mcp_event(event)

                # 修改函数的__qualname__，让事件系统识别为插件方法
                dynamic_handler.__qualname__ = f"{plugin_class_name}._handle_mcp_event"
                dynamic_handler.__name__ = "_handle_mcp_event"

                # 监听MCP服务器就绪事件
                eventmanager.add_event_listener(EventType.PluginAction, dynamic_handler)

                # 保存处理器引用，用于后续注销
                self._mcp_event_handler = dynamic_handler

                logger.debug(f"已注册MCP事件监听器: {dynamic_handler.__qualname__}")
        except Exception as e:
            logger.error(f"注册MCP事件监听器失败: {str(e)}")

    def _handle_mcp_event(self, event):
        """处理MCP相关事件"""
        try:
            logger.info(f"收到事件: {event.event_type.value}")
            if not hasattr(event, 'event_data') or not event.event_data:
                logger.debug("事件数据为空，跳过处理")
                return

            event_data = event.event_data
            action = event_data.get("action")
            logger.debug(f"事件动作: {action}")

            if action == "mcp_server_ready":
                logger.info(f"收到MCP服务器就绪事件，开始注册")
                # 异步执行注册，避免阻塞主线程
                self._async_register_mcp()
            else:
                logger.debug(f"忽略不相关的事件动作: {action}")

        except Exception as e:
            logger.error(f"处理MCP事件失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())

    def _async_register_mcp(self):
        """异步执行MCP注册，避免阻塞主线程"""

        def register_worker():
            try:
                self._try_register_mcp()
            except Exception as e:
                logger.error(f"异步MCP注册失败: {str(e)}")

        # 使用守护线程，避免影响主程序退出
        thread = threading.Thread(target=register_worker, daemon=True)
        thread.start()
        logger.debug(f"已启动异步MCP注册线程")

    def _try_register_mcp(self, retry_count: int = 0):
        """尝试注册MCP工具和提示"""
        max_retries = 3
        try:
            if hasattr(self, 'mcp_registry'):
                # 检查是否有工具或提示需要注册
                tools_count = len(self.mcp_registry.tools)
                prompts_count = len(self.mcp_registry.prompts)

                if tools_count == 0 and prompts_count == 0:
                    logger.debug(f"没有工具或提示需要注册")
                    return

                self.mcp_registry.initialize_with_helper(
                    enable_tools=self._enable_tools,
                    enable_prompts=self._enable_prompts
                )
                logger.info(f"MCP注册完成 - {tools_count}个工具, {prompts_count}个提示")

        except Exception as e:
            logger.error(f"MCP注册失败 (尝试 {retry_count + 1}/{max_retries + 1}): {str(e)}")

            # 如果还有重试次数，异步延迟后重试
            if retry_count < max_retries:
                self._schedule_retry(retry_count + 1)

    def _schedule_retry(self, retry_count: int):
        """调度重试，使用异步方式避免阻塞"""
        import time

        delay = 2 ** (retry_count - 1)  # 指数退避：1秒、2秒、4秒

        def delayed_retry():
            try:
                time.sleep(delay)
                self._try_register_mcp(retry_count)
            except Exception as e:
                logger.error(f"重试调度失败: {str(e)}")

        # 使用守护线程执行延迟重试
        thread = threading.Thread(target=delayed_retry, daemon=True)
        thread.start()
        logger.info(f"将在 {delay} 秒后重试注册 (第{retry_count}次重试)")

    def stop_mcp_decorators(self):
        """停止MCP装饰器支持"""
        try:
            # 注销事件监听器
            if eventmanager and EventType and hasattr(self, '_mcp_event_handler'):
                try:
                    eventmanager.remove_event_listener(EventType.PluginAction, self._mcp_event_handler)
                    logger.debug(f"已注销MCP事件监听器")
                except Exception as e:
                    logger.warning(f"注销MCP事件监听器失败: {str(e)}")

            # 停止MCP注册表
            if hasattr(self, 'mcp_registry'):
                self.mcp_registry.stop()
                logger.info(f"MCP装饰器已停止")
        except Exception as e:
            logger.error(f"停止MCP装饰器失败: {str(e)}")

    def get_mcp_api_endpoints(self) -> List[Dict[str, Any]]:
        """获取MCP相关的API端点，供插件的get_api方法调用"""
        if hasattr(self, 'mcp_registry') and self.mcp_registry._mcp_helper:
            return self.mcp_registry._mcp_helper.get_mcp_api_endpoints()
        return []