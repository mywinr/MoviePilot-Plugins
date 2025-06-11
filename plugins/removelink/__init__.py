import os
import threading
import time
import traceback
from pathlib import Path
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from datetime import datetime

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from app.db.transferhistory_oper import TransferHistoryOper
from app.log import logger
from app.plugins import _PluginBase
from app.schemas import NotificationType
from app.core.event import eventmanager
from app.schemas.types import EventType

state_lock = threading.Lock()
deletion_queue_lock = threading.Lock()


@dataclass
class DeletionTask:
    """延迟删除任务"""
    file_path: Path
    deleted_inode: int
    timestamp: datetime
    processed: bool = False


class FileMonitorHandler(FileSystemEventHandler):
    """
    目录监控处理
    """

    def __init__(self, monpath: str, sync: Any, **kwargs):
        super(FileMonitorHandler, self).__init__(**kwargs)
        self._watch_path = monpath
        self.sync = sync

    def on_created(self, event):
        if event.is_directory:
            return
        file_path = Path(event.src_path)
        if file_path.suffix in [".!qB", ".part", ".mp"]:
            return
        logger.info(f"监测到新增文件：{file_path}")
        if self.sync.exclude_keywords:
            for keyword in self.sync.exclude_keywords.split("\n"):
                if keyword and keyword in str(file_path):
                    logger.info(f"{file_path} 命中过滤关键字 {keyword}，不处理")
                    return
        # 新增文件记录
        with state_lock:
            try:
                self.sync.state_set[str(file_path)] = file_path.stat().st_ino
            except Exception as e:
                logger.error(f"新增文件记录失败：{str(e)}")

    def on_moved(self, event):
        if event.is_directory:
            return
        file_path = Path(event.dest_path)
        if file_path.suffix in [".!qB", ".part", ".mp"]:
            return
        logger.info(f"监测到新增文件：{file_path}")
        if self.sync.exclude_keywords:
            for keyword in self.sync.exclude_keywords.split("\n"):
                if keyword and keyword in str(file_path):
                    logger.info(f"{file_path} 命中过滤关键字 {keyword}，不处理")
                    return
        # 新增文件记录
        with state_lock:
            self.sync.state_set[str(file_path)] = file_path.stat().st_ino

    def on_deleted(self, event):
        file_path = Path(event.src_path)
        if event.is_directory:
            # 单独处理文件夹删除触发删除种子
            if self.sync._delete_torrents:
                # 发送事件
                logger.info(f"监测到删除文件夹：{file_path}")
                eventmanager.send_event(
                    EventType.DownloadFileDeleted, {"src": str(file_path)}
                )
            return
        if file_path.suffix in [".!qB", ".part", ".mp"]:
            return
        logger.info(f"监测到删除文件：{file_path}")
        # 命中过滤关键字不处理
        if self.sync.exclude_keywords:
            for keyword in self.sync.exclude_keywords.split("\n"):
                if keyword and keyword in str(file_path):
                    logger.info(f"{file_path} 命中过滤关键字 {keyword}，不处理")
                    return
        # 删除硬链接文件
        self.sync.handle_deleted(file_path)


def updateState(monitor_dirs: List[str]):
    """
    更新监控目录的文件列表
    """
    # 记录开始时间
    start_time = time.time()
    state_set = {}
    for mon_path in monitor_dirs:
        for root, _, files in os.walk(mon_path):
            for file in files:
                file = Path(root) / file
                if not file.exists():
                    continue
                # 记录文件inode
                state_set[str(file)] = file.stat().st_ino
    # 记录结束时间
    end_time = time.time()
    # 计算耗时
    elapsed_time = end_time - start_time
    logger.info(f"更新文件列表完成，共计{len(state_set)}个文件，耗时：{elapsed_time}秒")

    return state_set


class RemoveLink(_PluginBase):
    # 插件名称
    plugin_name = "清理硬链接"
    # 插件描述
    plugin_desc = "监控目录内文件被删除时，同步删除监控目录内所有和它硬链接的文件"
    # 插件图标
    plugin_icon = "Ombi_A.png"
    # 插件版本
    plugin_version = "2.3"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "linkdeleted_"
    # 加载顺序
    plugin_order = 0
    # 可使用的用户级别
    auth_level = 1

    # preivate property
    monitor_dirs = ""
    exclude_dirs = ""
    exclude_keywords = ""
    _enabled = False
    _notify = False
    _delete_scrap_infos = False
    _delete_torrents = False
    _delete_history = False
    _delayed_deletion = True
    _delay_seconds = 30
    _transferhistory = None
    _observer = []
    # 监控目录的文件列表
    state_set: Dict[str, int] = {}
    # 延迟删除队列
    deletion_queue: List[DeletionTask] = []
    # 延迟删除定时器
    _deletion_timer = None

    def init_plugin(self, config: dict = None):
        logger.info(f"初始化硬链接清理插件")
        self._transferhistory = TransferHistoryOper()
        if config:
            self._enabled = config.get("enabled")
            self._notify = config.get("notify")
            self.monitor_dirs = config.get("monitor_dirs")
            self.exclude_dirs = config.get("exclude_dirs") or ""
            self.exclude_keywords = config.get("exclude_keywords") or ""
            self._delete_scrap_infos = config.get("delete_scrap_infos")
            self._delete_torrents = config.get("delete_torrents")
            self._delete_history = config.get("delete_history")
            self._delayed_deletion = config.get("delayed_deletion", True)
            # 验证延迟时间范围
            delay_seconds = config.get("delay_seconds", 30)
            self._delay_seconds = max(10, min(300, int(delay_seconds))) if delay_seconds else 30

        # 停止现有任务
        self.stop_service()

        # 初始化延迟删除队列
        self.deletion_queue = []

        if self._enabled:
            # 记录延迟删除配置状态
            if self._delayed_deletion:
                logger.info(f"延迟删除功能已启用，延迟时间: {self._delay_seconds} 秒")
            else:
                logger.info("延迟删除功能已禁用，将使用立即删除模式")
            # 读取目录配置
            monitor_dirs = self.monitor_dirs.split("\n")
            logger.info(f"监控目录：{monitor_dirs}")
            if not monitor_dirs:
                return
            for mon_path in monitor_dirs:
                # 格式源目录:目的目录
                if not mon_path:
                    continue
                try:
                    observer = Observer(timeout=10)
                    self._observer.append(observer)
                    observer.schedule(
                        FileMonitorHandler(mon_path, self), mon_path, recursive=True
                    )
                    observer.daemon = True
                    observer.start()
                    logger.info(f"{mon_path} 的目录监控服务启动")
                except Exception as e:
                    err_msg = str(e)
                    logger.error(f"{mon_path} 启动目录监控失败：{err_msg}")
                    self.systemmessage.put(f"{mon_path} 启动目录监控失败：{err_msg}", title="清理硬链接")

            # 更新监控集合 - 在所有线程停止后安全获取锁
            with state_lock:
                self.state_set = updateState(monitor_dirs)
                logger.debug("监控集合更新完成")

    def __update_config(self):
        """
        更新配置
        """
        self.update_config(
            {
                "enabled": self._enabled,
                "notify": self._notify,
                "monitor_dirs": self.monitor_dirs,
                "exclude_keywords": self.exclude_keywords,
                "delayed_deletion": self._delayed_deletion,
                "delay_seconds": self._delay_seconds,
            }
        )

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        pass

    def get_api(self) -> List[Dict[str, Any]]:
        pass

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VForm",
                "content": [
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
                                            "model": "enabled",
                                            "label": "启用插件",
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
                                            "model": "notify",
                                            "label": "发送通知",
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
                                            "model": "delete_scrap_infos",
                                            "label": "清理刮削文件(beta)",
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
                                            "model": "delete_torrents",
                                            "label": "联动删除种子",
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
                                            "model": "delete_history",
                                            "label": "删除转移记录",
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
                                            "model": "delayed_deletion",
                                            "label": "启用延迟删除",
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
                                            "model": "delay_seconds",
                                            "label": "延迟时间(秒)",
                                            "type": "number",
                                            "min": 10,
                                            "max": 300,
                                            "placeholder": "30",
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
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "monitor_dirs",
                                            "label": "监控目录",
                                            "rows": 5,
                                            "placeholder": "源目录及硬链接目录均需加入监控，每一行一个目录",
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
                                            "label": "不删除目录",
                                            "rows": 5,
                                            "placeholder": "该目录下的文件不会被动删除，一行一个目录",
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
                                        "component": "VTextarea",
                                        "props": {
                                            "model": "exclude_keywords",
                                            "label": "排除关键词",
                                            "rows": 2,
                                            "placeholder": "每一行一个关键词",
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
                                            "text": "联动删除种子需安装插件[下载器助手]并打开监听源文件事件",
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
                                            "text": "清理刮削文件为测试功能，请谨慎开启。",
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
                                            "text": "监控目录如有多个需换行，源目录和硬链接目录都需要添加到监控目录中；如需实现删除硬链接时不删除源文件，可把源文件目录配置到不删除目录中。",
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
                                            "type": "warning",
                                            "variant": "tonal",
                                            "text": "延迟删除功能：启用后，文件删除时不会立即删除硬链接，而是等待指定时间后再检查文件是否仍被删除。这可以防止媒体重整理导致的意外删除。",
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
            "notify": False,
            "monitor_dirs": "",
            "exclude_keywords": "",
            "delayed_deletion": True,
            "delay_seconds": 30,
        }

    def get_page(self) -> List[dict]:
        pass

    def stop_service(self):
        """
        退出插件
        """
        logger.debug("开始停止服务")

        # 首先停止文件监控，防止新的删除事件
        if self._observer:
            for observer in self._observer:
                try:
                    observer.stop()
                    observer.join()
                except Exception as e:
                    print(str(e))
                    logger.error(f"停止目录监控失败：{str(e)}")
        self._observer = []
        logger.debug("文件监控已停止")

        # 停止延迟删除定时器
        if self._deletion_timer:
            try:
                self._deletion_timer.cancel()
                self._deletion_timer = None
                logger.debug("延迟删除定时器已停止")
            except Exception as e:
                logger.error(f"停止延迟删除定时器失败：{str(e)}")

        # 处理剩余的延迟删除任务
        tasks_to_process = []
        with deletion_queue_lock:
            if self.deletion_queue:
                logger.info(f"处理剩余的 {len(self.deletion_queue)} 个延迟删除任务")
                tasks_to_process = [task for task in self.deletion_queue if not task.processed]
                self.deletion_queue.clear()

        # 在锁外处理任务，避免死锁
        for task in tasks_to_process:
            self._execute_delayed_deletion(task)

        logger.debug("服务停止完成")

    def __is_excluded(self, file_path: Path) -> bool:
        """
        是否排除目录
        """
        for exclude_dir in self.exclude_dirs.split("\n"):
            if exclude_dir and exclude_dir in str(file_path):
                return True
        return False

    @staticmethod
    def scrape_files_left(path):
        """
        检查path目录是否只包含刮削文件
        """
        # 检查path下是否有目录
        for dir_path in os.listdir(path):
            if os.path.isdir(os.path.join(path, dir_path)):
                return False

        # 检查path下是否有非刮削文件
        for file in path.iterdir():
            if not file.suffix.lower() in [
                ".jpg",
                ".nfo",
            ]:
                return False
        return True

    def delete_scrap_infos(self, path):
        """
        清理path相关的刮削文件
        """
        if not self._delete_scrap_infos:
            return
        # 文件所在目录已被删除则退出
        if not os.path.exists(path.parent):
            return
        try:
            if not path.suffix.lower() in [
                ".jpg",
                ".nfo",
            ]:
                # 清理与path相关的刮削文件
                name_prefix = path.stem
                for file in path.parent.iterdir():
                    if file.name.startswith(name_prefix):
                        file.unlink()
                        logger.info(f"删除刮削文件：{file}")
        except Exception as e:
            logger.error(f"清理刮削文件发生错误：{str(e)}.")
        # 清理空目录
        self.delete_empty_folders(path)

    def delete_history(self, path):
        """
        清理path相关的转移记录
        """
        if not self._delete_history:
            return
        # 查找转移记录
        transfer_history = self._transferhistory.get_by_src(path)
        if transfer_history:
            # 删除转移记录
            self._transferhistory.delete(transfer_history.id)
            logger.info(f"删除转移记录：{transfer_history.id}")

    def delete_empty_folders(self, path):
        """
        从指定路径开始，逐级向上层目录检测并删除空目录，直到遇到非空目录或到达指定监控目录为止
        """
        # logger.info(f"清理空目录: {path}")
        while True:
            parent_path = path.parent
            if self.__is_excluded(parent_path):
                break
            # parent_path如已被删除则退出检查
            if not os.path.exists(parent_path):
                break
            # 如果当前路径等于监控目录之一，停止向上检查
            if parent_path in self.monitor_dirs.split("\n"):
                break

            # 若目录下只剩刮削文件，则清空文件夹
            try:
                if self.scrape_files_left(parent_path):
                    # 清除目录下所有文件
                    for file in parent_path.iterdir():
                        file.unlink()
                        logger.info(f"删除刮削文件：{file}")
            except Exception as e:
                logger.error(f"清理刮削文件发生错误：{str(e)}.")

            try:
                if not os.listdir(parent_path):
                    os.rmdir(parent_path)
                    logger.info(f"清理空目录：{parent_path}")
                    if self._notify:
                        self.post_message(
                            mtype=NotificationType.SiteMessage,
                            title="📁 目录清理",
                            text=f"🗑️ 清理空目录：{parent_path.name}",
                        )
                else:
                    break
            except Exception as e:
                logger.error(f"清理空目录发生错误：{str(e)}")

            # 更新路径为父目录，准备下一轮检查
            path = parent_path

    def _execute_delayed_deletion(self, task: DeletionTask):
        """
        执行延迟删除任务
        """
        try:
            logger.debug(f"开始执行延迟删除任务: {task.file_path}")

            # 验证原文件是否仍然被删除（未被重新创建）
            if task.file_path.exists():
                logger.info(f"文件 {task.file_path} 已被重新创建，跳过删除操作")
                return

            # 延迟执行所有删除相关操作
            logger.debug(f"文件 {task.file_path} 确认被删除，开始执行延迟删除操作")

            # 清理刮削文件
            self.delete_scrap_infos(task.file_path)
            if self._delete_torrents:
                # 发送事件
                eventmanager.send_event(
                    EventType.DownloadFileDeleted, {"src": str(task.file_path)}
                )
            # 删除转移记录
            self.delete_history(str(task.file_path))

            # 查找并删除硬链接文件
            deleted_files = []
            with state_lock:
                for path, inode in self.state_set.copy().items():
                    if inode == task.deleted_inode:
                        file = Path(path)
                        if self.__is_excluded(file):
                            logger.debug(f"文件 {file} 在不删除目录中，跳过")
                            continue

                        # 删除硬链接文件
                        logger.info(f"延迟删除硬链接文件：{path}")
                        file.unlink()
                        deleted_files.append(path)

                        # 清理硬链接文件相关的刮削文件
                        self.delete_scrap_infos(file)
                        if self._delete_torrents:
                            # 发送事件
                            eventmanager.send_event(
                                EventType.DownloadFileDeleted, {"src": str(file)}
                            )
                        # 删除硬链接文件的转移记录
                        self.delete_history(str(file))

                        # 从状态集合中移除
                        self.state_set.pop(path, None)

            # 发送通知（在锁外执行）
            if self._notify and deleted_files:
                file_count = len(deleted_files)

                # 构建通知内容
                notification_parts = [f"🗂️ 源文件：{task.file_path.name}"]

                if file_count == 1:
                    notification_parts.append(f"🔗 硬链接：{Path(deleted_files[0]).name}")
                else:
                    notification_parts.append(f"🔗 删除了 {file_count} 个硬链接文件")

                # 添加其他操作记录
                if self._delete_history:
                    notification_parts.append("📝 已清理转移记录")
                if self._delete_torrents:
                    notification_parts.append("🌱 已联动删除种子")
                if self._delete_scrap_infos:
                    notification_parts.append("🖼️ 已清理刮削文件")

                self.post_message(
                    mtype=NotificationType.SiteMessage,
                    title="🧹 硬链接清理",
                    text=f"⏰ 延迟删除完成\n\n" + "\n".join(notification_parts),
                )

        except Exception as e:
            logger.error(f"执行延迟删除任务失败：{str(e)} - {traceback.format_exc()}")
        finally:
            task.processed = True

    def _process_deletion_queue(self):
        """
        处理延迟删除队列
        """
        try:
            current_time = datetime.now()
            # 先获取需要处理的任务，避免在处理任务时持有锁
            with deletion_queue_lock:
                # 找到需要处理的任务
                tasks_to_process = [
                    task for task in self.deletion_queue
                    if not task.processed and
                    (current_time - task.timestamp).total_seconds() >= self._delay_seconds
                ]

                if tasks_to_process:
                    logger.debug(f"处理延迟删除队列，待处理任务数: {len(tasks_to_process)}")

            # 在锁外处理任务，避免死锁
            for task in tasks_to_process:
                self._execute_delayed_deletion(task)

            # 重新获取锁进行清理和定时器管理
            with deletion_queue_lock:
                # 清理已处理的任务
                self.deletion_queue = [
                    task for task in self.deletion_queue if not task.processed
                ]

                # 如果还有未处理的任务，重新启动定时器
                if self.deletion_queue:
                    logger.debug(f"还有 {len(self.deletion_queue)} 个任务待处理，重新启动定时器")
                    self._start_deletion_timer()
                else:
                    self._deletion_timer = None
                    logger.debug("延迟删除队列已清空，定时器停止")

        except Exception as e:
            logger.error(f"处理延迟删除队列失败：{str(e)} - {traceback.format_exc()}")
            # 确保定时器状态正确
            self._deletion_timer = None

    def _start_deletion_timer(self):
        """
        启动延迟删除定时器
        注意：此方法假设调用前已检查没有运行中的定时器
        """
        self._deletion_timer = threading.Timer(self._delay_seconds, self._process_deletion_queue)
        self._deletion_timer.daemon = True
        self._deletion_timer.start()

    def handle_deleted(self, file_path: Path):
        """
        处理删除事件
        """
        logger.debug(f"处理删除事件: {file_path}")

        # 删除的文件对应的监控信息
        with state_lock:
            # 删除的文件inode
            deleted_inode = self.state_set.get(str(file_path))
            if not deleted_inode:
                logger.debug(f"文件 {file_path} 未在监控列表中，跳过处理")
                return
            else:
                self.state_set.pop(str(file_path))

            # 根据配置选择立即删除或延迟删除
            if self._delayed_deletion:
                # 延迟删除模式 - 所有删除操作都延迟执行
                logger.info(f"文件 {file_path.name} 加入延迟删除队列，延迟 {self._delay_seconds} 秒")
                task = DeletionTask(
                    file_path=file_path,
                    deleted_inode=deleted_inode,
                    timestamp=datetime.now()
                )

                with deletion_queue_lock:
                    self.deletion_queue.append(task)
                    # 只有在没有定时器运行时才启动新的定时器
                    # 避免频繁的删除事件重置定时器导致任务永远不被处理
                    if not self._deletion_timer:
                        self._start_deletion_timer()
                        logger.debug("启动延迟删除定时器")
                    else:
                        logger.debug("延迟删除定时器已在运行，任务已加入队列")
            else:
                # 立即删除模式（原有逻辑）
                deleted_files = []

                # 清理刮削文件
                self.delete_scrap_infos(file_path)
                if self._delete_torrents:
                    # 发送事件
                    eventmanager.send_event(
                        EventType.DownloadFileDeleted, {"src": str(file_path)}
                    )
                # 删除转移记录
                self.delete_history(str(file_path))

                try:
                    # 在current_set中查找与deleted_inode有相同inode的文件并删除
                    for path, inode in self.state_set.copy().items():
                        if inode == deleted_inode:
                            file = Path(path)
                            if self.__is_excluded(file):
                                logger.debug(f"文件 {file} 在不删除目录中，跳过")
                                continue
                            # 删除硬链接文件
                            logger.info(f"立即删除硬链接文件：{path}")
                            file.unlink()
                            deleted_files.append(path)

                            # 清理刮削文件
                            self.delete_scrap_infos(file)
                            if self._delete_torrents:
                                # 发送事件
                                eventmanager.send_event(
                                    EventType.DownloadFileDeleted, {"src": str(file)}
                                )
                            # 删除转移记录
                            self.delete_history(str(file))

                    # 发送通知
                    if self._notify and deleted_files:
                        file_count = len(deleted_files)

                        # 构建通知内容
                        notification_parts = [f"🗂️ 源文件：{file_path.name}"]

                        if file_count == 1:
                            notification_parts.append(f"🔗 硬链接：{Path(deleted_files[0]).name}")
                        else:
                            notification_parts.append(f"🔗 删除了 {file_count} 个硬链接文件")

                        # 添加其他操作记录
                        if self._delete_history:
                            notification_parts.append("📝 已清理整理记录")
                        if self._delete_torrents:
                            notification_parts.append("🌱 已联动删除种子")
                        if self._delete_scrap_infos:
                            notification_parts.append("🖼️ 已清理刮削文件")

                        self.post_message(
                            mtype=NotificationType.SiteMessage,
                            title="🧹 硬链接清理",
                            text=f"⚡ 立即删除完成\n\n" + "\n".join(notification_parts),
                        )

                except Exception as e:
                    logger.error(
                        "删除硬链接文件发生错误：%s - %s" % (str(e), traceback.format_exc())
                    )
