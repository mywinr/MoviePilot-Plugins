"""
插件工具代理
负责代理执行动态注册的插件工具
"""
import logging
import asyncio
import json
from typing import Dict, List, Any
import mcp.types as types
from .base import BaseTool
from .plugin_registry import PluginToolInfo

logger = logging.getLogger(__name__)


class PluginToolProxy(BaseTool):
    """插件工具代理"""
    
    def __init__(self, tool_info: PluginToolInfo, token_manager=None):
        super().__init__(token_manager)
        self.tool_info_data = tool_info
        self._timeout = 30  # 默认超时时间30秒
        
    @property
    def tool_info(self) -> types.Tool:
        """返回工具信息"""
        return self.tool_info_data.to_mcp_tool()
    
    async def execute(self, tool_name: str, arguments: dict) -> List[types.TextContent]:
        """
        执行插件工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            执行结果
        """
        try:
            logger.debug(f"[PluginToolProxy] 开始执行插件工具")
            logger.debug(f"[PluginToolProxy] 插件ID: {self.tool_info_data.plugin_id}")
            logger.debug(f"[PluginToolProxy] 工具名称: {tool_name}")
            logger.debug(f"[PluginToolProxy] 工具参数: {arguments}")
            logger.debug(f"[PluginToolProxy] API端点: {self.tool_info_data.api_endpoint}")
            logger.debug(f"[PluginToolProxy] 工具参数定义: {self.tool_info_data.parameters}")

            logger.info(f"执行插件工具: {self.tool_info_data.plugin_id}.{tool_name}")

            # 验证参数
            logger.debug(f"[PluginToolProxy] 开始验证参数...")
            validation_result = self._validate_arguments(arguments)
            logger.debug(f"[PluginToolProxy] 参数验证结果: {validation_result}")

            if not validation_result["valid"]:
                logger.error(f"[PluginToolProxy] 参数验证失败: {validation_result['error']}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"参数验证失败: {validation_result['error']}"
                    )
                ]

            # 执行工具
            if self.tool_info_data.api_endpoint:
                logger.debug(f"[PluginToolProxy] 通过API端点调用工具...")
                # 通过API端点调用
                result = await self._execute_via_api(tool_name, arguments)
                logger.debug(f"[PluginToolProxy] API调用结果: {result}")
            else:
                logger.error(f"[PluginToolProxy] 工具配置错误: 未指定API端点")
                return [
                    types.TextContent(
                        type="text",
                        text="工具配置错误: 未指定API端点"
                    )
                ]

            # 格式化返回结果
            logger.debug(f"[PluginToolProxy] 开始格式化结果...")
            formatted_result = self._format_result(result)
            logger.debug(f"[PluginToolProxy] 格式化后的结果: {formatted_result}")
            return formatted_result
            
        except asyncio.TimeoutError:
            logger.error(f"插件工具执行超时: {tool_name}")
            return [
                types.TextContent(
                    type="text",
                    text=f"工具执行超时({self._timeout}秒)"
                )
            ]
        except Exception as e:
            logger.error(f"执行插件工具时发生异常: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"工具执行失败: {str(e)}"
                )
            ]
    
    async def _execute_via_api(self, tool_name: str, arguments: dict) -> dict:
        """通过API端点执行工具"""
        try:
            logger.debug(f"[PluginToolProxy] 开始API调用")

            # 构建API请求
            endpoint = self.tool_info_data.api_endpoint
            logger.debug(f"[PluginToolProxy] API端点: {endpoint}")

            # 构建请求数据，包含工具名称和参数
            request_data = {
                "tool_name": tool_name,
                "arguments": arguments
            }
            logger.debug(f"[PluginToolProxy] 请求数据: {request_data}")
            logger.debug(f"[PluginToolProxy] 超时时间: {self._timeout}秒")

            # 发送API请求
            logger.debug(f"[PluginToolProxy] 发送POST请求到: {endpoint}")
            response = await asyncio.wait_for(
                self._make_request(
                    method="POST",
                    endpoint=endpoint,
                    json_data=request_data
                ),
                timeout=self._timeout
            )

            logger.debug(f"[PluginToolProxy] 收到API响应: {response}")
            logger.debug(f"[PluginToolProxy] 响应类型: {type(response)}")

            if response and response.get("success"):
                logger.debug(f"[PluginToolProxy] API调用成功")
                return response
            else:
                error_msg = response.get("message", "API调用失败") if response else "API响应为空"
                logger.error(f"[PluginToolProxy] API调用失败: {error_msg}")
                logger.debug(f"[PluginToolProxy] 失败响应详情: {response}")
                return {
                    "success": False,
                    "message": error_msg,
                    "data": None
                }

        except asyncio.TimeoutError as e:
            logger.error(f"[PluginToolProxy] API调用超时: {str(e)}")
            return {
                "success": False,
                "message": f"API调用超时({self._timeout}秒)",
                "data": None
            }
        except Exception as e:
            logger.error(f"[PluginToolProxy] API调用异常: {str(e)}")
            import traceback
            logger.debug(f"[PluginToolProxy] 异常堆栈: {traceback.format_exc()}")
            return {
                "success": False,
                "message": f"API调用异常: {str(e)}",
                "data": None
            }
    

    
    def _validate_arguments(self, arguments: dict) -> Dict[str, Any]:
        """
        验证工具参数
        
        Args:
            arguments: 工具参数
            
        Returns:
            验证结果
        """
        try:
            parameters = self.tool_info_data.parameters
            
            # 检查必需参数
            required_params = parameters.get("required", [])
            for param in required_params:
                if param not in arguments:
                    return {
                        "valid": False,
                        "error": f"缺少必需参数: {param}"
                    }
            
            # 检查参数类型（简单验证）
            properties = parameters.get("properties", {})
            for param_name, param_value in arguments.items():
                if param_name in properties:
                    param_def = properties[param_name]
                    expected_type = param_def.get("type")
                    
                    # 简单的类型检查
                    if expected_type == "string" and not isinstance(param_value, str):
                        return {
                            "valid": False,
                            "error": f"参数 {param_name} 应该是字符串类型"
                        }
                    elif expected_type == "integer" and not isinstance(param_value, int):
                        return {
                            "valid": False,
                            "error": f"参数 {param_name} 应该是整数类型"
                        }
                    elif expected_type == "number" and not isinstance(param_value, (int, float)):
                        return {
                            "valid": False,
                            "error": f"参数 {param_name} 应该是数字类型"
                        }
                    elif expected_type == "boolean" and not isinstance(param_value, bool):
                        return {
                            "valid": False,
                            "error": f"参数 {param_name} 应该是布尔类型"
                        }
            
            return {"valid": True}
            
        except Exception as e:
            return {
                "valid": False,
                "error": f"参数验证异常: {str(e)}"
            }
    
    def _format_result(self, result: dict) -> List[types.TextContent]:
        """
        格式化执行结果
        
        Args:
            result: 执行结果
            
        Returns:
            格式化后的结果
        """
        try:
            if result.get("success"):
                # 成功结果
                data = result.get("data")
                message = result.get("message", "执行成功")
                
                if isinstance(data, str):
                    # 数据是字符串，直接返回
                    text = data
                elif isinstance(data, (dict, list)):
                    # 数据是复杂对象，格式化为JSON
                    text = f"{message}\n\n结果数据:\n{json.dumps(data, ensure_ascii=False, indent=2)}"
                else:
                    # 其他类型，转换为字符串
                    text = f"{message}\n\n结果: {str(data)}"
                
                return [
                    types.TextContent(
                        type="text",
                        text=text
                    )
                ]
            else:
                # 失败结果
                error_msg = result.get("message", "执行失败")
                return [
                    types.TextContent(
                        type="text",
                        text=f"执行失败: {error_msg}"
                    )
                ]
                
        except Exception as e:
            logger.error(f"格式化结果时发生异常: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"结果格式化失败: {str(e)}"
                )
            ]
    
    def set_timeout(self, timeout: int):
        """设置执行超时时间"""
        self._timeout = timeout
        logger.debug(f"设置工具执行超时时间: {timeout}秒")
