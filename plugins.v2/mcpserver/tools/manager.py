from typing import Dict, Type, List
import logging
import mcp.types as types

from .base import BaseTool
from .user.info import UserInfoTool
from .site.sites import GetSitesTool
from .media.subscribe import SubscribeTool
from .media.download import MovieDownloadTool
from .media.recognize import MediaRecognizeTool
from .database.pt_stats import PTStatsTool


# Configure logging
logger = logging.getLogger(__name__)


class ToolManager:
    """工具管理器，负责注册和管理所有可用的工具"""

    def __init__(self, token_manager=None):
        self.token_manager = token_manager
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._register_tools()

    def _register_tools(self):
        """注册所有可用的工具"""
        tools = [
            UserInfoTool,
            GetSitesTool,
            SubscribeTool,
            MovieDownloadTool,
            MediaRecognizeTool,
            PTStatsTool
        ]

        for tool_class in tools:
            tool = tool_class(self.token_manager)
            tool_infos = tool.tool_info
            if isinstance(tool_infos, list):
                # 如果是工具列表，注册所有工具
                for tool_info in tool_infos:
                    self._tools[tool_info.name] = tool_class
                    logger.info(f"注册工具: {tool_info.name}")
            else:
                # 单个工具直接注册
                self._tools[tool_infos.name] = tool_class
                logger.info(f"注册工具: {tool_infos.name}")

    def list_tools(self) -> List[types.Tool]:
        """列出所有可用的工具"""
        tools = []
        # 创建每个工具类的实例并获取工具信息
        for tool_class in set(self._tools.values()):  # 使用set去重
            tool = tool_class(self.token_manager)
            tool_infos = tool.tool_info

            # 处理单个工具或工具列表
            if isinstance(tool_infos, list):
                tools.extend(tool_infos)
            else:
                tools.append(tool_infos)

        logger.debug(f"可用工具列表: {[tool.name for tool in tools]}")
        return tools

    async def call_tool(
        self, name: str, arguments: dict
    ) -> List[
        types.TextContent | types.ImageContent | types.EmbeddedResource
    ]:
        """调用指定的工具"""
        if name not in self._tools:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{name}'"
                )
            ]

        tool = self._tools[name](self.token_manager)
        return await tool.execute(name, arguments)
