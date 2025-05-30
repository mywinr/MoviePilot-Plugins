"""
插件提示代理
负责执行动态注册的插件提示
"""

import asyncio
import logging
from typing import Dict, Any, Optional
import mcp.types as types
import os
import sys
from .plugin_registry import PluginPromptInfo

parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from utils import make_request

logger = logging.getLogger(__name__)


class PluginPromptProxy:
    """插件提示代理"""

    def __init__(self, prompt_info: PluginPromptInfo, token_manager=None):
        self.prompt_info_data = prompt_info
        self.token_manager = token_manager
        self._timeout = 30  # 默认30秒超时

    async def get_prompt(
        self, prompt_name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """
        获取插件提示

        Args:
            prompt_name: 提示名称
            arguments: 提示参数

        Returns:
            提示结果
        """
        try:
            logger.info(
                f"获取插件提示: {self.prompt_info_data.plugin_id}.{prompt_name}"
            )

            # 验证参数
            validation_result = self._validate_arguments(arguments or {})
            if not validation_result["valid"]:
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text",
                                text=f"参数验证失败: {validation_result['error']}",
                            ),
                        )
                    ]
                )

            # 通过API端点调用
            result = await self._execute_via_api(prompt_name, arguments or {})

            # 格式化返回结果
            return self._format_result(result)

        except Exception as e:
            logger.error(f"获取插件提示失败: {str(e)}")
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text", text=f"提示获取失败: {str(e)}"
                        ),
                    )
                ]
            )

    async def _execute_via_api(self, prompt_name: str, arguments: dict) -> dict:
        """通过API端点执行提示"""
        try:
            # 构建API请求
            endpoint = self.prompt_info_data.api_endpoint

            # 构建请求数据，包含提示名称和参数
            request_data = {"prompt_name": prompt_name, "arguments": arguments}

            # 获取访问令牌
            access_token = None
            if self.token_manager:
                access_token = self.token_manager.get_access_token()

            # 发送API请求
            response = await asyncio.wait_for(
                make_request(
                    method="POST",
                    endpoint=endpoint,
                    access_token=access_token,
                    json_data=request_data,
                ),
                timeout=self._timeout,
            )

            if response and response.get("success"):
                return response
            else:
                error_msg = (
                    response.get("message", "API调用失败")
                    if response
                    else "API响应为空"
                )
                return {"success": False, "message": error_msg, "data": None}

        except Exception as e:
            logger.error(f"API调用失败: {str(e)}")
            return {"success": False, "message": f"API调用异常: {str(e)}", "data": None}

    def _validate_arguments(self, arguments: dict) -> Dict[str, Any]:
        """
        验证提示参数

        Args:
            arguments: 提示参数

        Returns:
            验证结果
        """
        try:
            # 检查必需参数
            for arg_def in self.prompt_info_data.arguments:
                arg_name = arg_def["name"]
                is_required = arg_def.get("required", False)

                if is_required and arg_name not in arguments:
                    return {"valid": False, "error": f"缺少必需参数: {arg_name}"}

            return {"valid": True}

        except Exception as e:
            return {"valid": False, "error": f"参数验证异常: {str(e)}"}

    def _format_result(self, result: dict) -> types.GetPromptResult:
        """
        格式化提示结果

        Args:
            result: API返回结果

        Returns:
            格式化的提示结果
        """
        try:
            if not result.get("success"):
                error_message = result.get("message", "提示执行失败")
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(type="text", text=error_message),
                        )
                    ]
                )

            data = result.get("data", {})

            # 检查数据格式
            if not isinstance(data, dict) or "messages" not in data:
                return types.GetPromptResult(
                    messages=[
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text", text="提示数据格式错误"
                            ),
                        )
                    ]
                )

            # 转换消息格式
            messages = []
            for msg_data in data["messages"]:
                try:
                    role = msg_data.get("role", "user")
                    content_data = msg_data.get("content", {})

                    if content_data.get("type") == "text":
                        content = types.TextContent(
                            type="text", text=content_data.get("text", "")
                        )
                    else:
                        # 默认处理为文本内容
                        content = types.TextContent(type="text", text=str(content_data))

                    messages.append(types.PromptMessage(role=role, content=content))

                except Exception as e:
                    logger.error(f"转换消息格式失败: {str(e)}")
                    # 添加错误消息
                    messages.append(
                        types.PromptMessage(
                            role="user",
                            content=types.TextContent(
                                type="text", text=f"消息格式转换失败: {str(e)}"
                            ),
                        )
                    )

            if not messages:
                # 如果没有有效消息，返回默认消息
                messages.append(
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(type="text", text="提示内容为空"),
                    )
                )

            return types.GetPromptResult(messages=messages)

        except Exception as e:
            logger.error(f"格式化提示结果失败: {str(e)}")
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text", text=f"格式化结果失败: {str(e)}"
                        ),
                    )
                ]
            )

    def set_timeout(self, timeout: int):
        """设置超时时间"""
        self._timeout = timeout
