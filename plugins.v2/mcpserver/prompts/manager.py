"""
Prompt manager for MCP Server.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Type, List, Any, Optional

import mcp.types as types

from .base import BasePrompt
from .media import MediaPrompt
from .plugin_registry import PluginPromptRegistry
from .plugin_proxy import PluginPromptProxy

# 添加父目录到路径以导入utils
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Configure logging
logger = logging.getLogger(__name__)


class PromptManager:
    """Prompt manager, responsible for registering and managing all available prompts"""

    def __init__(self, token_manager=None):
        self.token_manager = token_manager
        self._prompts: Dict[str, Type[BasePrompt]] = {}
        self._plugin_prompt_registry = PluginPromptRegistry()
        self._state_sync_enabled = False
        self._register_prompts()
        self._setup_state_sync()

    def _register_prompts(self):
        """Register all available prompts"""
        prompts = [
            MediaPrompt
        ]

        for prompt_class in prompts:
            prompt = prompt_class()
            prompt_infos = prompt.prompt_info
            if isinstance(prompt_infos, list):
                # If it's a list of prompts, register all prompts
                for prompt_info in prompt_infos:
                    self._prompts[prompt_info.name] = prompt_class
                    logger.info(f"Registered prompt: {prompt_info.name}")
            else:
                # Register a single prompt directly
                self._prompts[prompt_infos.name] = prompt_class
                logger.info(f"Registered prompt: {prompt_infos.name}")

    def list_prompts(self) -> List[types.Prompt]:
        """List all available prompts"""
        prompts = []

        # 添加内置prompts
        for prompt_class in set(self._prompts.values()):  # Use set to deduplicate
            prompt = prompt_class()
            prompt_infos = prompt.prompt_info

            # Handle single prompt or list of prompts
            if isinstance(prompt_infos, list):
                prompts.extend(prompt_infos)
            else:
                prompts.append(prompt_infos)

        # 添加插件prompts
        plugin_prompts = self._plugin_prompt_registry.list_registered_prompts()
        prompts.extend(plugin_prompts)

        prompt_names = [prompt.name for prompt in prompts]
        logger.info(f"Available prompts: {prompt_names} (内置: {len(prompts) - len(plugin_prompts)}, 插件: {len(plugin_prompts)})")
        print(f"Available prompts: {prompt_names}")
        return prompts

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """Get prompt messages for the specified prompt name and arguments"""
        try:
            # 首先检查是否是内置prompt
            if name in self._prompts:
                prompt = self._prompts[name]()
                return await prompt.get_prompt(name, arguments)

            # 检查是否是插件prompt
            plugin_prompt_info = self._plugin_prompt_registry.get_prompt_info(name)
            if plugin_prompt_info:
                prompt_proxy = PluginPromptProxy(plugin_prompt_info, self.token_manager)
                return await prompt_proxy.get_prompt(name, arguments)

            # 提示不存在
            logger.warning(f"请求了未知的提示: '{name}'")
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"未找到名为 '{name}' 的提示。请使用search-movie工具时一次只搜索一个站点，找到合适资源后停止搜索。"
                        )
                    )
                ]
            )

        except Exception as e:
            logger.error(f"获取提示时出错: {str(e)}")
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=f"获取提示时出错: {str(e)}。请使用search-movie工具时一次只搜索一个站点，找到合适资源后停止搜索。"
                        )
                    )
                ]
            )

    def register_plugin_prompts(self, plugin_id: str, prompts: List[dict]) -> Dict[str, Any]:
        """注册插件prompts"""
        return self._plugin_prompt_registry.register_prompts(plugin_id, prompts)

    def unregister_plugin_prompts(self, plugin_id: str) -> Dict[str, Any]:
        """注销插件prompts"""
        return self._plugin_prompt_registry.unregister_plugin_prompts(plugin_id)

    def get_plugin_prompt_registry(self):
        """获取插件prompt注册表"""
        return self._plugin_prompt_registry

    def _setup_state_sync(self):
        """设置状态同步"""
        try:
            from utils.state_sync import register_sync_target, start_state_monitoring

            # 获取插件提示文件路径
            current_dir = Path(os.path.dirname(__file__)).parent
            prompts_file = current_dir / "plugin_prompts.json"

            # 注册状态同步目标
            register_sync_target(
                name="plugin_prompts",
                file_path=prompts_file,
                memory_getter=self._get_memory_state,
                memory_setter=self._set_memory_state,
                sync_interval=30  # 30秒检查一次
            )

            # 启动状态监控（如果还没启动）
            try:
                start_state_monitoring()
                self._state_sync_enabled = True
                logger.info("插件提示状态同步已启用")
            except Exception as e:
                # 可能已经启动了，这是正常的
                if "已在运行" in str(e):
                    self._state_sync_enabled = True
                    logger.debug("插件提示状态同步已启用（监控已在运行）")
                else:
                    raise e

        except Exception as e:
            logger.warning(f"设置提示状态同步失败: {e}")
            self._state_sync_enabled = False

    def _get_memory_state(self) -> Dict[str, any]:
        """获取当前内存中的插件提示状态"""
        try:
            # 获取所有插件的提示信息
            memory_state = {}

            # 遍历插件注册表中的所有插件
            for plugin_id in self._plugin_prompt_registry._plugin_prompts.keys():
                prompts = self._plugin_prompt_registry.get_plugin_prompts(plugin_id)
                if prompts:
                    # 构建与文件格式一致的数据结构
                    prompt_infos = []
                    for prompt_name in prompts:
                        prompt_info = self._plugin_prompt_registry.get_prompt_info(prompt_name)
                        if prompt_info:
                            prompt_infos.append(prompt_info.to_dict())

                    memory_state[plugin_id] = {
                        "prompts": prompt_infos,
                        "registered_at": prompt_infos[0].get("registered_at") if prompt_infos else None
                    }

            return memory_state

        except Exception as e:
            logger.error(f"获取提示内存状态失败: {e}")
            return {}

    def _set_memory_state(self, file_state: Dict[str, any]):
        """根据文件状态更新内存状态"""
        try:
            logger.info("开始从文件同步插件提示状态到内存")

            # 获取当前内存中的插件列表
            current_plugins = set(self._plugin_prompt_registry._plugin_prompts.keys())
            file_plugins = set(file_state.keys())

            # 移除不在文件中的插件提示
            plugins_to_remove = current_plugins - file_plugins
            for plugin_id in plugins_to_remove:
                logger.info(f"移除不在文件中的插件提示: {plugin_id}")
                self._plugin_prompt_registry.unregister_plugin_prompts(plugin_id)

            # 添加或更新文件中的插件提示
            for plugin_id, plugin_data in file_state.items():
                prompts = plugin_data.get("prompts", [])
                if prompts:
                    # 先移除现有提示
                    if plugin_id in current_plugins:
                        self._plugin_prompt_registry.unregister_plugin_prompts(plugin_id)

                    # 注册新提示
                    result = self._plugin_prompt_registry.register_prompts(plugin_id, prompts)
                    if result.get("success"):
                        logger.debug(f"同步插件提示成功: {plugin_id}")
                    else:
                        logger.warning(f"同步插件提示失败: {plugin_id}, {result.get('message')}")

            logger.info("插件提示状态同步完成")

        except Exception as e:
            logger.error(f"设置提示内存状态失败: {e}")

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
                logger.info("插件提示状态同步已禁用")
            except Exception as e:
                logger.error(f"禁用提示状态同步失败: {e}")

    def force_sync_from_file(self):
        """强制从文件同步状态"""
        if self._state_sync_enabled:
            try:
                from utils.state_sync import get_state_sync_manager
                sync_manager = get_state_sync_manager()
                sync_manager.force_sync("plugin_prompts")
                logger.info("强制提示状态同步完成")
            except Exception as e:
                logger.error(f"强制提示状态同步失败: {e}")
        else:
            logger.warning("提示状态同步未启用，无法执行强制同步")
