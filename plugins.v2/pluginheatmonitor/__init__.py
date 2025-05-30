"""
插件热度监控插件
监控其他插件的下载量热度，当达到设定的里程碑时发送通知
"""
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from threading import Lock

from apscheduler.triggers.cron import CronTrigger
from app.plugins import _PluginBase
from app.core.plugin import PluginManager
from app.helper.plugin import PluginHelper
from app.schemas import NotificationType
from app.log import logger


class PluginHeatMonitor(_PluginBase):
    """插件热度监控"""
    
    plugin_name = "插件热度监控"
    plugin_desc = "监控已安装的下载量热度"
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png"
    plugin_version = "1.2"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "pluginheatmonitor_"
    plugin_order = 20
    auth_level = 1
    
    # 私有属性
    _enabled = False
    _cron = "0 */1 * * *"  # 默认每小时执行一次
    _monitored_plugins = {}  # 监控的插件配置
    _enable_notification = True  # 是否启用通知
    _run_once = False  # 立即运行一次
    _scheduler = None
    _lock = Lock()
    
    def init_plugin(self, config: dict = None):
        """初始化插件"""
        if config:
            self._enabled = config.get("enabled", False)
            self._cron = config.get("cron", "0 */1 * * *")
            self._monitored_plugins = config.get("monitored_plugins", {})
            self._enable_notification = config.get("enable_notification", True)
            self._run_once = config.get("run_once", False)

            # 处理新的插件监控配置
            selected_plugins = config.get("selected_plugins", [])
            download_increment = config.get("download_increment")

            # 如果有选中的插件列表（无论是否为空），都需要更新监控配置
            if "selected_plugins" in config:
                # 解析下载增量设置
                try:
                    # 如果没有设置下载增量，使用默认值100
                    if download_increment:
                        increment_value = int(download_increment)
                    else:
                        # 如果没有设置增量，尝试从现有配置中获取，否则使用默认值
                        existing_increments = [cfg.get("download_increment", 100) for cfg in self._monitored_plugins.values()]
                        increment_value = existing_increments[0] if existing_increments else 100

                    if increment_value > 0:
                        # 获取当前监控的插件列表，用于清理不再监控的插件
                        old_monitored_plugins = set(self._monitored_plugins.keys())
                        new_monitored_plugins = set(selected_plugins)

                        # 清理不再监控的插件的历史数据
                        removed_plugins = old_monitored_plugins - new_monitored_plugins
                        for plugin_id in removed_plugins:
                            history_key = f"history_{plugin_id}"
                            self.del_data(history_key)
                            logger.info(f"清理插件 {plugin_id} 的历史数据")

                        # 重新构建监控插件配置（完全替换，而不是追加）
                        self._monitored_plugins = {}
                        for plugin_id in selected_plugins:
                            self._monitored_plugins[plugin_id] = {
                                "download_increment": increment_value
                            }
                            logger.info(f"添加插件监控：{plugin_id}，下载增量：{increment_value}")

                        # 更新监控插件配置，但不清空用户界面的临时字段
                        # 这样用户可以继续看到刚才的选择，方便进行调整
                        logger.info(f"成功更新监控列表：移除 {len(removed_plugins)} 个，当前监控 {len(selected_plugins)} 个插件")
                except ValueError as e:
                    logger.error(f"解析下载增量设置失败：{str(e)}")

        # 停止现有服务
        self.stop_service()

        if self._enabled:
            logger.info("插件热度监控已启用")
            logger.info(f"插件热度监控定时任务已配置，Cron表达式：{self._cron}")
            logger.info(f"当前监控 {len(self._monitored_plugins)} 个插件")
            logger.info(f"通知功能：{'启用' if self._enable_notification else '禁用'}")

            # 处理立即运行一次
            if self._run_once:
                logger.info("执行立即运行一次...")
                self._check_plugin_heat()
                # 关闭立即运行开关
                if config:
                    config["run_once"] = False
                    self.update_config(config)
                logger.info("立即运行完成，开关已关闭")
        else:
            logger.info("插件热度监控已禁用")
    
    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled
    
    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件服务
        """
        if self._enabled and self._cron:
            return [
                {
                    "id": "PluginHeatMonitor",
                    "name": "插件热度监控",
                    "trigger": CronTrigger.from_crontab(self._cron),
                    "func": self._check_plugin_heat,
                    "kwargs": {}
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
            history_data = self.get_data(history_key) or {}

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
                self.save_data(history_key, history_data)
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
            self.save_data(history_key, history_data)

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

            # 发送通知（如果启用）
            if self._enable_notification:
                self.post_message(
                    mtype=NotificationType.Plugin,
                    title=title,
                    text=text
                )
                logger.info(f"插件 {plugin_name} 下载增量 {increment}，当前下载量：{current_downloads}，用时：{time_str}")
            else:
                logger.info(f"插件 {plugin_name} 下载增量 {increment}，当前下载量：{current_downloads}，用时：{time_str}（通知已禁用）")

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

    def _parse_cron_interval(self, cron_expr: str) -> str:
        """解析cron表达式获取间隔描述"""
        try:
            parts = cron_expr.split()
            if len(parts) >= 5:
                minute, hour, day, month, weekday = parts[:5]

                # 检查小时字段
                if hour.startswith("*/"):
                    interval = int(hour[2:])
                    return f"{interval}小时"
                elif hour == "*":
                    if minute.startswith("*/"):
                        interval = int(minute[2:])
                        return f"{interval}分钟"
                    elif minute.isdigit():
                        return "每小时"

                # 检查天字段
                if day.startswith("*/"):
                    interval = int(day[2:])
                    return f"{interval}天"
                elif day == "*":
                    return "每天"

                # 默认返回
                return "自定义"
        except:
            pass
        return "未知"

    def _get_plugin_icon(self, plugin_id: str) -> str:
        """获取插件图标"""
        try:
            plugin_manager = PluginManager()
            local_plugins = plugin_manager.get_local_plugins()

            for plugin in local_plugins:
                if plugin.id == plugin_id:
                    if plugin.plugin_icon:
                        # 如果是网络图片，返回原始URL
                        if plugin.plugin_icon.startswith('http'):
                            return plugin.plugin_icon
                        # 如果是本地图片，返回相对路径
                        else:
                            return f"./plugin_icon/{plugin.plugin_icon}"

            # 默认图标
            return "mdi-puzzle"
        except Exception as e:
            logger.debug(f"获取插件 {plugin_id} 图标失败：{str(e)}")
            return "mdi-puzzle"
    
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
                if plugin.installed:  # 移除排除自己的条件
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
                history_data = self.get_data(history_key) or {}

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
            if plugin.installed:  # 移除排除自己的条件
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
                                        'cols': 12
                                    },
                                    'content': [
                                        {
                                            'component': 'VCard',
                                            'props': {
                                                'variant': 'tonal',
                                                'color': 'info'
                                            },
                                            'content': [
                                                {
                                                    'component': 'VAlert',
                                                    'props': {
                                                        "type": "info",
                                                        "variant": "tonal",
                                                        'text': '💡 使用提示：选择要监控的插件并设置下载增量，当插件下载量增长达到设定值时会发送通知。支持监控包括本插件在内的所有已安装插件。'
                                                    }
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
                                        'md': 4
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
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VSwitch',
                                            'props': {
                                                'model': 'enable_notification',
                                                'label': '启用通知',
                                                'hint': '开启后达到增量时发送通知',
                                                'persistent-hint': True
                                            }
                                        }
                                    ]
                                },
                                {
                                    'component': 'VCol',
                                    'props': {
                                        'cols': 12,
                                        'md': 4
                                    },
                                    'content': [
                                        {
                                            'component': 'VSwitch',
                                            'props': {
                                                'model': 'run_once',
                                                'label': '立即运行一次',
                                                'hint': '保存配置后立即执行一次检查',
                                                'persistent-hint': True,
                                                'color': 'warning'
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
                                            'component': 'VCronField',
                                            'props': {
                                                'model': 'cron',
                                                'label': '执行周期',
                                                'placeholder': '0 0 0 ? *'
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
                                                                                'model': 'selected_plugins',
                                                                                'label': '选择要监控的插件',
                                                                                'items': plugin_options,
                                                                                'hint': '可选择多个插件进行监控',
                                                                                'persistent-hint': True,
                                                                                'multiple': True,
                                                                                'chips': True,
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
                "enable_notification": True,
                "run_once": False,
                "cron": "0 */1 * * *",
                "monitored_plugins": {},
                "selected_plugins": [],
                "download_increment": 100
            }
        )

    def get_page(self) -> List[dict]:
        """获取插件数据页面"""
        # 如果没有监控插件，显示提示信息
        if not self._monitored_plugins:
            return [
                {
                    "component": "VContainer",
                    "props": {"fluid": True},
                    "content": [
                        {
                            "component": "VRow",
                            "props": {"justify": "center"},
                            "content": [
                                {
                                    "component": "VCol",
                                    "props": {"cols": 12, "md": 8},
                                    "content": [
                                        {
                                            "component": "VCard",
                                            "props": {
                                                "variant": "tonal",
                                                "color": "info",
                                                "class": "text-center pa-8"
                                            },
                                            "content": [
                                                {
                                                    "component": "VIcon",
                                                    "props": {
                                                        "icon": "mdi-chart-line-variant",
                                                        "size": "64",
                                                        "color": "info",
                                                        "class": "mb-4"
                                                    }
                                                },
                                                {
                                                    "component": "VCardTitle",
                                                    "props": {
                                                        "class": "text-h5 mb-2"
                                                    },
                                                    "text": "暂无监控插件"
                                                },
                                                {
                                                    "component": "VCardText",
                                                    "props": {
                                                        "class": "text-body-1"
                                                    },
                                                    "text": "请先在配置页面添加要监控的插件，开始追踪插件下载量的增长趋势"
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

        # 获取当前统计数据
        try:
            plugin_helper = PluginHelper()
            current_stats = plugin_helper.get_statistic()

            # 构建插件卡片数据
            plugin_cards = []
            total_downloads = 0

            # 获取全局信息（所有插件共享）
            global_last_check_time = None
            global_download_increment = None

            for plugin_id, config in self._monitored_plugins.items():
                # 获取历史数据
                history_key = f"history_{plugin_id}"
                history_data = self.plugindata.get_data(self.__class__.__name__, history_key) or {}

                # 获取插件名称和图标
                plugin_manager = PluginManager()
                local_plugins = plugin_manager.get_local_plugins()
                plugin_name = plugin_id
                plugin_icon = self._get_plugin_icon(plugin_id)
                for plugin in local_plugins:
                    if plugin.id == plugin_id:
                        plugin_name = plugin.plugin_name or plugin_id
                        break

                current_downloads = current_stats.get(plugin_id, 0)
                download_increment = config.get("download_increment", 100)
                last_notification_downloads = history_data.get("last_notification_downloads", 0)
                notifications_sent = history_data.get("notifications_sent", [])

                # 收集全局信息（第一次遇到时设置）
                if global_download_increment is None:
                    global_download_increment = download_increment
                if global_last_check_time is None and history_data.get("last_check_time"):
                    from datetime import datetime
                    last_check_time = datetime.fromtimestamp(history_data["last_check_time"])
                    global_last_check_time = last_check_time.strftime("%Y-%m-%d %H:%M:%S")

                # 计算距离下次通知的进度
                increment_since_last = current_downloads - last_notification_downloads
                progress = (increment_since_last / download_increment) * 100 if download_increment > 0 else 0
                progress = min(100, max(0, progress))

                # 计算平均增长速度（基于历史通知记录）
                avg_growth_rate = "暂无数据"
                if len(notifications_sent) >= 2:
                    # 计算从第一次通知到最后一次通知的时间跨度
                    total_time = notifications_sent[-1]["notification_time"] - notifications_sent[0]["notification_time"]
                    # 计算总增量（所有通知的增量之和）
                    total_increment = sum([n["increment"] for n in notifications_sent])
                    if total_time > 0:
                        # 计算每天的平均增长速度
                        daily_rate = total_increment / (total_time / 86400)
                        avg_growth_rate = f"{daily_rate:.1f} 下载/天"

                # 确定进度条颜色
                progress_color = "success" if progress >= 80 else "warning" if progress >= 50 else "info"

                # 统计总数
                total_downloads += current_downloads

                # 构建插件卡片
                plugin_cards.append({
                    "component": "VCol",
                    "props": {"cols": 12, "md": 6, "lg": 4},
                    "content": [
                        {
                            "component": "VCard",
                            "props": {
                                "variant": "outlined",
                                "class": "h-100"
                            },
                            "content": [
                                {
                                    "component": "VCardTitle",
                                    "props": {
                                        "class": "d-flex align-center pa-4 pb-2"
                                    },
                                    "content": [
                                        # 使用插件图标或默认图标
                                        {
                                            "component": "VAvatar" if not plugin_icon.startswith("mdi-") else "VIcon",
                                            "props": {
                                                "size": "24" if not plugin_icon.startswith("mdi-") else None,
                                                "icon": plugin_icon if plugin_icon.startswith("mdi-") else None,
                                                "color": "primary" if plugin_icon.startswith("mdi-") else None,
                                                "class": "mr-2"
                                            },
                                            "content": [] if plugin_icon.startswith("mdi-") else [
                                                {
                                                    "component": "VImg",
                                                    "props": {
                                                        "src": plugin_icon,
                                                        "alt": plugin_name
                                                    }
                                                }
                                            ]
                                        },
                                        {
                                            "component": "span",
                                            "props": {
                                                "class": "text-truncate"
                                            },
                                            "text": plugin_name
                                        }
                                    ]
                                },
                                {
                                    "component": "VCardText",
                                    "props": {"class": "pa-4 pt-0"},
                                    "content": [
                                        # 下载量统计
                                        {
                                            "component": "div",
                                            "props": {"class": "mb-3"},
                                            "content": [
                                                {
                                                    "component": "div",
                                                    "props": {"class": "d-flex justify-space-between align-center mb-1"},
                                                    "content": [
                                                        {
                                                            "component": "span",
                                                            "props": {"class": "text-caption text-medium-emphasis"},
                                                            "text": "当前下载量"
                                                        },
                                                        {
                                                            "component": "span",
                                                            "props": {"class": "text-h6 font-weight-bold"},
                                                            "text": f"{current_downloads:,}"
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        # 达标进度条
                                        {
                                            "component": "div",
                                            "props": {"class": "mb-3"},
                                            "content": [
                                                {
                                                    "component": "div",
                                                    "props": {"class": "d-flex justify-space-between align-center mb-1"},
                                                    "content": [
                                                        {
                                                            "component": "span",
                                                            "props": {"class": "text-caption text-medium-emphasis"},
                                                            "text": "达标进度"
                                                        },
                                                        {
                                                            "component": "span",
                                                            "props": {"class": "text-caption font-weight-medium"},
                                                            "text": f"{increment_since_last}/{download_increment}"
                                                        }
                                                    ]
                                                },
                                                {
                                                    "component": "VProgressLinear",
                                                    "props": {
                                                        "model-value": progress,
                                                        "color": progress_color,
                                                        "height": "8",
                                                        "rounded": True
                                                    }
                                                },
                                                {
                                                    "component": "div",
                                                    "props": {"class": "text-center mt-1"},
                                                    "content": [
                                                        {
                                                            "component": "span",
                                                            "props": {"class": "text-caption"},
                                                            "text": f"{progress:.1f}%"
                                                        }
                                                    ]
                                                }
                                            ]
                                        },
                                        # 增长速度信息 - 独占一行，居中显示
                                        {
                                            "component": "div",
                                            "props": {"class": "text-center mt-2"},
                                            "content": [
                                                {
                                                    "component": "VChip",
                                                    "props": {
                                                        "size": "small",
                                                        "color": "info",
                                                        "variant": "tonal",
                                                        "prepend-icon": "mdi-trending-up"
                                                    },
                                                    "text": avg_growth_rate
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                })

        except Exception as e:
            logger.error(f"获取页面数据时出错：{str(e)}")
            plugin_cards = []
            total_downloads = 0

        # 构建美化的页面布局
        return [
            {
                "component": "VContainer",
                "props": {"fluid": True},
                "content": [
                    # 全局信息摘要 - 分散的美观卡片
                    {
                        "component": "VRow",
                        "props": {"class": "mb-4"},
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "sm": 4},
                                "content": [
                                    {
                                        "component": "VCard",
                                        "props": {
                                            "variant": "tonal",
                                            "color": "primary"
                                        },
                                        "content": [
                                            {
                                                "component": "VCardText",
                                                "props": {"class": "text-center pa-4"},
                                                "content": [
                                                    {
                                                        "component": "VIcon",
                                                        "props": {
                                                            "icon": "mdi-puzzle",
                                                            "size": "32",
                                                            "color": "primary",
                                                            "class": "mb-2"
                                                        }
                                                    },
                                                    {
                                                        "component": "div",
                                                        "props": {"class": "text-h4 font-weight-bold"},
                                                        "text": str(len(self._monitored_plugins))
                                                    },
                                                    {
                                                        "component": "div",
                                                        "props": {"class": "text-subtitle-2"},
                                                        "text": "监控插件"
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "sm": 4},
                                "content": [
                                    {
                                        "component": "VCard",
                                        "props": {
                                            "variant": "tonal",
                                            "color": "success"
                                        },
                                        "content": [
                                            {
                                                "component": "VCardText",
                                                "props": {"class": "text-center pa-4"},
                                                "content": [
                                                    {
                                                        "component": "VIcon",
                                                        "props": {
                                                            "icon": "mdi-download",
                                                            "size": "32",
                                                            "color": "success",
                                                            "class": "mb-2"
                                                        }
                                                    },
                                                    {
                                                        "component": "div",
                                                        "props": {"class": "text-h4 font-weight-bold"},
                                                        "text": f"{total_downloads:,}"
                                                    },
                                                    {
                                                        "component": "div",
                                                        "props": {"class": "text-subtitle-2"},
                                                        "text": "总下载量"
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "sm": 4},
                                "content": [
                                    {
                                        "component": "VCard",
                                        "props": {
                                            "variant": "tonal",
                                            "color": "info"
                                        },
                                        "content": [
                                            {
                                                "component": "VCardText",
                                                "props": {"class": "text-center pa-4"},
                                                "content": [
                                                    {
                                                        "component": "VIcon",
                                                        "props": {
                                                            "icon": "mdi-clock-outline",
                                                            "size": "32",
                                                            "color": "info",
                                                            "class": "mb-2"
                                                        }
                                                    },
                                                    {
                                                        "component": "div",
                                                        "props": {"class": "text-h6 font-weight-bold"},
                                                        "text": global_last_check_time or "未检查"
                                                    },
                                                    {
                                                        "component": "div",
                                                        "props": {"class": "text-subtitle-2"},
                                                        "text": "最后检查"
                                                    }
                                                ]
                                            }
                                        ]
                                    }
                                ]
                            }
                        ]
                    },
                    # 插件监控卡片
                    {
                        "component": "VRow",
                        "content": plugin_cards
                    }
                ]
            }
        ]

    def get_dashboard(self) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], List[dict]]]:
        """
        获取插件仪表盘页面，需要返回：1、仪表板col配置字典；2、全局配置（自动刷新等）；3、仪表板页面元素配置json（含数据）
        """
        # 列配置 - 全宽显示，与Page页面保持一致
        cols = {"cols": 12}

        # 全局配置 - 增强视觉效果
        attrs = {
            "refresh": 30,  # 30秒自动刷新
            "border": True,  # 启用边框以显示插件标识
            "title": "插件热度监控",  # 插件名称
            "subtitle": "实时监控插件下载量增长趋势",
            "icon": "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/heatmonitor.png"  # 插件图标
        }

        # 直接使用 page 的 UI，提取其中的内容部分
        page_elements = self.get_page()
        if page_elements and len(page_elements) > 0:
            # 提取 VContainer 中的 content 部分作为 dashboard 元素
            container = page_elements[0]
            if container.get("component") == "VContainer" and "content" in container:
                dashboard_elements = container["content"]
                return cols, attrs, dashboard_elements

        # 如果没有监控插件或获取页面失败，显示简洁的提示
        dashboard_elements = [
            {
                "component": "VCard",
                "props": {
                    "variant": "tonal",
                    "color": "info",
                    "class": "text-center pa-6"
                },
                "content": [
                    {
                        "component": "VIcon",
                        "props": {
                            "icon": "mdi-chart-line-variant",
                            "size": "48",
                            "color": "info",
                            "class": "mb-3"
                        }
                    },
                    {
                        "component": "VCardTitle",
                        "props": {"class": "text-h6 mb-2"},
                        "text": "暂无监控插件"
                    },
                    {
                        "component": "VCardText",
                        "props": {"class": "text-caption"},
                        "text": "请在配置页面添加要监控的插件"
                    }
                ]
            }
        ]
        return cols, attrs, dashboard_elements
