import subprocess
import time
import signal
import requests
import venv
import traceback
import threading
import socket
import secrets
import string
import json
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

from app.log import logger
from app.plugins import _PluginBase
from app.core.config import settings
from app.helper.downloader import DownloaderHelper
from app.helper.directory import DirectoryHelper


def generate_token(length=32):
    """生成指定长度的随机安全token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class ServerState(Enum):
    """服务器状态枚举"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


class ProcessManager:
    """进程管理器 - 统一管理MCP服务器进程的生命周期"""

    # 细粒度锁设计，避免死锁
    _instance_lock = threading.Lock()  # 仅用于单例创建
    _monitor_lock = threading.Lock()   # 仅用于监控线程管理
    _global_instance = None
    _global_monitor_active = False

    def __new__(cls, plugin_instance):
        """确保只有一个ProcessManager实例"""
        with cls._instance_lock:
            if cls._global_instance is None:
                logger.info("创建全局唯一的ProcessManager实例")
                cls._global_instance = super().__new__(cls)
                cls._global_instance._initialized = False
            else:
                logger.info("返回现有的ProcessManager实例")
            return cls._global_instance

    def __init__(self, plugin_instance):
        if hasattr(self, '_initialized') and self._initialized:
            self.plugin = plugin_instance
            return

        self.plugin = plugin_instance
        self.state = ServerState.STOPPED
        self.process = None
        self.monitor_thread = None
        self.monitor_stop_event = None
        self._state_lock = threading.Lock()
        self._operation_lock = threading.Lock()
        self._restart_lock = threading.Lock()
        self._initialized = True
        logger.info("ProcessManager实例初始化完成")

    def get_state(self) -> ServerState:
        with self._state_lock:
            return self.state

    def _set_state(self, new_state: ServerState):
        with self._state_lock:
            old_state = self.state
            self.state = new_state
            if old_state != new_state:
                logger.info(f"进程状态变更: {old_state.value} -> {new_state.value}")

    def is_running(self) -> bool:
        """检查进程是否正在运行，使用PID检测和健康检查双重验证"""
        return self._robust_process_check()

    def _robust_process_check(self) -> bool:
        """健壮的进程状态检测 - 基于PID存在性和健康检查"""
        if self.process is None:
            return False

        try:
            pid_exists = False
            try:
                import psutil
                if hasattr(self.process, 'pid') and self.process.pid:
                    proc = psutil.Process(self.process.pid)
                    pid_exists = proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
            except (ImportError, psutil.NoSuchProcess, psutil.AccessDenied):
                pid_exists = False

            health_ok = False
            if pid_exists:
                health_ok = self._health_check()

            if pid_exists and health_ok:
                logger.debug("进程检查: PID存在且健康检查通过 -> running")
                if self.get_state() != ServerState.RUNNING:
                    self._set_state(ServerState.RUNNING)
                return True
            elif pid_exists and not health_ok:
                logger.debug("进程检查: PID存在但健康检查失败 -> error")
                if self.get_state() != ServerState.ERROR:
                    self._set_state(ServerState.ERROR)
                return False
            else:
                logger.debug("进程检查: PID不存在 -> stop")
                if self.get_state() != ServerState.STOPPED:
                    self._set_state(ServerState.STOPPED)
                return False

        except Exception as e:
            logger.error(f"进程状态检查时发生异常: {str(e)}")
            return False

    def start_server(self) -> bool:
        """启动服务器"""
        with self._operation_lock:
            if self.get_state() in [ServerState.STARTING, ServerState.RUNNING]:
                logger.info("服务器已在启动中或运行中，跳过启动")
                return True

            self._set_state(ServerState.STARTING)

            try:
                if not self._check_prerequisites():
                    self._set_state(ServerState.ERROR)
                    return False

                self._cleanup_existing_process()

                if self._start_process():
                    self._set_state(ServerState.RUNNING)
                    self._start_monitor()
                    logger.info("服务器启动成功")
                    return True
                else:
                    self._set_state(ServerState.ERROR)
                    return False

            except Exception as e:
                logger.error(f"启动服务器失败: {str(e)}")
                logger.error(traceback.format_exc())
                self._set_state(ServerState.ERROR)
                return False

    def stop_server(self) -> bool:
        """停止服务器"""
        if self.get_state() == ServerState.STOPPED:
            logger.info("服务器已停止")
            return True

        self._set_state(ServerState.STOPPING)

        try:
            self._stop_monitor()
            self._stop_process()
            self._set_state(ServerState.STOPPED)
            return True

        except Exception as e:
            logger.error(f"停止服务器失败: {str(e)}")
            logger.error(traceback.format_exc())
            self._set_state(ServerState.ERROR)
            return False

    def restart_server(self) -> bool:
        """重启服务器，使用专用锁防止并发重启"""
        with self._restart_lock:
            logger.info("正在重启服务器...")

            if self.stop_server():
                time.sleep(2)
                return self.start_server()
            return False

    def _check_prerequisites(self) -> bool:
        """检查启动前置条件：虚拟环境、用户凭据、access token"""
        try:
            if not self.plugin._ensure_venv():
                logger.error("无法创建或验证虚拟环境")
                return False

            username = self.plugin._config.get("mp_username", "")
            password = self.plugin._config.get("mp_password", "")

            if not username or not password:
                logger.error("未配置 MoviePilot 用户名或密码")
                return False

            access_token = self.plugin._get_moviepilot_access_token()
            if not access_token:
                logger.error("无法获取 MoviePilot 的 access token")
                return False

            self.plugin._config["access_token"] = access_token
            logger.info("已获取 MoviePilot 的 access token")
            return True

        except Exception as e:
            logger.error(f"检查前置条件失败: {str(e)}")
            return False

    def _cleanup_existing_process(self):
        """清理现有进程和端口占用"""
        try:
            self.plugin._check_and_clear_port()

            if self.process and self.process.poll() is None:
                logger.info("停止现有进程...")
                self._stop_process()
                time.sleep(1)

        except Exception as e:
            logger.error(f"清理现有进程失败: {str(e)}")

    def _start_process(self) -> bool:
        """启动新进程并等待健康检查通过"""
        try:
            cmd = self._build_start_command()
            if not cmd:
                return False

            logger.info(f"启动命令: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.plugin._plugin_dir)
            )

            if self.process is None:
                raise RuntimeError("进程启动失败")

            logger.info(f"服务器进程已启动，PID: {self.process.pid}")

            if self._wait_for_startup():
                logger.info(
                    f"MCP服务器已成功启动 - {self.plugin._config['host']}:{self.plugin._config['port']}")
                return True
            else:
                logger.error("服务器启动失败或健康检查未通过")
                self._stop_process()
                return False

        except Exception as e:
            logger.error(f"启动进程失败: {str(e)}")
            logger.error(traceback.format_exc())
            if self.process:
                try:
                    self.process.terminate()
                except:
                    pass
                self.process = None
            return False

    def _build_start_command(self) -> Optional[List[str]]:
        """构建MCP服务器启动命令，包含认证token和配置参数"""
        try:
            server_type = self.plugin._config.get("server_type", "streamable")
            if server_type == "sse":
                script_path = self.plugin._plugin_dir / "sse_server.py"
            else:
                script_path = self.plugin._plugin_dir / "server.py"

            if not script_path.exists():
                logger.error(f"启动脚本不存在: {script_path}")
                return None

            try:
                script_path.chmod(0o755)
            except Exception as e:
                logger.warning(f"无法设置脚本执行权限: {e}")

            auth_token = self.plugin._config.get("auth_token", "")
            if not auth_token:
                auth_token = generate_token(32)
                self.plugin._config["auth_token"] = auth_token
                self.plugin.update_config({
                    "enable": self.plugin._enable,
                    "config": self.plugin._config
                })
                logger.info("已生成新的API认证token")

            access_token = self.plugin._config.get("access_token", "")

            log_file_path = str(Path(settings.LOG_PATH) /
                                "plugins" / "mcpserver.log")

            cmd = [
                str(self.plugin._python_bin),
                str(script_path),
                "--host", self.plugin._config["host"],
                "--port", str(self.plugin._config["port"]),
                "--log-level", self.plugin._config["log_level"],
                "--log-file", log_file_path,
                "--moviepilot-port", str(settings.PORT)
            ]

            if auth_token:
                cmd.extend(["--auth-token", auth_token])

            if access_token:
                cmd.extend(["--access-token", access_token])

            return cmd

        except Exception as e:
            logger.error(f"构建启动命令失败: {str(e)}")
            return None

    def _wait_for_startup(self) -> bool:
        """等待服务器启动并进行健康检查"""
        start_time = time.time()
        max_time = self.plugin._config["max_startup_time"]
        interval = self.plugin._config["health_check_interval"]

        logger.info(f"等待服务器启动，最长等待{max_time}秒")

        while time.time() - start_time < max_time:
            if self.process is None or self.process.poll() is not None:
                if self.process:
                    exitcode = self.process.poll()
                    logger.error(f"服务器进程已退出，返回码: {exitcode}")
                return False

            if self._health_check():
                return True

            time.sleep(interval)

        logger.error(f"等待服务器启动超时 ({max_time}秒)")
        return False

    def _health_check(self) -> bool:
        """向服务器发送健康检查请求"""
        try:
            response = requests.get(self.plugin._health_check_url, timeout=2)
            return response.status_code == 200

        except requests.RequestException:
            return False

    def _stop_process(self):
        """停止进程，先尝试优雅终止，失败后强制终止"""
        if self.process is None:
            return

        try:
            pid = self.process.pid
            logger.info(f"正在停止进程 PID: {pid}")

            if self.process.poll() is not None:
                logger.info("进程已经终止")
                self.process = None
                return

            try:
                self.process.send_signal(signal.SIGTERM)
                logger.info("已发送SIGTERM信号")
            except Exception as e:
                logger.error(f"发送SIGTERM信号失败: {str(e)}")
                try:
                    self.process.kill()
                    logger.info("已直接强制终止进程")
                except Exception as kill_error:
                    logger.error(f"强制终止进程失败: {str(kill_error)}")
                self.process = None
                return

            for i in range(5):
                if self.process.poll() is not None:
                    logger.info(f"进程已优雅退出，返回码: {self.process.poll()}")
                    break
                logger.info(f"等待进程退出... ({i+1}/5)")
                time.sleep(1)
            else:
                try:
                    if self.process.poll() is None:
                        logger.info("优雅终止失败，强制终止进程")
                        self.process.kill()
                        time.sleep(2)
                except Exception as e:
                    logger.error(f"强制终止进程失败: {str(e)}")

            self.process = None
            logger.info("进程已停止")

        except Exception as e:
            logger.error(f"停止进程失败: {str(e)}")
            self.process = None

    def _start_monitor(self):
        """启动全局唯一的监控线程，负责自动重启意外终止的服务器"""
        if not self.plugin._config.get("auto_restart", True):
            logger.info("自动重启已禁用，不启动监控线程")
            return

        self._stop_monitor()

        with ProcessManager._monitor_lock:
            if ProcessManager._global_monitor_active:
                logger.debug("全局监控线程已在运行，跳过启动")
                return

            self.monitor_stop_event = threading.Event()
            self.monitor_thread = threading.Thread(
                target=self._monitor_loop,
                daemon=True
            )
            self.monitor_thread.start()
            ProcessManager._global_monitor_active = True
            logger.info("进程监控线程已启动")

    def _stop_monitor(self):
        """停止监控线程并重置全局状态"""
        if self.monitor_stop_event:
            self.monitor_stop_event.set()

        if self.monitor_thread and self.monitor_thread.is_alive():
            logger.debug("正在停止监控线程...")
            self.monitor_thread.join(timeout=3)
            if self.monitor_thread.is_alive():
                logger.warning("监控线程未能在3秒内停止")

        lock_acquired = ProcessManager._monitor_lock.acquire(blocking=False)
        if lock_acquired:
            try:
                ProcessManager._global_monitor_active = False
            finally:
                ProcessManager._monitor_lock.release()
        else:
            logger.warning("无法获取监控锁，跳过重置全局监控状态")

        self.monitor_thread = None
        self.monitor_stop_event = None

    def _monitor_loop(self):
        """监控循环，检测进程状态并自动重启意外终止的服务器"""
        try:
            logger.info("进程监控线程开始运行")

            while not self.monitor_stop_event.is_set():
                if not self.plugin._enable:
                    logger.info("插件已禁用，监控线程退出")
                    break

                restart_needed = False
                delay = 5
                current_state = None

                with self._operation_lock:
                    current_state = self.get_state()
                    if current_state == ServerState.STARTING:
                        if self.monitor_stop_event.wait(2):
                            break
                        continue

                    process_running = self._robust_process_check()

                    if not process_running:
                        if self.monitor_stop_event.is_set():
                            break

                        exitcode = self.process.poll() if self.process else "unknown"
                        logger.warning(f"服务器进程意外终止，返回码: {exitcode}")

                        if exitcode == 1:
                            logger.error("服务器启动失败（返回码1），可能是配置或依赖问题，暂停监控60秒")
                            self._set_state(ServerState.ERROR)
                            break

                        self._set_state(ServerState.STARTING)
                        restart_needed = True
                        delay = self.plugin._config.get("restart_delay", 5)
                        logger.info(f"将在{delay}秒后重启服务器")

                # 在锁外处理等待和重启，避免长时间持锁
                if current_state == ServerState.ERROR:
                    # 错误状态下等待60秒
                    if self.monitor_stop_event.wait(60):
                        logger.info("监控线程在暂停期间收到停止信号，退出")
                        break
                    continue

                # 在锁外等待和重启，避免长时间持有锁
                if restart_needed:
                    if self.monitor_stop_event.wait(delay):
                        logger.info("监控线程在等待期间收到停止信号，取消重启")
                        self._set_state(ServerState.STOPPED)
                        break

                    # 再次检查插件状态和停止信号
                    if not self.plugin._enable or self.monitor_stop_event.is_set():
                        logger.info("插件已禁用或收到停止信号，取消重启")
                        self._set_state(ServerState.STOPPED)
                        break

                    # 重启服务器 - 使用操作锁而非全局锁
                    with self._operation_lock:
                        # 再次检查状态，确保仍需要重启
                        if self.get_state() == ServerState.STARTING:
                            logger.info("正在重启MCP服务器...")
                            if self._start_process():
                                self._set_state(ServerState.RUNNING)
                                logger.info("服务器重启成功")
                            else:
                                self._set_state(ServerState.ERROR)
                                logger.error("服务器重启失败，暂停监控60秒")
                                if self.monitor_stop_event.wait(60):
                                    logger.info("监控线程在暂停期间收到停止信号，退出")
                                    break

                # 正常情况下每5秒检查一次
                if self.monitor_stop_event.wait(5):
                    break

        except Exception as e:
            logger.error(f"监控线程发生异常: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            # 重置全局监控状态 - 使用监控锁而非全局锁
            with ProcessManager._monitor_lock:
                ProcessManager._global_monitor_active = False
            logger.info("进程监控线程已结束")


class MCPServer(_PluginBase):
    plugin_name = "MCP Server"
    plugin_desc = "使用MCP客户端通过大模型来操作MoviePilot"
    plugin_icon = (
        "https://raw.githubusercontent.com/DzAvril/MoviePilot-Plugins/main/icons/mcp.png"
    )
    plugin_version = "1.6"
    plugin_author = "DzAvril"
    author_url = "https://github.com/DzAvril"
    plugin_config_prefix = "mcpserver_"
    plugin_order = 0
    auth_level = 1

    _enable = False
    _config = {
        "server_type": "streamable",
        "host": "0.0.0.0",
        "port": 3111,
        "log_level": "INFO",
        "health_check_interval": 3,
        "max_startup_time": 60,
        "venv_dir": "venv",
        "dependencies": ["mcp[cli]"],
        "auto_restart": True,
        "restart_delay": 5,
        "auth_token": "",
    }

    _venv_path = None
    _python_bin = None
    _health_check_url = None
    _server_script_path = None
    _downloader_helper = DownloaderHelper()
    _process_manager = None

    def __init__(self):
        """初始化MCPServer类，创建ProcessManager实例和设置基本路径"""
        super().__init__()

        self._plugin_dir = Path(__file__).parent.absolute()
        self._venv_path = self._plugin_dir / self._config["venv_dir"]
        self._python_bin = self._venv_path / "bin" / "python"

        self._process_manager = ProcessManager(self)
        logger.info("MCPServer插件已初始化")

    def init_plugin(self, config: dict = None):
        """初始化插件，检测配置变化并处理服务器状态"""
        if not config:
            return

        previous_enable = self._enable
        previous_server_type = self._config.get("server_type", "streamable")

        self._enable = config.get('enable', False)
        self._config.update(config.get('config', {}))

        current_enable = self._enable
        current_server_type = self._config.get("server_type", "streamable")

        enable_changed = previous_enable != current_enable
        server_type_changed = previous_server_type != current_server_type

        if enable_changed or server_type_changed:
            logger.info(f"配置变化: enable={previous_enable}->{current_enable}, "
                        f"server_type={previous_server_type}->{current_server_type}")

        self._plugin_dir = Path(__file__).parent.absolute()
        self._venv_path = self._plugin_dir / self._config["venv_dir"]
        self._python_bin = self._venv_path / "bin" / "python"

        if current_server_type == "sse":
            self._server_script_path = self._plugin_dir / "sse_server.py"
        else:
            self._server_script_path = self._plugin_dir / "server.py"

        port = int(self._config["port"])
        self._health_check_url = f"http://localhost:{port}/health"

        if self._process_manager is None:
            logger.warning("ProcessManager不存在，重新创建")
            self._process_manager = ProcessManager(self)

        self._handle_server_operations(enable_changed, server_type_changed,
                                       current_enable)

    def _should_skip_server_operations(self, enable_changed: bool,
                                       server_type_changed: bool) -> bool:
        """检查是否应该跳过服务器操作，避免与_save_config重复"""
        # 使用时间戳来检测是否是短时间内的重复调用
        import time
        current_time = time.time()

        # 如果没有配置变化，不需要跳过
        if not enable_changed and not server_type_changed:
            return False

        # 检查是否在短时间内（5秒）有相同的配置变化
        if hasattr(self, '_last_config_change_time'):
            time_diff = current_time - self._last_config_change_time
            if time_diff < 5:  # 5秒内的重复调用
                logger.info(f"检测到{time_diff:.1f}秒内的重复配置变化，跳过服务器操作")
                return True

        # 记录本次配置变化时间
        self._last_config_change_time = current_time
        return False

    def _handle_server_operations(self, enable_changed: bool,
                                  server_type_changed: bool, current_enable: bool):
        """根据配置变化处理服务器启动、停止、重启操作"""

        if server_type_changed:
            logger.info("检测到服务器类型变化，需要重启服务器")
            if current_enable:
                self._process_manager.restart_server()
            else:
                self._process_manager.stop_server()
            return

        if enable_changed:
            if current_enable:
                logger.info("插件从禁用变为启用，启动服务器...")
                self._process_manager.start_server()
            else:
                logger.info("插件从启用变为禁用，停止服务器...")
                self._process_manager.stop_server()
            return

        if not current_enable and self._process_manager.is_running():
            logger.info("插件已禁用但服务器仍在运行，正在停止服务器...")
            self._process_manager.stop_server()
            return

        if current_enable and not self._process_manager.is_running():
            logger.info("插件已启用但服务器未运行，正在自动启动服务器...")
            self._process_manager.start_server()

    def _ensure_venv(self) -> bool:
        """确保虚拟环境存在并安装了所需依赖"""
        try:
            if not self._python_bin.exists():
                logger.info(f"创建虚拟环境: {self._venv_path}")
                venv.create(self._venv_path, with_pip=True)

                if not self._python_bin.exists():
                    logger.error(f"创建虚拟环境失败，找不到Python解释器: {self._python_bin}")
                    return False

                logger.info("虚拟环境创建成功")

                # 安装依赖
                self._install_dependencies()
            else:
                logger.info(f"虚拟环境已存在: {self._venv_path}")

            return True

        except Exception as e:
            logger.error(f"设置虚拟环境失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _install_dependencies(self) -> bool:
        """安装依赖包"""
        try:
            deps = self._config["dependencies"]
            deps_str = " ".join(f"'{dep}'" for dep in deps)
            logger.info(f"正在安装依赖: {deps_str}")

            # 构建安装命令
            install_cmd = [
                str(self._python_bin),
                "-m",
                "pip",
                "install",
                "--upgrade",
                "-i", "https://mirrors.aliyun.com/pypi/simple/"
            ]

            # 添加依赖
            for dep in self._config["dependencies"]:
                install_cmd.append(dep)

            logger.info(f"执行安装命令: {' '.join(install_cmd)}")

            # 执行安装
            result = subprocess.run(
                install_cmd,
                cwd=str(self._plugin_dir),
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                logger.error(f"安装依赖失败: {result.stderr}")
                return False

            logger.info("依赖安装成功")
            return True

        except Exception as e:
            logger.error(f"安装依赖失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _stop_all_threads(self):
        """停止所有线程"""
        logger.info("正在停止所有监控线程...")

        # 停止ProcessManager的监控线程
        if self._process_manager:
            self._process_manager._stop_monitor()

        # 强制清理所有线程引用
        if hasattr(self, '_monitor_thread') and self._monitor_thread:
            if self._monitor_thread.is_alive():
                logger.warning("监控线程仍在运行，强制清理")
            self._monitor_thread = None

        if hasattr(self, '_monitor_stop_event') and self._monitor_stop_event:
            self._monitor_stop_event.set()
            self._monitor_stop_event = None

        # 等待一段时间确保线程完全停止
        import time
        time.sleep(2)

        logger.info("所有监控线程已停止")

    def _check_and_clear_port(self):
        """检查端口是否被占用，如果被占用则尝试停止占用进程"""
        port = int(self._config["port"])
        host = self._config["host"]

        # 判断地址类型：IPv4 or IPv6
        try:
            # getaddrinfo 自动判断协议族
            addr_info = socket.getaddrinfo(
                host, port, proto=socket.IPPROTO_TCP)
        except socket.gaierror as e:
            logger.error(f"地址解析失败: {host}, error: {e}")
            return

        family = addr_info[0][0]  # AF_INET or AF_INET6
        sock_type = addr_info[0][1]

        s = socket.socket(family, sock_type)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.close()
            logger.debug(f"端口 {port}（{host}）可用")
            return
        except socket.error as e:
            logger.warning(f"端口 {port}（{host}）已被占用，尝试处理: {e}")
            s.close()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.close()
            logger.debug(f"端口 {port} 可用")
            return
        except Exception as e:
            logger.warning(f"端口 {port} 已被占用，尝试清理")
            s.close()

        # 端口被占用，尝试终止占用进程
        try:
            # 尝试终止占用进程
            if self._try_terminate_port_process():
                # 成功终止进程，等待端口释放
                if self._wait_for_port_release(port, host):
                    return

            # 如果无法释放端口，报告错误
            self._report_port_occupied(port)

            raise RuntimeError(f"端口 {port} 被占用且无法清理，请手动终止占用进程或修改端口配置")

        except Exception as e:
            logger.error(f"检查和清理端口时出错: {str(e)}")
            logger.error(traceback.format_exc())
            raise RuntimeError(f"无法启动MCP服务器: {str(e)}")

    def _report_port_occupied(self, port):
        """报告端口占用情况"""
        logger.error("无法清理端口，请尝试以下操作:")
        logger.error(f"1. 检查是否有其他程序占用了端口 {port}")
        logger.error("2. 手动终止占用端口的进程")
        logger.error("3. 在插件设置中修改端口号后重新启动")
        logger.error("4. 如果使用Docker，检查端口映射是否正确")

        # 提供进一步诊断信息
        try:
            # 尝试导入psutil提供更多信息
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port:
                    if conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            logger.error(
                                f"占用端口 {port} 的进程: PID={conn.pid}, "
                                f"名称={proc.name()}, "
                                f"命令行={' '.join(proc.cmdline() or [])}"
                            )
                        except psutil.NoSuchProcess:
                            logger.error(
                                f"占用端口 {port} 的进程: PID={conn.pid}（进程不存在）"
                            )
                    else:
                        logger.error(f"占用端口 {port} 的连接信息: {conn}")
        except ImportError:
            pass

    def _try_terminate_port_process(self) -> bool:
        """尝试查找并终止占用端口的进程，使用psutil库"""
        port = int(self._config["port"])
        host = self._config["host"]

        try:
            import psutil

            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    for conn in proc.connections(kind='inet'):
                        is_target_port = conn.laddr.port == port
                        is_bind_addr = (conn.laddr.ip == host or
                                        conn.laddr.ip == '0.0.0.0' or
                                        conn.laddr.ip == '::')

                        if is_target_port and is_bind_addr:
                            pid = proc.pid
                            cmd_line = " ".join(
                                proc.cmdline() if proc.cmdline() else []
                            )
                            logger.info(f"找到占用端口 {port} 的进程 PID: {pid}, 命令: {cmd_line}")

                            is_python = "python" in cmd_line.lower()
                            is_server = (
                                "server.py" in cmd_line or "sse_server.py" in cmd_line)

                            if is_python and is_server:
                                return self._terminate_process(proc)
                            else:
                                logger.warning("占用端口的不是MCP服务器进程，不自动终止")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            logger.warning(f"未找到占用端口 {port} 的MCP服务器进程")
            return False

        except ImportError:
            logger.error("psutil模块未安装，无法查找和终止占用端口的进程")
            return False
        except Exception as e:
            logger.error(f"使用psutil查找和终止进程时出错: {str(e)}")
            return False

    def _terminate_process(self, proc) -> bool:
        """终止指定进程"""
        try:
            import psutil

            logger.info("确认是MCP服务器进程，尝试终止")
            proc.terminate()
            _, alive = psutil.wait_procs([proc], timeout=3)

            if proc in alive:
                logger.warning("进程未响应终止信号，尝试强制终止")
                proc.kill()

            logger.info("成功终止占用端口的进程")
            return True
        except Exception as e:
            logger.error(f"终止进程失败: {str(e)}")
            return False

    def _wait_for_port_release(self, port, host, timeout=10) -> bool:
        """等待端口释放"""
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((host, port))
                s.close()
                logger.info(f"端口 {port} 已释放")
                return True
            except socket.error:
                time.sleep(0.5)

        logger.error("等待端口释放超时")
        return False





    def _get_server_status(self) -> Dict[str, Any]:
        """获取服务器详细状态"""
        # 获取当前服务器类型和相关信息
        server_type = self._config.get("server_type", "streamable")
        host = self._config.get("host", "0.0.0.0")
        port = self._config.get("port", 3111)

        # 初始化状态信息
        status = {
            "running": False,
            "pid": None,
            "url": None,
            "health": False,
            "server_type": server_type,
            "listen_address": f"{host}:{port}",
            "venv_path": str(self._venv_path) if self._venv_path else None,
            "python_bin": str(self._python_bin) if self._python_bin else None,
            "auth_token": self._mask_token(self._config.get("auth_token", "")),
            "requires_auth": True,
            "resource_usage": None,
            "state": "unknown"
        }

        # 设置服务URL
        port = int(self._config["port"])
        host = self._config["host"]
        if server_type == "sse":
            status["url"] = f"http://{host}:{port}/sse/"
        else:
            status["url"] = f"http://{host}:{port}/mcp/"

        if self._process_manager:
            status["state"] = self._process_manager.get_state().value
            status["running"] = self._process_manager.is_running()

            if status["running"] and self._process_manager.process:
                status["pid"] = self._process_manager.process.pid

                if self._process_manager._health_check():
                    status["health"] = True
                else:
                    logger.warning("健康检查失败")

                try:
                    resource_usage = self._get_process_resource_usage(
                        status["pid"])
                    status["resource_usage"] = resource_usage
                except Exception as e:
                    logger.debug(f"获取进程资源占用信息失败: {str(e)}")
                    status["resource_usage"] = None
            else:
                logger.debug(f"进程未运行: running={status['running']}")
        else:
            logger.error("ProcessManager不存在！")

        logger.debug(
            f"服务器状态: running={status['running']}, health={status['health']}, "
            f"pid={status['pid']}, state={status['state']}"
        )
        return status

    def _get_process_resource_usage(self, pid: int) -> Optional[Dict[str, Any]]:
        """获取指定进程的资源占用信息"""
        try:
            import psutil

            proc = psutil.Process(pid)

            # 获取进程信息
            with proc.oneshot():
                # CPU和内存信息
                cpu_percent = proc.cpu_percent(interval=0.1)  # 0.1秒采样间隔
                memory_info = proc.memory_info()
                memory_percent = proc.memory_percent()

                # 线程和文件描述符
                num_threads = proc.num_threads()
                try:
                    num_fds = proc.num_fds() if hasattr(proc, 'num_fds') else 0
                except (psutil.AccessDenied, AttributeError):
                    num_fds = 0

                # 计算运行时长
                runtime_seconds = time.time() - proc.create_time()
                runtime_hours = runtime_seconds / 3600
                if runtime_hours < 1:
                    runtime = f"{runtime_seconds / 60:.1f} 分钟"
                elif runtime_hours < 24:
                    runtime = f"{runtime_hours:.1f} 小时"
                else:
                    runtime = f"{runtime_hours / 24:.1f} 天"

                return {
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_info.rss / 1024 / 1024,  # 物理内存 MB
                    'memory_percent': memory_percent,
                    'runtime': runtime,
                    'num_threads': num_threads,
                    'num_fds': num_fds
                }

        except ImportError:
            logger.debug("psutil模块未安装，无法获取进程资源信息")
            return None
        except psutil.NoSuchProcess:
            logger.debug(f"进程 {pid} 不存在")
            return None
        except psutil.AccessDenied:
            logger.debug(f"无权限访问进程 {pid}")
            return None
        except Exception as e:
            logger.debug(f"获取进程 {pid} 资源信息时出错: {str(e)}")
            return None

    def _mask_token(self, token: str) -> str:
        """掩盖token，只显示前4位和后4位"""
        if not token or len(token) < 10:
            return "******" if token else ""
        return f"{token[:4]}...{token[-4:]}"

    def _generate_new_token(self) -> Dict[str, Any]:
        """API Endpoint: 生成新的API令牌"""
        try:
            # 生成新token
            new_token = generate_token(32)

            # 更新插件配置中的令牌
            self._config["auth_token"] = new_token

            # 保存配置
            self.update_config({
                "enable": self._enable,
                "config": self._config
            })

            # 检查服务器是否正在运行，如果在运行需要提示用户重启
            if self._process_manager and self._process_manager.is_running():
                message = "已生成新的API Token，需要重启服务器才能生效"
                logger.info("已生成新token，但需要重启服务器才能应用")
            else:
                # 服务器未运行，将在启动时使用新token
                message = "已生成新的API Token，将在服务器启动时生效"
                logger.info("已生成新token，将在服务器启动时生效")

            return {
                "message": message,
                "status": "success",
                "token": new_token,
                "masked_token": self._mask_token(new_token)
            }
        except Exception as e:
            logger.error(f"生成新token失败: {str(e)}")
            return {
                "message": f"生成新token失败: {str(e)}",
                "status": "error"
            }

    def get_state(self) -> bool:
        """获取插件状态"""
        return self._enable

    # --- Instance methods for API endpoints ---
    def _get_config(self) -> Dict[str, Any]:
        """API Endpoint: Returns current plugin configuration."""
        return {
            "enable": self._enable,
            "config": self._config,
            "server_status": self._get_server_status()
        }

    def _save_config(self, config_payload: dict) -> Dict[str, Any]:
        """API Endpoint: Saves plugin configuration. Expects a dict payload."""
        logger.info(f"{self.plugin_name}: 收到配置保存请求: {config_payload}")
        try:
            # 验证配置数据
            if not isinstance(config_payload, dict):
                raise ValueError("配置数据必须是字典格式")

            # 检测配置变化（但不更新内部状态）
            previous_enable = self._enable
            previous_server_type = self._config.get("server_type", "streamable")

            current_enable = config_payload.get('enable', False)
            current_server_type = config_payload.get('config', {}).get("server_type", "streamable")

            enable_changed = previous_enable != current_enable
            server_type_changed = previous_server_type != current_server_type

            logger.info(
                f"配置变化检测: enable={previous_enable}->{current_enable}, server_type={previous_server_type}->{current_server_type}")

            # 保存到系统配置
            from app.db.systemconfig_oper import SystemConfigOper
            system_config = SystemConfigOper()
            config_key = f"plugin.{self.plugin_name.lower()}"
            system_config.set(config_key, config_payload)

            # 不在这里更新内部配置，让init_plugin来处理
            # 这样可以确保init_plugin能正确检测到配置变化
            logger.info("配置已保存，等待MoviePilot调用init_plugin处理服务器操作")

            return {
                "message": "配置已保存",
                "saved_config": self._get_config(),
                "enable_changed": enable_changed,
                "server_type_changed": server_type_changed
            }

        except Exception as e:
            logger.error(f"{self.plugin_name}: 保存配置时发生错误: {e}",
                         exc_info=True)
            return {
                "message": f"保存配置失败: {e}",
                "error": True,
                "saved_config": self._get_config()
            }

    def _restart_server(self) -> Dict[str, Any]:
        """API Endpoint: 重启服务器"""
        try:
            logger.info("正在执行服务器重启...")

            # 重启服务器
            if self._process_manager and self._process_manager.restart_server():
                # 等待服务器完全启动
                time.sleep(5)

                # 获取最新状态
                current_status = self._get_server_status()

                return {
                    "message": "服务器已成功重启",
                    "server_status": current_status
                }
            else:
                return {
                    "message": "服务器重启失败，请检查配置和日志",
                    "error": True,
                    "server_status": self._get_server_status()
                }

        except Exception as e:
            logger.error(f"重启服务器失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "message": f"重启服务器失败: {str(e)}",
                "error": True,
                "server_status": self._get_server_status()
            }

    # --- Abstract/Base Methods Implementation ---
    def get_form(self) -> Tuple[Optional[List[dict]], Dict[str, Any]]:
        """Returns None for Vue form, but provides initial config data."""
        return None, self._get_config()

    def get_page(self) -> Optional[List[dict]]:
        """Vue mode doesn't use Vuetify page definitions."""
        return None

    def get_api(self) -> List[Dict[str, Any]]:
        """Defines API endpoints accessible via props.api in Vue components."""
        return [
            {
                "path": "/config",
                "endpoint": self._get_config,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取当前配置"
            },
            {
                "path": "/config",
                "endpoint": self._save_config,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "保存配置"
            },
            {
                "path": "/restart",
                "endpoint": self._restart_server,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "重启服务器"
            },
            {
                "path": "/start",
                "endpoint": self._start_server_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "启动服务器"
            },
            {
                "path": "/stop",
                "endpoint": self._stop_server_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "停止服务器"
            },
            {
                "path": "/token",
                "endpoint": self._generate_new_token,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "生成新的API令牌"
            },
            {
                "path": "/status",
                "endpoint": self._get_server_status_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取服务器状态"
            },
            {
                "path": "/download_torrent",
                "endpoint": self._download_torrent_api,
                "methods": ["POST"],
                "auth": "bear",
                "summary": "下载种子"
            },
            {
                "path": "/process-stats",
                "endpoint": self._get_process_stats_api,
                "methods": ["GET"],
                "auth": "bear",
                "summary": "获取MCP服务器进程资源占用统计"
            }
        ]

    def _start_server_api(self) -> Dict[str, Any]:
        """API Endpoint: 启动服务器"""
        try:
            # 检查服务器是否已经在运行
            if self._process_manager and self._process_manager.is_running():
                return {
                    "message": "服务器已经在运行中",
                    "server_status": self._get_server_status()
                }

            # 启动服务器
            if self._process_manager and self._process_manager.start_server():
                # 等待服务器完全启动
                time.sleep(3)

                # 获取最新状态
                current_status = self._get_server_status()

                return {
                    "message": "服务器已成功启动",
                    "server_status": current_status
                }
            else:
                return {
                    "message": "服务器启动失败，请检查配置和日志",
                    "error": True,
                    "server_status": self._get_server_status()
                }

        except Exception as e:
            logger.error(f"启动服务器失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "message": f"启动服务器失败: {str(e)}",
                "error": True,
                "server_status": self._get_server_status()
            }

    def _stop_server_api(self) -> Dict[str, Any]:
        """API Endpoint: 停止服务器"""
        try:
            # 检查服务器是否已经停止
            if self._process_manager and not self._process_manager.is_running():
                return {
                    "message": "服务器已经停止",
                    "server_status": self._get_server_status()
                }

            # 停止服务器
            if self._process_manager and self._process_manager.stop_server():
                # 等待服务器完全停止
                time.sleep(2)

                # 获取最新状态
                current_status = self._get_server_status()

                return {
                    "message": "服务器已成功停止",
                    "server_status": current_status
                }
            else:
                return {
                    "message": "服务器停止失败，请手动刷新状态",
                    "error": True,
                    "server_status": self._get_server_status()
                }

        except Exception as e:
            logger.error(f"停止服务器失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "message": f"停止服务器失败: {str(e)}",
                "error": True,
                "server_status": self._get_server_status()
            }

    def _get_server_status_api(self) -> Dict[str, Any]:
        """API Endpoint: 获取服务器状态"""
        try:
            # 获取最新的服务器状态
            status = self._get_server_status()

            # 记录日志
            logger.info(
                "插件启动：%s, 获取服务器状态: running=%s, health=%s", self._enable,
                status['running'], status['health']
            )

            return {
                "enable": self._enable,
                "server_status": status,
                "message": "获取服务器状态成功"
            }
        except Exception as e:
            logger.error(f"获取服务器状态失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "message": f"获取服务器状态失败: {str(e)}",
                "error": True,
                "server_status": {
                    "running": False,
                    "health": False,
                    "pid": None,
                    "url": None
                }
            }

    def _get_process_stats_api(self) -> Dict[str, Any]:
        """API Endpoint: 获取MCP服务器进程资源占用统计"""
        try:
            # 获取服务器状态，包含PID信息
            status = self._get_server_status()

            if not status["running"] or not status["pid"]:
                return {
                    "message": "MCP服务器未运行或无法获取进程ID",
                    "error": True,
                    "process_stats": None,
                    "enable": self._enable,
                }

            pid = status["pid"]

            # 获取详细的进程资源统计
            try:
                import psutil

                proc = psutil.Process(pid)

                # 获取进程信息
                with proc.oneshot():
                    # 基本信息
                    name = proc.name()
                    status_str = proc.status()
                    create_time_timestamp = proc.create_time()  # 保持原始时间戳

                    # CPU和内存信息
                    cpu_percent = proc.cpu_percent(interval=0.5)  # 0.5秒采样间隔
                    memory_info = proc.memory_info()
                    memory_percent = proc.memory_percent()

                    # 线程和文件描述符
                    num_threads = proc.num_threads()
                    try:
                        num_fds = proc.num_fds() if hasattr(proc, 'num_fds') else 0
                    except (psutil.AccessDenied, AttributeError):
                        num_fds = 0

                    # 网络连接
                    try:
                        connections = len(proc.connections())
                    except (psutil.AccessDenied, psutil.NoSuchProcess):
                        connections = 0

                    # 计算运行时长
                    runtime_seconds = time.time() - create_time_timestamp
                    runtime_hours = runtime_seconds / 3600
                    if runtime_hours < 1:
                        runtime = f"{runtime_seconds / 60:.1f} 分钟"
                    elif runtime_hours < 24:
                        runtime = f"{runtime_hours:.1f} 小时"
                    else:
                        runtime = f"{runtime_hours / 24:.1f} 天"

                    process_stats = {
                        'pid': pid,
                        'name': name,
                        'status': status_str,
                        'cpu_percent': cpu_percent,
                        'memory_mb': memory_info.rss / 1024 / 1024,  # 物理内存 MB
                        'virtual_memory_mb': memory_info.vms / 1024 / 1024,  # 虚拟内存 MB
                        'memory_percent': memory_percent,
                        'create_time': create_time_timestamp,  # 返回原始时间戳
                        'runtime': runtime,
                        'num_threads': num_threads,
                        'num_fds': num_fds,
                        'connections': connections
                    }

                    return {
                        "message": "获取进程统计信息成功",
                        "process_stats": process_stats,
                        "server_status": status,
                        "enable": self._enable,
                    }

            except ImportError:
                return {
                    "message": "psutil模块未安装，无法获取进程统计信息",
                    "error": True,
                    "process_stats": None,
                    "enable": self._enable,
                }
            except psutil.NoSuchProcess:
                return {
                    "message": f"进程 {pid} 不存在",
                    "error": True,
                    "process_stats": None,
                    "enable": self._enable,
                }
            except psutil.AccessDenied:
                return {
                    "message": f"无权限访问进程 {pid}",
                    "error": True,
                    "process_stats": None,
                    "enable": self._enable,
                }
            except Exception as e:
                logger.error(f"获取进程统计信息时出错: {str(e)}")
                return {
                    "message": f"获取进程统计信息时出错: {str(e)}",
                    "error": True,
                    "process_stats": None,
                    "enable": self._enable,
                }

        except Exception as e:
            logger.error(f"获取进程统计信息API失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "message": f"获取进程统计信息失败: {str(e)}",
                "error": True,
                "process_stats": None,
                "enable": self._enable,
            }

    def _download_torrent_api(self, body: dict = None) -> Dict[str, Any]:
        """API Endpoint: 下载种子"""
        try:
            # 从请求体中获取参数
            if body is None:
                logger.error("请求体为空")
                return {
                    "success": False,
                    "message": "请求体为空，请提供torrent_url参数"
                }

            # 记录请求体
            logger.info(f"下载种子API请求体: {json.dumps(body, ensure_ascii=False)}")

            # 获取参数
            torrent_url = body.get("torrent_url")
            downloader = body.get("downloader")
            save_path = body.get("save_path")
            if save_path is None:
                # get default path based on media type
                default_paths = DirectoryHelper().get_local_download_dirs()
                for d in default_paths:
                    if d.media_type == body.get("media_type"):
                        save_path = d.download_path
                        break

            if not torrent_url:
                return {
                    "success": False,
                    "message": "缺少种子链接参数"
                }

            # 如果没有指定下载器，返回错误信息
            if not downloader:
                logger.error("未指定下载器，请在请求中提供downloader参数")
                return {
                    "success": False,
                    "message": (
                        "未指定下载器，请使用get-downloaders工具获取可用的下载器列表，"
                        "然后在请求中提供downloader参数"
                    )
                }

            # 导入必要的模块
            from app.db.site_oper import SiteOper
            from app.utils.string import StringUtils

            # 初始化辅助类
            site_oper = SiteOper()

            # 获取种子对应站点cookie
            domain = StringUtils.get_url_domain(torrent_url)
            if not domain:
                return {
                    "success": False,
                    "message": f"无法从链接获取站点域名: {torrent_url}"
                }

            # 查询站点
            site = site_oper.get_by_domain(domain)
            if not site or not site.cookie:
                return {
                    "success": False,
                    "message": f"无法获取站点 {domain} 的cookie信息"
                }

            # 获取下载器服务
            service = self._downloader_helper.get_service(downloader)
            if not service or not service.instance:
                return {
                    "success": False,
                    "message": f"获取下载器 {downloader} 实例失败"
                }

            if service.instance.is_inactive():
                return {
                    "success": False,
                    "message": f"下载器 {downloader} 未连接"
                }

            # 添加下载任务
            downloader_instance = service.instance
            download_id = None
            cookie = site.cookie if site.cookie else None
            if self._downloader_helper.is_downloader("qbittorrent", service=service):
                torrent = downloader_instance.add_torrent(content=torrent_url,
                                                          download_dir=save_path,
                                                          is_paused=False,
                                                          cookie=cookie,
                                                          tag=[settings.TORRENT_TAG, site.name])
                if torrent:
                    download_id = torrent
            elif self._downloader_helper.is_downloader("transmission", service=service):
                torrent = downloader_instance.add_torrent(content=torrent_url,
                                                          download_dir=save_path,
                                                          is_paused=False,
                                                          cookie=cookie,
                                                          labels=[settings.TORRENT_TAG, site.name])
                if torrent:
                    download_id = torrent.hashString

            if not download_id:
                return {
                    "success": False,
                    "message": "添加下载任务失败"
                }

            return {
                "success": True,
                "message": "种子添加下载成功",
                "site": site.name,
                "save_path": save_path
            }

        except Exception as e:
            logger.error(f"下载种子失败: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "success": False,
                "message": f"下载种子失败: {str(e)}"
            }

    # --- 获取 MoviePilot 的 access token ---
    def _get_moviepilot_access_token(self) -> Optional[str]:
        """
        获取 MoviePilot 的 access token
        通过用户名和密码登录获取 access_token，用于访问需要 Bearer 认证的 API
        """
        try:
            # 获取用户名和密码
            username = self._config.get("mp_username", "admin")
            password = self._config.get("mp_password", "")

            if not username or not password:
                logger.error("未配置 MoviePilot 用户名或密码，无法获取 access token")
                return None

            logger.info(f"尝试使用用户名 {username} 登录获取 access token")

            # 构建请求 URL
            base_url = f"http://localhost:{settings.PORT}"
            token_url = f"{base_url}/api/v1/login/access-token"

            # 构建请求数据
            data = {
                "username": username,
                "password": password
            }

            # 发送请求
            response = requests.post(
                token_url,
                data=data,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10
            )

            if response.status_code != 200:
                logger.error(
                    f"登录获取 access token 失败，状态码: {response.status_code}, "
                    f"响应: {response.text}")
                return None

            # 解析响应获取 access_token
            token_data = response.json()
            access_token = token_data.get("access_token")

            if not access_token:
                logger.error("响应中未包含 access_token")
                return None

            logger.info("成功获取 MoviePilot 的 access token")
            return access_token

        except Exception as e:
            logger.error(f"获取 MoviePilot access token 失败: {str(e)}")
            logger.error(traceback.format_exc())
            return None

    # --- V2 Vue Interface Method ---
    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """Declare Vue rendering mode and assets path."""
        # 不要添加任何查询参数，保持路径纯净
        return "vue", "dist/assets"

    # --- Other Base Methods ---
    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []  # No commands defined for this plugin

    def stop_service(self):
        """停止服务和所有线程"""
        return

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        """获取插件仪表盘元信息"""
        return [
            {
                "key": "mcpserver",
                "name": "MCP Server"
            }
        ]

    def get_dashboard(
        self, key: str = "", **kwargs
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """
        获取插件仪表盘页面

        参数:
            key: 仪表盘键名，未使用
            kwargs: 额外参数，未使用
        """
        # 获取Dashboard配置
        dashboard_refresh_interval = self._config.get(
            "dashboard_refresh_interval", 30)
        dashboard_auto_refresh = self._config.get(
            "dashboard_auto_refresh", True)

        return {
            "cols": 12,
            "md": 6
        }, {
            "refresh": dashboard_refresh_interval,  # 使用配置的刷新间隔
            "border": True,
            "title": "MCP Server",
            "subtitle": "启动MCP服务器实现大模型操作MoviePilot",
            "render_mode": "vue",  # 使用Vue渲染模式
            "pluginConfig": {  # 传递插件配置给前端组件
                "dashboard_refresh_interval": dashboard_refresh_interval,
                "dashboard_auto_refresh": dashboard_auto_refresh
            }
        }, None
