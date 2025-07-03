import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from xml.dom import minidom
import platform
import threading

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from watchdog.events import FileSystemEventHandler
from watchdog.observers.polling import PollingObserver

from app.plugins.embyrating.DoubanHelper import DoubanHelper

from app.core.config import settings
from app.core.event import eventmanager, Event
from app.core.metainfo import MetaInfoPath
from app.chain.media import MediaChain
from app.schemas import FileItem
from app.schemas.types import EventType, MediaType
from app.plugins import _PluginBase
from app.log import logger
from app.schemas import NotificationType


class NFOFileHandler(FileSystemEventHandler):
    """NFO文件监控处理器"""

    def __init__(self, emby_rating_instance):
        super().__init__()
        self.emby_rating = emby_rating_instance

    def on_created(self, event):
        """文件创建事件"""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # 只处理.nfo文件
        if file_path.suffix.lower() != '.nfo':
            return

        # 过滤掉一些不需要的文件
        filename = file_path.name.lower()
        if filename in ['fanart.nfo', 'poster.nfo', 'banner.nfo', 'thumb.nfo']:
            return

        logger.info(f"检测到新NFO文件: {file_path}")

        # 直接处理文件，不使用线程池
        try:
            self.emby_rating._handle_new_nfo_file(file_path)
        except Exception as e:
            logger.error(f"处理NFO文件失败: {str(e)}")


class EmbyRating(_PluginBase):
    # 插件名称
    plugin_name = "Emby评分管理"
    # 插件描述
    plugin_desc = "修改Emby媒体评分，支持豆瓣评分和TMDB评分切换"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/emby_rating.png"
    # 插件版本
    plugin_version = "1.4"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "embyrating"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1
    # 支持的媒体文件扩展名
    MEDIA_EXTENSIONS = {'.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.strm'}



    # 私有属性
    _enabled = False
    _cron = None
    _notify = False
    _onlyonce = False
    _rating_source = "tmdb"  # tmdb 或 douban
    _update_interval = 7  # 豆瓣评分更新间隔（天）
    _auto_scrape = True  # 是否自动刮削
    _cache_enabled = True  # 缓存功能默认开启
    _media_dirs = ""  # 媒体目录，多个用逗号分隔
    _refresh_library = True  # 是否在更新NFO后刷新媒体库
    _douban_cookie = ""  # 豆瓣cookie配置
    _file_monitor_enabled = False  # 是否启用文件监控

    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None

    # 文件监控相关
    _file_observers = []
    _monitor_thread = None
    _monitor_stop_event = None

    # 评分缓存 {media_key: {"rating": float, "last_update": timestamp}}
    _rating_cache: Dict[str, Dict] = {}

    # 处理结果收集器，用于批量通知
    _processing_results: List[Dict] = []
    # 失败结果收集器
    _failed_results: List[Dict] = []
    # 跳过结果收集器
    _skipped_results: List[Dict] = []

    # 停止标志，用于中断长时间运行的任务
    _should_stop = False

    def __choose_observer(self, force_polling=False):
        """
        选择最优的监控模式
        :param force_polling: 是否强制使用轮询模式（适用于有大量软连接的目录）
        """
        if force_polling:
            logger.info("强制使用 PollingObserver 监控模式")
            return PollingObserver()

        system = platform.system()

        try:
            if system == "Linux":
                from watchdog.observers.inotify import InotifyObserver
                logger.debug("使用 InotifyObserver 监控模式")
                return InotifyObserver()
            elif system == "Darwin":
                from watchdog.observers.fsevents import FSEventsObserver
                logger.debug("使用 FSEventsObserver 监控模式")
                return FSEventsObserver()
            elif system == "Windows":
                from watchdog.observers.read_directory_changes import WindowsApiObserver
                logger.debug("使用 WindowsApiObserver 监控模式")
                return WindowsApiObserver()
        except Exception as error:
            logger.warn(f"导入模块错误：{error}，将使用 PollingObserver 监控目录")

        logger.info("使用 PollingObserver 监控模式")
        return PollingObserver()

    def init_plugin(self, config: dict = None):
        """初始化插件"""
        # 停止现有任务
        self.stop_service()

        if config:
            self._enabled = config.get("enabled")
            self._cron = config.get("cron")
            self._notify = config.get("notify")
            self._onlyonce = config.get("onlyonce")
            self._rating_source = config.get("rating_source", "tmdb")
            self._update_interval = config.get("update_interval", 7)
            self._auto_scrape = config.get("auto_scrape", True)
            # 缓存功能默认开启，不再从配置读取
            self._cache_enabled = True
            self._media_dirs = config.get("media_dirs", "")
            self._refresh_library = config.get("refresh_library", True)
            self._douban_cookie = config.get("douban_cookie", "")
            self._file_monitor_enabled = config.get("file_monitor_enabled", False)
            self._douban_helper = DoubanHelper(user_cookie=self._douban_cookie)

        # 加载缓存数据
        self._load_cache_data()

        # 初始化处理结果收集器
        self._processing_results = []
        self._failed_results = []
        self._skipped_results = []

        if self._enabled:
            # 启动定时任务
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)

            if self._onlyonce:
                logger.info(f"立即运行一次评分更新")
                self._scheduler.add_job(
                    func=self.update_all_ratings,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(
                        settings.TZ)) + timedelta(seconds=3),
                    name="立即更新评分",
                )
                self._onlyonce = False
                self._update_config()

            # 启动文件监控
            if self._file_monitor_enabled:
                self._start_file_monitor()

            if self._cron:
                logger.info(f"启动定时任务：{self._cron}")
                self._scheduler.add_job(
                    func=self.update_all_ratings,
                    trigger=CronTrigger.from_crontab(self._cron),
                    name="定时更新评分",
                )

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()


    def get_state(self) -> bool:
        """获取插件运行状态"""
        return self._enabled

    def _update_config(self):
        """更新配置"""
        self.update_config({
            "enabled": self._enabled,
            "cron": self._cron,
            "notify": self._notify,
            "onlyonce": self._onlyonce,
            "rating_source": self._rating_source,
            "update_interval": self._update_interval,
            "auto_scrape": self._auto_scrape,
            "media_dirs": self._media_dirs,
            "refresh_library": self._refresh_library,
            "douban_cookie": self._douban_cookie,
            "file_monitor_enabled": self._file_monitor_enabled
        })

    def _cleanup_cache(self):
        """清理过期和无效的缓存数据"""
        try:
            current_time = time.time()
            # 缓存最大保留时间（2倍更新间隔）
            max_cache_age = self._update_interval * 24 * 3600 * 2

            # 清理评分缓存
            if self._rating_cache:
                expired_keys = []

                for cache_key, cache_data in self._rating_cache.items():
                    last_update = cache_data.get("last_update", 0)
                    # 删除过期的缓存条目
                    if current_time - last_update > max_cache_age:
                        expired_keys.append(cache_key)

                for key in expired_keys:
                    del self._rating_cache[key]

                if expired_keys:
                    logger.info(
                        f"清理了 {len(expired_keys)} 个过期缓存条目")

            # 保存清理后的缓存
            self._save_cache_data()

        except Exception as e:
            logger.error(f"清理缓存失败：{str(e)}")

    def _load_cache_data(self):
        """加载缓存数据"""
        try:
            cache_data = self.get_data("rating_cache")
            if cache_data:
                self._rating_cache = cache_data

            # 加载后立即清理
            self._cleanup_cache()

        except Exception as e:
            logger.error(f"加载缓存数据失败：{str(e)}")

    def _save_cache_data(self):
        """保存缓存数据"""
        try:
            self.save_data("rating_cache", self._rating_cache)
        except Exception as e:
            logger.error(
                f"保存缓存数据失败：{str(e)}")

    def get_media_key(self, title: str, year: Optional[int] = None,
                      media_type: MediaType = None) -> str:
        """生成媒体唯一标识"""
        key_parts = [title]
        if year:
            key_parts.append(str(year))
        if media_type:
            key_parts.append(media_type.value)
        return "|".join(key_parts)



    def get_tmdb_rating_from_nfo(self, nfo_path: Path) -> Optional[float]:
        """从NFO文件中获取TMDB评分"""
        try:
            tree = ET.parse(nfo_path)
            root = tree.getroot()

            # 首先尝试从EmbyRating标签中获取TMDB评分
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is not None:
                tmdb_elem = emby_rating_elem.find("tmdb")
                if tmdb_elem is not None and tmdb_elem.text:
                    return float(tmdb_elem.text)

            # 如果没有EmbyRating标签，尝试从传统的rating标签获取
            rating_elem = root.find("rating")
            if rating_elem is not None:
                rating_text = rating_elem.text
                if rating_text:
                    return float(rating_text)

            # 如果没有找到rating，尝试从uniqueid中获取TMDB ID并查询
            tmdb_id = None
            for uniqueid in root.findall("uniqueid"):
                if uniqueid.get("type") == "tmdb":
                    tmdb_id = uniqueid.text
                    break

            if tmdb_id:
                # 这里可以调用TMDB API获取评分，暂时返回None
                logger.info(
                    f"找到TMDB ID: {tmdb_id}，"
                    f"需要调用API获取评分")
                return None

        except Exception as e:
            logger.error(
                f"读取NFO文件评分失败 {nfo_path}: {str(e)}")

        return None

    def backup_tmdb_rating(self, nfo_path: Path, media_key: str):
        """备份TMDB评分到EmbyRating标签"""
        try:
            # 读取原始文件内容
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    logger.error(
                        f"无法读取NFO文件编码: {nfo_path}")
                    return

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(
                    f"XML解析失败: {nfo_path}, "
                    f"错误: {str(e)}")
                return

            # 检查是否已有EmbyRating标签
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                emby_rating_elem = ET.SubElement(root, "EmbyRating")
                logger.debug(f"创建EmbyRating标签")

            # 检查是否已有tmdb评分
            tmdb_elem = emby_rating_elem.find("tmdb")
            if tmdb_elem is not None and tmdb_elem.text:
                logger.debug(
                    f"EmbyRating标签中已有TMDB评分: "
                    f"{tmdb_elem.text}")
                return

            # 获取当前评分
            current_rating = None

            # 首先尝试从传统rating标签获取
            rating_elem = root.find("rating")
            if rating_elem is not None and rating_elem.text:
                try:
                    current_rating = float(rating_elem.text)
                except ValueError:
                    pass

            # 保存TMDB评分到EmbyRating标签
            if tmdb_elem is None:
                tmdb_elem = ET.SubElement(emby_rating_elem, "tmdb")

            # 如果没有找到评分，记录为"none"，表示原本就没有评分
            if current_rating is None:
                tmdb_elem.text = "none"
                logger.info(f"原NFO文件无评分，备份为none: {nfo_path}")
            else:
                tmdb_elem.text = str(current_rating)
                logger.info(f"备份TMDB评分: {media_key} = {current_rating}")

            # 添加更新时间
            update_elem = emby_rating_elem.find("update")
            if update_elem is None:
                update_elem = ET.SubElement(emby_rating_elem, "update")
            update_elem.text = datetime.now().strftime("%Y-%m-%d")

            # 格式化XML并直接保存
            try:
                xml_str = self.format_xml(root)
                with open(nfo_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                logger.debug(f"备份操作完成: {nfo_path}")
            except Exception as e:
                logger.error(
                    f"保存NFO文件失败: {nfo_path}, "
                    f"错误: {str(e)}")
        except Exception as e:
            logger.error(
                f"备份TMDB评分失败 {nfo_path}: {str(e)}")

    def get_douban_rating(self, title: str,
                          year: Optional[int] = None) -> Optional[float]:
        """获取豆瓣评分"""
        try:
            # 检查缓存
            if self._cache_enabled:
                cache_key = self.get_media_key(title, year, MediaType.MOVIE)
                if cache_key in self._rating_cache:
                    cache_data = self._rating_cache[cache_key]
                    last_update = cache_data.get("last_update", 0)
                    # 检查是否在更新间隔内
                    update_interval_seconds = self._update_interval * 24 * 3600
                    if time.time() - last_update < update_interval_seconds:
                        logger.info(
                            f"使用缓存豆瓣评分: "
                            f"{title} = {cache_data['rating']}")
                        return cache_data["rating"]

            logger.debug(f"开始搜索豆瓣评分: {title}")
            found_title, subject_id, score = self._douban_helper.get_subject_id(title)

            if subject_id and score and score != "0":
                rating = float(score)

                logger.debug(f"豆瓣搜索结果: 标题='{found_title}', ID={subject_id}, 评分={score}")

                # 更新缓存
                if self._cache_enabled:
                    cache_key = self.get_media_key(
                        title, year, MediaType.MOVIE)
                    self._rating_cache[cache_key] = {
                        "rating": rating,
                        "last_update": time.time()
                    }

                logger.info(
                    f"获取豆瓣评分成功: {title} = {rating} (找到: {found_title})")
                return rating
            else:
                logger.debug(f"豆瓣搜索无结果: 标题='{found_title}', ID={subject_id}, 评分={score}")
                logger.warning(f"未找到豆瓣评分: {title}")
                return None

        except Exception as e:
            logger.error(
                f"获取豆瓣评分失败 {title}: {str(e)}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return None

    def format_xml(self, root) -> str:
        """格式化XML，避免多余的空行"""
        try:
            # 使用minidom格式化，但处理多余的空行
            xml_str = minidom.parseString(
                ET.tostring(root, encoding='unicode')
            ).toprettyxml(indent="  ")

            # 移除多余的空行
            lines = xml_str.split('\n')
            formatted_lines = []

            for i, line in enumerate(lines):
                # 保留非空行
                if line.strip():
                    formatted_lines.append(line)
                # 对于空行，只在特定情况下保留
                elif i > 0 and i < len(lines) - 1:
                    # 检查前后行是否都是标签
                    prev_line = lines[i-1].strip()
                    next_line = lines[i+1].strip()

                    # 如果前后都是标签，保留一个空行
                    if (prev_line.startswith('<') and prev_line.endswith('>') and
                            next_line.startswith('<') and next_line.endswith('>')):
                        formatted_lines.append('')

            return '\n'.join(formatted_lines)

        except Exception as e:
            logger.error(f"XML格式化失败: {str(e)}")
            # 如果格式化失败，使用简单的tostring
            return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def should_skip_rating_update(self, nfo_path: Path, rating_source: str) -> bool:
        """检查是否应该跳过评分更新（跳过逻辑）"""
        try:
            # TMDB评分不需要检查更新时间，因为它是静态数据
            if rating_source == "tmdb":
                return False

            # 只对豆瓣评分进行更新时间检查
            if rating_source != "douban":
                return False

            # 读取NFO文件
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    return False

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError:
                return False

            # 查找EmbyRating标签
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                return False

            # 检查当前评分源
            current_source_elem = emby_rating_elem.find("rating_source")
            if current_source_elem is None or current_source_elem.text != rating_source:
                return False

            # 检查更新时间
            update_elem = emby_rating_elem.find("update")
            if update_elem is None or not update_elem.text:
                return False

            try:
                last_update = datetime.strptime(update_elem.text, "%Y-%m-%d")
                days_since_update = (datetime.now() - last_update).days

                if days_since_update < self._update_interval:
                    logger.debug(
                        f"跳过更新，距离上次更新仅{days_since_update}天 "
                        f"(间隔设置: {self._update_interval}天): {nfo_path}"
                    )
                    return True
            except ValueError:
                # 如果日期格式不正确，不跳过更新
                return False

            return False

        except Exception as e:
            logger.debug(f"检查跳过逻辑时出错: {str(e)}")
            return False

    def update_nfo_rating(self, nfo_path: Path, new_rating: float,
                          rating_source: str = "douban", title: str = None,
                          media_type: str = None):
        """更新NFO文件中的评分（包含跳过检查）"""
        try:
            logger.debug(
                f"开始更新NFO评分: {nfo_path} = "
                f"{new_rating} ({rating_source})"
            )

            # 跳过逻辑检查
            if self.should_skip_rating_update(nfo_path, rating_source):
                logger.info(f"跳过评分更新: {nfo_path}")
                # 记录跳过的结果
                if title and media_type:
                    self._skipped_results.append({
                        'title': title,
                        'reason': '距离上次更新时间过短',
                        'media_type': media_type
                    })
                return True

            # 调用直接更新方法
            return self._update_nfo_rating_direct(nfo_path, new_rating, rating_source)

        except Exception as e:
            logger.error(f"更新NFO评分失败 {nfo_path}: {str(e)}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return False

    def _update_nfo_rating_direct(self, nfo_path: Path, new_rating: float,
                                 rating_source: str = "douban"):
        """直接更新NFO文件中的评分（不进行跳过检查）"""
        try:
            # 读取原始文件内容
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    logger.error(
                        f"无法读取NFO文件编码: {nfo_path}"
                    )
                    return False

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(
                    f"XML解析失败: {nfo_path}, "
                    f"错误: {str(e)}"
                )
                return False

            # 查找或创建EmbyRating标签
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                emby_rating_elem = ET.SubElement(root, "EmbyRating")
                logger.debug(f"创建EmbyRating标签")

            # 备份原始TMDB评分（如果存在且当前要更新为豆瓣评分）
            if rating_source == "douban":
                # 检查是否已经有tmdb备份
                tmdb_elem = emby_rating_elem.find("tmdb")
                if tmdb_elem is None:
                    # 尝试从传统rating标签获取原始评分
                    traditional_rating_elem = root.find("rating")
                    if traditional_rating_elem is not None and traditional_rating_elem.text:
                        try:
                            original_rating = float(traditional_rating_elem.text)
                            # 只有当原始评分不是0且不等于当前豆瓣评分时才备份
                            if original_rating > 0 and abs(original_rating - new_rating) > 0.1:
                                tmdb_elem = ET.SubElement(emby_rating_elem, "tmdb")
                                tmdb_elem.text = str(original_rating)
                                logger.info(f"备份原始TMDB评分: {original_rating}")
                        except (ValueError, TypeError):
                            logger.debug("原始rating标签值无效，跳过备份")

            # 更新对应评分源的评分
            rating_elem = emby_rating_elem.find(rating_source)
            if rating_elem is None:
                rating_elem = ET.SubElement(emby_rating_elem, rating_source)
            rating_elem.text = str(new_rating)

            # 添加或更新rating_source字段
            rating_source_elem = emby_rating_elem.find("rating_source")
            if rating_source_elem is None:
                rating_source_elem = ET.SubElement(emby_rating_elem, "rating_source")
            rating_source_elem.text = rating_source

            # 更新传统rating标签（保持兼容性）
            traditional_rating_elem = root.find("rating")
            if traditional_rating_elem is None:
                traditional_rating_elem = ET.SubElement(root, "rating")
            traditional_rating_elem.text = str(new_rating)

            # 添加更新时间
            update_elem = emby_rating_elem.find("update")
            if update_elem is None:
                update_elem = ET.SubElement(emby_rating_elem, "update")
            update_elem.text = datetime.now().strftime("%Y-%m-%d")

            # 使用改进的格式化方法
            xml_str = self.format_xml(root)

            # 直接写入原文件
            try:
                with open(nfo_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)
                logger.info(
                    f"更新NFO评分成功: {nfo_path} = "
                    f"{new_rating} ({rating_source})"
                )

                return True

            except Exception as e:
                logger.error(
                    f"保存NFO文件失败: {nfo_path}, "
                    f"错误: {str(e)}"
                )
                return False

        except Exception as e:
            logger.error(
                f"更新NFO评分失败 {nfo_path}: {str(e)}"
            )
            import traceback
            logger.debug(
                f"详细错误信息: {traceback.format_exc()}"
            )
            return False

    def _get_media_servers_from_config(self) -> set:
        """从媒体目录配置中获取所有涉及的媒体服务器名称"""
        servers = set()
        if not self._media_dirs:
            return servers

        for dir_config in self._media_dirs.split("\n"):
            dir_config = dir_config.strip()
            if not dir_config:  # 跳过空行
                continue
            if "#" in dir_config:
                # 解析路径和媒体服务器名称
                _, server_part = dir_config.split("#", 1)
                server_name = server_part.strip()
                if server_name:
                    servers.add(server_name)

        return servers

    def _refresh_media_servers(self, server_names: set):
        """刷新指定的媒体服务器"""
        if not self._refresh_library or not server_names:
            return

        try:
            # 获取模块管理器
            from app.core.module import ModuleManager
            from app.schemas.types import ModuleType
            module_manager = ModuleManager()

            # 获取所有媒体服务器模块
            media_server_modules = list(
                module_manager.get_running_type_modules(ModuleType.MediaServer)
            )

            if not media_server_modules:
                logger.warning(f"未找到可用的媒体服务器模块")
                return

            # 刷新每个指定的媒体服务器
            for server_name in server_names:
                target_module = None
                for module in media_server_modules:
                    try:
                        instances = module.get_instances()
                        if server_name in instances:
                            target_module = module
                            break
                    except Exception as e:
                        logger.debug(
                            f"检查模块 {module.__class__.__name__} "
                            f"时出错: {str(e)}"
                        )
                        continue

                if not target_module:
                    logger.warning(
                        f"未找到指定的媒体服务器: {server_name}"
                    )
                    continue

                # 获取服务器实例并刷新
                server_instance = target_module.get_instance(server_name)
                if not server_instance:
                    logger.warning(
                        f"无法获取媒体服务器实例: {server_name}"
                    )
                    continue

                if hasattr(server_instance, 'refresh_root_library'):
                    success = server_instance.refresh_root_library()
                    if success:
                        logger.info(
                            f"成功刷新媒体库: {server_name}"
                        )
                    else:
                        logger.warning(
                            f"刷新媒体库失败: {server_name}"
                        )
                else:
                    logger.warning(
                        f"媒体服务器 {server_name} 不支持刷新功能"
                    )

        except Exception as e:
            logger.error(f"刷新媒体库失败: {str(e)}")

    def update_all_ratings(self):
        """更新所有媒体评分"""
        logger.info(f"开始更新所有媒体评分")

        # 重置停止标志
        self._should_stop = False

        # 初始化处理结果收集器
        self._processing_results = []
        self._failed_results = []
        self._skipped_results = []

        # 获取媒体目录列表
        media_dirs = []
        if self._media_dirs:
            for dir_config in self._media_dirs.split("\n"):
                dir_config = dir_config.strip()
                if not dir_config:  # 跳过空行
                    continue
                if "#" in dir_config:
                    # 解析路径和媒体服务器名称
                    path_part, _ = dir_config.split("#", 1)
                    media_dir = Path(path_part.strip())
                else:
                    # 没有指定媒体服务器，只使用路径
                    media_dir = Path(dir_config.strip())

                if media_dir:
                    media_dirs.append(media_dir)

        if not media_dirs:
            logger.warning(f"未配置媒体目录")
            return

        # 处理每个媒体目录
        for media_dir in media_dirs:
            if self._should_stop:
                logger.info(f"检测到停止信号，中断评分更新任务")
                break

            if not media_dir.exists():
                logger.warning(f"媒体目录不存在: {media_dir}")
                continue

            logger.info(f"处理媒体目录: {media_dir}")
            self.process_media_directory(media_dir)

        # 发送批量通知
        self._send_batch_notification()

        # 保存缓存数据
        self._save_cache_data()

        # 清理过期缓存
        self._cleanup_cache()

        # 批量处理完成后，刷新所有涉及的媒体服务器
        if self._refresh_library:
            server_names = self._get_media_servers_from_config()
            if server_names:
                logger.info(
                    f"开始刷新媒体服务器: {', '.join(server_names)}"
                )
                self._refresh_media_servers(server_names)
            else:
                logger.debug(f"未配置需要刷新的媒体服务器")

        logger.info(f"评分更新完成")

    def _send_batch_notification(self):
        """发送汇总通知"""
        if not self._notify:
            return

        try:
            # 统计处理结果
            success_count = len(self._processing_results)
            failed_count = len(self._failed_results)
            skipped_count = len(self._skipped_results)
            total_count = success_count + failed_count + skipped_count

            # 如果没有任何处理结果，不发送通知
            if total_count == 0:
                return

            # 按评分源统计成功的更新
            douban_count = sum(
                1 for result in self._processing_results
                if result['source'] == 'douban'
            )
            tmdb_count = sum(
                1 for result in self._processing_results
                if result['source'] == 'tmdb'
            )

            # 按媒体类型统计成功的更新
            movie_count = sum(
                1 for result in self._processing_results
                if result['media_type'] == 'MOVIE'
            )
            tv_count = sum(
                1 for result in self._processing_results
                if result['media_type'] == 'TV'
            )

            # 按媒体类型统计失败的更新
            failed_movie_count = sum(
                1 for result in self._failed_results
                if result['media_type'] == 'MOVIE'
            )
            failed_tv_count = sum(
                1 for result in self._failed_results
                if result['media_type'] == 'TV'
            )

            # 按媒体类型统计跳过的更新
            skipped_movie_count = sum(
                1 for result in self._skipped_results
                if result['media_type'] == 'MOVIE'
            )
            skipped_tv_count = sum(
                1 for result in self._skipped_results
                if result['media_type'] == 'TV'
            )

            # 构建通知标题
            if failed_count == 0:
                title = "🎬 评分更新完成"
            else:
                title = "🎬 评分更新完成（部分失败）"

            # 构建通知内容
            text_parts = []

            # 总体统计
            total_movie_count = movie_count + failed_movie_count + skipped_movie_count
            total_tv_count = tv_count + failed_tv_count + skipped_tv_count

            if total_movie_count > 0 and total_tv_count > 0:
                text_parts.append(f"📊 共处理 {total_count} 部影片（🎥 电影 {total_movie_count} 部，📺 电视剧 {total_tv_count} 部）")
            elif total_movie_count > 0:
                text_parts.append(f"📊 共处理 {total_count} 部电影")
            elif total_tv_count > 0:
                text_parts.append(f"📊 共处理 {total_count} 部电视剧")
            else:
                text_parts.append(f"📊 共处理 {total_count} 部影片")

            if success_count > 0:
                # 成功统计 - 按媒体类型显示
                success_parts = []
                if movie_count > 0:
                    success_parts.append(f"🎥 电影 {movie_count} 部")
                if tv_count > 0:
                    success_parts.append(f"📺 电视剧 {tv_count} 部")

                if success_parts:
                    text_parts.append(f"✅ 成功更新：{' | '.join(success_parts)}")
                else:
                    text_parts.append(f"✅ 成功更新 {success_count} 部")

                # 按评分源分类显示
                source_parts = []
                if douban_count > 0:
                    source_parts.append(f"豆瓣 {douban_count} 部")
                if tmdb_count > 0:
                    source_parts.append(f"TMDB {tmdb_count} 部")
                if source_parts:
                    text_parts.append(f"📈 评分源：{' | '.join(source_parts)}")

            if failed_count > 0:
                # 失败统计 - 按媒体类型显示
                failed_parts = []
                if failed_movie_count > 0:
                    failed_parts.append(f"🎥 电影 {failed_movie_count} 部")
                if failed_tv_count > 0:
                    failed_parts.append(f"📺 电视剧 {failed_tv_count} 部")

                if failed_parts:
                    text_parts.append(f"❌ 失败：{' | '.join(failed_parts)}")
                else:
                    text_parts.append(f"❌ 失败 {failed_count} 部")

            if skipped_count > 0:
                # 跳过统计 - 按媒体类型显示
                skipped_parts = []
                if skipped_movie_count > 0:
                    skipped_parts.append(f"🎥 电影 {skipped_movie_count} 部")
                if skipped_tv_count > 0:
                    skipped_parts.append(f"📺 电视剧 {skipped_tv_count} 部")

                if skipped_parts:
                    text_parts.append(f"⏭️ 跳过：{' | '.join(skipped_parts)}")
                else:
                    text_parts.append(f"⏭️ 跳过 {skipped_count} 部")

            text = "\n".join(text_parts)

            # 发送通知
            self.post_message(
                mtype=NotificationType.MediaServer,
                title=title,
                text=text
            )

            logger.info(f"发送汇总通知：{title}")
            logger.debug(f"通知内容：{text}")

        except Exception as e:
            logger.error(f"发送批量通知失败：{str(e)}")

        finally:
            # 清空处理结果列表
            self._processing_results.clear()
            self._failed_results.clear()
            self._skipped_results.clear()

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """定义远程控制命令"""
        return [
            {
                "cmd": "/embyrating_update",
                "event": EventType.PluginAction,
                "desc": "更新Emby评分",
                "category": "媒体管理",
                "data": {"action": "update_ratings"}
            },
            {
                "cmd": "/embyrating_switch_tmdb",
                "event": EventType.PluginAction,
                "desc": "切换到TMDB评分",
                "category": "媒体管理",
                "data": {"action": "switch_to_tmdb"}
            },
            {
                "cmd": "/embyrating_switch_douban",
                "event": EventType.PluginAction,
                "desc": "切换到豆瓣评分",
                "category": "媒体管理",
                "data": {"action": "switch_to_douban"}
            }
        ]

    @eventmanager.register(EventType.PluginAction)
    def handle_commands(self, event: Event):
        """处理远程命令"""
        if not self._enabled:
            return

        if not event or not event.event_data:
            return

        action = event.event_data.get("action")
        if not action:
            return

        if action == "update_ratings":
            self.update_all_ratings()
        elif action == "switch_to_tmdb":
            self._rating_source = "tmdb"
            self._update_config()
            self.update_all_ratings()
        elif action == "switch_to_douban":
            self._rating_source = "douban"
            self._update_config()
            self.update_all_ratings()

    def get_api(self) -> List[Dict[str, Any]]:
        """注册插件API"""
        return [
            {
                "path": "/monitor_status",
                "endpoint": self.get_monitor_status_api,
                "methods": ["GET"],
                "summary": "获取文件监控状态",
                "description": "返回当前文件监控线程和observer的状态信息"
            }
        ]

    def get_monitor_status_api(self):
        """获取监控状态API"""
        try:
            status = self.get_monitor_status()
            return {
                "success": True,
                "data": status
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"获取监控状态失败: {str(e)}"
            }

    def switch_rating_source(self, source: str):
        """切换评分源API"""
        if source not in ["tmdb", "douban"]:
            return {"success": False, "message": "无效的评分源"}

        self._rating_source = source
        self._update_config()
        self.update_all_ratings()

        return {"success": True, "message": f"已切换到{source}评分"}

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """拼装插件配置页面"""
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
                                    'cols': 12
                                },
                                'content': [
                                    {
                                        'component': 'VAlert',
                                        'props': {
                                            'type': 'info',
                                            'variant': 'tonal',
                                            'text': ('📖 插件工作机制说明：\n'
                                                   '• 插件通过修改NFO文件中的rating字段来更新媒体评分\n'
                                                   '• 对于电影：直接更新电影NFO文件的评分信息\n'
                                                   '• 对于电视剧：整体评分（tvshow.nfo）使用第一季的评分\n'
                                                   '• 支持豆瓣评分和TMDB评分之间的智能切换\n'
                                                   '• 文件监控：实时监控新创建的NFO文件并自动更新评分（仅在评分源为豆瓣时生效）')
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
                                            'model': 'notify',
                                            'label': '发送通知',
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
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'rating_source',
                                            'label': '评分源',
                                            'items': [
                                                {'title': 'TMDB评分',
                                                 'value': 'tmdb'},
                                                {'title': '豆瓣评分',
                                                 'value': 'douban'}
                                            ]
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
                                            'model': 'update_interval',
                                            'label': '豆瓣评分更新间隔（天）',
                                            'type': 'number',
                                            'min': 1,
                                            'max': 365
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
                                            'model': 'auto_scrape',
                                            'label': '自动刮削',
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
                                            'model': 'file_monitor_enabled',
                                            'label': '启用文件监控',
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
                                            'model': 'refresh_library',
                                            'label': '更新后刷新媒体库',
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
                                            'model': 'media_dirs',
                                            'label': '媒体目录（多个用换行分隔）',
                                            'rows': 3,
                                            'placeholder': ('例如：\n'
                                                          '/sata/影视/电影#Emby\n'
                                                          '/sata/影视/电视剧#Emby\n'
                                                          '格式：媒体库根目录#媒体服务器名称')
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
                                            'model': 'douban_cookie',
                                            'label': '豆瓣Cookie',
                                            'rows': 3,
                                            'placeholder': '留空则从CookieCloud获取，格式：bid=xxx; ck=xxx; dbcl2=xxx; ...'
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
                                        'component': 'VCronField',
                                        'props': {
                                            'model': 'cron',
                                            'label': '定时任务',
                                            'placeholder': '0 2 * * *'
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
                                            'model': 'onlyonce',
                                            'label': '立即全量运行一次',
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
            "cron": "0 2 * * *",
            "notify": False,
            "onlyonce": False,
            "rating_source": "tmdb",
            "update_interval": 7,
            "auto_scrape": True,

            "media_dirs": "",
            "refresh_library": True,
            "douban_cookie": "",
            "file_monitor_enabled": False
        }

    def get_page(self) -> List[dict]:
        """拼装插件详情页面"""
        return None

    def stop_service(self):
        """停止插件"""
        # 设置停止标志，中断正在运行的任务
        self._should_stop = True
        logger.info(f"设置停止标志，正在中断运行中的任务...")

        # 停止监控线程
        try:
            self._stop_monitor_thread()
        except Exception as e:
            logger.error(f"停止监控线程失败：{str(e)}")

        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error(f"停止定时任务失败：{str(e)}")

        # 停止文件监控
        try:
            self._stop_file_monitor()
        except Exception as e:
            logger.error(f"停止文件监控失败：{str(e)}")
        self._should_stop = False

    def _stop_monitor_thread(self):
        """停止监控线程"""
        try:
            # 设置停止事件
            if self._monitor_stop_event:
                self._monitor_stop_event.set()
                logger.debug("已设置监控线程停止事件")

            # 等待监控线程结束
            if self._monitor_thread and self._monitor_thread.is_alive():
                logger.info("正在等待监控线程停止...")
                self._monitor_thread.join(timeout=5.0)

                if self._monitor_thread.is_alive():
                    logger.warning("监控线程在5秒内未能停止")
                else:
                    logger.info("监控线程已成功停止")

            # 清理线程对象
            self._monitor_thread = None
            self._monitor_stop_event = None

        except Exception as e:
            logger.error(f"停止监控线程时出错: {str(e)}")

    def get_monitor_status(self) -> dict:
        """获取监控状态"""
        return {
            "monitor_thread_alive": self._monitor_thread.is_alive() if self._monitor_thread else False,
            "monitor_thread_name": self._monitor_thread.name if self._monitor_thread else None,
            "observers_count": len(self._file_observers),
            "observers_status": [
                {
                    "index": i,
                    "alive": obs.is_alive(),
                    "class": obs.__class__.__name__
                }
                for i, obs in enumerate(self._file_observers)
            ]
        }

    def process_media_directory(self, media_dir: Path):
        """处理媒体目录"""
        try:
            # 检查目录是否存在
            if not media_dir.exists():
                logger.warning(f"媒体目录不存在: {media_dir}")
                return

            # 收集所有需要处理的NFO文件
            processed_shows = set()  # 记录已处理的电视剧，避免重复处理

            # 统计目录中的文件
            total_files = 0
            media_files = 0
            nfo_files = 0

            # 遍历目录查找媒体文件
            for item in media_dir.rglob("*"):
                if self._should_stop:
                    logger.info(f"检测到停止信号，中断媒体目录处理")
                    break

                if item.is_file():
                    total_files += 1
                    if item.suffix.lower() == '.nfo':
                        nfo_files += 1
                    elif item.suffix.lower() in self.MEDIA_EXTENSIONS:
                        media_files += 1

                if item.is_file() and item.suffix.lower() in self.MEDIA_EXTENSIONS:
                    logger.debug(f"发现媒体文件: {item}")
                    # 检查是否为电视剧结构
                    if self._is_tv_show_structure(item):
                        logger.debug(f"识别为电视剧结构: {item}")
                        # 处理电视剧
                        show_root = self._get_tv_show_root(item)
                        if show_root and show_root not in processed_shows:
                            logger.info(f"开始处理电视剧: {show_root}")
                            processed_shows.add(show_root)
                            self._process_tv_show(show_root)
                        elif show_root in processed_shows:
                            logger.debug(f"电视剧已处理，跳过: {show_root}")
                    else:
                        logger.debug(f"识别为电影: {item}")
                        # 处理电影
                        nfo_path = item.with_suffix('.nfo')
                        if not nfo_path.exists():
                            logger.debug(f"NFO文件不存在，尝试刮削: {nfo_path}")
                            # 尝试刮削，传递目标媒体文件
                            if not self.scrape_media_if_needed(item.parent, False, item):
                                logger.debug(f"刮削失败或跳过: {item}")
                                continue
                            # 重新检查NFO文件
                            if not nfo_path.exists():
                                logger.warning(
                                    f"刮削后仍未找到NFO文件: {nfo_path}"
                                )
                                continue
                        # 处理NFO文件
                        self.process_nfo_file(nfo_path, MediaType.MOVIE)

            # 输出统计信息
            logger.info(f"目录统计 - 总文件: {total_files}, 媒体文件: {media_files}, NFO文件: {nfo_files}")
            if media_files == 0:
                logger.warning(f"目录中未找到任何媒体文件: {media_dir}")
            if nfo_files == 0:
                logger.warning(f"目录中未找到任何NFO文件: {media_dir}")

        except Exception as e:
            logger.error(f"处理媒体目录失败 {media_dir}: {str(e)}")

    def _is_tv_show_structure(self, media_file: Path) -> bool:
        """判断是否为电视剧结构"""
        try:
            # 检查路径结构，电视剧通常有 剧集名/季/集 的结构
            parts = media_file.parts
            if len(parts) >= 3:
                # 检查是否有季的目录结构
                for part in parts:
                    if ('season' in part.lower() or
                            part.lower().startswith('s') and part[1:].isdigit()):
                        return True
            return False
        except Exception:
            return False

    def _get_tv_show_root(self, media_file: Path) -> Optional[Path]:
        """获取电视剧根目录"""
        try:
            current = media_file.parent
            while current and current.name:
                # 检查是否有tvshow.nfo文件
                tvshow_nfo = current / "tvshow.nfo"
                if tvshow_nfo.exists():
                    return current
                current = current.parent
            return None
        except Exception:
            return None

    def _process_tv_show(self, show_root: Path):
        """处理电视剧，更新tvshow.nfo文件评分"""
        try:
            tvshow_nfo = show_root / "tvshow.nfo"

            # 如果tvshow.nfo不存在，尝试刮削
            if not tvshow_nfo.exists():
                logger.info(f"未找到tvshow.nfo文件，尝试刮削: {show_root}")

                # 检查是否为电视剧目录（包含季目录结构）
                if self._is_tv_show_directory(show_root):
                    # 尝试刮削
                    if self.scrape_media_if_needed(show_root, is_tv_show=True):
                        # 重新检查tvshow.nfo文件
                        if not tvshow_nfo.exists():
                            logger.warning(f"刮削后仍未找到tvshow.nfo文件: {show_root}")
                            return
                    else:
                        logger.warning(f"刮削失败: {show_root}")
                        return
                else:
                    logger.warning(f"目录结构不符合电视剧格式，跳过: {show_root}")
                    return

            logger.info(f"使用统一方法处理电视剧NFO: {tvshow_nfo}")
            self.process_nfo_file(tvshow_nfo, MediaType.TV)



        except Exception as e:
            logger.error(f"处理电视剧失败 {show_root}: {str(e)}")
            # 添加到失败结果
            self._failed_results.append({
                'title': f"{show_root.name} (电视剧)" if show_root else "未知电视剧",
                'reason': f'处理异常: {str(e)}',
                'media_type': 'TV'
            })

    def _is_tv_show_directory(self, directory: Path) -> bool:
        """判断是否为电视剧目录"""
        try:
            # 检查是否包含季目录结构
            season_dirs = []
            for item in directory.iterdir():
                if item.is_dir():
                    # 检查是否为季目录
                    if ('season' in item.name.lower() or
                        item.name.lower().startswith('s') and item[1:].isdigit()):
                        season_dirs.append(item)
            
            # 如果包含多个季目录，很可能是电视剧根目录
            if len(season_dirs) >= 1:
                logger.debug(f"发现季目录结构: {[d.name for d in season_dirs]}")
                return True
            
            # 检查是否直接包含媒体文件（可能是季目录）
            media_files = []
            for item in directory.iterdir():
                if item.is_file() and item.suffix.lower() in self.MEDIA_EXTENSIONS:
                    media_files.append(item)
            
            # 如果包含媒体文件但没有季目录，可能是季目录或电影目录
            if media_files:
                logger.debug(f"发现媒体文件，可能是季目录或电影目录: {len(media_files)} 个文件")
                return False
            
            # 如果既没有季目录也没有媒体文件，可能是空的电视剧目录
            logger.debug(f"目录为空或只包含其他文件，可能是空的电视剧目录")
            return True
            
        except Exception as e:
            logger.error(f"检查电视剧目录结构失败 {directory}: {str(e)}")
            return False

    def _get_first_season_rating(self, base_title: str, year: str) -> Optional[float]:
        """获取剧集评分（优先使用第一季评分）"""
        try:
            rating = self.get_douban_rating(base_title, year)
            if rating:
                logger.info(f"直接获取豆瓣评分成功: {base_title} = {rating}")
                return rating

            # 如果直接获取失败，尝试用"第一季"格式
            season_title_formats = [
                f"{base_title} 第一季",
                f"{base_title} 第 一 季",
                f"{base_title} Season 1",
                f"{base_title} S1",
                f"{base_title} S01"
            ]

            for season_title in season_title_formats:
                logger.info(f"尝试季格式: {season_title}")
                rating = self.get_douban_rating(season_title, year)
                if rating:
                    logger.info(f"季格式获取豆瓣评分成功: {season_title} = {rating}")
                    return rating

            logger.warning(f"无法获取豆瓣评分: {base_title}")
            return None

        except Exception as e:
            logger.error(f"获取剧集评分失败: {str(e)}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")
            return None

    def _extract_title_from_tvshow_nfo(self, root) -> Optional[str]:
        """从tvshow.nfo的XML根元素中提取标题"""
        try:
            # 尝试多种标题元素
            title_tags = ["title", "originaltitle", "sorttitle", "name", "showname"]

            for tag_name in title_tags:
                # 使用简单的查找方法
                elem = root.find(tag_name)
                if elem is not None and elem.text and elem.text.strip():
                    title = elem.text.strip()
                    logger.info(f"从{tag_name}元素获取标题: {title}")
                    return title

                # 如果简单查找失败，尝试忽略命名空间的查找
                for child in root.iter():
                    if child.tag.lower().endswith(tag_name.lower()) and child.text and child.text.strip():
                        title = child.text.strip()
                        logger.info(f"从{child.tag}元素获取标题: {title}")
                        return title

            logger.warning(f"未找到任何有效的标题元素")
            return None

        except Exception as e:
            logger.error(f"提取标题失败: {str(e)}")
            return None

    def find_elem_ignore_ns(self, root, tag_name):
        """在root下查找忽略命名空间和不可见字符的tag_name元素，输出调试信息"""
        found_elements = []
        logger.debug(f"开始查找元素: {tag_name}")

        for elem in root.iter():
            tag = elem.tag
            if tag.lower().strip().endswith(tag_name.lower()):
                found_elements.append(elem)
                logger.debug(f"命中tag: {repr(tag)}")

        logger.debug(f"查找完成，找到 {len(found_elements)} 个 {tag_name} 元素")

        if found_elements:
            # 返回第一个找到的元素
            logger.debug(f"找到 {len(found_elements)} 个 {tag_name} 元素，返回第一个")
            return found_elements[0]
        else:
            logger.debug(f"未找到任何 {tag_name} 元素")
            return None

    def process_nfo_file(self, nfo_path: Path, media_type: MediaType = MediaType.UNKNOWN):
        """处理单个NFO文件，兼容命名空间"""
        try:
            # 检查是否需要停止
            if self._should_stop:
                logger.info(f"检测到停止信号，跳过NFO文件处理: {nfo_path}")
                return

            # 检查文件是否存在
            if not nfo_path.exists():
                logger.warning(f"NFO文件不存在: {nfo_path}")
                return

            # 检查文件大小
            file_size = nfo_path.stat().st_size
            if file_size == 0:
                logger.warning(f"NFO文件为空: {nfo_path}")
                return

            logger.info(
                f"开始处理NFO文件: {nfo_path} (大小: {file_size} bytes)")

            # 尝试读取文件内容
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.debug(f"成功读取NFO文件内容，长度: {len(content)}")
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                    logger.debug(f"使用GBK编码成功读取NFO文件")
                except UnicodeDecodeError:
                    logger.error(f"NFO文件编码无法识别: {nfo_path}")
                    return
                except Exception as e:
                    logger.error(
                        f"读取NFO文件失败: {nfo_path}, 错误: {str(e)}")
                    return

            # 解析XML
            try:
                root = ET.fromstring(content)
                logger.debug(f"成功解析XML，根元素: {root.tag}")
            except ET.ParseError as e:
                logger.error(
                    f"XML解析失败: {nfo_path}, 错误: {str(e)}")
                return
            except Exception as e:
                logger.error(
                    f"XML解析异常: {nfo_path}, 错误: {str(e)}")
                return

            # 获取媒体信息（忽略命名空间）
            title_elem = self.find_elem_ignore_ns(root, "title")
            if title_elem is None:
                logger.warning(f"NFO文件中未找到title元素: {nfo_path}")
                # 尝试查找其他可能的标题元素
                alt_title_elem = None
                for title_tag in ["originaltitle", "sorttitle", "name", "showname"]:
                    alt_title_elem = self.find_elem_ignore_ns(root, title_tag)
                    if alt_title_elem is not None and alt_title_elem.text:
                        logger.info(
                            f"使用替代标题元素 {title_tag}: {alt_title_elem.text}")
                        break
                if alt_title_elem and alt_title_elem.text:
                    title_elem = alt_title_elem
                else:
                    logger.warning(
                        f"NFO文件缺少有效标题，尝试从文件名推断: {nfo_path}")
                    # 从文件名推断标题
                    filename = nfo_path.stem  # 去掉扩展名
                    import re
                    title_from_filename = re.sub(
                        r'\s*\(\d{4}\)\s*.*$', '', filename)
                    title_from_filename = re.sub(
                        r'\s*-\s*\d+p.*$', '', title_from_filename)
                    title_from_filename = re.sub(
                        r'\s*-\s*2160p.*$', '', title_from_filename)
                    title_from_filename = title_from_filename.strip()
                    if title_from_filename:
                        logger.info(
                            f"从文件名推断标题: {title_from_filename}")
                        title_elem = ET.Element("title")
                        title_elem.text = title_from_filename
                    else:
                        logger.warning(
                            f"无法从文件名推断标题: {filename}")
                        full_xml = ET.tostring(root, encoding='unicode')
                        logger.debug(f"完整XML结构: {full_xml}")
                        return
            elif not title_elem.text or not title_elem.text.strip():
                logger.warning(f"NFO文件中title元素内容为空: {nfo_path}")
                # 尝试查找其他可能的标题元素
                alt_title_elem = None
                for title_tag in ["originaltitle", "sorttitle", "name", "showname"]:
                    alt_title_elem = self.find_elem_ignore_ns(root, title_tag)
                    if alt_title_elem is not None and alt_title_elem.text and alt_title_elem.text.strip():
                        logger.info(
                            f"使用替代标题元素 {title_tag}: {alt_title_elem.text}")
                        break
                if alt_title_elem and alt_title_elem.text and alt_title_elem.text.strip():
                    title_elem = alt_title_elem
                else:
                    logger.warning(
                        f"NFO文件title内容为空且无替代标题，尝试从文件名推断: {nfo_path}")
                    # 从文件名推断标题
                    filename = nfo_path.stem  # 去掉扩展名
                    import re
                    title_from_filename = re.sub(
                        r'\s*\(\d{4}\)\s*.*$', '', filename)
                    title_from_filename = re.sub(
                        r'\s*-\s*\d+p.*$', '', title_from_filename)
                    title_from_filename = re.sub(
                        r'\s*-\s*2160p.*$', '', title_from_filename)
                    title_from_filename = title_from_filename.strip()
                    if title_from_filename:
                        logger.info(
                            f"从文件名推断标题: {title_from_filename}")
                        title_elem = ET.Element("title")
                        title_elem.text = title_from_filename
                    else:
                        logger.warning(
                            f"无法从文件名推断标题: {filename}")
                        return
            else:
                logger.debug(f"找到title元素: {title_elem.text}")

            title = title_elem.text.strip()
            if not title:
                logger.warning(f"NFO文件标题为空: {nfo_path}")
                return
            logger.debug(f"最终使用标题: {title}")

            # 获取年份（忽略命名空间）
            year = None
            year_elem = self.find_elem_ignore_ns(root, "year")
            if year_elem is None:
                logger.debug(f"NFO文件中未找到year元素")
            elif not year_elem.text or not year_elem.text.strip():
                logger.debug(
                    f"NFO文件中year元素内容为空: '{year_elem.text}'")
            else:
                try:
                    year = int(year_elem.text.strip())
                    logger.debug(f"找到年份: {year}")
                except ValueError:
                    logger.warning(
                        f"年份格式无效: '{year_elem.text}'")

            # 如果从XML中没找到年份，尝试从文件名推断
            if not year:
                import re
                year_match = re.search(r'\((\d{4})\)', nfo_path.name)
                if year_match:
                    try:
                        year = int(year_match.group(1))
                        logger.info(f"从文件名推断年份: {year}")
                    except ValueError:
                        pass

            # 生成媒体键
            media_key = self.get_media_key(title, year, media_type)
            logger.debug(f"生成媒体键: {media_key}")

            # 备份TMDB评分
            self.backup_tmdb_rating(nfo_path, media_key)

            # 根据评分源处理
            if self._rating_source == "douban":
                # 先检查是否可以跳过更新
                if self.should_skip_rating_update(nfo_path, self._rating_source):
                    logger.info(f"跳过评分更新: {nfo_path}")
                    # 记录跳过的结果
                    self._skipped_results.append({
                        'title': title,
                        'reason': '距离上次更新时间过短',
                        'media_type': media_type.value
                    })
                else:
                    # 根据媒体类型获取评分
                    if media_type == MediaType.TV:
                        # 电视剧：获取第一季的评分作为整个剧集的评分
                        douban_rating = self._get_first_season_rating(title, year)
                        if not douban_rating:
                            logger.warning(f"无法获取剧集评分: {title}")
                            # 添加到失败结果
                            self._failed_results.append({
                                'title': f"{title} (电视剧)",
                                'reason': '无法获取剧集评分',
                                'media_type': 'TV'
                            })
                            return
                    else:
                        # 电影：直接获取豆瓣评分
                        douban_rating = self.get_douban_rating(title, year)

                    if douban_rating:
                        # 更新NFO文件（跳过内部的跳过检查，因为已经检查过了）
                        if self._update_nfo_rating_direct(nfo_path, douban_rating, "douban"):
                            # 添加到处理结果
                            self._processing_results.append({
                                'title': title,
                                'rating': douban_rating,
                                'source': 'douban',
                                'media_type': media_type.value
                            })
                    else:
                        logger.warning(f"无法获取豆瓣评分: {title}")
                        # 添加到失败结果
                        self._failed_results.append({
                            'title': title,
                            'reason': '无法获取豆瓣评分',
                            'media_type': media_type.value
                        })

            elif self._rating_source == "tmdb":
                # 恢复TMDB评分
                if media_key:
                    restored_rating = self.restore_tmdb_rating(
                        nfo_path, media_key)
                    if restored_rating is not None:
                        # 添加到处理结果
                        if restored_rating == 0.0:
                            # 原本就没有评分，成功删除rating标签
                            self._processing_results.append({
                                'title': title,
                                'rating': '无评分',
                                'source': 'tmdb',
                                'media_type': media_type.value
                            })
                        else:
                            # 成功恢复评分
                            self._processing_results.append({
                                'title': title,
                                'rating': restored_rating,
                                'source': 'tmdb',
                                'media_type': media_type.value
                            })
                    else:
                        # 添加到失败结果
                        self._failed_results.append({
                            'title': title,
                            'reason': '无法恢复TMDB评分',
                            'media_type': media_type.value
                        })
                else:
                    logger.warning(f"未找到TMDB评分备份: {title}")
                    # 添加到失败结果
                    self._failed_results.append({
                        'title': title,
                        'reason': '未找到TMDB评分备份',
                        'media_type': media_type.value
                    })
        except Exception as e:
            logger.error(f"处理NFO文件失败 {nfo_path}: {str(e)}")
            # 添加到失败结果
            self._failed_results.append({
                'title': title if 'title' in locals() else str(nfo_path.stem),
                'reason': f'处理异常: {str(e)}',
                'media_type': 'UNKNOWN'
            })
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")

    def scrape_media_if_needed(self, media_path: Path, is_tv_show: bool = False,
                               target_media_file: Path = None) -> bool:
        """如果需要则进行刮削"""
        if not self._auto_scrape:
            return True

        try:
            # 对于电视剧目录，检查tvshow.nfo文件
            if is_tv_show:
                tvshow_nfo = media_path / "tvshow.nfo"
                if tvshow_nfo.exists():
                    logger.debug(f"电视剧目录已存在tvshow.nfo文件: {media_path}")
                    return True
                else:
                    logger.info(f"电视剧目录缺少tvshow.nfo，开始刮削: {media_path}")
                    return self._scrape_directory(media_path)

            # 如果指定了目标媒体文件，检查对应的NFO文件
            if target_media_file:
                target_nfo = target_media_file.with_suffix('.nfo')
                if target_nfo.exists():
                    logger.debug(f"NFO文件已存在: {target_nfo}")
                    return True
                else:
                    logger.info(f"NFO文件不存在，开始刮削: {target_media_file}")
                    return self._scrape_directory(target_media_file.parent)

            # 默认刮削整个目录
            return self._scrape_directory(media_path)

        except Exception as e:
            logger.error(f"刮削失败 {media_path}: {str(e)}")
            return False

    def _scrape_directory(self, media_path: Path) -> bool:
        """刮削目录"""
        try:
            logger.info(f"开始刮削目录: {media_path}")

            # 调用MoviePilot的刮削功能
            mediachain = MediaChain()

            # 创建FileItem
            fileitem = FileItem(
                path=str(media_path),
                type="dir",
                storage="local"
            )

            # 识别媒体信息
            meta = MetaInfoPath(media_path)
            mediainfo = mediachain.recognize_media(meta)

            if mediainfo:
                # 执行刮削
                mediachain.scrape_metadata(
                    fileitem=fileitem, meta=meta, mediainfo=mediainfo, overwrite=True)
                logger.info(f"目录刮削完成: {media_path}")
                return True
            else:
                logger.warning(f"无法识别媒体信息: {media_path}")
                return False

        except Exception as e:
            logger.error(f"刮削目录失败 {media_path}: {str(e)}")
            return False

    def restore_tmdb_rating(self, nfo_path: Path, media_key: str) -> Optional[float]:
        """从EmbyRating标签恢复TMDB评分，返回恢复的评分值"""
        try:
            # 读取原始文件内容
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    logger.error(f"无法读取NFO文件编码: {nfo_path}")
                    return False

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(
                    f"XML解析失败: {nfo_path}, 错误: {str(e)}")
                return False

            # 从EmbyRating标签中获取TMDB评分
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                logger.warning(f"未找到EmbyRating标签: {media_key}")
                return None

            tmdb_elem = emby_rating_elem.find("tmdb")
            if tmdb_elem is None or not tmdb_elem.text:
                logger.warning(f"未找到TMDB评分备份: {media_key}")
                # 如果没有备份，记录为none，表示原本就没有TMDB评分
                if tmdb_elem is None:
                    tmdb_elem = ET.SubElement(emby_rating_elem, "tmdb")
                tmdb_elem.text = "none"
                logger.info(f"记录原NFO文件无TMDB评分: {media_key}")

                # 删除rating标签（如果存在）
                traditional_rating_elem = root.find("rating")
                if traditional_rating_elem is not None:
                    root.remove(traditional_rating_elem)
                    logger.debug(f"已删除rating标签")

                # 更新rating_source为tmdb
                rating_source_elem = emby_rating_elem.find("rating_source")
                if rating_source_elem is None:
                    rating_source_elem = ET.SubElement(emby_rating_elem, "rating_source")
                rating_source_elem.text = "tmdb"

                # 保存文件
                try:
                    xml_str = self.format_xml(root)
                    with open(nfo_path, 'w', encoding='utf-8') as f:
                        f.write(xml_str)
                    logger.info(f"恢复TMDB状态成功（无评分）: {media_key}")
                    return 0.0
                except Exception as e:
                    logger.error(f"保存NFO文件失败: {nfo_path}, 错误: {str(e)}")
                    return None

            # 检查是否为"none"，表示原本就没有评分
            if tmdb_elem.text.strip().lower() == "none":
                logger.info(f"原NFO文件无评分，删除rating标签: {media_key}")
                # 删除rating标签（如果存在）
                traditional_rating_elem = root.find("rating")
                if traditional_rating_elem is not None:
                    root.remove(traditional_rating_elem)
                    logger.debug(f"已删除rating标签")

                # 更新rating_source为tmdb
                rating_source_elem = emby_rating_elem.find("rating_source")
                if rating_source_elem is None:
                    rating_source_elem = ET.SubElement(emby_rating_elem, "rating_source")
                rating_source_elem.text = "tmdb"

                return 0.0  # 返回0表示成功但无评分

            # 尝试解析评分
            try:
                rating = float(tmdb_elem.text)
            except ValueError:
                logger.error(f"TMDB评分格式无效: {tmdb_elem.text}")
                return None

            # 更新传统rating标签
            traditional_rating_elem = root.find("rating")
            if traditional_rating_elem is None:
                traditional_rating_elem = ET.SubElement(root, "rating")
            traditional_rating_elem.text = str(rating)

            # 更新EmbyRating标签中的rating_source
            rating_source_elem = emby_rating_elem.find("rating_source")
            if rating_source_elem is None:
                rating_source_elem = ET.SubElement(emby_rating_elem, "rating_source")
            rating_source_elem.text = "tmdb"

            # 更新更新时间
            update_elem = emby_rating_elem.find("update")
            if update_elem is None:
                update_elem = ET.SubElement(emby_rating_elem, "update")
            update_elem.text = datetime.now().strftime("%Y-%m-%d")

            # 格式化XML并直接保存
            try:
                xml_str = self.format_xml(root)

                with open(nfo_path, 'w', encoding='utf-8') as f:
                    f.write(xml_str)

                if rating == 0.0:
                    logger.info(f"恢复TMDB状态成功（无评分）: {media_key}")
                else:
                    logger.info(f"恢复TMDB评分成功: {media_key} = {rating}")
                return rating

            except Exception as e:
                logger.error(
                    f"保存NFO文件失败: {nfo_path}, 错误: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"恢复TMDB评分失败 {nfo_path}: {str(e)}")
            return None

    def _start_file_monitor(self):
        """启动文件监控（异步）"""
        if not self._media_dirs:
            logger.warning(f"未配置媒体目录，无法启用文件监控")
            return

        # 停止现有的监控线程
        self._stop_monitor_thread()

        # 创建停止事件
        self._monitor_stop_event = threading.Event()

        # 启动监控线程
        self._monitor_thread = threading.Thread(
            target=self._monitor_thread_worker,
            name="EmbyRating-FileMonitor",
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("文件监控线程已启动")

    def _monitor_thread_worker(self):
        """监控线程工作函数"""
        try:
            logger.info("文件监控线程开始工作")

            # 停止现有的监控
            self._stop_file_monitor()

            # 解析媒体目录
            media_dirs = [d.strip() for d in self._media_dirs.split("\n") if d.strip()]
            logger.info(f"准备启动文件监控，共 {len(media_dirs)} 个目录")

            # 为每个目录启动监控
            for dir_config in media_dirs:
                # 检查是否收到停止信号
                if self._monitor_stop_event.is_set():
                    logger.info("收到停止信号，中断文件监控启动")
                    break

                if not dir_config:
                    continue

                try:
                    # 解析目录路径
                    if "#" in dir_config:
                        mon_path = dir_config.split("#", 1)[0].strip()
                    else:
                        mon_path = dir_config.strip()

                    # 检查目录是否存在
                    if not Path(mon_path).exists():
                        logger.warning(f"目录不存在，跳过: {mon_path}")
                        continue

                    logger.debug(f"正在为目录 {mon_path} 创建文件监控...")
                    # 可以根据需要强制使用轮询模式，适用于有大量软连接的目录
                    observer = self.__choose_observer(force_polling=False)

                    # 先添加到列表，即使后续失败也能在停止时清理
                    self._file_observers.append(observer)

                    # 设置监控，非递归模式避免软连接性能问题
                    observer.schedule(
                        NFOFileHandler(self),
                        mon_path,
                        recursive=True
                    )

                    observer.daemon = True

                    # 启动observer，这里可能会阻塞
                    logger.debug(f"正在启动 {mon_path} 的文件监控服务...")
                    observer.start()

                    # 简单验证observer是否成功启动
                    if observer.is_alive():
                        logger.info(f"{mon_path} 的文件监控服务启动成功")
                    else:
                        logger.warning(f"{mon_path} 的文件监控服务启动后状态异常")

                except Exception as e:
                    logger.error(f"{mon_path} 启动文件监控失败：{str(e)}")
                    # 如果启动失败，尝试从列表中移除这个observer
                    if 'observer' in locals() and observer in self._file_observers:
                        try:
                            self._file_observers.remove(observer)
                            observer.stop()
                        except:
                            pass

            logger.info(f"文件监控启动完成")

        except Exception as e:
            logger.error(f"监控线程工作过程中发生错误: {str(e)}")
        finally:
            logger.info("文件监控线程工作结束")


    def _stop_file_monitor(self):
        """停止文件监控"""
        # 首先停止文件监控，防止新的删除事件
        if self._file_observers:
            for observer in self._file_observers:
                try:
                    observer.stop()
                    observer.join()
                except Exception as e:
                    print(str(e))
                    logger.error(f"停止目录监控失败：{str(e)}")
        self._file_observers = []
        logger.debug("文件监控已停止")

    def _handle_new_nfo_file(self, nfo_path: Path):
        """处理新创建的NFO文件"""
        try:
            logger.info(f"处理新NFO文件: {nfo_path}")

            # 等待文件写入完成
            time.sleep(2)

            # 检查文件是否仍然存在
            if not nfo_path.exists():
                logger.debug(f"NFO文件已不存在，跳过处理: {nfo_path}")
                return

            # 判断NFO文件类型
            media_type = self._determine_nfo_type(nfo_path)
            if not media_type:
                logger.debug(f"无法确定NFO文件类型或不需要处理: {nfo_path}")
                return

            # 检查评分源配置
            if self._rating_source == "tmdb":
                logger.debug(f"当前评分源为TMDB，跳过处理: {nfo_path}")
                return

            # 根据媒体类型处理
            if media_type == "movie":
                self._handle_movie_nfo(nfo_path)
            elif media_type == "tvshow":
                self._handle_tvshow_nfo(nfo_path)

        except Exception as e:
            logger.error(f"处理NFO文件失败 {nfo_path}: {str(e)}")
            import traceback
            logger.debug(f"详细错误信息: {traceback.format_exc()}")

    def _determine_nfo_type(self, nfo_path: Path) -> Optional[str]:
        """判断NFO文件类型"""
        try:
            # 读取NFO文件内容
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    logger.debug(f"无法读取NFO文件编码: {nfo_path}")
                    return None

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.debug(f"XML解析失败: {nfo_path}, 错误: {str(e)}")
                return None

            # 根据根元素判断类型
            root_tag = root.tag.lower()
            if root_tag == "movie":
                return "movie"
            elif root_tag == "tvshow":
                return "tvshow"
            elif root_tag == "episodedetails":
                # 电视剧集数，跳过处理
                logger.debug(f"检测到剧集NFO文件，跳过处理: {nfo_path}")
                return None
            else:
                logger.debug(f"未知的NFO文件类型: {root_tag}, 文件: {nfo_path}")
                return None

        except Exception as e:
            logger.error(f"判断NFO文件类型失败 {nfo_path}: {str(e)}")
            return None

    def _handle_movie_nfo(self, nfo_path: Path):
        """处理电影NFO文件"""
        try:
            logger.info(f"处理电影NFO文件: {nfo_path}")

            # 调用现有的电影处理方法
            self.process_nfo_file(nfo_path, MediaType.MOVIE)

            # 发送单个文件的通知
            self._send_single_file_notification()

        except Exception as e:
            logger.error(f"处理电影NFO文件失败 {nfo_path}: {str(e)}")

    def _handle_tvshow_nfo(self, nfo_path: Path):
        """处理电视剧NFO文件"""
        try:
            logger.info(f"处理电视剧NFO文件: {nfo_path}")

            self.process_nfo_file(nfo_path, MediaType.TV)

            # 发送单个文件的通知
            self._send_single_file_notification()

        except Exception as e:
            logger.error(f"处理电视剧NFO文件失败 {nfo_path}: {str(e)}")

    def _send_single_file_notification(self):
        """发送单个文件处理的通知"""
        try:
            # 统计处理结果
            success_count = len(self._processing_results)
            failed_count = len(self._failed_results)
            skipped_count = len(self._skipped_results)
            total_count = success_count + failed_count + skipped_count

            if total_count == 0:
                return

            # 构建简化的通知内容
            if success_count > 0:
                result = self._processing_results[0]
                title = "🎬 文件监控 - 评分更新成功"
                text = f"✅ {result['title']}\n📈 评分: {result['rating']} ({result['source']})"
            elif skipped_count > 0:
                result = self._skipped_results[0]
                title = "🎬 文件监控 - 跳过更新"
                text = f"⏭️ {result['title']}\n💡 原因: {result['reason']}"
            else:
                result = self._failed_results[0]
                title = "🎬 文件监控 - 更新失败"
                text = f"❌ {result['title']}\n💡 原因: {result['reason']}"

            # 发送通知
            if self._notify:
                self.post_message(
                    mtype=NotificationType.Plugin,
                    title=title,
                    text=text
                )

        except Exception as e:
            logger.error(f"发送文件监控通知失败: {str(e)}")
        finally:
            # 清空结果列表
            self._processing_results.clear()
            self._failed_results.clear()
            self._skipped_results.clear()
