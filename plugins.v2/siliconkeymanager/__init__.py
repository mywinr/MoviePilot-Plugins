"""
硅基KEY管理插件
管理硅基流API keys，支持余额检查、自动清理、分类管理等功能
"""
import json
import requests
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

from apscheduler.triggers.cron import CronTrigger
from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.schemas.types import EventType
from app.core.event import eventmanager, Event
from app.log import logger


class SiliconKeyManager(_PluginBase):
    """硅基KEY管理"""

    plugin_name = "硅基KEY管理"
    plugin_desc = "管理硅基流API keys，支持余额检查、自动清理、分类管理等功能"
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/siliconkey.png"
    plugin_version = "1.2"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "siliconkeymanager_"
    plugin_order = 21
    auth_level = 1
    # Vue组件支持
    plugin_component = True

    # 常量
    DEFAULT_CRON = "0 */6 * * *"  # 每6小时检查一次
    DEFAULT_MIN_BALANCE = 1.0
    DEFAULT_CACHE_TTL = 300  # 5分钟缓存
    DEFAULT_TIMEOUT = 60

    # 私有属性
    _enabled = False
    _cron = DEFAULT_CRON
    _min_balance_limit = DEFAULT_MIN_BALANCE
    _enable_notification = True
    _cache_ttl = DEFAULT_CACHE_TTL
    _timeout = DEFAULT_TIMEOUT
    _run_once = False

    # 缓存
    _balance_cache = {}
    _lock = threading.Lock()
    _scheduler = None

    def __init__(self):
        """初始化插件"""
        super().__init__()
        # 确保调度器属性存在
        self._scheduler = None

    def init_plugin(self, config: dict = None):
        """初始化插件"""
        if config:
            self._enabled = config.get("enabled", False)
            self._cron = config.get("cron", self.DEFAULT_CRON)
            self._min_balance_limit = float(config.get("min_balance_limit", self.DEFAULT_MIN_BALANCE))
            self._enable_notification = config.get("enable_notification", True)
            self._cache_ttl = int(config.get("cache_ttl", self.DEFAULT_CACHE_TTL))
            self._timeout = int(config.get("timeout", self.DEFAULT_TIMEOUT))
            self._run_once = config.get("run_once", False)

        # 停止现有任务
        self.stop_service()

        if self._enabled:
            # 启动定时任务
            try:
                from apscheduler.schedulers.background import BackgroundScheduler
                from app.core.config import settings

                # 创建调度器实例
                if not self._scheduler:
                    self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                    self._scheduler.start()

                self._scheduler.add_job(
                    func=self._check_keys_task,
                    trigger=CronTrigger.from_crontab(self._cron),
                    id=f"{self.plugin_name}_check",
                    name=f"{self.plugin_name}定时检查",
                    misfire_grace_time=60
                )

                # 立即运行一次
                if self._run_once:
                    self._scheduler.add_job(
                        func=self._check_keys_task,
                        trigger="date",
                        run_date=datetime.now() + timedelta(seconds=3),
                        id=f"{self.plugin_name}_run_once",
                        name=f"{self.plugin_name}立即运行"
                    )
                    # 重置运行一次标志
                    self._run_once = False
                    self.__update_config()

                logger.info(f"硅基KEY管理插件已启动，检查周期：{self._cron}")

            except Exception as e:
                logger.error(f"启动硅基KEY管理定时任务失败：{str(e)}", exc_info=True)
                self._scheduler = None

    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enabled

    def stop_service(self):
        """停止插件服务"""
        try:
            if hasattr(self, '_scheduler') and self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown(wait=False)
                self._scheduler = None
                logger.info("硅基KEY管理插件定时任务已停止")
        except Exception as e:
            logger.error(f"停止硅基KEY管理插件服务时出错: {e}")

    @eventmanager.register(EventType.PluginAction)
    def handle_plugin_action(self, event: Event):
        """处理插件动作事件"""
        if event.event_data.get("action") == "silicon_keys":
            # 可以在这里处理命令行调用的逻辑
            logger.info("收到硅基KEY管理命令")
            return {
                "status": "success",
                "message": "硅基KEY管理插件正在运行"
            }

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """获取插件命令"""
        return [
            {
                "cmd": "/silicon_keys",
                "event": EventType.PluginAction,
                "desc": "硅基KEY管理",
                "category": "管理",
                "data": {
                    "action": "silicon_keys"
                }
            }
        ]



    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """Declare Vue rendering mode and assets path."""
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """Returns None for Vue form, but provides initial config data."""
        return None, {
            "enabled": self._enabled,
            "cron": self._cron,
            "min_balance_limit": self._min_balance_limit,
            "enable_notification": self._enable_notification,
            "cache_ttl": self._cache_ttl,
            "timeout": self._timeout,
            "run_once": False
        }

    def get_page(self) -> Optional[List[dict]]:
        """Vue mode doesn't use Vuetify page definitions."""
        return None

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        """获取插件仪表盘元信息"""
        return [
            {
                "key": "siliconkey",
                "name": "硅基KEY管理"
            }
        ]

    def get_dashboard(self, key: str = "", **kwargs) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """获取插件仪表盘页面 - Vue模式"""
        # 忽略未使用的参数警告
        _ = key, kwargs
        return (
            {"cols": 12, "md": 6},
            {
                "refresh": 30,
                "border": True,
                "title": "硅基KEY管理",
                "subtitle": "管理硅基流API keys状态",
                "render_mode": "vue",
                "pluginConfig": {
                    "dashboard_refresh_interval": 30,
                    "dashboard_auto_refresh": True,
                },
            },
            None,
        )

    def __update_config(self):
        """更新配置"""
        config = {
            "enabled": self._enabled,
            "cron": self._cron,
            "min_balance_limit": self._min_balance_limit,
            "enable_notification": self._enable_notification,
            "cache_ttl": self._cache_ttl,
            "timeout": self._timeout,
            "run_once": self._run_once
        }
        self.update_config(config)

    def _check_api_key(self, api_key: str) -> Optional[float]:
        """检查单个API key的余额"""
        with self._lock:
            # 检查缓存
            cache_key = api_key
            if cache_key in self._balance_cache:
                cache_time, balance = self._balance_cache[cache_key]
                if datetime.now() - cache_time < timedelta(seconds=self._cache_ttl):
                    logger.debug(f'使用缓存的API key {api_key[:8]}... 余额: {balance}')
                    return balance

        logger.info(f'检查API key: {api_key[:8]}...')
        try:
            response = requests.get(
                'https://api.siliconflow.cn/v1/user/info',
                headers={'Authorization': f'Bearer {api_key}'},
                timeout=self._timeout
            )
            response.encoding = 'utf-8'

            if response.ok:
                try:
                    balance_data = response.json()
                    if (isinstance(balance_data, dict) and
                        'data' in balance_data and
                        isinstance(balance_data['data'], dict) and
                        'totalBalance' in balance_data['data']):

                        balance = float(balance_data['data']['totalBalance'])

                        # 更新缓存
                        with self._lock:
                            self._balance_cache[cache_key] = (datetime.now(), balance)

                        logger.info(f'API key {api_key[:8]}... 有效，余额: {balance}')
                        return balance
                    else:
                        logger.warning(f"API key {api_key[:8]}... 响应结构无效: {balance_data}")
                        with self._lock:
                            self._balance_cache[cache_key] = (datetime.now(), None)
                        return None

                except (ValueError, TypeError, json.JSONDecodeError) as e:
                    logger.warning(f'解析API key {api_key[:8]}... 响应失败: {e}')
                    with self._lock:
                        self._balance_cache[cache_key] = (datetime.now(), None)
                    return None
            else:
                logger.warning(f'API key {api_key[:8]}... 无效或检查出错, 响应: {response.status_code}')
                if response.status_code in [401, 403, 404]:
                    # 无效key，缓存为0
                    with self._lock:
                        self._balance_cache[cache_key] = (datetime.now(), 0)
                    return 0
                else:
                    # 其他错误，缓存为None
                    with self._lock:
                        self._balance_cache[cache_key] = (datetime.now(), None)
                    return None

        except requests.exceptions.Timeout:
            logger.error(f'检查API key {api_key[:8]}... 时超时')
            with self._lock:
                self._balance_cache[cache_key] = (datetime.now(), None)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f'检查API key {api_key[:8]}... 时网络错误: {e}')
            with self._lock:
                self._balance_cache[cache_key] = (datetime.now(), None)
            return None
        except Exception as e:
            logger.error(f'检查API key {api_key[:8]}... 时未知错误: {e}', exc_info=True)
            with self._lock:
                self._balance_cache[cache_key] = (datetime.now(), None)
            return None

    def _get_keys_data(self, key_type: str = "public") -> List[Dict[str, Any]]:
        """从数据库获取keys数据"""
        data_key = f"keys_{key_type}"
        keys_data = self.get_data(data_key) or []
        return keys_data

    def _save_keys_data(self, keys_data: List[Dict[str, Any]], key_type: str = "public"):
        """保存keys数据到数据库"""
        data_key = f"keys_{key_type}"
        self.save_data(data_key, keys_data)

    def _add_key_to_db(self, api_key: str, key_type: str = "public") -> Tuple[bool, str]:
        """添加key到数据库"""
        try:
            # 获取现有keys
            keys_data = self._get_keys_data(key_type)

            # 检查是否已存在
            for key_info in keys_data:
                if key_info.get("key") == api_key:
                    return False, f"Key已存在于{key_type}列表中"

            # 检查key有效性
            balance = self._check_api_key(api_key)

            if balance is None:
                return False, "Key检查失败，请稍后重试"
            elif balance < self._min_balance_limit:
                return False, f"Key余额({balance})低于阈值({self._min_balance_limit})"

            # 添加到数据库
            key_info = {
                "key": api_key,
                "balance": balance,
                "status": "valid",
                "last_check": datetime.now().isoformat(),
                "added_time": datetime.now().isoformat()
            }

            keys_data.append(key_info)
            self._save_keys_data(keys_data, key_type)

            logger.info(f"成功添加{key_type} API key: {api_key[:8]}..., 余额: {balance}")
            return True, f"成功添加Key，余额: {balance}"

        except Exception as e:
            logger.error(f"添加{key_type} API key时出错: {e}", exc_info=True)
            return False, f"添加Key时出错: {str(e)}"

    def _remove_key_from_db(self, api_key: str, key_type: str = "public") -> Tuple[bool, str]:
        """从数据库移除key"""
        try:
            keys_data = self._get_keys_data(key_type)

            # 查找并移除key
            original_count = len(keys_data)
            keys_data = [k for k in keys_data if k.get("key") != api_key]

            if len(keys_data) == original_count:
                return False, "Key不存在"

            self._save_keys_data(keys_data, key_type)

            # 清除缓存
            with self._lock:
                self._balance_cache.pop(api_key, None)

            logger.info(f"成功移除{key_type} API key: {api_key[:8]}...")
            return True, "成功移除Key"

        except Exception as e:
            logger.error(f"移除{key_type} API key时出错: {e}", exc_info=True)
            return False, f"移除Key时出错: {str(e)}"

    def _check_keys_task(self):
        """定时检查keys任务"""
        try:
            logger.info("🔍 开始检查硅基API keys状态...")

            # 清除缓存以获取最新数据
            with self._lock:
                self._balance_cache.clear()

            total_checked = 0
            total_removed = 0
            total_updated = 0

            # 检查公有keys
            public_checked, public_removed, public_updated = self._check_keys_by_type("public")
            total_checked += public_checked
            total_removed += public_removed
            total_updated += public_updated

            # 检查私有keys
            private_checked, private_removed, private_updated = self._check_keys_by_type("private")
            total_checked += private_checked
            total_removed += private_removed
            total_updated += private_updated

            # 发送通知
            if self._enable_notification and (total_removed > 0 or total_updated > 0):
                message = f"硅基KEY检查完成\n"
                message += f"检查: {total_checked}个\n"
                if total_updated > 0:
                    message += f"更新: {total_updated}个\n"
                if total_removed > 0:
                    message += f"移除: {total_removed}个"

                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title="硅基KEY管理",
                    text=message
                )

            logger.info(f"✅ 硅基API keys检查完成，检查: {total_checked}, 更新: {total_updated}, 移除: {total_removed}")

        except Exception as e:
            logger.error(f"❌ 检查硅基API keys时出错：{str(e)}", exc_info=True)

    def _check_keys_by_type(self, key_type: str) -> Tuple[int, int, int]:
        """检查指定类型的keys"""
        try:
            keys_data = self._get_keys_data(key_type)
            if not keys_data:
                return 0, 0, 0

            checked_count = 0
            removed_count = 0
            updated_count = 0
            valid_keys = []

            logger.info(f"检查{key_type} keys，共{len(keys_data)}个")

            for key_info in keys_data:
                api_key = key_info.get("key")
                if not api_key:
                    continue

                checked_count += 1
                old_balance = key_info.get("balance", 0)

                # 检查余额
                balance = self._check_api_key(api_key)

                if balance is None:
                    # 检查失败，保留key但标记状态
                    key_info.update({
                        "status": "check_failed",
                        "last_check": datetime.now().isoformat()
                    })
                    valid_keys.append(key_info)
                    logger.warning(f"{key_type} key {api_key[:8]}... 检查失败，保留待重试")

                elif balance < self._min_balance_limit:
                    # 余额不足，移除key
                    removed_count += 1
                    logger.info(f"移除{key_type} key {api_key[:8]}...，余额不足: {balance}")

                else:
                    # 有效key，更新信息
                    if abs(balance - old_balance) > 0.01:  # 余额有变化
                        updated_count += 1

                    key_info.update({
                        "balance": balance,
                        "status": "valid",
                        "last_check": datetime.now().isoformat()
                    })
                    valid_keys.append(key_info)

            # 保存更新后的keys
            self._save_keys_data(valid_keys, key_type)

            return checked_count, removed_count, updated_count

        except Exception as e:
            logger.error(f"检查{key_type} keys时出错: {e}", exc_info=True)
            return 0, 0, 0

    # API方法
    def _get_keys(self) -> Dict[str, Any]:
        """获取所有keys - 返回完整keys供前端处理"""
        try:
            public_keys = self._get_keys_data("public")
            private_keys = self._get_keys_data("private")

            # 直接返回完整的key数据，让前端处理mask和复制
            return {
                "status": "success",
                "public_keys": public_keys,
                "private_keys": private_keys,
                "public_count": len(public_keys),
                "private_count": len(private_keys),
                "total_count": len(public_keys) + len(private_keys)
            }

        except Exception as e:
            logger.error(f"获取keys时出错: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"获取keys时出错: {str(e)}"
            }

    def _add_keys(self, **kwargs) -> Dict[str, Any]:
        """添加keys API"""
        try:
            keys = kwargs.get("keys", "")
            key_type = kwargs.get("key_type", "public")

            if not keys or not keys.strip():
                return {
                    "status": "error",
                    "message": "请输入API keys"
                }

            # 解析keys，支持逗号、空格、换行分隔
            import re
            key_list = re.split(r'[,\s\n]+', keys.strip())
            key_list = [k.strip() for k in key_list if k.strip()]

            if not key_list:
                return {
                    "status": "error",
                    "message": "未找到有效的API keys"
                }

            results = []
            success_count = 0

            for api_key in key_list:
                success, message = self._add_key_to_db(api_key, key_type)
                results.append({
                    "key": api_key[:8] + "...",
                    "success": success,
                    "message": message
                })
                if success:
                    success_count += 1

            return {
                "status": "success",
                "message": f"成功添加 {success_count}/{len(key_list)} 个keys",
                "results": results,
                "success_count": success_count,
                "total_count": len(key_list)
            }

        except Exception as e:
            logger.error(f"添加keys时出错: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"添加keys时出错: {str(e)}"
            }

    def _delete_keys(self, **kwargs) -> Dict[str, Any]:
        """删除keys API"""
        try:
            key_indices = kwargs.get("key_indices", [])
            key_type = kwargs.get("key_type", "public")

            keys_data = self._get_keys_data(key_type)

            if not keys_data:
                return {
                    "status": "error",
                    "message": f"没有{key_type} keys可删除"
                }

            if not key_indices:
                return {
                    "status": "error",
                    "message": "请选择要删除的keys"
                }

            # 按索引倒序删除，避免索引变化
            key_indices = sorted(set(key_indices), reverse=True)
            deleted_keys = []

            for index in key_indices:
                if 0 <= index < len(keys_data):
                    deleted_key = keys_data.pop(index)
                    deleted_keys.append(deleted_key["key"][:8] + "...")

                    # 清除缓存
                    with self._lock:
                        self._balance_cache.pop(deleted_key["key"], None)

            # 保存更新后的数据
            self._save_keys_data(keys_data, key_type)

            return {
                "status": "success",
                "message": f"成功删除 {len(deleted_keys)} 个keys",
                "deleted_keys": deleted_keys
            }

        except Exception as e:
            logger.error(f"删除keys时出错: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"删除keys时出错: {str(e)}"
            }

    def _check_keys_api(self, **kwargs) -> Dict[str, Any]:
        """检查keys API"""
        try:
            key_indices = kwargs.get("key_indices", None)
            key_type = kwargs.get("key_type", "public")

            keys_data = self._get_keys_data(key_type)

            if not keys_data:
                return {
                    "status": "error",
                    "message": f"没有{key_type} keys可检查"
                }

            # 如果指定了索引，只检查指定的keys
            if key_indices is not None:
                keys_to_check = []
                for index in key_indices:
                    if 0 <= index < len(keys_data):
                        keys_to_check.append(keys_data[index])
            else:
                keys_to_check = keys_data

            if not keys_to_check:
                return {
                    "status": "error",
                    "message": "没有有效的keys可检查"
                }

            # 清除缓存以获取最新数据
            for key_info in keys_to_check:
                api_key = key_info.get("key")
                if api_key:
                    with self._lock:
                        self._balance_cache.pop(api_key, None)

            results = []
            valid_count = 0
            invalid_count = 0
            failed_count = 0

            for key_info in keys_to_check:
                api_key = key_info.get("key")
                if not api_key:
                    continue

                balance = self._check_api_key(api_key)

                if balance is None:
                    status = "check_failed"
                    failed_count += 1
                elif balance < self._min_balance_limit:
                    status = "invalid"
                    invalid_count += 1
                else:
                    status = "valid"
                    valid_count += 1

                # 更新key信息
                key_info.update({
                    "balance": balance,
                    "status": status,
                    "last_check": datetime.now().isoformat()
                })

                results.append({
                    "masked_key": key_info["key"][:8] + "...",
                    "balance": balance,
                    "status": status,
                    "last_check": key_info["last_check"]
                })

            # 保存更新后的数据
            self._save_keys_data(keys_data, key_type)

            return {
                "status": "success",
                "message": f"检查完成：有效 {valid_count}，无效 {invalid_count}，失败 {failed_count}",
                "results": results,
                "valid_count": valid_count,
                "invalid_count": invalid_count,
                "failed_count": failed_count
            }

        except Exception as e:
            logger.error(f"检查keys时出错: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"检查keys时出错: {str(e)}"
            }

    def _get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            public_keys = self._get_keys_data("public")
            private_keys = self._get_keys_data("private")

            # 统计公有keys
            public_stats = self._calculate_key_stats(public_keys)

            # 统计私有keys
            private_stats = self._calculate_key_stats(private_keys)

            # 总体统计
            total_stats = {
                "total_count": public_stats["total_count"] + private_stats["total_count"],
                "valid_count": public_stats["valid_count"] + private_stats["valid_count"],
                "invalid_count": public_stats["invalid_count"] + private_stats["invalid_count"],
                "failed_count": public_stats["failed_count"] + private_stats["failed_count"],
                "total_balance": public_stats["total_balance"] + private_stats["total_balance"]
            }

            return {
                "status": "success",
                "public_stats": public_stats,
                "private_stats": private_stats,
                "total_stats": total_stats,
                "config": {
                    "enabled": self._enabled,
                    "cron": self._cron,
                    "min_balance_limit": self._min_balance_limit,
                    "enable_notification": self._enable_notification
                }
            }

        except Exception as e:
            logger.error(f"获取统计信息时出错: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"获取统计信息时出错: {str(e)}"
            }

    def _calculate_key_stats(self, keys_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算keys统计信息"""
        total_count = len(keys_data)
        valid_count = 0
        invalid_count = 0
        failed_count = 0
        total_balance = 0.0

        for key_info in keys_data:
            status = key_info.get("status", "unknown")
            balance = key_info.get("balance", 0)

            if status == "valid":
                valid_count += 1
                if isinstance(balance, (int, float)) and balance > 0:
                    total_balance += balance
            elif status == "invalid":
                invalid_count += 1
            elif status == "check_failed":
                failed_count += 1

        return {
            "total_count": total_count,
            "valid_count": valid_count,
            "invalid_count": invalid_count,
            "failed_count": failed_count,
            "total_balance": round(total_balance, 4)
        }



    def _check_keys_task(self):
        """定时检查keys任务"""
        try:
            logger.info("🔍 开始检查硅基API keys状态...")

            # 清除缓存以获取最新数据
            with self._lock:
                self._balance_cache.clear()

            total_checked = 0
            total_removed = 0
            total_updated = 0

            # 检查公有keys
            public_checked, public_removed, public_updated = self._check_keys_by_type("public")
            total_checked += public_checked
            total_removed += public_removed
            total_updated += public_updated

            # 检查私有keys
            private_checked, private_removed, private_updated = self._check_keys_by_type("private")
            total_checked += private_checked
            total_removed += private_removed
            total_updated += private_updated

            # 发送通知
            if self._enable_notification and (total_removed > 0 or total_updated > 0):
                message = f"硅基KEY检查完成\n"
                message += f"检查: {total_checked}个\n"
                if total_updated > 0:
                    message += f"更新: {total_updated}个\n"
                if total_removed > 0:
                    message += f"移除: {total_removed}个"

                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title="硅基KEY管理",
                    text=message
                )

            logger.info(f"✅ 硅基API keys检查完成，检查: {total_checked}, 更新: {total_updated}, 移除: {total_removed}")

        except Exception as e:
            logger.error(f"❌ 检查硅基API keys时出错：{str(e)}", exc_info=True)

    def _check_keys_by_type(self, key_type: str) -> Tuple[int, int, int]:
        """检查指定类型的keys"""
        try:
            keys_data = self._get_keys_data(key_type)
            if not keys_data:
                return 0, 0, 0

            checked_count = 0
            removed_count = 0
            updated_count = 0
            valid_keys = []

            logger.info(f"检查{key_type} keys，共{len(keys_data)}个")

            for key_info in keys_data:
                api_key = key_info.get("key")
                if not api_key:
                    continue

                checked_count += 1
                old_balance = key_info.get("balance", 0)

                # 检查余额
                balance = self._check_api_key(api_key)

                if balance is None:
                    # 检查失败，保留key但标记状态
                    key_info.update({
                        "status": "check_failed",
                        "last_check": datetime.now().isoformat()
                    })
                    valid_keys.append(key_info)
                    logger.warning(f"{key_type} key {api_key[:8]}... 检查失败，保留待重试")

                elif balance < self._min_balance_limit:
                    # 余额不足，移除key
                    removed_count += 1
                    logger.info(f"移除{key_type} key {api_key[:8]}...，余额不足: {balance}")

                else:
                    # 有效key，更新信息
                    if abs(balance - old_balance) > 0.01:  # 余额有变化
                        updated_count += 1

                    key_info.update({
                        "balance": balance,
                        "status": "valid",
                        "last_check": datetime.now().isoformat()
                    })
                    valid_keys.append(key_info)

            # 保存更新后的keys
            self._save_keys_data(valid_keys, key_type)

            return checked_count, removed_count, updated_count

        except Exception as e:
            logger.error(f"检查{key_type} keys时出错: {e}", exc_info=True)
            return 0, 0, 0



    # --- Vue API Endpoints ---
    def _get_config(self) -> Dict[str, Any]:
        """API Endpoint: Returns current plugin configuration."""
        return {
            "enabled": self._enabled,
            "cron": self._cron,
            "min_balance_limit": self._min_balance_limit,
            "enable_notification": self._enable_notification,
            "cache_ttl": self._cache_ttl,
            "timeout": self._timeout
        }

    def _save_config(self, config_payload: dict) -> Dict[str, Any]:
        """API Endpoint: Saves plugin configuration."""
        try:
            logger.info(f"收到配置保存请求: {config_payload}")

            # 更新配置
            self.init_plugin(config_payload)

            # 保存配置
            self.update_config(config_payload)

            logger.info("配置已保存并重新初始化")
            return {"status": "success", "message": "配置已成功保存", "config": self._get_config()}

        except Exception as e:
            logger.error(f"保存配置时发生错误: {e}", exc_info=True)
            return {"status": "error", "message": f"保存配置失败: {e}", "config": self._get_config()}

    def _get_dashboard_data(self) -> Dict[str, Any]:
        """API Endpoint: Returns dashboard data for Vue components."""
        try:
            public_keys = self._get_keys_data("public")
            private_keys = self._get_keys_data("private")

            # 统计信息
            public_stats = self._calculate_key_stats(public_keys)
            private_stats = self._calculate_key_stats(private_keys)

            total_stats = {
                "total_count": public_stats["total_count"] + private_stats["total_count"],
                "valid_count": public_stats["valid_count"] + private_stats["valid_count"],
                "invalid_count": public_stats["invalid_count"] + private_stats["invalid_count"],
                "failed_count": public_stats["failed_count"] + private_stats["failed_count"],
                "total_balance": public_stats["total_balance"] + private_stats["total_balance"]
            }

            return {
                "status": "success",
                "public_stats": public_stats,
                "private_stats": private_stats,
                "total_stats": total_stats,
                "last_check_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }

        except Exception as e:
            logger.error(f"获取仪表板数据时出错：{str(e)}", exc_info=True)
            return {
                "status": "error",
                "message": f"获取数据时出错: {str(e)}",
                "total_stats": {"total_count": 0, "valid_count": 0, "invalid_count": 0, "failed_count": 0, "total_balance": 0}
            }

    def _trigger_run_once(self) -> Dict[str, Any]:
        """API Endpoint: Trigger immediate execution."""
        try:
            if not self._enabled:
                return {"status": "error", "message": "插件未启用"}

            # 执行立即检查
            def run_check():
                try:
                    self._check_keys_task()
                    logger.info("手动触发的立即运行完成")
                except Exception as e:
                    logger.error(f"手动触发的立即运行出错：{str(e)}", exc_info=True)

            thread = threading.Thread(target=run_check, daemon=True)
            thread.start()

            return {"status": "success", "message": "已触发立即运行"}

        except Exception as e:
            logger.error(f"触发立即运行时出错：{str(e)}", exc_info=True)
            return {"status": "error", "message": f"触发失败: {str(e)}"}

    # --- Update get_api method to include Vue endpoints ---
    def get_api(self) -> List[Dict[str, Any]]:
        """获取插件API"""
        return [
            {
                "path": "/config",
                "endpoint": self._get_config,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取当前配置",
            },
            {
                "path": "/config",
                "endpoint": self._save_config,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存配置",
            },
            {
                "path": "/data",
                "endpoint": self._get_dashboard_data,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取仪表板数据",
            },
            {
                "path": "/run_once",
                "endpoint": self._trigger_run_once,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "立即运行一次",
            },
            {
                "path": "/keys",
                "endpoint": self._get_keys,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取所有API keys"
            },
            {
                "path": "/keys/add",
                "endpoint": self._add_keys,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "添加API keys"
            },
            {
                "path": "/keys/delete",
                "endpoint": self._delete_keys,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "删除API keys"
            },
            {
                "path": "/keys/check",
                "endpoint": self._check_keys_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "检查API keys"
            },
            {
                "path": "/stats",
                "endpoint": self._get_stats,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取统计信息"
            },

        ]

    def _add_keys(self, payload: dict) -> Dict[str, Any]:
        """API Endpoint: Add multiple keys."""
        try:
            keys_text = payload.get("keys", "")
            key_type = payload.get("key_type", "public")

            if not keys_text.strip():
                return {"status": "error", "message": "请输入API keys"}

            # 解析keys
            import re
            keys = re.split(r'[,\s\n]+', keys_text.strip())
            keys = [key.strip() for key in keys if key.strip()]

            if not keys:
                return {"status": "error", "message": "未找到有效的API keys"}

            success_count = 0
            total_count = len(keys)
            errors = []

            for api_key in keys:
                success, message = self._add_key_to_db(api_key, key_type)
                if success:
                    success_count += 1
                else:
                    errors.append(f"{api_key[:8]}...: {message}")

            if success_count == total_count:
                return {
                    "status": "success",
                    "message": f"成功添加 {success_count}/{total_count} 个keys",
                    "success_count": success_count,
                    "total_count": total_count
                }
            elif success_count > 0:
                return {
                    "status": "partial",
                    "message": f"成功添加 {success_count}/{total_count} 个keys，{len(errors)} 个失败",
                    "success_count": success_count,
                    "total_count": total_count,
                    "errors": errors[:5]  # 只返回前5个错误
                }
            else:
                return {
                    "status": "error",
                    "message": f"添加失败，共 {total_count} 个keys",
                    "errors": errors[:5]
                }

        except Exception as e:
            logger.error(f"添加keys时出错：{str(e)}", exc_info=True)
            return {"status": "error", "message": f"添加keys时出错: {str(e)}"}

    def _delete_keys(self, payload: dict) -> Dict[str, Any]:
        """API Endpoint: Delete keys by indices."""
        try:
            key_indices = payload.get("key_indices", [])
            key_type = payload.get("key_type", "public")

            if not key_indices:
                return {"status": "error", "message": "请选择要删除的keys"}

            keys_data = self._get_keys_data(key_type)
            if not keys_data:
                return {"status": "error", "message": "没有找到keys数据"}

            # 按索引删除（从大到小排序以避免索引变化）
            deleted_count = 0
            for index in sorted(key_indices, reverse=True):
                if 0 <= index < len(keys_data):
                    removed_key = keys_data.pop(index)
                    # 清除缓存
                    with self._lock:
                        self._balance_cache.pop(removed_key.get("key", ""), None)
                    deleted_count += 1

            # 保存更新后的数据
            self._save_keys_data(keys_data, key_type)

            return {
                "status": "success",
                "message": f"成功删除 {deleted_count} 个keys"
            }

        except Exception as e:
            logger.error(f"删除keys时出错：{str(e)}", exc_info=True)
            return {"status": "error", "message": f"删除keys时出错: {str(e)}"}

    def _check_keys_api(self, payload: dict) -> Dict[str, Any]:
        """API Endpoint: Check keys by indices."""
        try:
            key_indices = payload.get("key_indices", [])
            key_type = payload.get("key_type", "public")

            if not key_indices:
                return {"status": "error", "message": "请选择要检查的keys"}

            keys_data = self._get_keys_data(key_type)
            if not keys_data:
                return {"status": "error", "message": "没有找到keys数据"}

            checked_count = 0
            valid_count = 0
            invalid_count = 0
            failed_count = 0

            for index in key_indices:
                if 0 <= index < len(keys_data):
                    key_info = keys_data[index]
                    api_key = key_info.get("key")
                    if not api_key:
                        continue

                    checked_count += 1
                    balance = self._check_api_key(api_key)

                    if balance is None:
                        # 检查失败
                        key_info.update({
                            "status": "check_failed",
                            "last_check": datetime.now().isoformat()
                        })
                        failed_count += 1
                    elif balance < self._min_balance_limit:
                        # 余额不足，标记为无效
                        key_info.update({
                            "balance": balance,
                            "status": "invalid",
                            "last_check": datetime.now().isoformat()
                        })
                        invalid_count += 1
                    else:
                        # 有效
                        key_info.update({
                            "balance": balance,
                            "status": "valid",
                            "last_check": datetime.now().isoformat()
                        })
                        valid_count += 1

            # 保存更新后的数据
            self._save_keys_data(keys_data, key_type)

            return {
                "status": "success",
                "message": f"检查完成：有效 {valid_count}，无效 {invalid_count}，失败 {failed_count}"
            }

        except Exception as e:
            logger.error(f"检查keys时出错：{str(e)}", exc_info=True)
            return {"status": "error", "message": f"检查keys时出错: {str(e)}"}


