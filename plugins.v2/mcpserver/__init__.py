from datetime import datetime
import os
from pydantic import BaseModel
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

from app.core.config import settings
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import SystemConfigKey
from app.schemas import NotificationType

# --- Plugin Class ---
class MCPServer(_PluginBase):
    # 插件名称
    plugin_name = "MCP Server"
    # 插件描述
    plugin_desc = "启动MCP服务器实现大模型操作MoviePilot"
    # 插件图标
    plugin_icon = "https://avatars.githubusercontent.com/u/182288589?s=200&v=4"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "mcpserver_"
    # 加载顺序
    plugin_order = 50
    # 可使用的用户级别
    auth_level = 1

    _enable = False

    def init_plugin(self, config: dict = None):
        if config:
            self._enable = config.get('enable', False)

    def get_state(self) -> bool:
        return self._enable

    # --- Instance methods for API endpoints ---
    def _get_config(self) -> Dict[str, Any]:
        """API Endpoint: Returns current plugin configuration."""
        return {
            "enable": self._enable
        }

    def _save_config(self, config_payload: dict) -> Dict[str, Any]:
        """API Endpoint: Saves plugin configuration. Expects a dict payload."""
        logger.info(f"{self.plugin_name}: 收到配置保存请求: {config_payload}")
        try:
            self._enable = config_payload.get('enable', self._enable)
            
            # Prepare config to save
            config_to_save = {
                "enable": self._enable
            }
            
            # 保存配置
            self.update_config(config_to_save)
            
            # 重新初始化插件
            self.init_plugin(self.get_config())
            
            logger.info(f"{self.plugin_name}: 配置已保存并通过 init_plugin 重新初始化。当前内存状态: enable={self._enable}")
            
            # 返回最终状态
            return {"message": "配置已成功保存", "saved_config": self._get_config()}

        except Exception as e:
            logger.error(f"{self.plugin_name}: 保存配置时发生错误: {e}", exc_info=True)
            return {"message": f"保存配置失败: {e}", "error": True, "saved_config": self._get_config()}

    # --- Abstract/Base Methods Implementation ---
    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """Returns None for Vue form, but provides initial config data."""
        return None, self._get_config()

    def get_page(self) -> Optional[List[dict]]:
        """Vue mode doesn't use Vuetify page definitions."""
        return None

    def get_api(self) -> List[Dict[str, Any]]:
        """Defines API endpoints accessible via props.api in Vue components."""
        return [
            {
                "path": "/config",
                "endpoint": self._get_config,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取当前配置"
            },
            {
                "path": "/config",
                "endpoint": self._save_config,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存配置"
            }
        ]

    # --- V2 Vue Interface Method ---
    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """Declare Vue rendering mode and assets path."""
        return "vue", "dist/assets"

    # --- Other Base Methods ---
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return [] # No commands defined for this plugin

    def stop_service(self):
        pass

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        """
        获取插件仪表盘元信息
        """
        return [
            {
                "key": "dashboard1",
                "name": "MCP Server"
            }
        ]

    def get_dashboard(self, key: str, **kwargs) -> Optional[
        Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """
        获取插件仪表盘页面
        """
        return {
            "cols": 12,
            "md": 6
        }, {
            "refresh": 10,
            "border": True,
            "title": "MCP Server",
            "subtitle": "启动MCP服务器实现大模型操作MoviePilot"
        }, None