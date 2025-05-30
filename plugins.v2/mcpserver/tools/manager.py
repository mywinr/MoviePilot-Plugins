from typing import Dict, Type, List
import logging
import mcp.types as types
import os
import sys
from pathlib import Path

from .base import BaseTool
from .user.info import UserInfoTool
from .site.sites import GetSitesTool
from .media.subscribe import SubscribeTool
from .media.download import MovieDownloadTool
from .media.recognize import MediaRecognizeTool
from .database.pt_stats import PTStatsTool
from .plugin_registry import PluginToolRegistry
from .plugin_proxy import PluginToolProxy

# 添加父目录到路径以导入utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Configure logging
logger = logging.getLogger(__name__)


class ToolManager:
    """工具管理器，负责注册和管理所有可用的工具"""

    def __init__(self, token_manager=None):
        self.token_manager = token_manager
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._plugin_registry = PluginToolRegistry()
        self._state_sync_enabled = False
        self._register_tools()
        self._setup_state_sync()

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

        # 添加内置工具
        for tool_class in set(self._tools.values()):  # 使用set去重
            tool = tool_class(self.token_manager)
            tool_infos = tool.tool_info

            # 处理单个工具或工具列表
            if isinstance(tool_infos, list):
                tools.extend(tool_infos)
            else:
                tools.append(tool_infos)

        # 添加动态注册的插件工具
        plugin_tools = self._plugin_registry.list_registered_tools()
        tools.extend(plugin_tools)

        logger.debug(f"可用工具列表: {[tool.name for tool in tools]}")
        return tools

    async def call_tool(
        self, name: str, arguments: dict
    ) -> List[
        types.TextContent | types.ImageContent | types.EmbeddedResource
    ]:
        """调用指定的工具"""
        logger.debug(f"[ToolManager] 开始调用工具")
        logger.debug(f"[ToolManager] 工具名称: {name}")
        logger.debug(f"[ToolManager] 工具参数: {arguments}")
        logger.debug(f"[ToolManager] 内置工具列表: {list(self._tools.keys())}")

        # 首先检查是否是内置工具
        if name in self._tools:
            logger.debug(f"[ToolManager] 找到内置工具: {name}")
            tool = self._tools[name](self.token_manager)
            logger.debug(f"[ToolManager] 创建内置工具实例: {tool}")
            return await tool.execute(name, arguments)

        # 检查是否是动态注册的插件工具
        logger.debug(f"[ToolManager] 检查插件工具注册表...")
        plugin_tool_info = self._plugin_registry.get_tool_info(name)
        logger.debug(f"[ToolManager] 插件工具信息: {plugin_tool_info}")

        if plugin_tool_info:
            logger.debug(f"[ToolManager] 找到插件工具: {name}")
            logger.debug(f"[ToolManager] 插件ID: {plugin_tool_info.plugin_id}")
            logger.debug(f"[ToolManager] API端点: {plugin_tool_info.api_endpoint}")
            tool_proxy = PluginToolProxy(plugin_tool_info, self.token_manager)
            logger.debug(f"[ToolManager] 创建插件工具代理: {tool_proxy}")
            return await tool_proxy.execute(name, arguments)

        # 工具不存在
        logger.error(f"[ToolManager] 未找到工具: {name}")
        logger.debug(f"[ToolManager] 可用的插件工具: {self._plugin_registry.get_all_tool_names()}")
        return [
            types.TextContent(
                type="text",
                text=f"错误：未知的工具 '{name}'"
            )
        ]

    def register_plugin_tools(self, plugin_id: str, tools: List[dict]) -> dict:
        """注册插件工具"""
        logger.info(f"注册插件工具: {plugin_id}, 工具数量: {len(tools)}")
        return self._plugin_registry.register_tools(plugin_id, tools)

    def unregister_plugin_tools(self, plugin_id: str) -> dict:
        """注销插件工具"""
        logger.info(f"注销插件工具: {plugin_id}")
        return self._plugin_registry.unregister_plugin_tools(plugin_id)

    def get_plugin_registry_stats(self) -> dict:
        """获取插件工具注册统计"""
        return self._plugin_registry.get_registry_stats()

    def get_plugin_tools(self, plugin_id: str) -> List[str]:
        """获取插件注册的工具列表"""
        return self._plugin_registry.get_plugin_tools(plugin_id)

    def _setup_state_sync(self):
        """设置状态同步"""
        try:
            from utils.state_sync import register_sync_target, start_state_monitoring

            # 获取插件工具文件路径
            current_dir = Path(os.path.dirname(__file__)).parent
            tools_file = current_dir / "plugin_tools.json"

            # 注册状态同步目标
            register_sync_target(
                name="plugin_tools",
                file_path=tools_file,
                memory_getter=self._get_memory_state,
                memory_setter=self._set_memory_state,
                sync_interval=30  # 30秒检查一次
            )

            # 启动状态监控
            start_state_monitoring()
            self._state_sync_enabled = True
            logger.info("插件工具状态同步已启用")

        except Exception as e:
            logger.warning(f"设置状态同步失败: {e}")
            self._state_sync_enabled = False

    def _get_memory_state(self) -> Dict[str, any]:
        """获取当前内存中的插件工具状态"""
        try:
            # 获取所有插件的工具信息
            memory_state = {}

            # 遍历插件注册表中的所有插件
            for plugin_id in self._plugin_registry._plugin_tools.keys():
                tools = self._plugin_registry.get_plugin_tools(plugin_id)
                if tools:
                    # 构建与文件格式一致的数据结构
                    tool_infos = []
                    for tool_name in tools:
                        tool_info = self._plugin_registry.get_tool_info(tool_name)
                        if tool_info:
                            tool_infos.append(tool_info.to_dict())

                    memory_state[plugin_id] = {
                        "tools": tool_infos,
                        "registered_at": tool_infos[0].get("registered_at") if tool_infos else None
                    }

            return memory_state

        except Exception as e:
            logger.error(f"获取内存状态失败: {e}")
            return {}

    def _set_memory_state(self, file_state: Dict[str, any]):
        """根据文件状态更新内存状态"""
        try:
            logger.info("开始从文件同步插件工具状态到内存")

            # 获取当前内存中的插件列表
            current_plugins = set(self._plugin_registry._plugin_tools.keys())
            file_plugins = set(file_state.keys())

            # 移除不在文件中的插件工具
            plugins_to_remove = current_plugins - file_plugins
            for plugin_id in plugins_to_remove:
                logger.info(f"移除不在文件中的插件工具: {plugin_id}")
                self._plugin_registry.unregister_plugin_tools(plugin_id)

            # 添加或更新文件中的插件工具
            for plugin_id, plugin_data in file_state.items():
                tools = plugin_data.get("tools", [])
                if tools:
                    # 先移除现有工具
                    if plugin_id in current_plugins:
                        self._plugin_registry.unregister_plugin_tools(plugin_id)

                    # 注册新工具
                    result = self._plugin_registry.register_tools(plugin_id, tools)
                    if result.get("success"):
                        logger.debug(f"同步插件工具成功: {plugin_id}")
                    else:
                        logger.warning(f"同步插件工具失败: {plugin_id}, {result.get('message')}")

            logger.info("插件工具状态同步完成")

        except Exception as e:
            logger.error(f"设置内存状态失败: {e}")

    def enable_state_sync(self):
        """启用状态同步"""
        if not self._state_sync_enabled:
            self._setup_state_sync()

    def disable_state_sync(self):
        """禁用状态同步"""
        if self._state_sync_enabled:
            try:
                from utils.state_sync import stop_state_monitoring
                stop_state_monitoring()
                self._state_sync_enabled = False
                logger.info("插件工具状态同步已禁用")
            except Exception as e:
                logger.error(f"禁用状态同步失败: {e}")

    def force_sync_from_file(self):
        """强制从文件同步状态"""
        if self._state_sync_enabled:
            try:
                from utils.state_sync import get_state_sync_manager
                sync_manager = get_state_sync_manager()
                sync_manager.force_sync("plugin_tools")
                logger.info("强制状态同步完成")
            except Exception as e:
                logger.error(f"强制状态同步失败: {e}")
        else:
            logger.warning("状态同步未启用，无法执行强制同步")
