from typing import List, Dict, Any
import mcp.types as types
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import make_request
import logging

# Configure logging
logger = logging.getLogger(__name__)

class BaseTool:
    def __init__(self, token_manager=None):
        self.token_manager = token_manager
        self._tool_info_cache = None  # 缓存工具信息
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> List[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        """执行工具逻辑"""
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
        return await make_request(
            method=method,
            endpoint=endpoint,
            access_token=self.token_manager.get_access_token() if self.token_manager else None,
            **kwargs
        )
