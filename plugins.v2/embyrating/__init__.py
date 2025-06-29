import time
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from xml.dom import minidom

import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.plugins.embyrating.DoubanHelper import *

from app.core.config import settings
from app.core.event import eventmanager, Event
from app.core.metainfo import MetaInfoPath
from app.chain.media import MediaChain
from app.schemas import FileItem
from app.schemas.types import EventType, MediaType
from app.plugins import _PluginBase
from app.log import logger
from app.schemas import NotificationType


class EmbyRating(_PluginBase):
    # 插件名称
    plugin_name = "Emby评分管理"
    # 插件描述
    plugin_desc = "修改Emby媒体评分，支持豆瓣评分和TMDB评分切换"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/emby_rating.png"
    # 插件版本
    plugin_version = "1.0"
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

    # 日志标签
    LOG_TAG = "[EmbyRating]"

    # 私有属性
    _enabled = False
    _cron = None
    _notify = False
    _onlyonce = False
    _rating_source = "tmdb"  # tmdb 或 douban
    _update_interval = 7  # 豆瓣评分更新间隔（天）
    _auto_scrape = True  # 是否自动刮削
    _cache_enabled = True  # 是否启用缓存
    _media_dirs = ""  # 媒体目录，多个用逗号分隔
    _refresh_library = True  # 是否在更新NFO后刷新媒体库

    # 定时器
    _scheduler: Optional[BackgroundScheduler] = None

    # 评分缓存 {media_key: {"rating": float, "last_update": timestamp}}
    _rating_cache: Dict[str, Dict] = {}

    # 处理结果收集器，用于批量通知
    _processing_results: List[Dict] = []

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
            self._cache_enabled = config.get("cache_enabled", True)
            self._media_dirs = config.get("media_dirs", "")
            self._refresh_library = config.get("refresh_library", True)

        # 加载缓存数据
        self._load_cache_data()

        # 初始化处理结果收集器
        self._processing_results = []

        if self._enabled:
            # 启动定时任务
            self._scheduler = BackgroundScheduler(timezone=settings.TZ)

            if self._onlyonce:
                logger.info(f"{self.LOG_TAG} 立即运行一次评分更新")
                self._scheduler.add_job(
                    func=self.update_all_ratings,
                    trigger="date",
                    run_date=datetime.now(tz=pytz.timezone(
                        settings.TZ)) + timedelta(seconds=3),
                    name="立即更新评分",
                )
                self._onlyonce = False
                self._update_config()

            if self._cron:
                logger.info(f"{self.LOG_TAG} 启动定时任务：{self._cron}")
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
            "cache_enabled": self._cache_enabled,
            "media_dirs": self._media_dirs,
            "refresh_library": self._refresh_library,
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
                        f"{self.LOG_TAG} 清理了 {len(expired_keys)} 个过期缓存条目")

            # 保存清理后的缓存
            self._save_cache_data()

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 清理缓存失败：{str(e)}")

    def _load_cache_data(self):
        """加载缓存数据"""
        try:
            cache_data = self.get_data("rating_cache")
            if cache_data:
                self._rating_cache = cache_data

            # 加载后立即清理
            self._cleanup_cache()

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 加载缓存数据失败：{str(e)}")

    def _save_cache_data(self):
        """保存缓存数据"""
        try:
            self.save_data("rating_cache", self._rating_cache)
        except Exception as e:
            logger.error(
                f"{self.LOG_TAG} 保存缓存数据失败：{str(e)}")

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
                    f"{self.LOG_TAG} 找到TMDB ID: {tmdb_id}，"
                    f"需要调用API获取评分")
                return None

        except Exception as e:
            logger.error(
                f"{self.LOG_TAG} 读取NFO文件评分失败 {nfo_path}: {str(e)}")

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
                        f"{self.LOG_TAG} 无法读取NFO文件编码: {nfo_path}")
                    return

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(
                    f"{self.LOG_TAG} XML解析失败: {nfo_path}, "
                    f"错误: {str(e)}")
                return

            # 检查是否已有EmbyRating标签
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                emby_rating_elem = ET.SubElement(root, "EmbyRating")
                logger.debug(f"{self.LOG_TAG} 创建EmbyRating标签")

            # 检查是否已有tmdb评分
            tmdb_elem = emby_rating_elem.find("tmdb")
            if tmdb_elem is not None and tmdb_elem.text:
                logger.debug(
                    f"{self.LOG_TAG} EmbyRating标签中已有TMDB评分: "
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

            # 如果传统rating标签没有，尝试从其他地方获取
            if current_rating is None:
                # 这里可以添加其他获取评分的逻辑
                logger.warning(
                    f"{self.LOG_TAG} 无法获取当前评分，跳过备份: {nfo_path}")
                return

            # 保存TMDB评分到EmbyRating标签
            if tmdb_elem is None:
                tmdb_elem = ET.SubElement(emby_rating_elem, "tmdb")
            tmdb_elem.text = str(current_rating)

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
                logger.info(
                    f"{self.LOG_TAG} 备份TMDB评分成功: "
                    f"{media_key} = {current_rating}")
            except Exception as e:
                logger.error(
                    f"{self.LOG_TAG} 保存NFO文件失败: {nfo_path}, "
                    f"错误: {str(e)}")
        except Exception as e:
            logger.error(
                f"{self.LOG_TAG} 备份TMDB评分失败 {nfo_path}: {str(e)}")

    def get_douban_rating(self, title: str, year: Optional[int] = None) -> Optional[float]:
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
                            f"{self.LOG_TAG} 使用缓存豆瓣评分: "
                            f"{title} = {cache_data['rating']}")
                        return cache_data["rating"]

            # 调用DoubanHelper获取评分
            douban_helper = DoubanHelper()
            subject_title, subject_id, score = douban_helper.get_subject_id(
                title)

            if subject_id and score and score != "0":
                rating = float(score)

                # 更新缓存
                if self._cache_enabled:
                    cache_key = self.get_media_key(
                        title, year, MediaType.MOVIE)
                    self._rating_cache[cache_key] = {
                        "rating": rating,
                        "last_update": time.time()
                    }

                logger.info(
                    f"{self.LOG_TAG} 获取豆瓣评分成功: {title} = {rating}")
                return rating
            else:
                logger.warning(f"{self.LOG_TAG} 未找到豆瓣评分: {title}")
                return None

        except Exception as e:
            logger.error(
                f"{self.LOG_TAG} 获取豆瓣评分失败 {title}: {str(e)}")
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
            logger.error(f"{self.LOG_TAG} XML格式化失败: {str(e)}")
            # 如果格式化失败，使用简单的tostring
            return ET.tostring(root, encoding='unicode', xml_declaration=True)

    def update_nfo_rating(self, nfo_path: Path, new_rating: float, 
                         rating_source: str = "douban"):
        """更新NFO文件中的评分"""
        try:
            logger.debug(
                f"{self.LOG_TAG} 开始更新NFO评分: {nfo_path} = "
                f"{new_rating} ({rating_source})"
            )

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
                        f"{self.LOG_TAG} 无法读取NFO文件编码: {nfo_path}"
                    )
                    return False

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(
                    f"{self.LOG_TAG} XML解析失败: {nfo_path}, "
                    f"错误: {str(e)}"
                )
                return False

            # 查找或创建EmbyRating标签
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                emby_rating_elem = ET.SubElement(root, "EmbyRating")
                logger.debug(f"{self.LOG_TAG} 创建EmbyRating标签")

            # 更新对应评分源的评分
            rating_elem = emby_rating_elem.find(rating_source)
            if rating_elem is None:
                rating_elem = ET.SubElement(emby_rating_elem, rating_source)
            rating_elem.text = str(new_rating)

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
                    f"{self.LOG_TAG} 更新NFO评分成功: {nfo_path} = "
                    f"{new_rating} ({rating_source})"
                )
                
                return True

            except Exception as e:
                logger.error(
                    f"{self.LOG_TAG} 保存NFO文件失败: {nfo_path}, "
                    f"错误: {str(e)}"
                )
                return False

        except Exception as e:
            logger.error(
                f"{self.LOG_TAG} 更新NFO评分失败 {nfo_path}: {str(e)}"
            )
            import traceback
            logger.debug(
                f"{self.LOG_TAG} 详细错误信息: {traceback.format_exc()}"
            )
            return False

    def _get_media_servers_from_config(self) -> set:
        """从媒体目录配置中获取所有涉及的媒体服务器名称"""
        servers = set()
        if not self._media_dirs:
            return servers

        for dir_config in self._media_dirs.split(","):
            dir_config = dir_config.strip()
            if "#" in dir_config:
                # 解析路径和媒体服务器名称
                path_part, server_part = dir_config.split("#", 1)
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
                logger.warning(f"{self.LOG_TAG} 未找到可用的媒体服务器模块")
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
                            f"{self.LOG_TAG} 检查模块 {module.__class__.__name__} "
                            f"时出错: {str(e)}"
                        )
                        continue

                if not target_module:
                    logger.warning(
                        f"{self.LOG_TAG} 未找到指定的媒体服务器: {server_name}"
                    )
                    continue

                # 获取服务器实例并刷新
                server_instance = target_module.get_instance(server_name)
                if not server_instance:
                    logger.warning(
                        f"{self.LOG_TAG} 无法获取媒体服务器实例: {server_name}"
                    )
                    continue

                if hasattr(server_instance, 'refresh_root_library'):
                    success = server_instance.refresh_root_library()
                    if success:
                        logger.info(
                            f"{self.LOG_TAG} 成功刷新媒体库: {server_name}"
                        )
                    else:
                        logger.warning(
                            f"{self.LOG_TAG} 刷新媒体库失败: {server_name}"
                        )
                else:
                    logger.warning(
                        f"{self.LOG_TAG} 媒体服务器 {server_name} 不支持刷新功能"
                    )

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 刷新媒体库失败: {str(e)}")

    def update_all_ratings(self):
        """更新所有媒体评分"""
        logger.info(f"{self.LOG_TAG} 开始更新所有媒体评分")

        # 初始化处理结果收集器
        self._processing_results = []

        # 获取媒体目录列表
        media_dirs = []
        if self._media_dirs:
            for dir_config in self._media_dirs.split(","):
                dir_config = dir_config.strip()
                if "#" in dir_config:
                    # 解析路径和媒体服务器名称
                    path_part, server_part = dir_config.split("#", 1)
                    media_dir = Path(path_part.strip())
                else:
                    # 没有指定媒体服务器，只使用路径
                    media_dir = Path(dir_config.strip())

                if media_dir:
                    media_dirs.append(media_dir)

        if not media_dirs:
            logger.warning(f"{self.LOG_TAG} 未配置媒体目录")
            return

        # 处理每个媒体目录
        for media_dir in media_dirs:
            if not media_dir.exists():
                logger.warning(f"{self.LOG_TAG} 媒体目录不存在: {media_dir}")
                continue

            logger.info(f"{self.LOG_TAG} 处理媒体目录: {media_dir}")
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
                    f"{self.LOG_TAG} 开始刷新媒体服务器: {', '.join(server_names)}"
                )
                self._refresh_media_servers(server_names)
            else:
                logger.debug(f"{self.LOG_TAG} 未配置需要刷新的媒体服务器")

        logger.info(f"{self.LOG_TAG} 评分更新完成")

    def _send_batch_notification(self):
        """发送批量通知"""
        if not self._notify or not self._processing_results:
            return

        try:
            # 按评分源分组
            douban_results = []
            tmdb_results = []

            for result in self._processing_results:
                if result['source'] == 'douban':
                    douban_results.append(result)
                elif result['source'] == 'tmdb':
                    tmdb_results.append(result)

            # 发送豆瓣评分通知
            if douban_results:
                title = f"🎬 豆瓣评分更新完成"
                text_lines = []
                for result in douban_results:
                    emoji = "📺" if result['media_type'] == 'TV' else "🎥"
                    text_lines.append(
                        f"{emoji} {result['title']} - 切换到豆瓣评分，评分为 {result['rating']}"
                    )

                text = "\n".join(text_lines)
                self.post_message(
                    mtype=NotificationType.MediaServer,
                    title=title,
                    text=text
                )

            # 发送TMDB评分通知
            if tmdb_results:
                title = f"🎬 TMDB评分恢复完成"
                text_lines = []
                for result in tmdb_results:
                    emoji = "📺" if result['media_type'] == 'TV' else "🎥"
                    text_lines.append(
                        f"{emoji} {result['title']} - 切换到TMDB评分，评分为 {result['rating']}"
                    )

                text = "\n".join(text_lines)
                self.post_message(
                    mtype=NotificationType.MediaServer,
                    title=title,
                    text=text
                )

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 发送批量通知失败：{str(e)}")

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
        """注册插件API（已废弃，保留兼容性）"""
        return []

    def switch_rating_source(self, source: str):
        """切换评分源API"""
        if source not in ["tmdb", "douban"]:
            return {"success": False, "message": "无效的评分源"}

        self._rating_source = source
        self._update_config()
        self.update_all_ratings()

        return {"success": True, "message": f"已切换到{source}评分"}

    def debug_nfo_file(self, nfo_path: Path) -> dict:
        """调试NFO文件，返回详细信息"""
        debug_info = {
            "file_path": str(nfo_path),
            "exists": False,
            "file_size": 0,
            "encoding": None,
            "xml_parse_success": False,
            "root_tag": None,
            "title_found": False,
            "title_text": None,
            "year_found": False,
            "year_text": None,
            "rating_found": False,
            "rating_text": None,
            "error": None
        }

        try:
            # 检查文件是否存在
            if not nfo_path.exists():
                debug_info["error"] = "文件不存在"
                return debug_info

            debug_info["exists"] = True
            debug_info["file_size"] = nfo_path.stat().st_size

            if debug_info["file_size"] == 0:
                debug_info["error"] = "文件为空"
                return debug_info

            # 尝试读取文件内容
            content = None
            for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-16']:
                try:
                    with open(nfo_path, 'r', encoding=encoding) as f:
                        content = f.read()
                    debug_info["encoding"] = encoding
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                debug_info["error"] = "无法识别文件编码"
                return debug_info

            # 解析XML
            try:
                root = ET.fromstring(content)
                debug_info["xml_parse_success"] = True
                debug_info["root_tag"] = root.tag
            except ET.ParseError as e:
                debug_info["error"] = f"XML解析失败: {str(e)}"
                return debug_info

            # 查找标题
            title_elem = root.find("title")
            if title_elem and title_elem.text:
                debug_info["title_found"] = True
                debug_info["title_text"] = title_elem.text.strip()

            # 查找年份
            year_elem = root.find("year")
            if year_elem and year_elem.text:
                debug_info["year_found"] = True
                debug_info["year_text"] = year_elem.text.strip()

            # 查找评分
            rating_elem = root.find("rating")
            if rating_elem and rating_elem.text:
                debug_info["rating_found"] = True
                debug_info["rating_text"] = rating_elem.text.strip()

            # 查找其他可能的标题元素
            alt_titles = {}
            for title_tag in ["originaltitle", "sorttitle", "name"]:
                alt_elem = root.find(title_tag)
                if alt_elem and alt_elem.text:
                    alt_titles[title_tag] = alt_elem.text.strip()

            if alt_titles:
                debug_info["alternative_titles"] = alt_titles

        except Exception as e:
            debug_info["error"] = f"处理异常: {str(e)}"
            import traceback
            debug_info["traceback"] = traceback.format_exc()

        return debug_info

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
                                                {'title': '豆瓣评分', 'value': 'douban'}
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
                                            'model': 'cache_enabled',
                                            'label': '启用缓存',
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
                                            'label': '媒体目录（多个用逗号分隔）',
                                            'rows': 3,
                                            'placeholder': '例如：/sata/影视/电影#Emby,/sata/影视/电视剧#Jellyfin\n格式：媒体库根目录#媒体服务器名称'
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
                                        'component': 'VTextField',
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
                                            'label': '立即运行一次',
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
            "cache_enabled": True,
            "media_dirs": "",
            "refresh_library": True
        }

    def get_page(self) -> List[dict]:
        """拼装插件详情页面（已废弃，保留兼容性）"""
        return []

    def stop_service(self):
        """停止插件"""
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error(f"{self.LOG_TAG} 停止插件失败：{str(e)}")

    def process_media_directory(self, media_dir: Path):
        """处理媒体目录"""
        try:
            # 检查目录是否存在
            if not media_dir.exists():
                logger.warning(f"{self.LOG_TAG} 媒体目录不存在: {media_dir}")
                return

            # 收集所有需要处理的NFO文件
            processed_shows = set()  # 记录已处理的电视剧，避免重复处理

            # 遍历目录查找媒体文件
            for item in media_dir.rglob("*"):
                if item.is_file() and item.suffix.lower() in [
                    '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'
                ]:
                    # 检查是否为电视剧结构
                    if self._is_tv_show_structure(item):
                        # 处理电视剧
                        show_root = self._get_tv_show_root(item)
                        if show_root and show_root not in processed_shows:
                            processed_shows.add(show_root)
                            self._process_tv_show(show_root)
                    else:
                        # 处理电影
                        nfo_path = item.with_suffix('.nfo')
                        if not nfo_path.exists():
                            # 尝试刮削
                            if not self.scrape_media_if_needed(item.parent):
                                continue
                            # 重新检查NFO文件
                            if not nfo_path.exists():
                                logger.warning(
                                    f"{self.LOG_TAG} 刮削后仍未找到NFO文件: {nfo_path}"
                                )
                                continue
                        # 处理NFO文件
                        self.process_nfo_file(nfo_path)

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 处理媒体目录失败 {media_dir}: {str(e)}")

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
        """处理电视剧，只更新tvshow.nfo文件"""
        try:
            tvshow_nfo = show_root / "tvshow.nfo"
            if not tvshow_nfo.exists():
                logger.warning(f"{self.LOG_TAG} 未找到tvshow.nfo文件: {show_root}")
                return

            # 获取第一季的豆瓣评分作为整个剧集的评分
            first_season_rating = self._get_first_season_rating(show_root)
            if not first_season_rating:
                logger.warning(f"{self.LOG_TAG} 无法获取第一季评分: {show_root}")
                return

            # 处理tvshow.nfo文件
            self.process_nfo_file(tvshow_nfo, override_rating=first_season_rating)

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 处理电视剧失败 {show_root}: {str(e)}")

    def _get_first_season_rating(self, show_root: Path) -> Optional[float]:
        """获取第一季的豆瓣评分"""
        try:
            # 查找第一季目录
            season_dirs = []
            for item in show_root.iterdir():
                if item.is_dir() and ('season' in item.name.lower() or
                                     item.name.lower().startswith('s')):
                    season_dirs.append(item)

            if not season_dirs:
                # 如果没有季目录，直接从剧集根目录获取标题
                return self._get_rating_from_tvshow_nfo(show_root / "tvshow.nfo")

            # 排序找到第一季
            season_dirs.sort(key=lambda x: x.name.lower())
            first_season = season_dirs[0]

            # 从第一季的标题获取豆瓣评分
            return self._get_rating_from_season_title(show_root, first_season)

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 获取第一季评分失败: {str(e)}")
            return None

    def _get_rating_from_tvshow_nfo(self, tvshow_nfo: Path) -> Optional[float]:
        """从tvshow.nfo文件获取标题并查询豆瓣评分"""
        try:
            if not tvshow_nfo.exists():
                return None

            with open(tvshow_nfo, 'r', encoding='utf-8') as f:
                content = f.read()

            root = ET.fromstring(content)
            title_elem = self.find_elem_ignore_ns(root, "title")
            if title_elem and title_elem.text:
                title = title_elem.text.strip()
                year_elem = self.find_elem_ignore_ns(root, "year")
                year = None
                if year_elem and year_elem.text:
                    try:
                        year = int(year_elem.text.strip())
                    except ValueError:
                        pass

                return self.get_douban_rating(title, year)

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 从tvshow.nfo获取评分失败: {str(e)}")

        return None

    def _get_rating_from_season_title(self, show_root: Path, season_dir: Path) -> Optional[float]:
        """从季标题获取豆瓣评分"""
        try:
            # 构造第一季的标题
            tvshow_nfo = show_root / "tvshow.nfo"
            if not tvshow_nfo.exists():
                return None

            with open(tvshow_nfo, 'r', encoding='utf-8') as f:
                content = f.read()

            root = ET.fromstring(content)
            title_elem = self.find_elem_ignore_ns(root, "title")
            if not title_elem or not title_elem.text:
                return None

            base_title = title_elem.text.strip()

            # 构造第一季标题
            season_title = f"{base_title} 第 1 季"

            year_elem = self.find_elem_ignore_ns(root, "year")
            year = None
            if year_elem and year_elem.text:
                try:
                    year = int(year_elem.text.strip())
                except ValueError:
                    pass

            return self.get_douban_rating(season_title, year)

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 从季标题获取评分失败: {str(e)}")
            return None

    def find_elem_ignore_ns(self, root, tag_name):
        """在root下查找忽略命名空间和不可见字符的tag_name元素，输出调试信息"""
        for elem in root.iter():
            tag = elem.tag
            if tag.lower().strip().endswith(tag_name):
                logger.debug(f"{self.LOG_TAG} 命中tag: {repr(tag)}")
                return elem
        return None

    def process_nfo_file(self, nfo_path: Path, override_rating: Optional[float] = None):
        """处理单个NFO文件，兼容命名空间"""
        try:
            # 检查文件是否存在
            if not nfo_path.exists():
                logger.warning(f"{self.LOG_TAG} NFO文件不存在: {nfo_path}")
                return

            # 检查文件大小
            file_size = nfo_path.stat().st_size
            if file_size == 0:
                logger.warning(f"{self.LOG_TAG} NFO文件为空: {nfo_path}")
                return

            logger.debug(
                f"{self.LOG_TAG} 开始处理NFO文件: {nfo_path} (大小: {file_size} bytes)")

            # 尝试读取文件内容
            try:
                with open(nfo_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                logger.debug(f"{self.LOG_TAG} 成功读取NFO文件内容，长度: {len(content)}")
            except UnicodeDecodeError:
                try:
                    with open(nfo_path, 'r', encoding='gbk') as f:
                        content = f.read()
                    logger.debug(f"{self.LOG_TAG} 使用GBK编码成功读取NFO文件")
                except UnicodeDecodeError:
                    logger.error(f"{self.LOG_TAG} NFO文件编码无法识别: {nfo_path}")
                    return
                except Exception as e:
                    logger.error(
                        f"{self.LOG_TAG} 读取NFO文件失败: {nfo_path}, 错误: {str(e)}")
                    return

            # 解析XML
            try:
                root = ET.fromstring(content)
                logger.debug(f"{self.LOG_TAG} 成功解析XML，根元素: {root.tag}")
            except ET.ParseError as e:
                logger.error(
                    f"{self.LOG_TAG} XML解析失败: {nfo_path}, 错误: {str(e)}")
                return
            except Exception as e:
                logger.error(
                    f"{self.LOG_TAG} XML解析异常: {nfo_path}, 错误: {str(e)}")
                return

            # 获取媒体信息（忽略命名空间）
            title_elem = self.find_elem_ignore_ns(root, "title")
            if title_elem is None:
                logger.warning(f"{self.LOG_TAG} NFO文件中未找到title元素: {nfo_path}")
                # 尝试查找其他可能的标题元素
                alt_title_elem = None
                for title_tag in ["originaltitle", "sorttitle", "name", "showname"]:
                    alt_title_elem = self.find_elem_ignore_ns(root, title_tag)
                    if alt_title_elem is not None and alt_title_elem.text:
                        logger.info(
                            f"{self.LOG_TAG} 使用替代标题元素 {title_tag}: {alt_title_elem.text}")
                        break
                if alt_title_elem and alt_title_elem.text:
                    title_elem = alt_title_elem
                else:
                    logger.warning(
                        f"{self.LOG_TAG} NFO文件缺少有效标题，尝试从文件名推断: {nfo_path}")
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
                            f"{self.LOG_TAG} 从文件名推断标题: {title_from_filename}")
                        title_elem = ET.Element("title")
                        title_elem.text = title_from_filename
                    else:
                        logger.warning(
                            f"{self.LOG_TAG} 无法从文件名推断标题: {filename}")
                        full_xml = ET.tostring(root, encoding='unicode')
                        logger.debug(f"{self.LOG_TAG} 完整XML结构: {full_xml}")
                        return
            elif not title_elem.text or not title_elem.text.strip():
                logger.warning(f"{self.LOG_TAG} NFO文件中title元素内容为空: {nfo_path}")
                # 尝试查找其他可能的标题元素
                alt_title_elem = None
                for title_tag in ["originaltitle", "sorttitle", "name", "showname"]:
                    alt_title_elem = self.find_elem_ignore_ns(root, title_tag)
                    if alt_title_elem is not None and alt_title_elem.text and alt_title_elem.text.strip():
                        logger.info(
                            f"{self.LOG_TAG} 使用替代标题元素 {title_tag}: {alt_title_elem.text}")
                        break
                if alt_title_elem and alt_title_elem.text and alt_title_elem.text.strip():
                    title_elem = alt_title_elem
                else:
                    logger.warning(
                        f"{self.LOG_TAG} NFO文件title内容为空且无替代标题，尝试从文件名推断: {nfo_path}")
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
                            f"{self.LOG_TAG} 从文件名推断标题: {title_from_filename}")
                        title_elem = ET.Element("title")
                        title_elem.text = title_from_filename
                    else:
                        logger.warning(
                            f"{self.LOG_TAG} 无法从文件名推断标题: {filename}")
                        return
            else:
                logger.debug(f"{self.LOG_TAG} 找到title元素: {title_elem.text}")

            title = title_elem.text.strip()
            if not title:
                logger.warning(f"{self.LOG_TAG} NFO文件标题为空: {nfo_path}")
                return
            logger.debug(f"{self.LOG_TAG} 最终使用标题: {title}")

            # 获取年份（忽略命名空间）
            year = None
            year_elem = self.find_elem_ignore_ns(root, "year")
            if year_elem is None:
                logger.debug(f"{self.LOG_TAG} NFO文件中未找到year元素")
            elif not year_elem.text or not year_elem.text.strip():
                logger.debug(
                    f"{self.LOG_TAG} NFO文件中year元素内容为空: '{year_elem.text}'")
            else:
                try:
                    year = int(year_elem.text.strip())
                    logger.debug(f"{self.LOG_TAG} 找到年份: {year}")
                except ValueError:
                    logger.warning(
                        f"{self.LOG_TAG} 年份格式无效: '{year_elem.text}'")

            # 如果从XML中没找到年份，尝试从文件名推断
            if not year:
                import re
                year_match = re.search(r'\((\d{4})\)', nfo_path.name)
                if year_match:
                    try:
                        year = int(year_match.group(1))
                        logger.info(f"{self.LOG_TAG} 从文件名推断年份: {year}")
                    except ValueError:
                        pass

            # 判断媒体类型
            media_type = MediaType.MOVIE
            if self.find_elem_ignore_ns(root, "episodedetails") is not None:
                media_type = MediaType.TV
                logger.debug(f"{self.LOG_TAG} 识别为电视剧")
            else:
                logger.debug(f"{self.LOG_TAG} 识别为电影")

            # 生成媒体键
            media_key = self.get_media_key(title, year, media_type)
            logger.debug(f"{self.LOG_TAG} 生成媒体键: {media_key}")

            # 备份TMDB评分
            self.backup_tmdb_rating(nfo_path, media_key)

            # 根据评分源处理
            if self._rating_source == "douban":
                # 获取豆瓣评分（优先使用override_rating）
                douban_rating = override_rating or self.get_douban_rating(title, year)
                if douban_rating:
                    # 更新NFO文件
                    if self.update_nfo_rating(nfo_path, douban_rating, "douban"):
                        # 添加到处理结果
                        self._processing_results.append({
                            'title': title,
                            'rating': douban_rating,
                            'source': 'douban',
                            'media_type': media_type.value
                        })
                else:
                    logger.warning(f"{self.LOG_TAG} 无法获取豆瓣评分: {title}")

            elif self._rating_source == "tmdb":
                # 恢复TMDB评分
                if media_key:
                    restored_rating = self.restore_tmdb_rating(nfo_path, media_key)
                    if restored_rating:
                        # 添加到处理结果
                        self._processing_results.append({
                            'title': title,
                            'rating': restored_rating,
                            'source': 'tmdb',
                            'media_type': media_type.value
                        })
                else:
                    logger.warning(f"{self.LOG_TAG} 未找到TMDB评分备份: {title}")
        except Exception as e:
            logger.error(f"{self.LOG_TAG} 处理NFO文件失败 {nfo_path}: {str(e)}")
            import traceback
            logger.debug(f"{self.LOG_TAG} 详细错误信息: {traceback.format_exc()}")

    def scrape_media_if_needed(self, media_path: Path) -> bool:
        """如果需要则进行刮削"""
        if not self._auto_scrape:
            return True

        try:
            # 检查是否存在NFO文件
            nfo_files = list(media_path.glob("*.nfo"))
            if nfo_files:
                return True

            # 检查是否为媒体文件
            media_extensions = ['.mkv', '.mp4', '.avi',
                                '.mov', '.wmv', '.flv', '.webm']
            media_files = [f for f in media_path.iterdir(
            ) if f.is_file() and f.suffix.lower() in media_extensions]

            if not media_files:
                return True

            logger.info(f"{self.LOG_TAG} 开始刮削媒体: {media_path}")

            # 调用MoviePilot的刮削功能
            mediachain = MediaChain()

            # 创建FileItem
            fileitem = FileItem(
                path=str(media_path),
                type="dir" if media_path.is_dir() else "file",
                storage="local"
            )

            # 识别媒体信息
            meta = MetaInfoPath(media_path)
            mediainfo = mediachain.recognize_media(meta)

            if mediainfo:
                # 执行刮削
                mediachain.scrape_metadata(
                    fileitem=fileitem, meta=meta, mediainfo=mediainfo, overwrite=True)
                logger.info(f"{self.LOG_TAG} 刮削完成: {media_path}")
                return True
            else:
                logger.warning(f"{self.LOG_TAG} 无法识别媒体信息，跳过刮削: {media_path}")
                return False

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 刮削失败 {media_path}: {str(e)}")
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
                    logger.error(f"{self.LOG_TAG} 无法读取NFO文件编码: {nfo_path}")
                    return False

            # 解析XML
            try:
                root = ET.fromstring(content)
            except ET.ParseError as e:
                logger.error(
                    f"{self.LOG_TAG} XML解析失败: {nfo_path}, 错误: {str(e)}")
                return False

            # 从EmbyRating标签中获取TMDB评分
            emby_rating_elem = root.find("EmbyRating")
            if emby_rating_elem is None:
                logger.warning(f"{self.LOG_TAG} 未找到EmbyRating标签: {media_key}")
                return None

            tmdb_elem = emby_rating_elem.find("tmdb")
            if tmdb_elem is None or not tmdb_elem.text:
                logger.warning(f"{self.LOG_TAG} 未找到TMDB评分备份: {media_key}")
                return None

            try:
                rating = float(tmdb_elem.text)
            except ValueError:
                logger.error(f"{self.LOG_TAG} TMDB评分格式无效: {tmdb_elem.text}")
                return None

            # 更新传统rating标签
            traditional_rating_elem = root.find("rating")
            if traditional_rating_elem is None:
                traditional_rating_elem = ET.SubElement(root, "rating")
            traditional_rating_elem.text = str(rating)

            # 更新EmbyRating标签中的tmdb评分
            tmdb_elem.text = str(rating)

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

                logger.info(
                    f"{self.LOG_TAG} 恢复TMDB评分成功: {media_key} = {rating}")
                return rating

            except Exception as e:
                logger.error(
                    f"{self.LOG_TAG} 保存NFO文件失败: {nfo_path}, 错误: {str(e)}")
                return None

        except Exception as e:
            logger.error(f"{self.LOG_TAG} 恢复TMDB评分失败 {nfo_path}: {str(e)}")
            return None