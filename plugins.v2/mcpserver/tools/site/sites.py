import json
import logging
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class GetSitesTool(BaseTool):
    async def execute(
        self, tool_name: str, arguments: dict
    ) -> list[types.TextContent]:
        if tool_name == "get-sites":
            return await self._get_sites()
        elif tool_name == "get-site-data":
            site_id = arguments.get("site_id")
            return await self._get_site_data(site_id)
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _get_site_data(self, site_id: str) -> list[types.TextContent]:
        """获取指定站点数据"""
        if not site_id:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供站点ID"
                )
            ]
        # 获取站点数据
        response = await self._make_request(
            method="GET",
            endpoint=f"/api/v1/site/{site_id}"
        )
        # 检查是否有错误
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取站点数据失败: {response['error']}"
                )
            ]
        # 格式化站点数据
        site_data = []
        for key, value in response.items():
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False, indent=2)
            site_data.append(f"{key}: {value}")
        return [
            types.TextContent(
                type="text",
                text="站点数据:\n" + "\n".join(site_data)
            )
        ]

    async def _get_sites(self) -> list[types.TextContent]:
        """获取所有站点信息"""
        # 获取站点列表
        response = await self._make_request(
            method="GET",
            endpoint="/api/v1/site/"
        )

        # 检查是否有错误
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取站点列表失败: {response['error']}"
                )
            ]

        # 格式化站点信息
        if not response:
            return [
                types.TextContent(
                    type="text",
                    text="暂无站点信息"
                )
            ]

        # 使用列表推导式简化代码
        sites_info = [
            json.dumps(site, ensure_ascii=False, indent=2)
            for site in response
        ]

        return [
            types.TextContent(
                type="text",
                text="站点列表:\n" + "\n".join(sites_info)
            )
        ]

    @property
    def tool_info(self) -> list[types.Tool]:
        return [
            types.Tool(
                name="get-sites",
                description="获取所有站点信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        # 不再要求显式传入 tool 参数
                    },
                },
            ),
            types.Tool(
                name="get-site-data",
                description="根据site_id获取站点数据",
                inputSchema={
                    "type": "object",
                    "required": ["site_id"],
                    "properties": {
                        "site_id": {
                            "type": "string",
                            "description": "站点ID"
                        }
                    },
                },
            )
        ]
