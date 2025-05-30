"""
插件热度监控插件
监控其他插件的下载量热度，当达到设定的里程碑时发送通知
"""
import json
import time
from datetime import datetime, timedelta
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
    plugin_version = "1.1"
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

            if selected_plugins and download_increment:
                # 解析下载增量设置
                try:
                    increment_value = int(download_increment)
                    if increment_value > 0:
                        # 为每个选中的插件添加监控
                        for plugin_id in selected_plugins:
                            self._monitored_plugins[plugin_id] = {
                                "download_increment": increment_value
                            }
                            logger.info(f"添加插件监控：{plugin_id}，下载增量：{increment_value}")

                        # 更新监控插件配置，但不清空用户界面的临时字段
                        # 这样用户可以继续看到刚才的选择，方便进行调整
                        logger.info(f"成功添加 {len(selected_plugins)} 个插件到监控列表")
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
                    "component": "div",
                    "text": "暂无监控插件，请先在配置页面添加要监控的插件",
                    "props": {
                        "class": "text-center pa-4",
                    },
                }
            ]

        # 获取当前统计数据
        try:
            plugin_helper = PluginHelper()
            current_stats = plugin_helper.get_statistic()

            # 构建表格行数据
            table_rows = []
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

                # 格式化最后检查时间
                last_check_str = "未检查"
                if history_data.get("last_check_time"):
                    last_check_time = datetime.fromtimestamp(history_data["last_check_time"])
                    last_check_str = last_check_time.strftime("%m-%d %H:%M")

                # 构建表格行
                table_rows.append({
                    "component": "tr",
                    "content": [
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": plugin_name,
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": f"{current_downloads:,}",
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": str(download_increment),
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": str(increment_since_last),
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": f"{progress:.1f}%",
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": str(len(notifications_sent)),
                        },
                        {
                            "component": "td",
                            "props": {"class": "text-start ps-4"},
                            "text": last_check_str,
                        },
                    ],
                })

        except Exception as e:
            logger.error(f"获取页面数据时出错：{str(e)}")
            table_rows = []

        # 构建简单的表格页面，参考契约检查插件的写法
        return [
            {
                "component": "VCol",
                "props": {
                    "cols": 12,
                },
                "content": [
                    {
                        "component": "VTable",
                        "props": {"hover": True},
                        "content": [
                            {
                                "component": "thead",
                                "content": [
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "插件名称",
                                    },
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "当前下载量",
                                    },
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "下载增量",
                                    },
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "距离通知",
                                    },
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "进度",
                                    },
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "通知次数",
                                    },
                                    {
                                        "component": "th",
                                        "props": {"class": "text-start ps-4"},
                                        "text": "最后检查",
                                    },
                                ],
                            },
                            {"component": "tbody", "content": table_rows},
                        ],
                    }
                ],
            }
        ]

    def get_dashboard(self) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], List[dict]]]:
        """
        获取插件仪表盘页面，需要返回：1、仪表板col配置字典；2、全局配置（自动刷新等）；3、仪表板页面元素配置json（含数据）
        """
        # 列配置
        cols = {"cols": 12, "md": 6}

        # 全局配置
        attrs = {
            "refresh": 30,  # 30秒自动刷新
            "border": True,
            "title": "插件热度监控",
            "subtitle": "监控插件下载量增长情况"
        }

        # 直接复用get_page的逻辑，保持一致性
        page_elements = self.get_page()

        return cols, attrs, page_elements
