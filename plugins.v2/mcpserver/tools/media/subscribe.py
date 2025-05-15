import json
import logging
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class SubscribeTool(BaseTool):
    async def execute(
        self, tool_name: str, _: dict
    ) -> list[types.TextContent]:
        if tool_name == "subscribe":
            return await self._subscribe()
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _subscribe(self) -> list[types.TextContent]:
        """获取订阅资源"""
        response = await self._make_request(
            method="GET",
            endpoint="/api/v1/subscribe/"
        )

        # 检查是否有错误
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取订阅资源失败: {response['error']}"
                )
            ]

        # 格式化站点信息
        if not response:
            return [
                types.TextContent(
                    type="text",
                    text="暂无订阅资源"
                )
            ]

        # 使用列表推导式简化代码
        subscribe_info = [
            json.dumps(item, ensure_ascii=False, indent=2)
            for item in response
        ]

        return [
            types.TextContent(
                type="text",
                text="订阅资源列表:\n" + "\n".join(subscribe_info)
            )
        ]

    @property
    def tool_info(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="subscribe",
                description="当前所有已订阅的资源，包括电影、电视剧、动漫等",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            )
        ]
