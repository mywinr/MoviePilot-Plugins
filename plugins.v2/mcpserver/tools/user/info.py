import json
import logging
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class UserInfoTool(BaseTool):
    async def execute(
        self, tool_name: str, arguments: dict
    ) -> list[types.TextContent]:
        if tool_name == "user-info":
            return await self._get_current_user()
        elif tool_name == "get-user":
            return await self._get_user_by_name(arguments.get("username"))
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _get_current_user(self) -> list[types.TextContent]:
        """获取当前用户信息"""
        response = await self._make_request(
            method="GET",
            endpoint="/api/v1/user/current"
        )
        return self._format_user_response(response, "当前用户信息")

    async def _get_user_by_name(
        self, username: str
    ) -> list[types.TextContent]:
        """获取指定用户信息"""
        if not username:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供用户名"
                )
            ]

        response = await self._make_request(
            method="GET",
            endpoint=f"/api/v1/user/{username}"
        )
        return self._format_user_response(response, f"用户 {username} 的信息")

    def _format_user_response(
        self, response: dict, title: str
    ) -> list[types.TextContent]:
        """格式化用户信息响应"""
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取用户信息失败: {response['error']}"
                )
            ]

        user_info = []
        for key, value in response.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            user_info.append(f"{key}: {value}")

        return [
            types.TextContent(
                type="text",
                text=f"{title}:\n" + "\n".join(user_info)
            )
        ]

    @property
    def tool_info(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="user-info",
                description="获取当前用户信息",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="get-user",
                description="获取指定用户信息",
                inputSchema={
                    "type": "object",
                    "required": ["username"],
                    "properties": {
                        "username": {
                            "type": "string",
                            "description": "要查询的用户名"
                        }
                    },
                },
            )
        ]
