from typing import Any, List, Dict, Optional, Tuple
from pathlib import Path

from app.core.event import eventmanager, Event
from app.plugins import _PluginBase
from app.log import logger
from app.schemas.types import ChainEventType
from app.schemas.event import ResourceDownloadEventData


class UserDownloadPath(_PluginBase):
    # 插件名称
    plugin_name = "用户目录配置"
    # 插件描述
    plugin_desc = "为不同用户设置不同的下载目录"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/userdownloadpath.png"
    # 插件版本
    plugin_version = "1.1"
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
    _enable_type_folder = True
    _enable_category_folder = True

    def init_plugin(self, config: dict = None):
        """
        初始化插件
        """
        if config:
            self._enabled = config.get("enabled", False)
            self._enable_logging = config.get("enable_logging", False)
            self._enable_type_folder = config.get("enable_type_folder", True)
            self._enable_category_folder = config.get("enable_category_folder", True)

            # 解析用户路径配置文本
            user_paths_text = config.get("user_paths_text", "")
            self._user_paths = self._parse_user_paths(user_paths_text)

        # 验证配置
        if self._enabled:
            self._validate_config()

    def _parse_user_paths(self, user_paths_text: str) -> Dict[str, Dict]:
        """
        解析用户路径配置文本
        支持格式：
        1. 简单格式：用户名=路径
        2. 扩展格式：用户名=路径:按类型分类开关:按类别分类开关
        """
        user_paths = {}
        if not user_paths_text:
            return user_paths

        for line in user_paths_text.strip().split('\n'):
            line = line.strip()
            if not line or '=' not in line:
                continue

            try:
                user, config_part = line.split('=', 1)
                user = user.strip()
                config_part = config_part.strip()

                if not user or not config_part:
                    continue

                # 解析配置部分
                config_parts = config_part.split(':')
                path = config_parts[0].strip()

                # 默认使用插件级别的配置
                enable_type = self._enable_type_folder
                enable_category = self._enable_category_folder

                # 如果有用户级别的配置，则覆盖默认值
                if len(config_parts) >= 2:
                    try:
                        enable_type = bool(int(config_parts[1].strip()))
                    except (ValueError, IndexError):
                        pass

                if len(config_parts) >= 3:
                    try:
                        enable_category = bool(int(config_parts[2].strip()))
                    except (ValueError, IndexError):
                        pass

                user_paths[user] = {
                    'path': path,
                    'enable_type_folder': enable_type,
                    'enable_category_folder': enable_category
                }

                if self._enable_logging:
                    logger.info(f"[用户目录配置] 配置用户路径: {user} -> {path} "
                              f"(按类型分类:{enable_type}, 按类别分类:{enable_category})")

            except Exception as e:
                logger.warning(f"[用户目录配置] 解析配置行失败: {line}, 错误: {e}")

        return user_paths

    def get_state(self) -> bool:
        return self._enabled

    def _validate_config(self):
        """
        验证配置的有效性
        """
        # 验证用户路径配置
        for username, config in self._user_paths.items():
            path = config['path']
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
            logger.info(f"[用户目录配置] 拦截下载请求 - 用户: {username}, ID: {userid}, 当前路径: {current_save_path}")

        # 如果已经有自定义保存路径，跳过处理
        if current_save_path:
            if self._enable_logging:
                logger.info(f"[用户目录配置] 已有自定义路径，跳过处理: {current_save_path}")
            return event

        # 根据用户名或用户ID查找对应的下载配置
        user_config = self._get_user_config(username, userid)

        # 如果找到了用户专用配置，修改保存路径
        if user_config:
            user_download_path = user_config['path']

            # 验证路径是否存在
            path_obj = Path(user_download_path)
            if not path_obj.exists():
                logger.error(f"[用户目录配置] 路径不存在: {user_download_path}")
                return event

            if not path_obj.is_dir():
                logger.error(f"[用户目录配置] 路径不是目录: {user_download_path}")
                return event

            # 根据媒体信息和用户配置构建带分类的完整路径
            final_download_path = user_download_path
            media_info = None
            if hasattr(event_data, 'context') and event_data.context:
                media_info = getattr(event_data.context, 'media_info', None)

            # 使用用户级别的分类配置
            enable_type = user_config['enable_type_folder']
            enable_category = user_config['enable_category_folder']

            # 构建分类路径
            final_download_path = self._build_categorized_path(
                user_download_path, media_info, enable_type, enable_category)

            # 修改保存路径
            if not event_data.options:
                event_data.options = {}
            event_data.options["save_path"] = final_download_path

            if self._enable_logging:
                logger.info(f"[用户目录配置] 设置用户专用路径: {user_download_path} -> {final_download_path}")
        else:
            if self._enable_logging:
                logger.info(f"[用户目录配置] 未找到用户专用路径，使用系统默认路径")

        return event

    def _get_user_config(self, username, userid):
        """
        获取用户专用配置
        """
        # 优先使用用户名匹配
        if username and username in self._user_paths:
            config = self._user_paths[username]
            if self._enable_logging:
                logger.info(f"[用户目录配置] 通过用户名匹配到配置: {username} -> {config}")
            return config

        # 如果用户名没有匹配到，尝试用户ID匹配
        elif userid and str(userid) in self._user_paths:
            config = self._user_paths[str(userid)]
            if self._enable_logging:
                logger.info(f"[用户目录配置] 通过用户ID匹配到配置: {userid} -> {config}")
            return config

        return None

    def _build_categorized_path(self, base_path: str, media_info, enable_type_folder: bool, enable_category_folder: bool) -> str:
        """
        根据媒体信息和配置在基础路径上构建分类子目录
        """
        if not media_info:
            return base_path

        download_dir = Path(base_path)

        try:
            # 一级目录：按媒体类型分类（电影/电视剧）
            if enable_type_folder and hasattr(media_info, 'type') and media_info.type:
                download_dir = download_dir / media_info.type.value

            # 二级目录：按媒体类别分类（如动漫、纪录片等）
            if enable_category_folder and hasattr(media_info, 'category') and media_info.category:
                download_dir = download_dir / media_info.category

            if self._enable_logging:
                logger.info(f"[用户目录配置] 构建分类路径: {base_path} -> {download_dir} "
                          f"(按类型分类:{enable_type_folder}, 按类别分类:{enable_category_folder})")

        except Exception as e:
            logger.warning(f"[用户目录配置] 构建分类路径时出错: {e}，使用原始路径")
            return base_path

        return str(download_dir)

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
                                    'cols': 12,
                                    'md': 6
                                },
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {
                                            'model': 'enable_type_folder',
                                            'label': '按类型分类',
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
                                            'model': 'enable_category_folder',
                                            'label': '按类别分类',
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
                                            'placeholder': '支持两种格式：\n1. 简单格式：用户名=路径\n2. 扩展格式：用户名=路径:按类型分类:按类别分类\n\n示例：\nadmin=/downloads/admin\nuser1=/downloads/user1:1:1\nuser2=/downloads/user2:1:0\nuser3=/downloads/user3:0:0\n123=/downloads/userid123',
                                            'rows': 10
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
                                            'text': '使用说明：\n1. 插件会拦截所有下载请求，根据用户身份设置不同的下载路径\n2. 优先匹配用户名，其次匹配用户ID\n3. 支持两种配置格式：简单格式和扩展格式\n4. 扩展格式中，1表示启用，0表示禁用目录分类\n5. 用户级别配置优先于插件默认配置\n6. 如果用户已指定自定义下载路径，插件不会覆盖\n7. 请确保所有路径都存在且可写'
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
            "enable_type_folder": True,
            "enable_category_folder": True,
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
