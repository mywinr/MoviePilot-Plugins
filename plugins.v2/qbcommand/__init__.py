from typing import List, Tuple, Dict, Any, Optional
from enum import Enum
from urllib.parse import urlparse
import urllib
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType, ServiceInfo
from app.schemas.types import EventType
from apscheduler.triggers.cron import CronTrigger
from app.core.event import eventmanager, Event
from apscheduler.schedulers.background import BackgroundScheduler
from app.core.config import settings
from app.helper.sites import SitesHelper
from app.db.site_oper import SiteOper
from app.utils.string import StringUtils
from app.helper.downloader import DownloaderHelper
from datetime import datetime, timedelta

import pytz
import time


class QbCommand(_PluginBase):
    # 插件名称
    plugin_name = "下载器远程操作"
    # 插件描述
    plugin_desc = "通过定时任务或交互命令远程操作qBittorrent/Transmission暂停/开始/限速等"
    # 插件图标
    plugin_icon = "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/qb_tr.png"
    # 插件版本
    plugin_version = "2.2"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "qbcommand_"
    # 加载顺序
    plugin_order = 1
    # 可使用的用户级别
    auth_level = 1

    # 私有属性
    _sites = None
    _siteoper = None
    _qb = None
    _enabled: bool = False
    _notify: bool = False
    _pause_cron = None
    _resume_cron = None
    _only_pause_once = False
    _only_resume_once = False
    _only_pause_upload = False
    _only_pause_download = False
    _only_pause_checking = False
    _upload_limit = 0
    _enable_upload_limit = False
    _download_limit = 0
    _enable_download_limit = False
    _op_site_ids = []
    _op_sites = []
    _multi_level_root_domain = ["edu.cn", "com.cn", "net.cn", "org.cn"]
    _scheduler = None
    _exclude_dirs = ""
    def init_plugin(self, config: dict = None):
        self._sites = SitesHelper()
        self._siteoper = SiteOper()
        self.downloader_helper = DownloaderHelper()
        # 停止现有任务
        self.stop_service()
        # 读取配置
        if config:
            self._enabled = config.get("enabled")
            self._notify = config.get("notify")
            self._pause_cron = config.get("pause_cron")
            self._resume_cron = config.get("resume_cron")
            self._only_pause_once = config.get("onlypauseonce")
            self._only_resume_once = config.get("onlyresumeonce")
            self._only_pause_upload = config.get("onlypauseupload")
            self._only_pause_download = config.get("onlypausedownload")
            self._only_pause_checking = config.get("onlypausechecking")
            self._download_limit = config.get("download_limit") or 0
            self._upload_limit = config.get("upload_limit") or 0
            self._enable_download_limit = config.get("enable_download_limit") or False
            self._enable_upload_limit = config.get("enable_upload_limit") or False

            self._op_site_ids = config.get("op_site_ids") or []
            self._downloaders = config.get("downloaders")
            # 查询所有站点
            all_sites = [site for site in self._sites.get_indexers() if not site.get("public")] + self.__custom_sites()
            # 过滤掉没有选中的站点
            self._op_sites = [site for site in all_sites if site.get("id") in self._op_site_ids]
            self._exclude_dirs = config.get("exclude_dirs") or ""

        if self._only_pause_once or self._only_resume_once:
            if self._only_pause_once and self._only_resume_once:
                logger.warning("只能选择一个: 立即暂停或立即开始所有任务")
            elif self._only_pause_once:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info(f"立即运行一次暂停所有任务")
                self._scheduler.add_job(
                    self.pause_torrent,
                    "date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                )
            elif self._only_resume_once:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info(f"立即运行一次开始所有任务")
                self._scheduler.add_job(
                    self.resume_torrent,
                    "date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                )

            self._only_resume_once = False
            self._only_pause_once = False
            self.update_config(
                {
                    "onlypauseonce": False,
                    "onlyresumeonce": False,
                    "enabled": self._enabled,
                    "notify": self._notify,
                    "downloaders": self._downloaders,
                    "pause_cron": self._pause_cron,
                    "resume_cron": self._resume_cron,
                    "op_site_ids": self._op_site_ids,
                    "exclude_dirs": self._exclude_dirs,
                    "upload_limit": self._upload_limit,
                    "download_limit": self._download_limit,
                    "enable_upload_limit": self._enable_upload_limit,
                    "enable_download_limit": self._enable_download_limit,
                }
            )

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

        if (
            self._only_pause_upload
            or self._only_pause_download
            or self._only_pause_checking
        ):
            if self._only_pause_upload:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info(f"立即运行一次暂停所有上传任务")
                self._scheduler.add_job(
                    self.pause_torrent,
                    "date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                    kwargs={
                        'type': self.TorrentType.UPLOADING
                    }
                )
            if self._only_pause_download:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info(f"立即运行一次暂停所有下载任务")
                self._scheduler.add_job(
                    self.pause_torrent,
                    "date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                    kwargs={
                        'type': self.TorrentType.DOWNLOADING
                    }
                )
            if self._only_pause_checking:
                self._scheduler = BackgroundScheduler(timezone=settings.TZ)
                logger.info(f"立即运行一次暂停所有检查任务")
                self._scheduler.add_job(
                    self.pause_torrent,
                    "date",
                    run_date=datetime.now(tz=pytz.timezone(settings.TZ))
                    + timedelta(seconds=3),
                    kwargs={
                        'type': self.TorrentType.CHECKING
                    }
                )

            self._only_pause_upload = False
            self._only_pause_download = False
            self._only_pause_checking = False
            self.update_config(
                {
                    "onlypauseupload": False,
                    "onlypausedownload": False,
                    "onlypausechecking": False,
                    "enabled": self._enabled,
                    "notify": self._notify,
                    "downloaders": self._downloaders,
                    "pause_cron": self._pause_cron,
                    "resume_cron": self._resume_cron,
                    "op_site_ids": self._op_site_ids,
                    "exclude_dirs": self._exclude_dirs,
                    "upload_limit": self._upload_limit,
                    "download_limit": self._download_limit,
                    "enable_upload_limit": self._enable_upload_limit,
                    "enable_download_limit": self._enable_download_limit,
                }
            )

            # 启动任务
            if self._scheduler.get_jobs():
                self._scheduler.print_jobs()
                self._scheduler.start()

        # 在初始化时设置限速，添加异常处理
        try:
            self.set_limit(self._upload_limit, self._download_limit)
        except Exception as e:
            logger.error(f"初始化时设置限速失败: {str(e)}")

    @property
    def service_info(self) -> Optional[ServiceInfo]:
        """
        服务信息
        """
        if not self._downloaders:
            logger.warning("尚未配置下载器，请检查配置")
            return None

        services = self.downloader_helper.get_services(name_filters=self._downloaders)

        if not services:
            logger.warning("获取下载器实例失败，请检查配置")
            return None

        active_services = {}
        for service_name, service_info in services.items():
            if service_info.instance.is_inactive():
                logger.warning(f"下载器 {service_name} 未连接，请检查配置")
                continue
            elif not self.check_is_supported_downloader(service_info):
                downloader_type = self.get_downloader_type(service_info)
                logger.warning(f"不支持的下载器类型 {service_name} ({downloader_type})，仅支持qBittorrent和Transmission，请检查配置")
                continue
            else:
                active_services[service_name] = service_info

        if not active_services:
            logger.warning("没有已连接的下载器，请检查配置")
            return None

        return active_services

    def check_is_supported_downloader(self, service_info) -> bool:
        """
        检查下载器类型是否为支持的类型（qbittorrent 或 transmission）
        """
        return (self.downloader_helper.is_downloader(service_type="qbittorrent", service=service_info) or
                self.downloader_helper.is_downloader(service_type="transmission", service=service_info))

    def get_downloader_type(self, service_info) -> str:
        """
        获取下载器类型
        """
        if self.downloader_helper.is_downloader(service_type="qbittorrent", service=service_info):
            return "qbittorrent"
        elif self.downloader_helper.is_downloader(service_type="transmission", service=service_info):
            return "transmission"
        return "unknown"
    def get_state(self) -> bool:
        return self._enabled

    class TorrentType(Enum):
        ALL = 1
        DOWNLOADING = 2
        UPLOADING = 3
        CHECKING = 4

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        """
        定义远程控制命令
        :return: 命令关键字、事件、描述、附带数据
        """
        return [
            {
                "cmd": "/pause_torrents",
                "event": EventType.PluginAction,
                "desc": "暂停下载器所有任务",
                "category": "下载器",
                "data": {"action": "pause_torrents"},
            },
            {
                "cmd": "/pause_upload_torrents",
                "event": EventType.PluginAction,
                "desc": "暂停下载器上传任务",
                "category": "下载器",
                "data": {"action": "pause_upload_torrents"},
            },
            {
                "cmd": "/pause_download_torrents",
                "event": EventType.PluginAction,
                "desc": "暂停下载器下载任务",
                "category": "下载器",
                "data": {"action": "pause_download_torrents"},
            },
            {
                "cmd": "/pause_checking_torrents",
                "event": EventType.PluginAction,
                "desc": "暂停下载器检查任务",
                "category": "下载器",
                "data": {"action": "pause_checking_torrents"},
            },
            {
                "cmd": "/resume_torrents",
                "event": EventType.PluginAction,
                "desc": "开始下载器所有任务",
                "category": "下载器",
                "data": {"action": "resume_torrents"},
            },
            {
                "cmd": "/downloader_status",
                "event": EventType.PluginAction,
                "desc": "下载器当前任务状态",
                "category": "下载器",
                "data": {"action": "downloader_status"},
            },
            {
                "cmd": "/toggle_upload_limit",
                "event": EventType.PluginAction,
                "desc": "下载器切换上传限速状态",
                "category": "下载器",
                "data": {"action": "toggle_upload_limit"},
            },
            {
                "cmd": "/toggle_download_limit",
                "event": EventType.PluginAction,
                "desc": "下载器切换下载限速状态",
                "category": "下载器",
                "data": {"action": "toggle_download_limit"},
            },
        ]

    def __custom_sites(self) -> List[Any]:
        custom_sites = []
        custom_sites_config = self.get_config("CustomSites")
        if custom_sites_config and custom_sites_config.get("enabled"):
            custom_sites = custom_sites_config.get("sites")
        return custom_sites

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_service(self) -> List[Dict[str, Any]]:
        """
        注册插件公共服务
        [{
            "id": "服务ID",
            "name": "服务名称",
            "trigger": "触发器：cron/interval/date/CronTrigger.from_crontab()",
            "func": self.xxx,
            "kwargs": {} # 定时器参数
        }]
        """
        if self._enabled and self._pause_cron and self._resume_cron:
            return [
                {
                    "id": "DownloaderPause",
                    "name": "暂停下载器所有任务",
                    "trigger": CronTrigger.from_crontab(self._pause_cron),
                    "func": self.pause_torrent,
                    "kwargs": {},
                },
                {
                    "id": "DownloaderResume",
                    "name": "开始下载器所有任务",
                    "trigger": CronTrigger.from_crontab(self._resume_cron),
                    "func": self.resume_torrent,
                    "kwargs": {},
                },
            ]
        if self._enabled and self._pause_cron:
            return [
                {
                    "id": "DownloaderPause",
                    "name": "暂停下载器所有任务",
                    "trigger": CronTrigger.from_crontab(self._pause_cron),
                    "func": self.pause_torrent,
                    "kwargs": {},
                }
            ]
        if self._enabled and self._resume_cron:
            return [
                {
                    "id": "DownloaderResume",
                    "name": "开始下载器所有任务",
                    "trigger": CronTrigger.from_crontab(self._resume_cron),
                    "func": self.resume_torrent,
                    "kwargs": {},
                }
            ]
        return []

    def get_all_torrents(self, service):
        downloader_name = service.name
        downloader_obj = service.instance
        downloader_type = self.get_downloader_type(service)

        logger.debug(f"正在获取下载器 {downloader_name} ({downloader_type}) 的种子列表")

        all_torrents, error = downloader_obj.get_torrents()
        if error:
            logger.error(f"获取下载器:{downloader_name}种子失败: {error}")
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"❌ 下载器连接失败",
                    text=f"🎯 下载器: {downloader_name}\n❌ 获取种子列表失败\n🔧 请检查下载器配置和连接状态",
                )
            return []

        if not all_torrents:
            logger.warning(f"下载器:{downloader_name}没有种子")
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"ℹ️ 下载器状态",
                    text=f"🎯 下载器: {downloader_name}\n📭 当前没有种子任务",
                )
            return []

        logger.debug(f"下载器 {downloader_name} 获取到 {len(all_torrents)} 个种子")
        return all_torrents

    @staticmethod
    def get_torrents_status(torrents):
        downloading_torrents = []
        uploading_torrents = []
        paused_torrents = []
        checking_torrents = []
        error_torrents = []

        total_count = len(torrents)
        if total_count == 0:
            return (downloading_torrents, uploading_torrents, paused_torrents, checking_torrents, error_torrents)

        # 对于大量种子，添加进度日志
        if total_count > 1000:
            logger.info(f"🔍 开始分析 {total_count} 个种子的状态...")

        # 检查第一个种子的结构，用于调试
        first_torrent = torrents[0]
        logger.debug(f"第一个种子对象类型: {type(first_torrent)}")

        # 检查种子类型，确定处理方式
        is_transmission = not hasattr(first_torrent, 'state_enum') and hasattr(first_torrent, 'status')
        is_qbittorrent = hasattr(first_torrent, 'state_enum')

        if is_transmission:
            logger.debug(f"检测到Transmission种子，使用status状态映射")
        elif is_qbittorrent:
            logger.debug(f"检测到qBittorrent种子，使用state_enum状态")
        else:
            logger.warning(f"未知种子类型，将尝试自动识别")

        # 对于大量种子，分批处理避免卡住
        batch_size = 1000 if total_count > 5000 else total_count
        logger.debug(f"批处理大小: {batch_size}")

        processed_count = 0

        # 分批处理种子，避免一次性处理太多导致卡住
        for batch_start in range(0, total_count, batch_size):
            batch_end = min(batch_start + batch_size, total_count)
            batch_torrents = torrents[batch_start:batch_end]

            if total_count > 1000:
                logger.info(f"🔄 处理批次 {batch_start//batch_size + 1}: 种子 {batch_start+1}-{batch_end}")

            for i, torrent in enumerate(batch_torrents, start=batch_start):
                # 对于大量种子，每处理1000个输出一次进度
                if total_count > 1000 and i > 0 and i % 1000 == 0:
                    logger.info(f"⏳ 已分析 {i}/{total_count} 个种子状态...")

                try:
                    # 获取种子hash，支持qBittorrent和Transmission
                    torrent_hash = None
                    # 尝试多种方式获取hash
                    if hasattr(torrent, 'get') and callable(torrent.get):
                        torrent_hash = torrent.get("hash")
                    if not torrent_hash and hasattr(torrent, 'hashString'):
                        torrent_hash = torrent.hashString
                    if not torrent_hash and hasattr(torrent, 'hash'):
                        torrent_hash = torrent.hash
                    if not torrent_hash and hasattr(torrent, 'id'):
                        torrent_hash = str(torrent.id)  # 使用ID作为备选

                    if not torrent_hash:
                        if i < 10:  # 只对前10个种子输出详细日志
                            logger.debug(f"种子 {i} 无法获取hash，可用属性: {[attr for attr in dir(torrent) if 'hash' in attr.lower() or 'id' in attr.lower()]}")
                        continue

                    # 获取种子名称用于调试
                    torrent_name = getattr(torrent, 'name', torrent.get('name', f'Unknown_{i}'))

                    # 只在处理前几个种子时输出详细日志
                    if i < 3:
                        logger.debug(f"正在分析种子 {i}: {torrent_name[:50]}...")

                    # 检查种子对象是否有state_enum属性
                    if not hasattr(torrent, 'state_enum'):
                        if i < 3:  # 只对前3个种子输出警告
                            logger.debug(f"种子 {torrent_name} 没有state_enum属性，使用Transmission状态映射")
                        # 对于没有state_enum的种子，尝试多种方式判断状态
                        status_found = False

                        # 尝试获取status属性
                        if hasattr(torrent, 'status'):
                            status = torrent.status
                            status_found = True
                            # 输出前几个种子的详细状态信息用于调试
                            if i < 5:
                                # 获取更多状态相关属性
                                status_attrs = {}
                                for attr in ['status', 'state', 'error', 'errorString', 'isFinished', 'isStalled', 'leftUntilDone', 'rateDownload', 'rateUpload']:
                                    if hasattr(torrent, attr):
                                        status_attrs[attr] = getattr(torrent, attr)
                                logger.debug(f"种子 {i} ({torrent_name[:30]}) 状态属性: {status_attrs}")

                            # 首先检查是否有错误 - 优先级最高
                            has_error = False
                            error_code = getattr(torrent, 'error', 0)
                            error_string = getattr(torrent, 'errorString', '')

                            # 检查错误状态
                            if error_code and error_code != 0:
                                has_error = True
                                if i < 10:  # 对前10个错误种子输出详细信息
                                    logger.debug(f"种子 {torrent_name} 有错误: code={error_code}, string='{error_string}'")
                            elif error_string and error_string.strip():
                                # 即使error code为0，但有错误字符串也认为是错误
                                has_error = True
                                if i < 10:
                                    logger.debug(f"种子 {torrent_name} 有错误字符串: '{error_string}'")

                            if has_error:
                                error_torrents.append(torrent_hash)
                            else:
                                # 没有错误时，根据状态进行分类
                                # Transmission状态映射 - 处理枚举类型和数值类型
                                status_value = status
                                status_str = str(status).lower()

                                # 如果是枚举对象，尝试获取其值
                                if hasattr(status, 'value'):
                                    status_value = status.value
                                elif hasattr(status, 'name'):
                                    status_str = status.name.lower()

                                # 根据字符串状态进行映射
                                if 'stop' in status_str or status_value == 0:
                                    paused_torrents.append(torrent_hash)
                                elif 'check' in status_str or status_value in [1, 2]:
                                    checking_torrents.append(torrent_hash)
                                elif 'download' in status_str or status_value in [3, 4]:
                                    downloading_torrents.append(torrent_hash)
                                elif 'seed' in status_str or status_value in [5, 6]:
                                    uploading_torrents.append(torrent_hash)
                                else:
                                    if i < 10:  # 对前10个未知状态的种子输出详细信息
                                        logger.warning(f"种子 {torrent_name} 未知状态值: {status} (str: {status_str}, value: {status_value})")
                                    error_torrents.append(torrent_hash)

                        # 如果没有status属性，尝试其他方式
                        if not status_found:
                            if i < 10:  # 只对前10个种子输出警告
                                available_attrs = [attr for attr in dir(torrent) if not attr.startswith('_')]
                                logger.warning(f"种子 {torrent_name} 无法获取status属性，可用属性: {available_attrs}")
                            error_torrents.append(torrent_hash)
                        processed_count += 1
                        continue

                    # 使用state_enum检查状态
                    if torrent.state_enum.is_paused:
                        paused_torrents.append(torrent_hash)
                    elif torrent.state_enum.is_errored:
                        error_torrents.append(torrent_hash)
                    elif torrent.state_enum.is_checking:
                        checking_torrents.append(torrent_hash)
                    elif torrent.state_enum.is_downloading:
                        downloading_torrents.append(torrent_hash)
                    elif torrent.state_enum.is_uploading:
                        uploading_torrents.append(torrent_hash)
                    else:
                        if i < 10:  # 只对前10个种子输出调试信息
                            logger.debug(f"种子 {torrent_name} 状态未知，归类为错误")
                        error_torrents.append(torrent_hash)

                    processed_count += 1

                except Exception as e:
                    logger.error(f"分析种子 {i} 状态时发生异常: {str(e)}")
                    if i < 5:  # 只对前5个种子输出详细错误信息
                        logger.debug(f"种子对象类型: {type(torrent)}")
                        logger.debug(f"种子对象属性: {[attr for attr in dir(torrent) if not attr.startswith('_')]}")
                    # 发生异常时，尝试获取种子hash并归类为错误
                    try:
                        torrent_hash = torrent.get("hash") or getattr(torrent, 'hashString', None)
                        if torrent_hash:
                            error_torrents.append(torrent_hash)
                            processed_count += 1
                    except:
                        if i < 10:  # 只对前10个种子输出错误
                            logger.error(f"无法获取种子 {i} 的hash")

        logger.info(f"📊 实际处理了 {processed_count}/{total_count} 个种子")

        if total_count > 1000:
            logger.info(f"✅ 种子状态分析完成: ⬇️下载{len(downloading_torrents)}, ⬆️上传{len(uploading_torrents)}, ⏸️暂停{len(paused_torrents)}, 🔄检查{len(checking_torrents)}, ❌错误{len(error_torrents)}")

        return (
            downloading_torrents,
            uploading_torrents,
            paused_torrents,
            checking_torrents,
            error_torrents,
        )

    @eventmanager.register(EventType.PluginAction)
    def handle_pause_torrent(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "pause_torrents":
                return
        self.pause_torrent()

    @eventmanager.register(EventType.PluginAction)
    def handle_pause_upload_torrent(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "pause_upload_torrents":
                return
        self.pause_torrent(self.TorrentType.UPLOADING)

    @eventmanager.register(EventType.PluginAction)
    def handle_pause_download_torrent(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "pause_download_torrents":
                return
        self.pause_torrent(self.TorrentType.DOWNLOADING)

    @eventmanager.register(EventType.PluginAction)
    def handle_pause_checking_torrent(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "pause_checking_torrents":
                return
        self.pause_torrent(self.TorrentType.CHECKING)

    def pause_torrent(self, type: TorrentType = TorrentType.ALL):
        if not self._enabled:
            return

        service_info = self.service_info
        if not service_info:
            logger.error("没有可用的下载器服务")
            return

        logger.info(f"⏸️ 开始暂停操作，共有 {len(service_info)} 个下载器服务: {list(service_info.keys())}")

        for service in service_info.values():
            downloader_name = service.name
            downloader_obj = service.instance
            if not downloader_obj:
                logger.error(f"获取下载器失败 {downloader_name}")
                continue
            all_torrents = self.get_all_torrents(service)
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(all_torrents)
            )

            logger.info(
                f"⏸️ 下载器{downloader_name}暂停任务启动 \n"
                f"📊 种子总数:  {len(all_torrents)} \n"
                f"⬆️ 做种数量:  {len(hash_uploading)}\n"
                f"⬇️ 下载数量:  {len(hash_downloading)}\n"
                f"🔄 检查数量:  {len(hash_checking)}\n"
                f"⏸️ 暂停数量:  {len(hash_paused)}\n"
                f"❌ 错误数量:  {len(hash_error)}\n"
                f"⏳ 暂停操作中请稍等...\n",
            )
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"⏸️ 下载器暂停任务启动",
                    text=f"🎯 下载器: {downloader_name}\n"
                    f"📊 种子总数: {len(all_torrents)}\n"
                    f"⬆️ 做种: {len(hash_uploading)} | ⬇️ 下载: {len(hash_downloading)}\n"
                    f"🔄 检查: {len(hash_checking)} | ⏸️ 暂停: {len(hash_paused)}\n"
                    f"❌ 错误: {len(hash_error)}\n"
                    f"⏳ 正在执行暂停操作...",
                )
            logger.info(f"🔍 开始过滤下载器 {downloader_name} 的种子...")

            # 对于大量种子，添加处理限制
            if len(all_torrents) > 5000:
                logger.warning(f"⚠️ 下载器 {downloader_name} 种子数量过多 ({len(all_torrents)} 个)，为避免处理超时，将限制处理数量")
                # 只处理前5000个种子
                all_torrents = all_torrents[:5000]
                logger.info(f"📊 已限制处理种子数量为 {len(all_torrents)} 个")

            pause_torrents = self.filter_pause_torrents(all_torrents)
            logger.info(f"✅ 过滤后剩余 {len(pause_torrents)} 个种子需要处理")

            logger.info(f"🔍 开始分析下载器 {downloader_name} 的种子状态...")
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(pause_torrents)
            )
            logger.info(f"✅ 种子状态分析完成")
            if type == self.TorrentType.DOWNLOADING:
                to_be_paused = hash_downloading
            elif type == self.TorrentType.UPLOADING:
                to_be_paused = hash_uploading
            elif type == self.TorrentType.CHECKING:
                to_be_paused = hash_checking
            else:
                to_be_paused = hash_downloading + hash_uploading + hash_checking

            if len(to_be_paused) > 0:
                logger.info(f"⏸️ 准备暂停下载器 {downloader_name} ({self.get_downloader_type(service)}) 的 {len(to_be_paused)} 个种子")
                if downloader_obj.stop_torrents(ids=to_be_paused):
                    logger.info(f"✅ 成功暂停下载器 {downloader_name} 的 {len(to_be_paused)} 个种子")
                else:
                    logger.error(f"❌ 下载器{downloader_name}暂停种子失败")
                    if self._notify:
                        self.post_message(
                            mtype=NotificationType.SiteMessage,
                            title=f"❌ 下载器操作失败",
                            text=f"🎯 下载器: {downloader_name}\n❌ 暂停种子操作失败\n🔧 请检查下载器连接状态",
                        )
            else:
                logger.info(f"ℹ️ 下载器 {downloader_name} ({self.get_downloader_type(service)}) 没有需要暂停的种子")
            # 每个种子等待1ms以让状态切换成功,至少等待1S
            wait_time = 0.001 * len(to_be_paused) + 1
            time.sleep(wait_time)

            all_torrents = self.get_all_torrents(service)
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(all_torrents)
            )
            logger.info(
                f"下载器{downloader_name}暂定任务完成 \n"
                f"种子总数:  {len(all_torrents)} \n"
                f"做种数量:  {len(hash_uploading)}\n"
                f"下载数量:  {len(hash_downloading)}\n"
                f"检查数量:  {len(hash_checking)}\n"
                f"暂停数量:  {len(hash_paused)}\n"
                f"错误数量:  {len(hash_error)}\n"
            )
            if self._notify:
                # 计算暂停的种子数量
                paused_count = len(to_be_paused) if len(to_be_paused) > 0 else 0
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"✅ 下载器暂停任务完成",
                    text=f"🎯 下载器: {downloader_name}\n"
                    f"⏸️ 已暂停: {paused_count} 个种子\n"
                    f"📊 当前状态:\n"
                    f"  ⬆️ 做种: {len(hash_uploading)} | ⬇️ 下载: {len(hash_downloading)}\n"
                    f"  🔄 检查: {len(hash_checking)} | ⏸️ 暂停: {len(hash_paused)}\n"
                    f"  ❌ 错误: {len(hash_error)}",
                )

    def __is_excluded(self, file_path) -> bool:
        """
        是否排除目录
        """
        for exclude_dir in self._exclude_dirs.split("\n"):
            if exclude_dir and exclude_dir in str(file_path):
                return True
        return False
    def filter_pause_torrents(self, all_torrents):
        torrents = []
        total_count = len(all_torrents)
        excluded_count = 0

        # 对于大量种子，添加进度日志
        if total_count > 1000:
            logger.info(f"处理大量种子 ({total_count} 个)，正在过滤排除目录...")

        for i, torrent in enumerate(all_torrents):
            # 对于大量种子，每处理1000个输出一次进度
            if total_count > 1000 and i > 0 and i % 1000 == 0:
                logger.info(f"已处理 {i}/{total_count} 个种子...")

            # 获取种子路径，支持qBittorrent和Transmission
            content_path = (torrent.get("content_path") or
                          getattr(torrent, 'download_dir', None) or
                          getattr(torrent, 'downloadDir', None))
            if self.__is_excluded(content_path):
                excluded_count += 1
                continue
            torrents.append(torrent)

        if excluded_count > 0:
            logger.info(f"排除了 {excluded_count} 个种子，剩余 {len(torrents)} 个种子")

        return torrents

    @eventmanager.register(EventType.PluginAction)
    def handle_resume_torrent(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "resume_torrents":
                return
        self.resume_torrent()

    def resume_torrent(self):
        if not self._enabled:
            return

        service_info = self.service_info
        if not service_info:
            logger.error("没有可用的下载器服务")
            return

        logger.info(f"▶️ 开始恢复操作，共有 {len(service_info)} 个下载器服务: {list(service_info.keys())}")

        for service in service_info.values():
            downloader_name = service.name
            downloader_obj = service.instance
            if not downloader_obj:
                logger.error(f"获取下载器失败 {downloader_name}")
                continue
            all_torrents = self.get_all_torrents(service)
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(all_torrents)
            )
            logger.info(
                f"下载器{downloader_name}开始任务启动 \n"
                f"种子总数:  {len(all_torrents)} \n"
                f"做种数量:  {len(hash_uploading)}\n"
                f"下载数量:  {len(hash_downloading)}\n"
                f"检查数量:  {len(hash_checking)}\n"
                f"暂停数量:  {len(hash_paused)}\n"
                f"错误数量:  {len(hash_error)}\n"
                f"开始操作中请稍等...\n",
            )
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"▶️ 下载器恢复任务启动",
                    text=f"🎯 下载器: {downloader_name}\n"
                    f"📊 种子总数: {len(all_torrents)}\n"
                    f"⬆️ 做种: {len(hash_uploading)} | ⬇️ 下载: {len(hash_downloading)}\n"
                    f"🔄 检查: {len(hash_checking)} | ⏸️ 暂停: {len(hash_paused)}\n"
                    f"❌ 错误: {len(hash_error)}\n"
                    f"⏳ 正在恢复暂停的种子...",
                )

            resume_torrents = self.filter_resume_torrents(all_torrents)
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(resume_torrents)
            )
            if not downloader_obj.start_torrents(ids=hash_paused):
                logger.error(f"下载器{downloader_name}开始种子失败")
                if self._notify:
                    self.post_message(
                        mtype=NotificationType.SiteMessage,
                        title=f"❌ 下载器操作失败",
                        text=f"🎯 下载器: {downloader_name}\n❌ 恢复种子操作失败\n🔧 请检查下载器连接状态",
                    )
            # 每个种子等待1ms以让状态切换成功,至少等待1S
            wait_time = 0.001 * len(hash_paused) + 1
            time.sleep(wait_time)

            all_torrents = self.get_all_torrents(service)
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(all_torrents)
            )
            logger.info(
                f"下载器{downloader_name}开始任务完成 \n"
                f"种子总数:  {len(all_torrents)} \n"
                f"做种数量:  {len(hash_uploading)}\n"
                f"下载数量:  {len(hash_downloading)}\n"
                f"检查数量:  {len(hash_checking)}\n"
                f"暂停数量:  {len(hash_paused)}\n"
                f"错误数量:  {len(hash_error)}\n"
            )
            if self._notify:
                # 计算恢复的种子数量
                resumed_count = len(hash_paused) if len(hash_paused) > 0 else 0
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"✅ 下载器恢复任务完成",
                    text=f"🎯 下载器: {downloader_name}\n"
                    f"▶️ 已恢复: {resumed_count} 个种子\n"
                    f"📊 当前状态:\n"
                    f"  ⬆️ 做种: {len(hash_uploading)} | ⬇️ 下载: {len(hash_downloading)}\n"
                    f"  🔄 检查: {len(hash_checking)} | ⏸️ 暂停: {len(hash_paused)}\n"
                    f"  ❌ 错误: {len(hash_error)}",
                )

    def filter_resume_torrents(self, all_torrents):
        """
        过滤掉不参与保种的种子
        """
        if len(self._op_sites) == 0:
            return all_torrents

        urls = [site.get("url") for site in self._op_sites]
        op_sites_main_domains = []
        for url in urls:
            domain = StringUtils.get_url_netloc(url)
            main_domain = self.get_main_domain(domain[1])
            op_sites_main_domains.append(main_domain)

        torrents = []
        for torrent in all_torrents:
            # 检查是否为暂停的上传状态种子
            is_paused_upload = False

            # qBittorrent状态检查
            if torrent.get("state") in ["pausedUP", "stoppedUP"]:
                is_paused_upload = True
            # Transmission状态检查
            elif hasattr(torrent, 'status') and torrent.status == "stopped":
                is_paused_upload = True

            if is_paused_upload:
                tracker_url = self.get_torrent_tracker(torrent)
                if not tracker_url:
                    torrent_name = getattr(torrent, 'name', torrent.get('name', 'Unknown'))
                    logger.info(f"获取种子 {torrent_name} Tracker失败，不过滤该种子")
                    torrents.append(torrent)
                    continue

                _, tracker_domain = StringUtils.get_url_netloc(tracker_url)
                if not tracker_domain:
                    torrent_name = getattr(torrent, 'name', torrent.get('name', 'Unknown'))
                    logger.info(f"获取种子 {torrent_name} Tracker失败，不过滤该种子")
                    torrents.append(torrent)
                    continue

                tracker_main_domain = self.get_main_domain(domain=tracker_domain)
                if tracker_main_domain in op_sites_main_domains:
                    torrent_name = getattr(torrent, 'name', torrent.get('name', 'Unknown'))
                    logger.info(
                        f"种子 {torrent_name} 属于站点{tracker_main_domain}，不执行操作"
                    )
                    continue

            torrents.append(torrent)
        return torrents

    @eventmanager.register(EventType.PluginAction)
    def handle_downloader_status(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "downloader_status":
                return
        self.downloader_status()

    def downloader_status(self):
        if not self._enabled:
            return
        for service in self.service_info.values():
            downloader_name = service.name
            downloader_obj = service.instance
            if not downloader_obj:
                logger.error(f"获取下载器失败 {downloader_name}")
                continue
            all_torrents = self.get_all_torrents(service)
            hash_downloading, hash_uploading, hash_paused, hash_checking, hash_error = (
                self.get_torrents_status(all_torrents)
            )
            logger.info(
                f"下载器{downloader_name}任务状态 \n"
                f"种子总数:  {len(all_torrents)} \n"
                f"做种数量:  {len(hash_uploading)}\n"
                f"下载数量:  {len(hash_downloading)}\n"
                f"检查数量:  {len(hash_checking)}\n"
                f"暂停数量:  {len(hash_paused)}\n"
                f"错误数量:  {len(hash_error)}\n"
            )
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"📊 下载器状态报告",
                    text=f"🎯 下载器: {downloader_name}\n"
                    f"📊 种子总数: {len(all_torrents)}\n\n"
                    f"📈 运行状态:\n"
                    f"  ⬆️ 做种中: {len(hash_uploading)}\n"
                    f"  ⬇️ 下载中: {len(hash_downloading)}\n"
                    f"  🔄 检查中: {len(hash_checking)}\n\n"
                    f"⏸️ 暂停: {len(hash_paused)}\n"
                    f"❌ 错误: {len(hash_error)}",
                )

    @eventmanager.register(EventType.PluginAction)
    def handle_toggle_upload_limit(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "toggle_upload_limit":
                return
        self.set_limit(self._upload_limit, self._download_limit)

    @eventmanager.register(EventType.PluginAction)
    def handle_toggle_download_limit(self, event: Event):
        if not self._enabled:
            return
        if event:
            event_data = event.event_data
            if not event_data or event_data.get("action") != "toggle_download_limit":
                return
        self.set_limit(self._upload_limit, self._download_limit)

    def set_both_limit(self, upload_limit, download_limit):
        if not self._enable_upload_limit or not self._enable_download_limit:
            return True

        # 确保参数是字符串类型
        upload_limit = str(upload_limit) if upload_limit is not None else "0"
        download_limit = str(download_limit) if download_limit is not None else "0"

        if (
            not upload_limit.isdigit()
            or not download_limit.isdigit()
        ):
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=f"❌ 限速设置参数错误",
                text=f"❌ 限速值必须为数字\n🔧 请检查上传/下载限速参数",
            )
            return False

        flag = True
        for service in self.service_info.values():
            downloader_name = service.name
            downloader_obj = service.instance
            downloader_type = self.get_downloader_type(service)
            if not downloader_obj:
                logger.error(f"获取下载器失败 {downloader_name}")
                continue

            # 根据下载器类型调用相应的限速方法
            if downloader_type == "qbittorrent":
                # qBittorrent需要转换单位
                flag = flag and downloader_obj.set_speed_limit(
                    download_limit=int(download_limit), upload_limit=int(upload_limit)
                )
            elif downloader_type == "transmission":
                # Transmission直接使用KB/s，0表示无限制
                dl_limit = int(download_limit)
                ul_limit = int(upload_limit)
                logger.debug(f"设置Transmission限速: 下载={dl_limit} KB/s, 上传={ul_limit} KB/s")
                flag = flag and downloader_obj.set_speed_limit(
                    download_limit=dl_limit, upload_limit=ul_limit
                )
            else:
                logger.warning(f"不支持的下载器类型: {downloader_type}")
                flag = False
        return flag

    def set_upload_limit(self, upload_limit):
        if not self._enable_upload_limit:
            return True

        # 确保参数是字符串类型
        upload_limit = str(upload_limit) if upload_limit is not None else "0"

        if not upload_limit.isdigit():
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=f"❌ 上传限速参数错误",
                text=f"❌ 上传限速值必须为数字\n🔧 请检查上传限速参数",
            )
            return False
        flag = True
        for service in self.service_info.values():
            downloader_name = service.name
            downloader_obj = service.instance
            downloader_type = self.get_downloader_type(service)
            if not downloader_obj:
                logger.error(f"获取下载器失败 {downloader_name}")
                continue

            # 获取当前下载限速
            speed_limit_result = downloader_obj.get_speed_limit()
            if speed_limit_result:
                download_limit_current_val, _ = speed_limit_result
                # 确保值不为None
                download_limit_current_val = download_limit_current_val if download_limit_current_val is not None else 0
            else:
                download_limit_current_val = 0

            # 根据下载器类型设置限速
            if downloader_type == "qbittorrent":
                flag = flag and downloader_obj.set_speed_limit(
                    download_limit=int(download_limit_current_val),
                    upload_limit=int(upload_limit),
                )
            elif downloader_type == "transmission":
                # Transmission直接使用KB/s，0表示无限制
                dl_limit = int(download_limit_current_val)
                ul_limit = int(upload_limit)
                flag = flag and downloader_obj.set_speed_limit(
                    download_limit=dl_limit,
                    upload_limit=ul_limit,
                )
            else:
                logger.warning(f"不支持的下载器类型: {downloader_type}")
                flag = False
        return flag

    def set_download_limit(self, download_limit):
        if not self._enable_download_limit:
            return True

        # 确保参数是字符串类型
        download_limit = str(download_limit) if download_limit is not None else "0"

        if not download_limit.isdigit():
            self.post_message(
                mtype=NotificationType.SiteMessage,
                title=f"❌ 下载限速参数错误",
                text=f"❌ 下载限速值必须为数字\n🔧 请检查下载限速参数",
            )
            return False

        flag = True
        for service in self.service_info.values():
            downloader_name = service.name
            downloader_obj = service.instance
            downloader_type = self.get_downloader_type(service)
            if not downloader_obj:
                logger.error(f"获取下载器失败 {downloader_name}")
                continue

            # 获取当前上传限速
            speed_limit_result = downloader_obj.get_speed_limit()
            if speed_limit_result:
                _, upload_limit_current_val = speed_limit_result
                # 确保值不为None
                upload_limit_current_val = upload_limit_current_val if upload_limit_current_val is not None else 0
            else:
                upload_limit_current_val = 0

            # 根据下载器类型设置限速
            if downloader_type == "qbittorrent":
                flag = flag and downloader_obj.set_speed_limit(
                    download_limit=int(download_limit),
                    upload_limit=int(upload_limit_current_val),
                )
            elif downloader_type == "transmission":
                # Transmission直接使用KB/s，0表示无限制
                dl_limit = int(download_limit)
                ul_limit = int(upload_limit_current_val)
                flag = flag and downloader_obj.set_speed_limit(
                    download_limit=dl_limit,
                    upload_limit=ul_limit,
                )
            else:
                logger.warning(f"不支持的下载器类型: {downloader_type}")
                flag = False
        return flag

    def set_limit(self, upload_limit, download_limit):
        # 限速，满足以下三种情况设置限速
        # 1. 插件启用 && download_limit启用
        # 2. 插件启用 && upload_limit启用
        # 3. 插件启用 && download_limit启用 && upload_limit启用

        # 确保参数不为None
        upload_limit = upload_limit if upload_limit is not None else 0
        download_limit = download_limit if download_limit is not None else 0

        flag = None
        if self._enabled and self._enable_download_limit and self._enable_upload_limit:
            flag = self.set_both_limit(upload_limit, download_limit)

        elif flag is None and self._enabled and self._enable_download_limit:
            flag = self.set_download_limit(download_limit)

        elif flag is None and self._enabled and self._enable_upload_limit:
            flag = self.set_upload_limit(upload_limit)

        if flag == True:
            logger.info(f"设置下载器限速成功")
            if self._notify:
                upload_text = "🚀 无限制" if upload_limit == 0 else f"🚀 {upload_limit} KB/s"
                download_text = "📥 无限制" if download_limit == 0 else f"📥 {download_limit} KB/s"

                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"⚡ 下载器限速设置成功",
                    text=f"🎯 已应用到所有下载器\n\n"
                    f"📊 限速配置:\n"
                    f"  ⬆️ 上传: {upload_text}\n"
                    f"  ⬇️ 下载: {download_text}",
                )
        elif flag == False:
            logger.error(f"下载器设置限速失败")
            if self._notify:
                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title=f"❌ 下载器限速设置失败",
                    text=f"❌ 设置下载器限速失败\n🔧 请检查下载器连接状态",
                )

    def get_torrent_tracker(self, torrent):
        """
        解析种子tracker，支持qBittorrent和Transmission
        :return: tracker url
        """
        if not torrent:
            return None

        # qBittorrent方式
        tracker = torrent.get("tracker")
        if tracker and len(tracker) > 0:
            return tracker

        # Transmission方式 - 检查trackers属性
        if hasattr(torrent, 'trackers') and torrent.trackers:
            for tracker_info in torrent.trackers:
                if hasattr(tracker_info, 'announce') and tracker_info.announce:
                    return tracker_info.announce
                elif isinstance(tracker_info, dict) and tracker_info.get('announce'):
                    return tracker_info.get('announce')

        # 从magnet链接解析
        magnet_uri = torrent.get("magnet_uri") or getattr(torrent, 'magnetLink', None)
        if not magnet_uri or len(magnet_uri) <= 0:
            return None
        magnet_uri_obj = urlparse(magnet_uri)
        query = urllib.parse.parse_qs(magnet_uri_obj.query)
        tr = query.get("tr")
        if not tr or len(tr) <= 0:
            return None
        return tr[0]

    def get_main_domain(self, domain):
        """
        获取域名的主域名
        :param domain: 原域名
        :return: 主域名
        """
        if not domain:
            return None
        domain_arr = domain.split(".")
        domain_len = len(domain_arr)
        if domain_len < 2:
            return None
        root_domain, root_domain_len = self.match_multi_level_root_domain(domain=domain)
        if root_domain:
            return f"{domain_arr[-root_domain_len - 1]}.{root_domain}"
        else:
            return f"{domain_arr[-2]}.{domain_arr[-1]}"

    def match_multi_level_root_domain(self, domain):
        """
        匹配多级根域名
        :param domain: 被匹配的域名
        :return: 匹配的根域名, 匹配的根域名长度
        """
        if not domain or not self._multi_level_root_domain:
            return None, 0
        for root_domain in self._multi_level_root_domain:
            if domain.endswith("." + root_domain):
                root_domain_len = len(root_domain.split("."))
                return root_domain, root_domain_len
        return None, 0

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        customSites = self.__custom_sites()

        site_options = [
            {"title": site.name, "value": site.id}
            for site in self._siteoper.list_order_by_pri()
        ] + [
            {"title": site.get("name"), "value": site.get("id")} for site in customSites
        ]
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "notify",
                                            "label": "发送通知",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlypauseonce",
                                            "label": "立即暂停所有任务",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlyresumeonce",
                                            "label": "立即开始所有任务",
                                        },
                                    }
                                ],
                            },
                        ],
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
                                        'component': 'VSelect',
                                        'props': {
                                            'multiple': True,
                                            'chips': True,
                                            'clearable': True,
                                            'model': 'downloaders',
                                            'label': '下载器',
                                            'items': [{"title": config.name, "value": config.name}
                                                      for config in self.downloader_helper.get_configs().values()]
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "pause_cron",
                                            "label": "暂停周期",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "resume_cron",
                                            "label": "开始周期",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enable_upload_limit",
                                            "label": "上传限速",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enable_download_limit",
                                            "label": "下载限速",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "upload_limit",
                                            "label": "上传限速 KB/s",
                                            "placeholder": "KB/s",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 6},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "download_limit",
                                            "label": "下载限速 KB/s",
                                            "placeholder": "KB/s",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlypauseupload",
                                            "label": "暂停上传任务",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlypausedownload",
                                            "label": "暂停下载任务",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "onlypausechecking",
                                            "label": "暂停检查任务",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "chips": True,
                                            "multiple": True,
                                            "model": "op_site_ids",
                                            "label": "停止保种站点(暂停保种后不会被恢复)",
                                            "items": site_options,
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "exclude_dirs",
                                            "label": "不暂停保种目录",
                                            "rows": 5,
                                            "placeholder": "该目录下的做种不会暂停，一行一个目录",
                                        },
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {
                                    "cols": 12,
                                },
                                "content": [
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "info",
                                            "variant": "tonal",
                                            "text": "开始周期和暂停周期使用Cron表达式，如：0 0 0 * *，仅针对开始/暂定全部任务",
                                        },
                                    }
                                ],
                            },
                            {
                                "component": "VCol",
                                "props": {
                                    "cols": 12,
                                },
                                "content": [
                                    {
                                        "component": "VAlert",
                                        "props": {
                                            "type": "info",
                                            "variant": "tonal",
                                            "text": "交互命令有暂停下载器种子、开始下载器种子、下载器切换上传限速状态、下载器切换下载限速状态",
                                        },
                                    }
                                ],
                            },
                        ],
                    },
                ],
            }
        ], {
            "enabled": False,
            "notify": True,
            "onlypauseonce": False,
            "onlyresumeonce": False,
            "onlypauseupload": False,
            "onlypausedownload": False,
            "onlypausechecking": False,
            "upload_limit": 0,
            "download_limit": 0,
            "enable_upload_limit": False,
            "enable_download_limit": False,
            "op_site_ids": [],
        }

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        try:
            if self._scheduler:
                self._scheduler.remove_all_jobs()
                if self._scheduler.running:
                    self._scheduler.shutdown()
                self._scheduler = None
        except Exception as e:
            logger.error("退出插件失败：%s" % str(e))
