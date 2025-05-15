import logging
import os
import sys
from typing import List, Dict, Any
import mcp.types as types

# 添加父目录到路径，以便导入utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
# 现在可以导入utils模块
from utils import make_request


# Configure logging
logger = logging.getLogger(__name__)


class BaseTool:
    def __init__(self, token_manager=None):
        self.token_manager = token_manager
        self._tool_info_cache = None  # 缓存工具信息

    async def execute(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> List[
        types.TextContent | types.ImageContent | types.EmbeddedResource
    ]:
        """
        执行工具逻辑

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        raise NotImplementedError("Tool must implement execute method")

    @property
    def tool_info(self) -> types.Tool | list[types.Tool]:
        """返回工具的描述信息

        Returns:
            types.Tool | list[types.Tool]: 单个工具或工具列表
        """
        raise NotImplementedError("Tool must implement tool_info property")

    async def _make_request(self, method: str, endpoint: str, **kwargs):
        """发送API请求的辅助方法"""
        # 确保json参数被正确传递为json_data
        if 'json' in kwargs and 'json_data' not in kwargs:
            kwargs['json_data'] = kwargs.pop('json')

        return await make_request(
            method=method,
            endpoint=endpoint,
            access_token=(
                self.token_manager.get_access_token()
                if self.token_manager else None
            ),
            **kwargs
        )
