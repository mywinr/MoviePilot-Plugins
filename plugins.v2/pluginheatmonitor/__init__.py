"""
插件热度监控插件
监控其他插件的下载量热度，当达到设定的里程碑时发送通知
"""
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from threading import Lock

from app.plugins import _PluginBase
from app.core.plugin import PluginManager
from app.helper.plugin import PluginHelper
from app.schemas import NotificationType
from app.log import logger


class PluginHeatMonitor(_PluginBase):
    """插件热度监控"""
    
    plugin_name = "插件热度监控"
    plugin_desc = "监控已安装的下载量热度"
    plugin_icon = "icon.svg"
    plugin_version = "1.0"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "pluginheatmonitor_"
    plugin_order = 20
    auth_level = 1
    
    # 私有属性
    _enabled = False
    _check_interval = 60  # 检查间隔（分钟）
    _monitored_plugins = {}  # 监控的插件配置
    _scheduler = None
    _lock = Lock()
    
    def init_plugin(self, config: dict = None):
        """初始化插件"""
        if config:
            self._enabled = config.get("enabled", False)
            self._check_interval = config.get("check_interval", 60)
            self._monitored_plugins = config.get("monitored_plugins", {})

            # 处理新的插件监控配置
            selected_plugin = config.get("selected_plugin")
            download_increment = config.get("download_increment")

            if selected_plugin and download_increment:
                # 解析下载增量设置
                try:
                    increment_value = int(download_increment)
                    if increment_value > 0:
                        self._monitored_plugins[selected_plugin] = {
                            "download_increment": increment_value
                        }
                        logger.info(f"添加插件监控：{selected_plugin}，下载增量：{increment_value}")

                        # 清空临时配置并保存
                        config["selected_plugin"] = ""
                        config["download_increment"] = ""
                        config["monitored_plugins"] = self._monitored_plugins
                        self.update_config(config)
                except ValueError as e:
                    logger.error(f"解析下载增量设置失败：{str(e)}")

        # 停止现有服务
        self.stop_service()

        if self._enabled:
            logger.info("插件热度监控已启用")
            logger.info(f"插件热度监控定时任务已配置，检查间隔：{self._check_interval}分钟")
            logger.info(f"当前监控 {len(self._monitored_plugins)} 个插件")
        else:
            logger.info("插件热度监控已禁用")
    
    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled
    
    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件服务
        """
        if self._enabled and self._check_interval:
            return [
                {
                    "id": "PluginHeatMonitor",
                    "name": "插件热度监控",
                    "trigger": "interval",
                    "func": self._check_plugin_heat,
                    "kwargs": {"minutes": self._check_interval}
                }
            ]
        return []

    def stop_service(self):
        """停止插件服务"""
        pass
    
    def _check_plugin_heat(self):
        """检查插件热度"""
        if not self._enabled or not self._monitored_plugins:
            return
        
        try:
            with self._lock:
                logger.info("开始检查插件热度...")
                
                # 获取插件统计数据
                plugin_helper = PluginHelper()
                statistics = plugin_helper.get_statistic()
                
                if not statistics:
                    logger.warning("无法获取插件统计数据")
                    return
                
                # 检查每个监控的插件
                for plugin_id, config in self._monitored_plugins.items():
                    self._check_single_plugin(plugin_id, config, statistics)
                
                logger.info("插件热度检查完成")
                
        except Exception as e:
            logger.error(f"检查插件热度时出错：{str(e)}")
    
    def _check_single_plugin(self, plugin_id: str, config: dict, statistics: dict):
        """检查单个插件的热度"""
        try:
            # 获取当前下载量
            current_downloads = statistics.get(plugin_id, 0)

            # 获取历史数据
            history_key = f"history_{plugin_id}"
            history_data = self.plugindata.get_data(self.__class__.__name__, history_key) or {}

            # 获取配置
            download_increment = config.get("download_increment", 100)
            last_notification_downloads = history_data.get("last_notification_downloads", 0)
            last_notification_time = history_data.get("last_notification_time", time.time())

            # 如果是第一次检查，初始化数据
            if "last_downloads" not in history_data:
                history_data.update({
                    "last_downloads": current_downloads,
                    "last_notification_downloads": current_downloads,
                    "last_notification_time": time.time(),
                    "last_check_time": time.time(),
                    "notifications_sent": []
                })
                self.plugindata.save(self.__class__.__name__, history_key, history_data)
                logger.info(f"初始化插件 {plugin_id} 监控数据，当前下载量：{current_downloads}")
                return

            # 计算自上次通知以来的增量
            increment_since_last_notification = current_downloads - last_notification_downloads

            # 检查是否达到下载增量阈值
            if increment_since_last_notification >= download_increment:
                # 计算时间间隔
                current_time = time.time()
                time_elapsed = current_time - last_notification_time

                # 发送增量通知
                self._send_increment_notification(
                    plugin_id,
                    current_downloads,
                    increment_since_last_notification,
                    time_elapsed
                )

                # 更新历史数据
                notification_record = {
                    "downloads": current_downloads,
                    "increment": increment_since_last_notification,
                    "time_elapsed": time_elapsed,
                    "notification_time": current_time
                }

                history_data.update({
                    "last_notification_downloads": current_downloads,
                    "last_notification_time": current_time,
                    "notifications_sent": history_data.get("notifications_sent", []) + [notification_record]
                })

            # 更新当前下载量和检查时间
            history_data.update({
                "last_downloads": current_downloads,
                "last_check_time": time.time()
            })

            # 保存历史数据
            self.plugindata.save(self.__class__.__name__, history_key, history_data)

        except Exception as e:
            logger.error(f"检查插件 {plugin_id} 热度时出错：{str(e)}")
    
    def _send_increment_notification(self, plugin_id: str, current_downloads: int, increment: int, time_elapsed: float):
        """发送下载增量通知"""
        try:
            # 获取插件信息
            plugin_manager = PluginManager()
            local_plugins = plugin_manager.get_local_plugins()
            plugin_name = plugin_id

            # 查找插件名称
            for plugin in local_plugins:
                if plugin.id == plugin_id:
                    plugin_name = plugin.plugin_name or plugin_id
                    break

            # 格式化时间间隔
            time_str = self._format_time_elapsed(time_elapsed)

            # 构建通知内容
            title = f"📈 插件下载增量通知"
            text = (f"插件「{plugin_name}」下载量增长！\n\n"
                   f"📊 当前下载量：{current_downloads:,}\n"
                   f"📈 下载增量：{increment:,}\n"
                   f"⏱️ 用时：{time_str}")

            # 发送通知
            self.post_message(
                mtype=NotificationType.Plugin,
                title=title,
                text=text
            )

            logger.info(f"插件 {plugin_name} 下载增量 {increment}，当前下载量：{current_downloads}，用时：{time_str}")

        except Exception as e:
            logger.error(f"发送下载增量通知时出错：{str(e)}")

    def _format_time_elapsed(self, seconds: float) -> str:
        """格式化时间间隔"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        elif seconds < 86400:
            hours = seconds / 3600
            return f"{hours:.1f}小时"
        else:
            days = seconds / 86400
            return f"{days:.1f}天"
    
    def get_command(self) -> List[Dict[str, Any]]:
        """注册插件命令"""
        return []
    
    def get_api(self) -> List[Dict[str, Any]]:
        """注册插件API"""
        return [
            {
                "path": "/plugin_list",
                "endpoint": self.get_plugin_list,
                "methods": ["GET"],
                "summary": "获取可监控的插件列表",
                "description": "获取已安装插件列表用于配置监控"
            },
            {
                "path": "/statistics",
                "endpoint": self.get_statistics,
                "methods": ["GET"],
                "summary": "获取插件热度统计",
                "description": "获取当前监控插件的热度统计数据"
            }
        ]
    
    def get_plugin_list(self) -> Dict[str, Any]:
        """获取可监控的插件列表"""
        try:
            plugin_manager = PluginManager()
            local_plugins = plugin_manager.get_local_plugins()
            
            # 只返回已安装的插件
            installed_plugins = []
            for plugin in local_plugins:
                if plugin.installed and plugin.id != self.__class__.__name__:  # 排除自己
                    installed_plugins.append({
                        "id": plugin.id,
                        "name": plugin.plugin_name or plugin.id,
                        "desc": plugin.plugin_desc or "",
                        "version": plugin.plugin_version or "",
                        "author": plugin.plugin_author or ""
                    })
            
            return {
                "success": True,
                "data": installed_plugins
            }
        except Exception as e:
            logger.error(f"获取插件列表时出错：{str(e)}")
            return {
                "success": False,
                "message": str(e)
            }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取插件热度统计"""
        try:
            # 获取当前统计数据
            plugin_helper = PluginHelper()
            current_stats = plugin_helper.get_statistic()

            # 获取监控插件的详细信息
            result = []
            for plugin_id, config in self._monitored_plugins.items():
                # 获取历史数据
                history_key = f"history_{plugin_id}"
                history_data = self.plugindata.get_data(self.__class__.__name__, history_key) or {}

                # 获取插件名称
                plugin_manager = PluginManager()
                local_plugins = plugin_manager.get_local_plugins()
                plugin_name = plugin_id
                for plugin in local_plugins:
                    if plugin.id == plugin_id:
                        plugin_name = plugin.plugin_name or plugin_id
                        break

                current_downloads = current_stats.get(plugin_id, 0)
                download_increment = config.get("download_increment", 100)
                last_notification_downloads = history_data.get("last_notification_downloads", 0)
                notifications_sent = history_data.get("notifications_sent", [])

                # 计算距离下次通知的进度
                increment_since_last = current_downloads - last_notification_downloads
                progress = (increment_since_last / download_increment) * 100 if download_increment > 0 else 0
                progress = min(100, max(0, progress))

                # 计算平均增长速度
                avg_growth_rate = "暂无数据"
                if len(notifications_sent) >= 2:
                    total_time = notifications_sent[-1]["notification_time"] - notifications_sent[0]["notification_time"]
                    total_increment = sum([n["increment"] for n in notifications_sent])
                    if total_time > 0:
                        daily_rate = total_increment / (total_time / 86400)
                        avg_growth_rate = f"{daily_rate:.1f} 下载/天"

                result.append({
                    "plugin_id": plugin_id,
                    "plugin_name": plugin_name,
                    "current_downloads": current_downloads,
                    "download_increment": download_increment,
                    "increment_since_last": increment_since_last,
                    "progress_to_next": progress,
                    "notifications_count": len(notifications_sent),
                    "avg_growth_rate": avg_growth_rate,
                    "last_check_time": history_data.get("last_check_time"),
                    "recent_notifications": notifications_sent[-5:]  # 最近5次通知
                })

            return {
                "success": True,
                "data": result
            }
        except Exception as e:
            logger.error(f"获取插件热度统计时出错：{str(e)}")
            return {
                "success": False,
                "message": str(e)
            }

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """获取插件配置表单"""
        # 获取已安装插件列表
        plugin_manager = PluginManager()
        local_plugins = plugin_manager.get_local_plugins()

        plugin_options = []
        for plugin in local_plugins:
            if plugin.installed and plugin.id != self.__class__.__name__:
                plugin_options.append({
                    "title": plugin.plugin_name or plugin.id,
                    "value": plugin.id
                })

        return (
            [
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
                                    },
                                    'content': [
                                        {
                                            'component': 'VAlert',
                                            'props': {
                                                'type': 'info',
                                                'variant': 'tonal',
                                                'text': '监控其他插件的下载量热度，当下载增量达到设定值时发送通知。支持同时监控多个插件，为每个插件设置不同的下载增量阈值。'
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
                                                'model': 'enabled',
                                                'label': '启用插件',
                                                'hint': '开启后将开始监控插件下载量',
                                                'persistent-hint': True
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
                                            'component': 'VSelect',
                                            'props': {
                                                'model': 'check_interval',
                                                'label': '检查间隔',
                                                'items': [
                                                    {'title': '30分钟', 'value': 30},
                                                    {'title': '1小时', 'value': 60},
                                                    {'title': '2小时', 'value': 120},
                                                    {'title': '6小时', 'value': 360},
                                                    {'title': '12小时', 'value': 720},
                                                    {'title': '24小时', 'value': 1440}
                                                ],
                                                'hint': '检查插件下载量的时间间隔',
                                                'persistent-hint': True
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
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardTitle',
                                                    'props': {
                                                        'text': '监控插件配置'
                                                    }
                                                },
                                                {
                                                    'component': 'VCardText',
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
                                                                            'component': 'VSelect',
                                                                            'props': {
                                                                                'model': 'selected_plugin',
                                                                                'label': '选择要监控的插件',
                                                                                'items': plugin_options,
                                                                                'hint': '选择要监控下载量的插件',
                                                                                'persistent-hint': True,
                                                                                'clearable': True
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
                                                                            'component': 'VTextField',
                                                                            'props': {
                                                                                'model': 'download_increment',
                                                                                'label': '下载增量',
                                                                                'placeholder': '例如：100',
                                                                                'hint': '当下载量增加达到此数值时发送通知',
                                                                                'persistent-hint': True,
                                                                                'type': 'number'
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
                                                                    },
                                                                    'content': [
                                                                        {
                                                                            'component': 'VAlert',
                                                                            'props': {
                                                                                'type': 'info',
                                                                                'variant': 'tonal',
                                                                                'text': '请在上方选择插件并设置下载增量，然后保存配置。下载增量是一个数字，表示当下载量增加达到此值时发送通知。'
                                                                            }
                                                                        }
                                                                    ]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                }
                                            ]
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
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'outlined'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VCardTitle',
                                                    'props': {
                                                        'text': '当前监控列表'
                                                    }
                                                },
                                                {
                                                    'component': 'VCardText',
                                                    'content': [
                                                        {
                                                            'component': 'VAlert',
                                                            'props': {
                                                                'type': 'info',
                                                                'variant': 'tonal',
                                                                'text': '当前监控的插件配置将在保存后显示在数据页面中。要修改监控配置，请重新选择插件和里程碑设置。'
                                                            }
                                                        }
                                                    ]
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ],
            {
                "enabled": False,
                "check_interval": 60,
                "monitored_plugins": {},
                "selected_plugin": "",
                "download_increment": 100
            }
        )

    def get_page(self) -> List[dict]:
        """获取插件数据页面"""
        # 获取当前统计数据
        try:
            plugin_helper = PluginHelper()
            current_stats = plugin_helper.get_statistic()

            # 构建监控插件的统计信息
            monitor_data = []
            for plugin_id, config in self._monitored_plugins.items():
                # 获取历史数据
                history_key = f"history_{plugin_id}"
                history_data = self.plugindata.get_data(self.__class__.__name__, history_key) or {}

                # 获取插件名称
                plugin_manager = PluginManager()
                local_plugins = plugin_manager.get_local_plugins()
                plugin_name = plugin_id
                for plugin in local_plugins:
                    if plugin.id == plugin_id:
                        plugin_name = plugin.plugin_name or plugin_id
                        break

                current_downloads = current_stats.get(plugin_id, 0)
                download_increment = config.get("download_increment", 100)
                last_notification_downloads = history_data.get("last_notification_downloads", 0)
                notifications_sent = history_data.get("notifications_sent", [])

                # 计算距离下次通知的进度
                increment_since_last = current_downloads - last_notification_downloads
                progress = (increment_since_last / download_increment) * 100 if download_increment > 0 else 0
                progress = min(100, max(0, progress))

                # 计算平均增长速度
                growth_rate = "暂无数据"
                if len(notifications_sent) >= 2:
                    total_time = notifications_sent[-1]["notification_time"] - notifications_sent[0]["notification_time"]
                    total_increment = sum([n["increment"] for n in notifications_sent])
                    if total_time > 0:
                        daily_rate = total_increment / (total_time / 86400)
                        growth_rate = f"{daily_rate:.1f} 下载/天"

                # 格式化最后检查时间
                last_check_str = "未检查"
                if history_data.get("last_check_time"):
                    last_check_time = datetime.fromtimestamp(history_data["last_check_time"])
                    last_check_str = last_check_time.strftime("%m-%d %H:%M")

                monitor_data.append({
                    "plugin_id": plugin_id,
                    "plugin_name": plugin_name,
                    "current_downloads": current_downloads,
                    "download_increment": download_increment,
                    "increment_since_last": increment_since_last,
                    "progress": progress,
                    "notifications_count": len(notifications_sent),
                    "growth_rate": growth_rate,
                    "last_check": last_check_str
                })

        except Exception as e:
            logger.error(f"获取页面数据时出错：{str(e)}")
            monitor_data = []

        return [
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
                                    'title': '插件热度监控',
                                    'text': f'当前监控 {len(self._monitored_plugins)} 个插件的下载量热度'
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
                                'component': 'VCard',
                                'content': [
                                    {
                                        'component': 'VCardTitle',
                                        'props': {
                                            'text': '监控统计'
                                        }
                                    },
                                    {
                                        'component': 'VCardText',
                                        'content': [
                                            {
                                                'component': 'VDataTable',
                                                'props': {
                                                    'headers': [
                                                        {'title': '插件名称', 'key': 'plugin_name', 'sortable': True},
                                                        {'title': '当前下载量', 'key': 'current_downloads', 'sortable': True},
                                                        {'title': '下载增量', 'key': 'download_increment', 'sortable': True},
                                                        {'title': '距离通知', 'key': 'increment_since_last', 'sortable': True},
                                                        {'title': '进度', 'key': 'progress', 'sortable': True},
                                                        {'title': '通知次数', 'key': 'notifications_count', 'sortable': True},
                                                        {'title': '增长速度', 'key': 'growth_rate', 'sortable': False},
                                                        {'title': '最后检查', 'key': 'last_check', 'sortable': False}
                                                    ],
                                                    'items': monitor_data,
                                                    'items-per-page': 10,
                                                    'no-data-text': '暂无监控数据'
                                                },
                                                'slots': {
                                                    'item.progress': {
                                                        'component': 'VProgressLinear',
                                                        'props': {
                                                            'model-value': '{{ item.progress }}',
                                                            'height': '8',
                                                            'color': 'primary'
                                                        }
                                                    },
                                                    'item.current_downloads': {
                                                        'component': 'VChip',
                                                        'props': {
                                                            'size': 'small',
                                                            'color': 'info',
                                                            'text': '{{ item.current_downloads.toLocaleString() }}'
                                                        }
                                                    },
                                                    'item.download_increment': {
                                                        'component': 'VChip',
                                                        'props': {
                                                            'size': 'small',
                                                            'color': 'primary',
                                                            'text': '{{ item.download_increment }}'
                                                        }
                                                    },
                                                    'item.increment_since_last': {
                                                        'component': 'VChip',
                                                        'props': {
                                                            'size': 'small',
                                                            'color': '{{ item.increment_since_last >= item.download_increment ? "success" : "warning" }}',
                                                            'text': '{{ item.increment_since_last }}'
                                                        }
                                                    },
                                                    'item.notifications_count': {
                                                        'component': 'VChip',
                                                        'props': {
                                                            'size': 'small',
                                                            'color': 'success',
                                                            'text': '{{ item.notifications_count }}'
                                                        }
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ] if monitor_data else [
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
                                    'type': 'warning',
                                    'variant': 'tonal',
                                    'title': '暂无监控数据',
                                    'text': '请先在配置页面添加要监控的插件'
                                }
                            }
                        ]
                    }
                ]
            }
        ]
