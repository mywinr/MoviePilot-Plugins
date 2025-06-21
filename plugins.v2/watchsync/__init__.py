import json
import traceback
import hashlib
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Any, List, Dict, Tuple, Optional
from functools import wraps
from collections import defaultdict
import sqlite3
import os

from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import WebhookEventInfo
from app.schemas.types import EventType
from app.core.config import settings


class SyncLoopProtector:
    """
    通过一个临时缓存来防止同步操作触发无限循环。
    当一个同步操作（例如，A -> B）成功后，B 会被临时"保护"起来。
    如果在短时间内（如15秒）收到了由 B 触发的相同类型的事件，该事件将被忽略。
    """

    def __init__(self, ttl_seconds: int = 15):
        # 缓存格式: (user_name, item_id, sync_type) -> 触发时间
        self._cache: Dict[Tuple[str, str, str], datetime] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
        self._lock = threading.Lock()

    def add(self, user_name: str, item_id: str, sync_type: str):
        """
        将一个被动同步的用户-项目组合添加到忽略缓存中。
        """
        if not all([user_name, item_id, sync_type]):
            return
        with self._lock:
            cache_key = (user_name, item_id, sync_type)
            self._cache[cache_key] = datetime.now()
            logger.debug(f"添加到防循环缓存: {cache_key}")
            # 主动清理一下过期条目，防止缓存无限增长
            self._cleanup_nolock()

    def is_protected(self, user_name: str, item_id: str, sync_type: str) -> bool:
        """
        检查一个传入的事件是否是被保护的（即，可能是同步循环）。
        """
        if not all([user_name, item_id, sync_type]):
            return False

        with self._lock:
            cache_key = (user_name, item_id, sync_type)
            if cache_key in self._cache:
                event_time = self._cache[cache_key]
                if datetime.now() - event_time < self._ttl:
                    logger.info(f"🔄 检测到循环同步事件，跳过处理: {cache_key}")
                    # 不再立即移除key，让它根据TTL自然过期，以处理并发事件
                    return True
        return False

    def _cleanup_nolock(self):
        """
        在锁内执行，移除缓存中的过期条目。
        """
        now = datetime.now()
        expired_keys = [
            key for key, timestamp in self._cache.items() if now - timestamp > self._ttl]
        for key in expired_keys:
            try:
                del self._cache[key]
            except KeyError:
                pass  # Already deleted by another thread


def retry_on_failure(max_retries=3, base_delay=1, max_delay=60, backoff_factor=2):
    """
    装饰器：为函数添加指数退避重试机制
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    result = func(*args, **kwargs)
                    if result:  # 如果成功，直接返回
                        return result
                    elif attempt == max_retries:  # 最后一次尝试失败
                        logger.error(
                            f"{func.__name__} 在 {max_retries} 次重试后仍然失败")
                        return False
                except Exception as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 重试 {max_retries} 次后仍然出现异常: {str(e)}")
                        raise e

                # 计算延迟时间（指数退避 + 随机抖动）
                delay = min(
                    base_delay * (backoff_factor ** attempt), max_delay)
                jitter = random.uniform(0, delay * 0.1)  # 添加10%的随机抖动
                total_delay = delay + jitter

                logger.warning(
                    f"{func.__name__} 第 {attempt + 1} 次尝试失败，{total_delay:.2f}秒后重试")
                time.sleep(total_delay)

            return False
        return wrapper
    return decorator


class WatchSync(_PluginBase):
    # 插件名称
    plugin_name = "Emby观看记录同步"
    # 插件描述
    plugin_desc = "在不同用户之间同步观看记录（自用插件，不保证兼容性）"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/emby_watch_sync.png"
    # 插件版本
    plugin_version = "1.0"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "watchsync_"
    # 加载顺序
    plugin_order = 20
    # 可使用的用户级别
    auth_level = 2

    def __init__(self):
        super().__init__()
        self._enabled = False
        self._sync_groups = []  # 改为同步组列表
        self._sync_movies = True
        self._sync_tv = True
        self._sync_favorite = True  # 是否同步收藏事件
        self._sync_played = True    # 是否同步播放完成事件
        self._min_watch_time = 300  # 最小观看时间（秒）
        self._emby_instances = {}
        self._db_path = None
        # 事件去重相关
        self._event_timestamps = {}
        self._sync_metrics = {
            'total_events': 0,
            'successful_syncs': 0,
            'failed_syncs': 0,
            'duplicate_events': 0,
            'api_errors': defaultdict(int),
            'last_sync_time': None
        }
        # 并发控制
        self._sync_lock = threading.RLock()  # 可重入锁
        self._active_syncs = {}  # 跟踪正在进行的同步
        self._max_concurrent_syncs = 3  # 最大并发同步数
        self._loop_protector = SyncLoopProtector(ttl_seconds=30)  # 用于防止同步循环
        self._init_database()

    def init_plugin(self, config: dict = None):
        """
        生效配置信息
        """
        logger.info("开始初始化观看记录同步插件...")

        if config:
            self._enabled = config.get("enabled", False)
            self._sync_groups = config.get("sync_groups", [])
            self._sync_movies = config.get("sync_movies", True)
            self._sync_tv = config.get("sync_tv", True)
            self._sync_favorite = config.get("sync_favorite", True)
            self._sync_played = config.get("sync_played", True)
            self._min_watch_time = config.get("min_watch_time", 300)
            logger.info(f"加载配置: enabled={self._enabled}, sync_groups={len(self._sync_groups)}, "
                        f"sync_favorite={self._sync_favorite}, sync_played={self._sync_played}")

        # 获取Emby服务器实例
        self._load_emby_instances()

        # 记录API端点信息（简化日志）
        api_endpoints = self.get_api()
        logger.info(f"注册了 {len(api_endpoints)} 个API端点")

        if self._enabled:
            logger.info("观看记录同步插件已启用")
        else:
            logger.info("观看记录同步插件已禁用")

    def _generate_event_fingerprint(self, event_data: WebhookEventInfo) -> str:
        """
        生成更可靠的事件指纹 - 修复版本
        """
        # 提取关键信息
        json_obj = event_data.json_object
        user_id = json_obj.get("User", {}).get("Id", "")
        item_id = json_obj.get("Item", {}).get("Id", "")
        session_id = json_obj.get("Session", {}).get("Id", "")

        # 对于观看进度，使用范围而不是精确值，避免微小差异导致重复处理
        position_ticks = (json_obj.get("Session", {}).get("PositionTicks", 0) or
                          json_obj.get("PlaybackInfo", {}).get("PositionTicks", 0))

        # 将位置四舍五入到最近的10秒（100,000,000 ticks = 10秒）
        position_rounded = (position_ticks // 100000000) * 100000000

        # 创建更精确的指纹，但允许位置的小幅变化
        fingerprint_data = (f"{event_data.channel}_{event_data.event}_"
                            f"{user_id}_{item_id}_{session_id}_{position_rounded}")

        # 使用SHA256生成指纹，避免hash冲突
        fingerprint = hashlib.sha256(fingerprint_data.encode()).hexdigest()
        logger.debug(f"生成事件指纹: {fingerprint_data} -> {fingerprint[:16]}...")
        return fingerprint

    def _is_duplicate_event(self, event_fingerprint: str, time_window_seconds: int = 30) -> bool:
        """
        检查是否为重复事件（基于时间窗口）- 修复版本
        缩短时间窗口，避免过度过滤正常事件
        """
        current_time = datetime.now()

        # 清理过期的事件记录
        cutoff_time = current_time - \
            timedelta(seconds=time_window_seconds * 2)  # 保留更长时间用于清理
        expired_events = [fp for fp, timestamp in self._event_timestamps.items()
                          if timestamp < cutoff_time]
        for fp in expired_events:
            del self._event_timestamps[fp]

        # 检查是否为重复事件
        if event_fingerprint in self._event_timestamps:
            last_time = self._event_timestamps[event_fingerprint]
            time_diff = current_time - last_time
            if time_diff < timedelta(seconds=time_window_seconds):
                logger.info(
                    f"🔄 检测到重复事件，跳过处理: {event_fingerprint[:16]}... (间隔: {time_diff.total_seconds():.1f}秒)")
                return True
            else:
                logger.debug(f"事件间隔足够长，允许处理: {time_diff.total_seconds():.1f}秒")

        # 记录新事件
        self._event_timestamps[event_fingerprint] = current_time
        logger.debug(f"记录新事件: {event_fingerprint[:16]}...")
        return False

    def _is_event_a_sync_loop(self, event_data: WebhookEventInfo) -> bool:
        """
        使用 SyncLoopProtector 检查事件是否由插件自身的同步操作触发。
        """
        try:
            json_obj = event_data.json_object
            user_name = json_obj.get("User", {}).get("Name")
            item_id = json_obj.get("Item", {}).get("Id")
            sync_type = self._get_sync_type_from_event(event_data)

            if not all([user_name, item_id, sync_type]):
                return False

            return self._loop_protector.is_protected(user_name, item_id, sync_type)

        except Exception as e:
            logger.error(f"检查循环事件出错: {e}")
            return False

    def _get_sync_type_from_event(self, event_data: WebhookEventInfo) -> Optional[str]:
        """ 从 webhook 事件中解析出对应的 sync_type """
        json_obj = event_data.json_object
        event_type = event_data.event
        sync_type = None

        if event_type in ["playback.pause", "playback.stop"]:
            sync_type = "playback"
        elif event_type in ["user.favorite", "item.favorite", "item.rate"]:
            is_favorite = json_obj.get("Item", {}).get(
                "UserData", {}).get("IsFavorite", False)
            sync_type = "favorite" if is_favorite else "not_favorite"
        elif event_type in ["item.markplayed", "playback.scrobble"]:
            sync_type = "mark_played"
        elif event_type == "item.markunplayed":
            sync_type = "mark_unplayed"

        return sync_type

    def _add_to_ignore_cache(self, user_name: str, item_id: str, sync_type: str):
        """
        将一个成功的同步操作添加到忽略缓存中。
        """
        if not all([user_name, item_id, sync_type]):
            return
        cache_key = (user_name, item_id, sync_type)
        self._sync_ignore_cache[cache_key] = datetime.now()
        logger.debug(f"添加到同步忽略缓存: {cache_key}")

        # 清理旧缓存
        cutoff = datetime.now() - timedelta(minutes=5)
        expired_keys = [
            k for k, v in self._sync_ignore_cache.items() if v < cutoff]
        for key in expired_keys:
            del self._sync_ignore_cache[key]

    def _update_sync_metrics(self, event_type: str, success: bool = True, error_type: str = None):
        """
        更新同步指标
        """
        if event_type == 'event_received':
            self._sync_metrics['total_events'] += 1
        elif event_type == 'sync_completed':
            if success:
                self._sync_metrics['successful_syncs'] += 1
                self._sync_metrics['last_sync_time'] = datetime.now()
            else:
                self._sync_metrics['failed_syncs'] += 1
        elif event_type == 'duplicate_event':
            self._sync_metrics['duplicate_events'] += 1
        elif event_type == 'api_error' and error_type:
            self._sync_metrics['api_errors'][error_type] += 1

    def _init_database(self):
        """
        初始化数据库
        """
        try:
            # 获取插件数据目录
            plugin_data_dir = os.path.join(
                settings.PLUGIN_DATA_PATH, "watchsync/data")
            if not os.path.exists(plugin_data_dir):
                os.makedirs(plugin_data_dir)

            self._db_path = os.path.join(plugin_data_dir, "watchsync.db")

            # 创建数据库表
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                # 同步记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        source_server TEXT NOT NULL,
                        source_user TEXT NOT NULL,
                        target_server TEXT NOT NULL,
                        target_user TEXT NOT NULL,
                        media_name TEXT NOT NULL,
                        media_type TEXT NOT NULL,
                        media_id TEXT,
                        position_ticks INTEGER,
                        sync_type TEXT DEFAULT 'playback',
                        status TEXT NOT NULL,
                        error_message TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 检查并添加sync_type字段（为了兼容旧数据库）
                try:
                    cursor.execute(
                        "ALTER TABLE sync_records ADD COLUMN sync_type TEXT DEFAULT 'playback'")
                except sqlite3.OperationalError:
                    # 字段已存在，忽略错误
                    pass

                # 统计信息表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS sync_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        date TEXT NOT NULL UNIQUE,
                        total_syncs INTEGER DEFAULT 0,
                        success_syncs INTEGER DEFAULT 0,
                        failed_syncs INTEGER DEFAULT 0,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                conn.commit()
                logger.info(f"数据库初始化完成: {self._db_path}")

        except Exception as e:
            logger.error(f"数据库初始化失败: {str(e)}")
            self._db_path = None

    def get_state(self) -> bool:
        return self._enabled

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        """获取插件仪表盘元信息"""
        return [{"key": "watchsync", "name": "观看记录同步"}]

    def get_dashboard(
        self, key: str = "", **kwargs
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """
        获取插件仪表盘页面
        """
        return (
            {"cols": 12, "md": 6},
            {
                "refresh": 30,  # 30秒刷新间隔
                "border": True,
                "title": "观看记录同步",
                "subtitle": "在不同用户之间同步观看记录和收藏状态",
                "render_mode": "vue",  # 使用Vue渲染模式
            },
            None,
        )

    def _load_emby_instances(self):
        """
        从主程序获取Emby服务器实例
        """
        try:
            from app.core.module import ModuleManager
            module_manager = ModuleManager()
            emby_module = module_manager._running_modules.get("EmbyModule")
            if emby_module and hasattr(emby_module, 'get_instances'):
                instances = emby_module.get_instances()
                if instances:
                    self._emby_instances = instances
                    logger.info(
                        f"通过ModuleManager加载了 {len(self._emby_instances)} 个Emby服务器实例")
                    return
        except Exception as e:
            logger.warning(f"ModuleManager方式获取失败: {str(e)}")

    @eventmanager.register(EventType.WebhookMessage)
    def handle_webhook_message(self, event: Event):
        """
        处理Webhook消息 - 改进版本
        """
        logger.info("收到Webhook消息")
        self._update_sync_metrics('event_received')

        if not self._enabled:
            logger.info("插件未启用，跳过处理")
            return

        if not event or not event.event_data:
            logger.warning("Webhook事件数据为空")
            return

        # 检查是否为插件自身操作触发的循环事件
        if self._is_event_a_sync_loop(event.event_data):
            self._update_sync_metrics('duplicate_events')
            return

        # 生成事件指纹并检查重复
        event_fingerprint = self._generate_event_fingerprint(event.event_data)
        if self._is_duplicate_event(event_fingerprint):
            logger.debug(f"检测到重复事件，跳过处理: {event_fingerprint[:16]}...")
            self._update_sync_metrics('duplicate_event')
            return

        # 处理WebhookEventInfo对象
        try:
            event_data: WebhookEventInfo = event.event_data

            # 只处理Emby的播放和收藏事件
            if event_data.channel != "emby":
                return

            # 支持的事件类型：播放事件、收藏事件和播放完成事件
            supported_events = [
                "playback.pause", "playback.stop",  # 播放事件
                "playback.scrobble",                # 播放完成事件
                "user.favorite", "item.favorite",   # 收藏事件（可能的事件名）
                "item.rate",                        # 评分/收藏事件（Emby客户端收藏触发）
                "library.new", "library.update",    # 库更新事件（可能包含收藏信息）
                "item.markplayed", "item.markunplayed"  # 标记播放完成/未完成事件
            ]

            if event_data.event not in supported_events:
                return

            # 提取基本信息用于日志
            json_obj = event_data.json_object
            user_name = json_obj.get("User", {}).get("Name", "Unknown")
            item_name = json_obj.get("Item", {}).get("Name", "Unknown")
            logger.info(f"处理同步事件: {user_name} - {item_name}")

            # 将WebhookEventInfo转换为字典格式
            webhook_data = {
                "channel": event_data.channel,
                "event": event_data.event,
                "server_name": event_data.server_name,
                "json_object": event_data.json_object
            }

            # 根据事件类型分发处理
            if event_data.event in ["playback.pause", "playback.stop"]:
                self._handle_playback_event(webhook_data)
            elif event_data.event in ["user.favorite", "item.favorite", "item.rate",
                                      "library.new", "library.update"]:
                self._handle_favorite_event(webhook_data)
            elif event_data.event in ["playback.scrobble", "item.markplayed",
                                      "item.markunplayed"]:
                self._handle_played_status_event(webhook_data)

        except Exception as e:
            logger.error(f"处理Webhook消息失败: {str(e)}")
            logger.error(traceback.format_exc())
            self._update_sync_metrics('api_error', False, 'webhook_processing')

    def _handle_favorite_event(self, webhook_data):
        """
        处理收藏事件
        """
        logger.info("开始处理收藏事件")

        # 检查是否启用收藏同步
        if not self._sync_favorite:
            logger.info("收藏同步已禁用，跳过处理")
            return

        # 从webhook数据中提取信息
        json_object = webhook_data.get("json_object", {})
        if not json_object:
            logger.warning("json_object为空，跳过处理")
            return

        # 提取关键信息
        server_name = webhook_data.get("server_name")
        if not server_name:
            server_info = json_object.get("Server", {})
            server_name = server_info.get("Name") or server_info.get("Id")

        if not server_name and self._emby_instances:
            server_name = list(self._emby_instances.keys())[0]

        user_name = json_object.get("User", {}).get("Name")
        item_info = json_object.get("Item", {})

        # 检查是否为收藏操作 - 尝试多种方式获取收藏状态
        is_favorite = False

        # 方式1: 直接从json_object获取
        if "IsFavorite" in json_object:
            is_favorite = json_object.get("IsFavorite", False)
        # 方式2: 从Item的UserData获取
        elif item_info.get("UserData", {}).get("IsFavorite") is not None:
            is_favorite = item_info.get(
                "UserData", {}).get("IsFavorite", False)
        # 方式3: 对于item.rate事件，检查是否为收藏操作
        elif webhook_data.get("event") == "item.rate":
            # 对于评分事件，检查UserData中的IsFavorite状态
            user_data = item_info.get("UserData", {})
            is_favorite = user_data.get("IsFavorite", False)
            logger.info(f"item.rate事件 - UserData: {user_data}")
        # 方式4: 根据事件类型判断
        elif webhook_data.get("event") in ["user.favorite", "item.favorite"]:
            # 对于收藏事件，假设是添加收藏（可能需要根据实际webhook数据调整）
            is_favorite = True

        logger.info(f"收藏事件 - 服务器: {server_name}, 用户: {user_name}")
        logger.info(
            f"媒体: {item_info.get('Name', 'Unknown')}, 收藏状态: {is_favorite}")
        logger.info(f"事件类型: {webhook_data.get('event')}")
        logger.info(f"完整webhook数据: {json_object}")

        if not all([server_name, user_name, item_info]):
            logger.warning("收藏事件数据不完整，跳过处理")
            logger.warning(
                f"server_name: {server_name}, user_name: {user_name}, item_info: {bool(item_info)}")
            return

        # 检查媒体类型是否需要同步
        item_type = item_info.get("Type")
        if item_type == "Movie" and not self._sync_movies:
            return
        if item_type in ["Episode", "Series"] and not self._sync_tv:
            return

        # 查找需要同步的目标用户
        target_users = self._find_sync_targets(server_name, user_name)
        if not target_users:
            logger.info(f"未找到用户 {user_name} 的同步目标")
            return

        # 执行收藏同步
        self._sync_favorite_to_targets(
            source_server=server_name,
            source_user=user_name,
            item_info=item_info,
            is_favorite=is_favorite,
            target_users=target_users
        )

    def _handle_played_status_event(self, webhook_data):
        """
        处理播放完成状态事件
        """
        logger.info("开始处理播放完成状态事件")

        # 检查是否启用播放完成同步
        if not self._sync_played:
            logger.info("播放完成同步已禁用，跳过处理")
            return

        # 从webhook数据中提取信息
        json_object = webhook_data.get("json_object", {})
        if not json_object:
            logger.warning("json_object为空，跳过处理")
            return

        # 提取关键信息
        server_name = webhook_data.get("server_name")
        if not server_name:
            server_info = json_object.get("Server", {})
            server_name = server_info.get("Name") or server_info.get("Id")

        if not server_name and self._emby_instances:
            server_name = list(self._emby_instances.keys())[0]

        user_name = json_object.get("User", {}).get("Name")
        item_info = json_object.get("Item", {})

        # 判断是标记为已播放还是未播放
        event_type = webhook_data.get("event")
        is_played = event_type in ["playback.scrobble", "item.markplayed"]

        logger.info(f"播放状态事件 - 服务器: {server_name}, 用户: {user_name}")
        logger.info(
            f"媒体: {item_info.get('Name', 'Unknown')}, 播放状态: {is_played}")

        if not all([server_name, user_name, item_info]):
            logger.warning("播放状态事件数据不完整，跳过处理")
            return

        # 检查媒体类型是否需要同步
        item_type = item_info.get("Type")
        if item_type == "Movie" and not self._sync_movies:
            return
        if item_type in ["Episode", "Series"] and not self._sync_tv:
            return

        # 查找需要同步的目标用户
        target_users = self._find_sync_targets(server_name, user_name)
        if not target_users:
            logger.info(f"未找到用户 {user_name} 的同步目标")
            return

        # 执行播放状态同步
        self._sync_played_status_to_targets(
            source_server=server_name,
            source_user=user_name,
            item_info=item_info,
            is_played=is_played,
            target_users=target_users
        )

    def _sync_played_status_to_targets(self, source_server, source_user, item_info,
                                       is_played, target_users):
        """
        将播放完成状态同步到目标用户
        """
        item_name = item_info.get("Name", "Unknown")

        logger.info(f"开始同步播放状态: {item_name} -> {is_played}")

        for target_server, target_user in target_users:
            try:
                # 获取目标服务器实例
                emby_instance = self._emby_instances.get(target_server)
                if not emby_instance:
                    logger.error(f"未找到服务器实例: {target_server}")
                    continue

                # 在目标服务器上查找对应的媒体项
                target_item = self._find_matching_item(
                    emby_instance, target_user, item_info
                )

                # 从返回的项目中获取ID
                if isinstance(target_item, dict):
                    target_item_id = target_item.get("Id")
                else:
                    target_item_id = target_item

                if not target_item_id:
                    logger.warning(f"在服务器 {target_server} 上未找到匹配的媒体项")
                    continue

                # 设置播放完成状态
                success = self._set_item_played_status(
                    emby_instance, target_user, target_item_id, is_played
                )

                if success:
                    # 添加到忽略缓存
                    sync_type = "mark_played" if is_played else "mark_unplayed"
                    self._loop_protector.add(
                        target_user, target_item_id, sync_type)

                # 记录同步结果
                sync_type = "mark_played" if is_played else "mark_unplayed"
                self._record_sync_result(
                    source_server=source_server,
                    source_user=source_user,
                    target_server=target_server,
                    target_user=target_user,
                    item_info=item_info,
                    position_ticks=0,
                    status="success" if success else "error",
                    error_message=None if success else "播放状态同步失败",
                    sync_type=sync_type
                )

                if success:
                    action = "标记为已播放" if is_played else "标记为未播放"
                    logger.info(
                        f"成功同步播放状态: {item_name} -> {target_user} ({action})")
                else:
                    logger.error(f"播放状态同步失败: {item_name} -> {target_user}")

            except Exception as e:
                logger.error(f"播放状态同步异常: {str(e)}")
                sync_type = "mark_played" if is_played else "mark_unplayed"
                self._record_sync_result(
                    source_server=source_server,
                    source_user=source_user,
                    target_server=target_server,
                    target_user=target_user,
                    item_info=item_info,
                    position_ticks=0,
                    status="error",
                    error_message=str(e),
                    sync_type=sync_type
                )

    def _set_item_played_status(self, emby_instance, user_name, item_id, is_played):
        """
        设置媒体项的播放完成状态
        """
        try:
            # 获取用户ID
            user_id = self._get_user_id(emby_instance, user_name)
            if not user_id:
                logger.error(f"未找到用户: {user_name}")
                return False

            # 构建API URL
            if is_played:
                url = f"[HOST]emby/Users/{user_id}/PlayedItems/{item_id}?api_key=[APIKEY]"
                response = emby_instance.post_data(url)
            else:
                # 对于取消播放状态，需要使用DELETE请求
                url = f"[HOST]emby/Users/{user_id}/PlayedItems/{item_id}?api_key=[APIKEY]"
                # 替换URL中的占位符
                actual_url = url.replace("[HOST]", emby_instance._host or '') \
                    .replace("[APIKEY]", emby_instance._apikey or '')
                # 使用RequestUtils发送DELETE请求
                from app.utils.http import RequestUtils
                response = RequestUtils().delete_res(actual_url)

            return response and response.status_code == 200

        except Exception as e:
            logger.error(f"设置播放状态失败: {str(e)}")
            return False

    def _find_sync_targets(self, source_server: str, source_user: str) -> List[Tuple[str, str]]:
        """
        查找需要同步的目标用户
        返回格式: [(target_server, target_user), ...]
        """
        target_users = []

        logger.info(f"查找同步目标 - 源用户: {source_server}:{source_user}")
        logger.info(f"当前配置的同步组数量: {len(self._sync_groups)}")

        # 查找包含源用户的同步组
        for i, group in enumerate(self._sync_groups):
            group_name = group.get("name", f"组{i+1}")
            logger.debug(
                f"检查同步组 '{group_name}' - 启用状态: {group.get('enabled', True)}")

            if not group.get("enabled", True):
                logger.debug(f"同步组 '{group_name}' 已禁用，跳过")
                continue

            # 检查源用户是否在这个同步组中
            source_user_found = False
            group_users = group.get("users", [])

            for user in group_users:
                user_server = user.get("server")
                user_name = user.get("username")

                # 检查服务器名匹配
                server_match = self._is_server_match(
                    user_server, source_server)

                if server_match and user_name == source_user:
                    source_user_found = True
                    logger.debug(f"在同步组 '{group_name}' 中找到源用户")
                    break

            if not source_user_found:
                logger.debug(f"源用户不在同步组 '{group_name}' 中")
                continue

            # 添加组内其他所有用户作为同步目标
            for target_user in group.get("users", []):
                target_server = target_user.get("server")
                target_username = target_user.get("username")

                # 跳过源用户自己
                server_match = self._is_server_match(
                    target_server, source_server)
                if server_match and target_username == source_user:
                    continue

                # 获取实际的目标服务器名称
                actual_target_server = self._get_actual_server_name(
                    target_server)
                if not actual_target_server:
                    logger.warning(f"无法找到目标服务器的实际名称: {target_server}")
                    continue

                target_users.append((actual_target_server, target_username))
                logger.debug(
                    f"添加同步目标: {actual_target_server}:{target_username}")

        logger.info(f"找到 {len(target_users)} 个同步目标用户")
        return target_users

    def _sync_favorite_to_targets(self, source_server, source_user, item_info,
                                  is_favorite, target_users):
        """
        将收藏状态同步到目标用户
        """
        item_name = item_info.get("Name", "Unknown")
        item_id = item_info.get("Id")

        logger.info(f"开始同步收藏状态: {item_name} -> {is_favorite}")

        for target_server, target_user in target_users:
            try:
                # 获取目标服务器实例
                emby_instance = self._emby_instances.get(target_server)
                if not emby_instance:
                    logger.error(f"未找到服务器实例: {target_server}")
                    continue

                # 在目标服务器上查找对应的媒体项
                target_item = self._find_matching_item(
                    emby_instance, target_user, item_info
                )

                # 从返回的项目中获取ID
                if isinstance(target_item, dict):
                    target_item_id = target_item.get("Id")
                else:
                    target_item_id = target_item

                if not target_item_id:
                    logger.warning(f"在服务器 {target_server} 上未找到匹配的媒体项")
                    continue

                # 设置收藏状态
                success = self._set_item_favorite(
                    emby_instance, target_user, target_item_id, is_favorite
                )

                if success:
                    # 添加到忽略缓存
                    sync_type = "favorite" if is_favorite else "not_favorite"
                    self._loop_protector.add(
                        target_user, target_item_id, sync_type)

                # 记录同步结果 - 区分收藏和取消收藏
                sync_type = "favorite" if is_favorite else "not_favorite"
                self._record_sync_result(
                    source_server=source_server,
                    source_user=source_user,
                    target_server=target_server,
                    target_user=target_user,
                    item_info=item_info,
                    position_ticks=0,
                    status="success" if success else "error",
                    error_message=None if success else "收藏同步失败",
                    sync_type=sync_type
                )

                if success:
                    action = "收藏" if is_favorite else "取消收藏"
                    logger.info(f"成功同步{action}: {item_name} -> {target_user}")
                else:
                    logger.error(f"收藏同步失败: {item_name} -> {target_user}")

            except Exception as e:
                logger.error(f"收藏同步异常: {str(e)}")
                # 在异常情况下也区分收藏和取消收藏
                sync_type = "favorite" if is_favorite else "not_favorite"
                self._record_sync_result(
                    source_server=source_server,
                    source_user=source_user,
                    target_server=target_server,
                    target_user=target_user,
                    item_info=item_info,
                    position_ticks=0,
                    status="error",
                    error_message=str(e),
                    sync_type=sync_type
                )

    def _set_item_favorite(self, emby_instance, user_name, item_id, is_favorite):
        """
        设置媒体项的收藏状态
        """
        try:
            # 获取用户ID
            user_id = self._get_user_id(emby_instance, user_name)
            if not user_id:
                logger.error(f"未找到用户: {user_name}")
                return False

            logger.info(
                f"设置收藏状态: user_id={user_id}, item_id={item_id}, is_favorite={is_favorite}")

            # 构建API URL - 使用正确的Emby API格式
            if is_favorite:
                url = f"[HOST]emby/Users/{user_id}/FavoriteItems/{item_id}?api_key=[APIKEY]"
                response = emby_instance.post_data(url, data="")
            else:
                # 对于取消收藏，需要使用DELETE请求
                url = f"[HOST]emby/Users/{user_id}/FavoriteItems/{item_id}?api_key=[APIKEY]"
                # 替换URL中的占位符
                actual_url = url.replace("[HOST]", emby_instance._host or '') \
                    .replace("[APIKEY]", emby_instance._apikey or '')
                # 使用RequestUtils发送DELETE请求
                from app.utils.http import RequestUtils
                response = RequestUtils().delete_res(actual_url)

            if response:
                logger.info(f"收藏API响应状态: {response.status_code}")
                if response.status_code in [200, 204]:
                    logger.info(f"成功设置收藏状态: {is_favorite}")
                    return True
                else:
                    logger.error(
                        f"收藏API调用失败: {response.status_code}, {response.text}")
                    return False
            else:
                logger.error("收藏API调用无响应")
                return False

        except Exception as e:
            logger.error(f"设置收藏状态失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _get_user_id(self, emby_instance, user_name):
        """
        获取用户ID
        """
        try:
            url = f"[HOST]emby/Users?api_key=[APIKEY]"
            response = emby_instance.get_data(url)

            if response and response.status_code == 200:
                users = response.json()
                for user in users:
                    if user.get("Name") == user_name:
                        return user.get("Id")

            return None
        except Exception as e:
            logger.error(f"获取用户ID失败: {str(e)}")
            return None

    def _cleanup_expired_syncs(self):
        """
        清理过期的同步记录
        """
        current_time = datetime.now()
        expired_threshold = timedelta(minutes=10)  # 10分钟超时

        with self._sync_lock:
            expired_keys = [
                key for key, start_time in self._active_syncs.items()
                if current_time - start_time > expired_threshold
            ]

            for key in expired_keys:
                logger.warning(f"清理过期同步: {key}")
                del self._active_syncs[key]

    def get_sync_status(self) -> dict:
        """
        获取同步状态信息
        """
        with self._sync_lock:
            return {
                "metrics": dict(self._sync_metrics),
                "active_syncs": len(self._active_syncs),
                "max_concurrent": self._max_concurrent_syncs,
                "event_cache_size": len(self._event_timestamps),
                "emby_servers": len(self._emby_instances),
                "sync_groups": len([g for g in self._sync_groups if g.get("enabled", True)])
            }

    def _handle_playback_event(self, webhook_data):
        """
        处理播放事件
        """
        logger.info("开始处理播放事件")
        logger.debug(f"Webhook数据: {webhook_data}")

        # 从webhook数据中提取信息
        json_object = webhook_data.get("json_object", {})
        if not json_object:
            logger.warning("json_object为空，跳过处理")
            return

        # 提取关键信息
        # 尝试多种方式获取服务器名称
        server_name = webhook_data.get("server_name")
        if not server_name:
            # 从Server字段获取服务器名称
            server_info = json_object.get("Server", {})
            server_name = server_info.get("Name") or server_info.get("Id")

        # 如果还是没有服务器名称，尝试使用第一个可用的服务器
        if not server_name and self._emby_instances:
            server_name = list(self._emby_instances.keys())[0]
            logger.info(f"未找到服务器名称，使用第一个可用服务器: {server_name}")

        user_name = json_object.get("User", {}).get("Name")
        item_info = json_object.get("Item", {})
        session_info = json_object.get("Session", {})

        # 尝试从PlaybackInfo获取观看进度信息
        playback_info = json_object.get("PlaybackInfo", {})
        if not session_info.get("PositionTicks") and playback_info.get("PositionTicks"):
            session_info["PositionTicks"] = playback_info.get("PositionTicks")

        logger.info(f"提取的信息 - 服务器: {server_name}, 用户: {user_name}")
        logger.info(
            f"媒体信息: {item_info.get('Name', 'Unknown')} ({item_info.get('Type', 'Unknown')})")
        logger.info(f"观看进度: {session_info.get('PositionTicks', 0)} ticks")

        if not all([server_name, user_name, item_info]):
            logger.warning("Webhook数据不完整，跳过处理")
            logger.warning(
                f"server_name: {server_name}, user_name: {user_name}, item_info: {bool(item_info)}")
            return

        # 检查媒体类型是否需要同步
        item_type = item_info.get("Type")
        if item_type == "Movie" and not self._sync_movies:
            return
        if item_type in ["Episode", "Series"] and not self._sync_tv:
            return

        # 检查观看时长 - 尝试多个数据源
        play_duration_ticks = session_info.get("PlayDurationTicks", 0)
        if not play_duration_ticks:
            # 尝试从PlaybackInfo获取
            playback_info = json_object.get("PlaybackInfo", {})
            play_duration_ticks = playback_info.get("PlayDurationTicks", 0)

        # 如果还是没有，尝试从Item的RunTimeTicks计算
        if not play_duration_ticks:
            item_runtime = item_info.get("RunTimeTicks", 0)
            position_ticks = session_info.get(
                "PositionTicks", 0) or playback_info.get("PositionTicks", 0)
            if item_runtime and position_ticks:
                # 假设播放时长等于观看进度（对于暂停/停止事件）
                play_duration_ticks = position_ticks

        play_duration = play_duration_ticks / 10000000  # 转换为秒
        logger.info(
            f"计算的观看时长: {play_duration}s (来源: {play_duration_ticks} ticks)")

        if play_duration < self._min_watch_time:
            logger.info(
                f"观看时长 {play_duration}s 小于最小时长 {self._min_watch_time}s，跳过同步")
            return

        # 获取观看进度
        position_ticks = session_info.get("PositionTicks", 0)
        if not position_ticks:
            position_ticks = playback_info.get("PositionTicks", 0)

        logger.info(
            f"观看进度: {position_ticks} ticks ({position_ticks / 10000000:.1f}s)")

        logger.info(
            f"开始同步观看记录: 服务器={server_name}, 用户={user_name}, 媒体={item_info.get('Name')}")

        # 查找需要同步的同步组
        self._sync_to_group_users(
            server_name, user_name, item_info, position_ticks)

    def _sync_to_group_users(self, source_server: str, source_user: str, item_info: dict, position_ticks: int):
        """
        同步到同步组内的其他用户
        """
        logger.info(f"开始查找同步组 - 源用户: {source_server}:{source_user}")
        logger.info(f"当前配置的同步组数量: {len(self._sync_groups)}")
        logger.info(f"可用的Emby服务器实例: {list(self._emby_instances.keys())}")

        synced_count = 0

        # 查找包含源用户的同步组
        for i, group in enumerate(self._sync_groups):
            group_name = group.get("name", f"组{i+1}")
            logger.info(
                f"检查同步组 '{group_name}' - 启用状态: {group.get('enabled', True)}")

            if not group.get("enabled", True):
                logger.info(f"同步组 '{group_name}' 已禁用，跳过")
                continue

            # 检查源用户是否在这个同步组中
            source_user_found = False
            group_users = group.get("users", [])
            logger.info(f"同步组 '{group_name}' 包含 {len(group_users)} 个用户")

            for user in group_users:
                user_server = user.get("server")
                user_name = user.get("username")
                logger.info(f"检查用户: {user_server}:{user_name}")

                # 改进服务器名匹配逻辑
                server_match = self._is_server_match(
                    user_server, source_server)
                logger.info(
                    f"服务器匹配结果: {user_server} vs {source_server} = {server_match}")

                if server_match and user_name == source_user:
                    source_user_found = True
                    logger.info(f"在同步组 '{group_name}' 中找到源用户")
                    break

            if not source_user_found:
                logger.info(f"源用户不在同步组 '{group_name}' 中")
                continue

            # 同步到组内其他所有用户
            logger.info(f"开始向同步组 '{group_name}' 内的其他用户同步")

            for target_user in group.get("users", []):
                target_server = target_user.get("server")
                target_username = target_user.get("username")

                # 跳过源用户自己
                server_match = self._is_server_match(
                    target_server, source_server)
                if server_match and target_username == source_user:
                    logger.info(f"跳过源用户自己: {target_server}:{target_username}")
                    continue

                # 获取实际的目标服务器名称（用于API调用）
                actual_target_server = self._get_actual_server_name(
                    target_server)
                if not actual_target_server:
                    logger.warning(f"无法找到目标服务器的实际名称: {target_server}")
                    logger.warning(
                        f"可用的服务器实例: {list(self._emby_instances.keys())}")
                    continue

                logger.info(
                    f"准备同步到用户: {target_server}:{target_username} (实际服务器: {actual_target_server})")
                logger.info(
                    f"目标服务器实例是否存在: {actual_target_server in self._emby_instances}")

                if self._sync_watch_progress_with_retry(source_server, source_user, actual_target_server, target_username, item_info, position_ticks):
                    synced_count += 1
                    logger.info(
                        f"同步到组内用户成功: {target_server}:{target_username}")
                    self._update_sync_metrics('sync_completed', True)
                else:
                    logger.warning(
                        f"同步到组内用户失败: {target_server}:{target_username}")
                    self._update_sync_metrics('sync_completed', False)

        if synced_count > 0:
            logger.info(f"成功同步到 {synced_count} 个组内用户")
        else:
            logger.info("未找到匹配的同步组或同步失败")

    def _is_server_match(self, config_server: str, actual_server: str) -> bool:
        """
        检查配置中的服务器名是否与实际服务器名匹配 - 改进版本
        支持多种匹配方式：
        1. 精确匹配（最高优先级）
        2. 配置中使用"Emby"作为通用名称时，匹配任何Emby服务器
        3. 严格的部分匹配（避免误匹配）
        """
        if not config_server or not actual_server:
            return False

        # 精确匹配（最高优先级）
        if config_server == actual_server:
            logger.debug(f"服务器精确匹配: {config_server}")
            return True

        # 如果配置中使用"Emby"作为通用名称，匹配任何Emby服务器实例
        if config_server.lower() == "emby":
            logger.debug(f"服务器通用匹配: {config_server} -> {actual_server}")
            return True

        # 改进的部分匹配逻辑 - 更严格的匹配条件
        config_lower = config_server.lower()
        actual_lower = actual_server.lower()

        # 只有当配置的服务器名是实际服务器名的子串，且长度足够时才匹配
        # 避免短名称误匹配（如"a"匹配"abc"）
        min_match_length = 3
        if (len(config_server) >= min_match_length and
            config_lower in actual_lower and
                len(config_server) / len(actual_server) > 0.3):  # 至少30%的长度匹配
            logger.debug(f"服务器部分匹配: {config_server} -> {actual_server}")
            return True

        # 反向匹配 - 实际服务器名是配置名的子串
        if (len(actual_server) >= min_match_length and
            actual_lower in config_lower and
                len(actual_server) / len(config_server) > 0.3):
            logger.debug(f"服务器反向匹配: {config_server} -> {actual_server}")
            return True

        logger.debug(f"服务器不匹配: {config_server} vs {actual_server}")
        return False

    def _get_actual_server_name(self, config_server: str) -> Optional[str]:
        """
        根据配置中的服务器名获取实际的服务器名称
        """
        if not config_server:
            return None

        # 如果配置的服务器名直接存在于实例中，直接返回
        if config_server in self._emby_instances:
            return config_server

        # 如果配置中使用"Emby"作为通用名称，返回第一个可用的服务器
        if config_server.lower() == "emby" and self._emby_instances:
            return list(self._emby_instances.keys())[0]

        # 尝试部分匹配
        for server_name in self._emby_instances.keys():
            if config_server.lower() in server_name.lower() or server_name.lower() in config_server.lower():
                return server_name

        return None

    @retry_on_failure(max_retries=3, base_delay=2, max_delay=30)
    def _sync_watch_progress_with_retry(self, source_server: str, source_user: str,
                                        target_server: str, target_user: str,
                                        item_info: dict, position_ticks: int) -> bool:
        """
        带重试机制和并发控制的观看进度同步
        """
        sync_key = f"{target_server}:{target_user}:{item_info.get('Id', '')}"

        with self._sync_lock:
            # 检查是否已有相同的同步在进行
            if sync_key in self._active_syncs:
                logger.debug(f"同步已在进行中，跳过: {sync_key}")
                return False

            # 检查并发同步数量限制
            if len(self._active_syncs) >= self._max_concurrent_syncs:
                logger.warning(
                    f"达到最大并发同步数限制 ({self._max_concurrent_syncs})，跳过同步")
                return False

            # 标记同步开始
            self._active_syncs[sync_key] = datetime.now()

        try:
            return self._sync_watch_progress(source_server, source_user, target_server,
                                             target_user, item_info, position_ticks)
        finally:
            # 清理同步标记
            with self._sync_lock:
                self._active_syncs.pop(sync_key, None)

    def _sync_watch_progress(self, source_server: str, source_user: str, target_server: str, target_user: str,
                             item_info: dict, position_ticks: int) -> bool:
        """
        同步观看进度到目标用户
        """
        try:
            # 获取目标服务器实例
            target_emby = self._emby_instances.get(target_server)
            if not target_emby:
                logger.error(f"未找到目标服务器实例: {target_server}")
                return False

            # 健康检查
            if not self._health_check_emby_connection(target_server, target_emby):
                logger.error(f"目标服务器 {target_server} 健康检查失败")
                return False

            # 在目标服务器查找对应媒体
            target_item = self._find_matching_item(
                target_emby, target_user, item_info)
            if not target_item:
                logger.warning(f"在目标服务器 {target_server} 中未找到匹配的媒体")
                return False

            # 检查目标媒体项目的数据结构
            logger.debug(f"找到的目标媒体项目类型: {type(target_item)}")
            if isinstance(target_item, dict):
                logger.debug(f"目标媒体项目字典键: {list(target_item.keys())}")
                logger.debug(f"目标媒体项目内容: {target_item}")
            else:
                logger.debug(f"目标媒体项目属性: {dir(target_item)}")
                logger.debug(f"目标媒体项目内容: {target_item}")

            # 获取媒体ID，支持不同的数据结构
            target_item_id = None
            if isinstance(target_item, dict):
                # 尝试多种可能的ID字段名
                target_item_id = (target_item.get("Id") or
                                  target_item.get("id") or
                                  target_item.get("item_id") or
                                  target_item.get("ItemId"))
                logger.info(
                    f"从字典获取ID: Id={target_item.get('Id')}, id={target_item.get('id')}, item_id={target_item.get('item_id')}, ItemId={target_item.get('ItemId')}")
            elif hasattr(target_item, 'Id'):
                target_item_id = target_item.Id
                logger.info(f"从对象属性获取ID: {target_item_id}")
            elif hasattr(target_item, 'id'):
                target_item_id = target_item.id
                logger.info(f"从对象属性获取id: {target_item_id}")
            elif hasattr(target_item, 'item_id'):
                target_item_id = target_item.item_id
                logger.info(f"从对象属性获取item_id: {target_item_id}")

            if not target_item_id:
                logger.error(f"无法获取目标媒体的ID")
                logger.error(f"数据结构: {type(target_item)}")
                if isinstance(target_item, dict):
                    logger.error(f"字典键: {list(target_item.keys())}")
                    logger.error(f"字典内容: {target_item}")
                else:
                    logger.error(
                        f"对象属性: {[attr for attr in dir(target_item) if not attr.startswith('_')]}")
                return False

            logger.info(f"目标媒体ID: {target_item_id}")

            # 更新目标用户的观看进度
            success = self._update_user_progress(
                target_emby, target_user, target_item_id, position_ticks)

            if success:
                # 添加到忽略缓存
                self._loop_protector.add(
                    target_user, target_item_id, "playback")

            # 记录同步结果
            self._record_sync_result(
                source_server=source_server,
                source_user=source_user,
                target_server=target_server,
                target_user=target_user,
                item_info=item_info,
                position_ticks=position_ticks,
                status="success" if success else "error",
                error_message=None if success else "更新观看进度失败",
                sync_type="playback"
            )

            if success:
                logger.info(
                    f"同步成功: {target_server}:{target_user} - {item_info.get('Name')}")
                return True
            else:
                logger.error(f"更新观看进度失败: {target_server}:{target_user}")
                return False

        except Exception as e:
            logger.error(f"同步观看进度失败: {str(e)}")
            return False

    def _find_matching_item(self, emby_instance, target_user, source_item: dict) -> Optional[dict]:
        """
        在目标服务器中查找匹配的媒体项目
        """
        try:
            media_name = source_item.get("Name", "Unknown")
            media_type = source_item.get("Type", "Unknown")
            logger.info(f"开始查找匹配媒体: {media_name} ({media_type})")

            # 优先使用TMDB ID匹配
            provider_ids = source_item.get("ProviderIds", {})
            tmdb_id = provider_ids.get("Tmdb")
            imdb_id = provider_ids.get("Imdb")

            logger.info(f"媒体标识符: TMDB={tmdb_id}, IMDB={imdb_id}")

            if tmdb_id:
                logger.info(f"尝试使用TMDB ID匹配: {tmdb_id}")
                # 使用TMDB ID搜索
                if source_item.get("Type") == "Movie":
                    results = emby_instance.get_movies(
                        title="", tmdb_id=int(tmdb_id))
                    logger.info(
                        f"电影TMDB搜索结果数量: {len(results) if results else 0}")
                else:
                    # 对于电视剧，需要特殊处理
                    results = self._search_tv_by_tmdb(emby_instance, tmdb_id)
                    logger.info(
                        f"电视剧TMDB搜索结果数量: {len(results) if results else 0}")

                if results:
                    result_item = results[0].__dict__ if hasattr(
                        results[0], '__dict__') else results[0]
                    logger.info(
                        f"TMDB匹配成功: {result_item.get('Name', 'Unknown')}")
                    return result_item
                else:
                    logger.info("TMDB匹配失败，继续尝试其他方式")

            # 如果TMDB ID匹配失败，尝试IMDB ID
            if imdb_id:
                logger.info(f"尝试使用IMDB ID匹配: {imdb_id}")
                # 这里可以添加IMDB ID搜索逻辑
                pass

            # 最后尝试名称匹配
            title = source_item.get("Name")
            year = source_item.get("ProductionYear")
            logger.info(f"尝试名称匹配: {title} ({year})")

            if title:
                try:
                    logger.info(f"通过名称搜索媒体: {title} ({year})")

                    user_id = emby_instance.get_user(target_user)
                    if not user_id:
                        logger.error(f"未找到用户: {target_user}")
                        return False
                    # 构建搜索URL
                    search_url = ''
                    if source_item.get("Type") == "Movie":
                        search_url = f"[HOST]emby/Users/{user_id}/Items?api_key=[APIKEY]&Recursive=true&IncludeItemTypes=Movie&SearchTerm={title}"
                    elif source_item.get("Type") in ["Episode", "Series"]:
                        search_url = f"[HOST]emby/Users/{user_id}/Items?api_key=[APIKEY]&Recursive=true&IncludeItemTypes=Series,Episode&SearchTerm={title}"
                    if year:
                        search_url += f"&Years={year}"

                    response = emby_instance.get_data(search_url)
                    if response and response.status_code == 200:
                        items = response.json().get("Items", [])
                        logger.info(f"名称搜索到 {len(items)} 个电视剧项目")

                        # 优先返回完全匹配的项目
                        results = None
                        for item in items:
                            if item.get("Name", "").lower() == title.lower():
                                logger.info(f"找到完全匹配的媒体: {item.get('Name')}")
                                results = [item]

                        # 如果没有完全匹配，返回第一个结果
                        if items and results is None:
                            logger.info(f"返回第一个搜索结果: {items[0].get('Name')}")
                            results = [items[0]]
                        else:
                            logger.info("未找到名称匹配的媒体")
                    else:
                        logger.warning(
                            f"媒体名称搜索API调用失败: {response.status_code if response else 'No response'}")

                    logger.info(
                        f"媒体名称搜索结果数量: {len(results) if results else 0}")
                    if results:
                        result_item = results[0].__dict__ if hasattr(
                            results[0], '__dict__') else results[0]
                        logger.info(
                            f"媒体名称匹配成功: {result_item.get('Name', 'Unknown')}")
                        return result_item
                    else:
                        return None

                except Exception as e:
                    logger.error(f"通过名称搜索电视剧失败: {str(e)}")
                    return None

            logger.warning(f"所有匹配方式都失败，未找到匹配的媒体: {media_name}")
            return None

        except Exception as e:
            logger.error(f"查找匹配媒体失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    def _search_tv_by_tmdb(self, emby_instance, tmdb_id: str):
        """
        通过TMDB ID搜索电视剧
        """
        try:
            logger.info(f"通过TMDB ID搜索电视剧: {tmdb_id}")

            # 尝试使用通用搜索API
            # 构建搜索URL
            search_url = f"[HOST]emby/Items?api_key=[APIKEY]&Recursive=true&IncludeItemTypes=Series,Episode&Fields=ProviderIds"

            response = emby_instance.get_data(search_url)
            if response and response.status_code == 200:
                items = response.json().get("Items", [])
                logger.info(f"搜索到 {len(items)} 个电视剧项目")

                # 查找匹配的TMDB ID
                for item in items:
                    provider_ids = item.get("ProviderIds", {})
                    if provider_ids.get("Tmdb") == tmdb_id:
                        logger.info(f"找到TMDB匹配的电视剧: {item.get('Name')}")
                        return [item]

                logger.info("未找到TMDB匹配的电视剧")
            else:
                logger.warning(
                    f"电视剧搜索API调用失败: {response.status_code if response else 'No response'}")

            return None

        except Exception as e:
            logger.error(f"通过TMDB ID搜索电视剧失败: {str(e)}")
            return None

    def _update_user_progress(self, emby_instance, user_name: str, item_id: str, position_ticks: int) -> bool:
        """
        更新用户观看进度
        """
        try:
            # 获取用户ID
            user_id = emby_instance.get_user(user_name)
            if not user_id:
                logger.error(f"未找到用户: {user_name}")
                return False

            success = self._update_progress_via_userdata(
                emby_instance, user_id, item_id, position_ticks)
            if success:
                return True

        except Exception as e:
            logger.error(f"更新用户观看进度失败: {str(e)}")
            return False

    def _update_progress_via_userdata(self, emby_instance, user_id: str, item_id: str, position_ticks: int) -> bool:
        """
        通过UserData API更新播放进度 - 修复版本
        """
        try:
            logger.info(
                f"使用UserData API更新进度: user_id={user_id}, item_id={item_id}, position={position_ticks}")

            # 首先获取当前的UserData以保持其他字段不变
            current_userdata = self._get_current_userdata(
                emby_instance, user_id, item_id)
            logger.debug(f"当前UserData: {current_userdata}")

            url = f"[HOST]emby/Users/{user_id}/Items/{item_id}/UserData"

            # 构建UserData更新请求 - 只包含必要字段
            data = {
                "PlaybackPositionTicks": position_ticks,
                "LastPlayedDate": datetime.now().isoformat() + "Z"  # 更新最后播放时间
            }

            # 保持现有的重要字段
            if current_userdata.get("PlayCount") is not None:
                data["PlayCount"] = current_userdata["PlayCount"]
            if current_userdata.get("IsFavorite") is not None:
                data["IsFavorite"] = current_userdata["IsFavorite"]
            if current_userdata.get("Rating") is not None:
                data["Rating"] = current_userdata["Rating"]
            if current_userdata.get("PlayCount") is not None:
                data["PlayCount"] = current_userdata["PlayCount"]
            if current_userdata.get("Played") is not None:
                data["Played"] = current_userdata["Played"]

            url_with_params = f"{url}?api_key=[APIKEY]"
            logger.debug(f"UserData API请求: {url_with_params}")
            logger.debug(f"请求数据: {data}")

            response = emby_instance.post_data(url_with_params, json.dumps(data),
                                               headers={"Content-Type": "application/json"})

            if response and response.status_code in [200, 204]:
                logger.info(
                    f"UserData API成功更新用户 {user_id} 的观看进度到 {position_ticks} ticks")

                # 验证更新是否成功
                updated_userdata = self._get_current_userdata(
                    emby_instance, user_id, item_id)
                actual_position = updated_userdata.get(
                    "PlaybackPositionTicks", 0)
                logger.info(
                    f"验证更新结果: 期望={position_ticks}, 实际={actual_position}")

                return True
            else:
                logger.error(
                    f"UserData API更新失败: {response.status_code if response else 'No response'}")
                if response:
                    logger.error(f"响应内容: {response.text}")
                self._update_sync_metrics('api_error', False, 'userdata_api')
                return False

        except Exception as e:
            logger.error(f"UserData API更新观看进度失败: {str(e)}")
            logger.error(traceback.format_exc())
            self._update_sync_metrics(
                'api_error', False, 'userdata_api_exception')
            return False

    def _get_current_userdata(self, emby_instance, user_id: str, item_id: str) -> dict:
        """
        获取当前的UserData
        """
        try:
            url = f"[HOST]emby/Users/{user_id}/Items/{item_id}?api_key=[APIKEY]"
            response = emby_instance.get_data(url)

            if response and response.status_code == 200:
                item_data = response.json()
                return item_data.get("UserData", {})
            else:
                logger.warning(
                    f"获取当前UserData失败: {response.status_code if response else 'No response'}")
                return {}

        except Exception as e:
            logger.warning(f"获取当前UserData异常: {str(e)}")
            return {}

    def _get_item_runtime(self, emby_instance, item_id: str) -> int:
        """
        获取媒体项目的运行时长
        """
        try:
            url = f"[HOST]emby/Items/{item_id}?api_key=[APIKEY]"
            response = emby_instance.get_data(url)

            if response and response.status_code == 200:
                item_data = response.json()
                return item_data.get("RunTimeTicks", 0)
            else:
                return 0

        except Exception as e:
            logger.warning(f"获取媒体运行时长异常: {str(e)}")
            return 0

    def _health_check_emby_connection(self, server_name: str, emby_instance) -> bool:
        """
        检查Emby服务器连接健康状态
        """
        try:
            url = f"[HOST]emby/System/Info?api_key=[APIKEY]"
            response = emby_instance.get_data(url)

            if response and response.status_code == 200:
                server_info = response.json()
                logger.debug(
                    f"Emby服务器 {server_name} 健康检查通过: {server_info.get('ServerName', 'Unknown')}")
                return True
            else:
                logger.warning(
                    f"Emby服务器 {server_name} 健康检查失败: {response.status_code if response else 'No response'}")
                return False

        except Exception as e:
            logger.error(f"Emby服务器 {server_name} 健康检查异常: {str(e)}")
            return False

    def _record_sync_result(self, source_server: str, source_user: str, target_server: str,
                            target_user: str, item_info: dict, position_ticks: int,
                            status: str, error_message: str = None, sync_type: str = "playback"):
        """
        记录同步结果到数据库
        """
        if not self._db_path:
            return

        try:
            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                # 插入同步记录
                cursor.execute('''
                    INSERT INTO sync_records
                    (timestamp, source_server, source_user, target_server, target_user,
                     media_name, media_type, media_id, position_ticks, sync_type, status, error_message)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    source_server,
                    source_user,
                    target_server,
                    target_user,
                    item_info.get('Name', ''),
                    item_info.get('Type', ''),
                    item_info.get('Id', ''),
                    position_ticks,
                    sync_type,
                    status,
                    error_message
                ))

                # 更新统计信息
                today = datetime.now().strftime('%Y-%m-%d')
                cursor.execute('''
                    INSERT OR IGNORE INTO sync_stats (date, total_syncs, success_syncs, failed_syncs)
                    VALUES (?, 0, 0, 0)
                ''', (today,))

                if status == 'success':
                    cursor.execute('''
                        UPDATE sync_stats
                        SET total_syncs = total_syncs + 1, success_syncs = success_syncs + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE date = ?
                    ''', (today,))
                else:
                    cursor.execute('''
                        UPDATE sync_stats
                        SET total_syncs = total_syncs + 1, failed_syncs = failed_syncs + 1,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE date = ?
                    ''', (today,))

                conn.commit()

        except Exception as e:
            logger.error(f"记录同步结果失败: {str(e)}")

    def get_api(self) -> List[Dict[str, Any]]:
        """
        注册插件API
        """
        return [
            {
                "path": "/servers",
                "endpoint": self._get_servers,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取Emby服务器列表",
                "description": "获取已配置的Emby服务器列表"
            },
            {
                "path": "/users",
                "endpoint": self._get_users_endpoint,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取服务器用户列表",
                "description": "获取指定服务器的用户列表"
            },

            {
                "path": "/stats",
                "endpoint": self._get_stats,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取同步统计",
                "description": "获取同步统计信息"
            },
            {
                "path": "/records",
                "endpoint": self._get_records_endpoint,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取同步记录",
                "description": "获取历史同步记录，支持分页参数(limit, offset)"
            },
            {
                "path": "/status",
                "endpoint": self._get_status,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取同步状态",
                "description": "获取实时同步状态和指标"
            },
            {
                "path": "/records/old",
                "endpoint": self._clear_old_records_endpoint,
                "methods": ["DELETE"],
                "auth": "bear",
                "summary": "清理旧记录",
                "description": "清理指定天数前的同步记录，支持days参数"
            }
        ]

    def _get_servers(self) -> Dict[str, Any]:
        """
        获取Emby服务器列表
        """
        try:
            logger.info("API调用: 获取Emby服务器列表")
            servers = []

            if not self._emby_instances:
                logger.warning("没有找到Emby服务器实例")
                return {"success": True, "data": [], "message": "没有找到Emby服务器实例"}

            for name, instance in self._emby_instances.items():
                server_info = {
                    "name": name,
                    "host": instance._host if hasattr(instance, '_host') else "",
                    "status": "online" if instance else "offline"
                }
                servers.append(server_info)
                logger.info(f"找到服务器: {name} - {server_info['host']}")

            logger.info(f"返回 {len(servers)} 个服务器")
            return {"success": True, "data": servers}
        except Exception as e:
            logger.error(f"获取服务器列表失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _get_users_endpoint(self) -> Dict[str, Any]:
        """
        API端点：获取所有服务器的用户列表
        """
        logger.info("用户API端点调用")
        logger.info(f"当前Emby实例数量: {len(self._emby_instances)}")
        logger.info(f"Emby实例列表: {list(self._emby_instances.keys())}")

        try:
            all_users = {}
            for server_name, emby_instance in self._emby_instances.items():
                logger.info(f"开始处理服务器: {server_name}")
                logger.info(f"Emby实例是否为空: {emby_instance is None}")

                users = self._get_server_users(emby_instance)
                all_users[server_name] = users
                logger.info(f"服务器 {server_name} 获取到 {len(users)} 个用户")

                if users:
                    logger.info(f"用户详情: {users}")
                else:
                    logger.warning(f"服务器 {server_name} 用户列表为空")

            logger.info(f"最终返回数据: {all_users}")
            return {"success": True, "data": all_users}
        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return {"success": False, "message": str(e)}

    def _get_users_internal(self, server) -> Dict[str, Any]:
        """
        内部方法：获取服务器用户列表
        """
        logger.info(f"内部用户获取方法调用，服务器: '{server}'")
        logger.info(
            f"可用的Emby服务器实例: {list(self._emby_instances.keys()) if self._emby_instances else '无'}")

        # 如果没有传入server参数，尝试获取第一个可用服务器
        if not server and self._emby_instances:
            server = list(self._emby_instances.keys())[0]
            logger.info(f"未指定服务器，使用第一个可用服务器: {server}")

        # 检查服务器名称是否存在
        if server and server not in self._emby_instances:
            logger.warning(f"请求的服务器 '{server}' 不存在")
            logger.info(f"尝试模糊匹配服务器名称...")

            # 尝试模糊匹配（忽略大小写，部分匹配）
            for available_server in self._emby_instances.keys():
                if server.lower() in available_server.lower() or available_server.lower() in server.lower():
                    logger.info(
                        f"找到匹配的服务器: '{available_server}' 匹配 '{server}'")
                    server = available_server
                    break

        return self._get_users(server)

    def _get_users(self, server: str = None) -> Dict[str, Any]:
        """
        获取服务器用户列表
        """
        try:
            server_name = server
            logger.info(f"API调用: 获取服务器用户列表, 服务器: {server_name}")

            if not server_name:
                logger.warning("缺少服务器名称参数")
                available_servers = list(self._emby_instances.keys())
                return {"success": False, "message": f"缺少服务器名称参数, 可用服务器: {available_servers}"}

            emby_instance = self._emby_instances.get(server_name)
            if not emby_instance:
                logger.error(f"未找到服务器: {server_name}")
                available_servers = list(self._emby_instances.keys())
                return {"success": False, "message": f"未找到服务器: {server_name}, 可用服务器: {available_servers}"}

            # 获取用户列表
            users = self._get_server_users(emby_instance)
            logger.info(f"获取到 {len(users)} 个用户")
            return {"success": True, "data": users}

        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return {"success": False, "message": str(e)}

    def _get_server_users(self, emby_instance) -> List[Dict[str, str]]:
        """
        获取服务器用户列表
        """
        try:
            logger.info(f"开始获取Emby服务器用户列表...")
            logger.info(f"Emby实例类型: {type(emby_instance)}")

            if not emby_instance:
                logger.error("Emby实例为空")
                return []

            url = f"[HOST]emby/Users?api_key=[APIKEY]"
            logger.info(f"请求URL模板: {url}")

            # 添加调试信息，查看Emby实例的属性
            logger.info(
                f"Emby实例host: {getattr(emby_instance, '_host', 'N/A')}")
            logger.info(f"Emby实例apikey: {getattr(emby_instance, '_apikey', 'N/A')[:10]}..." if getattr(
                emby_instance, '_apikey', None) else "Emby实例apikey: N/A")

            response = emby_instance.get_data(url)
            logger.info(
                f"API响应状态: {response.status_code if response else '无响应'}")

            if response is None:
                logger.error("响应对象为None，可能是网络连接问题或URL格式错误")
            elif hasattr(response, 'url'):
                logger.info(f"实际请求URL: {response.url}")

            if response and hasattr(response, 'request') and hasattr(response.request, 'url'):
                logger.info(f"请求URL: {response.request.url}")

            if response and response.status_code == 200:
                users_data = response.json()
                logger.info(f"从Emby API获取到 {len(users_data)} 个用户")

                user_list = []
                for user in users_data:
                    user_info = {"id": user["Id"], "name": user["Name"]}
                    user_list.append(user_info)
                    logger.info(
                        f"处理用户: {user_info['name']} (ID: {user_info['id']})")

                logger.info(f"最终返回 {len(user_list)} 个用户")
                return user_list
            else:
                logger.error(
                    f"Emby API调用失败，状态码: {response.status_code if response else '无响应'}")
                if response:
                    logger.error(f"响应内容: {response.text[:200]}")
                return []

        except Exception as e:
            logger.error(f"获取用户列表失败: {str(e)}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return []

    def _get_stats(self) -> Dict[str, Any]:
        """
        获取同步统计信息
        """
        try:
            if not self._db_path:
                return {"success": False, "message": "数据库未初始化"}

            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                # 从sync_records表获取详细统计
                cursor.execute('''
                    SELECT timestamp, source_user, target_user, sync_type, status, created_at
                    FROM sync_records
                    ORDER BY created_at DESC
                ''')

                all_records = cursor.fetchall()
                total_syncs = len(all_records)
                success_syncs = len(
                    [r for r in all_records if r[4] == 'success'])
                failed_syncs = total_syncs - success_syncs

                # 计算成功率
                success_rate = (success_syncs / total_syncs *
                                100) if total_syncs > 0 else 0

                # 计算今日同步次数 - 修复时区问题
                today = datetime.now().date()
                today_syncs = 0
                for record in all_records:
                    if record[5]:  # created_at字段
                        try:
                            # 处理不同的日期格式
                            record_date_str = record[5]
                            if 'T' in record_date_str:
                                record_date = datetime.fromisoformat(
                                    record_date_str.replace('Z', '+00:00')).date()
                            else:
                                record_date = datetime.strptime(
                                    record_date_str, '%Y-%m-%d %H:%M:%S').date()

                            if record_date == today:
                                today_syncs += 1
                        except Exception as e:
                            logger.debug(f"解析日期失败: {record_date_str}, 错误: {e}")
                            continue

                # 计算活跃用户数（最近24小时）
                yesterday = datetime.now() - timedelta(hours=24)
                recent_records = [r for r in all_records if r[5] and
                                  datetime.fromisoformat(r[5]) >= yesterday]
                active_users = set()
                for record in recent_records:
                    active_users.add(record[1])  # source_user
                    active_users.add(record[2])  # target_user

                # 统计同步类型
                sync_types = set()
                for record in all_records:
                    sync_types.add(record[3] or 'playback')

                # 获取同步组数量
                enabled_groups = len(
                    [g for g in self._sync_groups if g.get("enabled", True)])
                total_users = sum(len(g.get("users", []))
                                  for g in self._sync_groups if g.get("enabled", True))

                stats = {
                    "总同步次数": total_syncs,
                    "今日同步次数": today_syncs,
                    "成功次数": success_syncs,
                    "失败次数": failed_syncs,
                    "成功率": f"{success_rate:.1f}",
                    "活跃用户数": len(active_users),
                    "同步类型": list(sync_types),
                    "同步组数": enabled_groups,
                    "组内用户数": total_users
                }

                return {"success": True, "data": stats}

        except Exception as e:
            logger.error(f"获取统计信息失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _get_records(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        获取同步记录，支持分页
        """
        try:
            if not self._db_path:
                return {"success": False, "message": "数据库未初始化"}

            # 限制最大记录数，防止性能问题
            limit = min(max(limit, 10), 100)  # 最小10条，最大100条
            offset = max(offset, 0)  # offset不能为负数

            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                # 先获取总记录数
                cursor.execute('SELECT COUNT(*) FROM sync_records')
                total_count = cursor.fetchone()[0]

                # 获取同步记录
                cursor.execute('''
                    SELECT id, timestamp, source_server, source_user, target_server, target_user,
                           media_name, media_type, sync_type, status, error_message, created_at, position_ticks
                    FROM sync_records
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                ''', (limit, offset))

                records = []
                for row in cursor.fetchall():
                    records.append({
                        "id": row[0],
                        "timestamp": row[1],
                        "source_server": row[2],
                        "source_user": row[3],
                        "target_server": row[4],
                        "target_user": row[5],
                        "media_name": row[6],
                        "media_type": row[7],
                        "sync_type": row[8],
                        "status": row[9],
                        "error_message": row[10],
                        "created_at": row[11],
                        "position_ticks": row[12]
                    })

                # 计算是否还有更多记录
                has_more = (offset + len(records)) < total_count

                return {
                    "success": True,
                    "data": records,
                    "pagination": {
                        "total": total_count,
                        "offset": offset,
                        "limit": limit,
                        "has_more": has_more,
                        "current_count": len(records)
                    }
                }

        except Exception as e:
            logger.error(f"获取同步记录失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _get_records_endpoint(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """
        API端点：获取同步记录，支持分页参数
        """
        try:
            return self._get_records(limit, offset)
        except Exception as e:
            logger.error(f"获取同步记录端点失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _clear_old_records_endpoint(self, days: int = 30) -> Dict[str, Any]:
        """
        API端点：清理旧记录，支持days参数
        """
        try:
            return self._clear_old_records(days)
        except Exception as e:
            logger.error(f"清理旧记录端点失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _get_status(self):
        """
        获取同步状态API
        """
        try:
            # 清理过期的同步记录
            self._cleanup_expired_syncs()

            # 获取状态信息
            status = self.get_sync_status()

            # 添加额外的状态信息
            status.update({
                "plugin_enabled": self._enabled,
                "sync_movies": self._sync_movies,
                "sync_tv": self._sync_tv,
                "min_watch_time": self._min_watch_time,
                "last_update": datetime.now().isoformat()
            })

            return {
                "success": True,
                "data": status
            }

        except Exception as e:
            logger.error(f"获取同步状态失败: {str(e)}")
            return {"success": False, "message": str(e)}

    def _clear_old_records(self, days: int = 30) -> Dict[str, Any]:
        """
        清理指定天数前的旧记录
        """
        try:
            if not self._db_path:
                return {"success": False, "message": "数据库未初始化"}

            # 限制天数范围，防止误删
            days = max(min(days, 365), 1)  # 最小1天，最大365天
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()

            with sqlite3.connect(self._db_path) as conn:
                cursor = conn.cursor()

                # 删除指定天数前的记录
                cursor.execute('''
                    DELETE FROM sync_records
                    WHERE created_at < ?
                ''', (cutoff_date,))

                deleted_count = cursor.rowcount
                conn.commit()

                logger.info(f"清理了 {deleted_count} 条旧记录")
                return {
                    "success": True,
                    "message": f"成功清理了 {deleted_count} 条{days}天前的记录"
                }

        except Exception as e:
            logger.error(f"清理旧记录失败: {str(e)}")
            return {"success": False, "message": str(e)}

    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """
        获取插件渲染模式
        """
        return "vue", "dist/assets"

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """
        拼装插件配置页面，返回Vue组件配置
        """
        # 返回空配置，使用Vue组件
        return [], {}

    def get_page(self) -> List[dict]:
        """
        拼装插件详情页面，返回Vue组件配置
        """
        # 返回空配置，使用Vue组件
        return []

    def stop_service(self):
        """
        退出插件
        """
        logger.info("观看记录同步插件已停止")
