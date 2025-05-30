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
        logger.debug(f"[BaseTool] 开始发送API请求")
        logger.debug(f"[BaseTool] 请求方法: {method}")
        logger.debug(f"[BaseTool] 请求端点: {endpoint}")
        logger.debug(f"[BaseTool] 请求参数: {kwargs}")

        # 确保json参数被正确传递为json_data
        if 'json' in kwargs and 'json_data' not in kwargs:
            kwargs['json_data'] = kwargs.pop('json')
            logger.debug(f"[BaseTool] 转换json参数为json_data")

        # 获取访问令牌
        access_token = self.token_manager.get_access_token() if self.token_manager else None
        logger.debug(f"[BaseTool] 访问令牌: {'已设置' if access_token else '未设置'}")
        if access_token:
            logger.debug(f"[BaseTool] 令牌长度: {len(access_token)}")

        try:
            logger.debug(f"[BaseTool] 调用make_request函数...")
            result = await make_request(
                method=method,
                endpoint=endpoint,
                access_token=access_token,
                **kwargs
            )
            logger.debug(f"[BaseTool] make_request返回结果: {result}")
            logger.debug(f"[BaseTool] 返回结果类型: {type(result)}")
            return result
        except Exception as e:
            logger.error(f"[BaseTool] make_request调用异常: {str(e)}")
            import traceback
            logger.debug(f"[BaseTool] 异常堆栈: {traceback.format_exc()}")
            raise
