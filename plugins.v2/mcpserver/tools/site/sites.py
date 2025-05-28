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
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
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

        # 只保留指定字段的站点信息
        filtered_sites = []
        for site in response:
            filtered_site = {
                key: site.get(key)
                for key in ['id', 'name', 'pri']
                if key in site
            }
            filtered_sites.append(filtered_site)

        sites_info = [
            json.dumps(site, ensure_ascii=False, indent=2)
            for site in filtered_sites
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
            )
        ]
