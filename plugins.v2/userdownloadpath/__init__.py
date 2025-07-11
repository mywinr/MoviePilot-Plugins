from typing import Any, List, Dict, Optional, Tuple
from pathlib import Path

from app.core.event import eventmanager, Event
from app.plugins import _PluginBase
from app.log import logger
from app.schemas.types import ChainEventType
from app.schemas.event import ResourceDownloadEventData


class UserDownloadPath(_PluginBase):
    # 插件名称
    plugin_name = "用户下载路径修改"
    # 插件描述
    plugin_desc = "为不同用户设置不同的下载路径"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/userdownloadpath.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "userdownloadpath"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _enabled = False
    _user_paths = {}
    _enable_logging = False

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if config:
            self._enabled = config.get("enabled", False)
            self._enable_logging = config.get("enable_logging", False)

            # 解析用户路径配置文本
            user_paths_text = config.get("user_paths_text", "")
            self._user_paths = self._parse_user_paths(user_paths_text)

        # 验证配置
        if self._enabled:
            self._validate_config()

    def _parse_user_paths(self, user_paths_text: str) -> Dict[str, str]:
        """
        解析用户路径配置文本
        """
        user_paths = {}
        if not user_paths_text:
            return user_paths

        for line in user_paths_text.strip().split('\n'):
            line = line.strip()
            if not line or '=' not in line:
                continue

            try:
                user, path = line.split('=', 1)
                user = user.strip()
                path = path.strip()

                if user and path:
                    user_paths[user] = path
                    if self._enable_logging:
                        logger.info(f"[用户下载路径] 配置用户路径: {user} -> {path}")
            except Exception as e:
                logger.warning(f"[用户下载路径] 解析配置行失败: {line}, 错误: {e}")

        return user_paths

    def get_state(self) -> bool:
        return self._enabled

    def _validate_config(self):
        """
        验证配置的有效性
        """
        # 验证用户路径配置
        for username, path in self._user_paths.items():
            if not path:
                logger.warning(f"用户 {username} 的下载路径为空")
                continue

            path_obj = Path(path)
            if not path_obj.exists():
                logger.warning(f"用户 {username} 的下载路径不存在: {path}")
            elif not path_obj.is_dir():
                logger.warning(f"用户 {username} 的下载路径不是目录: {path}")

    @eventmanager.register(ChainEventType.ResourceDownload)
    def intercept_download(self, event: Event) -> Event:
        """
        拦截资源下载事件，修改下载路径
        """
        if not self._enabled:
            return event

        if not event or not event.event_data:
            return event

        event_data: ResourceDownloadEventData = event.event_data

        # 获取用户信息
        options = event_data.options or {}
        username = options.get("username")
        userid = options.get("userid")
        current_save_path = options.get("save_path")

        if self._enable_logging:
            logger.info(f"[用户下载路径] 拦截下载请求 - 用户: {username}, ID: {userid}, 当前路径: {current_save_path}")

        # 如果已经有自定义保存路径，跳过处理
        if current_save_path:
            if self._enable_logging:
                logger.info(f"[用户下载路径] 已有自定义路径，跳过处理: {current_save_path}")
            return event

        # 根据用户名或用户ID查找对应的下载路径
        user_download_path = self._get_user_path(username, userid)

        # 如果找到了用户专用路径，修改保存路径
        if user_download_path:
            # 验证路径是否存在
            path_obj = Path(user_download_path)
            if not path_obj.exists():
                logger.error(f"[用户下载路径] 路径不存在: {user_download_path}")
                return event

            if not path_obj.is_dir():
                logger.error(f"[用户下载路径] 路径不是目录: {user_download_path}")
                return event

            # 修改保存路径
            if not event_data.options:
                event_data.options = {}
            event_data.options["save_path"] = user_download_path

            if self._enable_logging:
                logger.info(f"[用户下载路径] 设置用户专用路径: {user_download_path}")
        else:
            if self._enable_logging:
                logger.info(f"[用户下载路径] 未找到用户专用路径，使用系统默认路径")

        return event

    def _get_user_path(self, username, userid):
        """
        获取用户专用路径
        """
        # 优先使用用户名匹配
        if username and username in self._user_paths:
            if self._enable_logging:
                logger.info(f"[用户下载路径] 通过用户名匹配到路径: {username} -> {self._user_paths[username]}")
            return self._user_paths[username]

        # 如果用户名没有匹配到，尝试用户ID匹配
        elif userid and str(userid) in self._user_paths:
            if self._enable_logging:
                logger.info(f"[用户下载路径] 通过用户ID匹配到路径: {userid} -> {self._user_paths[str(userid)]}")
            return self._user_paths[str(userid)]

        return None



    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，需要返回两块数据：1、页面配置；2、数据结构
        """
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enable_logging',
                                            'label': '启用详细日志',
                                        }
                                    }
                                ]
                            }
                        ]
                    },

                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'user_paths_text',
                                            'label': '用户路径配置',
                                            'placeholder': '每行一个配置，格式：用户名或用户ID=下载路径\n例如：\nadmin=/downloads/admin\nuser1=/downloads/user1\n123=/downloads/userid123',
                                            'rows': 8
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': '使用说明：\n1. 插件会拦截所有下载请求，根据用户身份设置不同的下载路径\n2. 优先匹配用户名，其次匹配用户ID\n3. 如果用户已经指定了自定义下载路径，插件不会覆盖\n4. 如果没有匹配到用户专用路径，将使用系统默认路径\n5. 请确保所有路径都存在且可写'
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "enable_logging": False,
            "user_paths_text": ""
        }

    def get_page(self) -> List[dict]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        pass
