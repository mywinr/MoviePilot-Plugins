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
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

from app.log import logger
from app.plugins import _PluginBase
from app.core.config import settings
from app.db.site_oper import SiteOper
from app.utils.string import StringUtils
from app.helper.downloader import DownloaderHelper
from app.helper.directory import DirectoryHelper
from app.schemas import ServiceInfo


def generate_token(length=32):
    """生成指定长度的随机安全token"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


class MCPServer(_PluginBase):
    # 插件名称
    plugin_name = "MCP Server"
    # 插件描述
    plugin_desc = "使用MCP客户端通过大模型来操作MoviePilot"
    # 插件图标
    plugin_icon = (
        "https://raw.githubusercontent.com/DzAvril/"
        "MoviePilot-Plugins/main/icons/mcp.png"
    )
    # 插件版本
    plugin_version = "1.3"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "mcpserver_"
    # 加载顺序
    plugin_order = 0
    # 可使用的用户级别
    auth_level = 1

    _enable = False
    _server_process = None
    _monitor_thread = None
    _monitor_stop_event = None
    _config = {
        "host": "0.0.0.0",  # 监听所有网络接口
        "port": 3111,
        "log_level": "INFO",
        "health_check_interval": 3,  # 健康检查间隔(秒)
        "max_startup_time": 60,      # 最大启动等待时间(秒)
        "venv_dir": "venv",          # 虚拟环境目录名
        "dependencies": ["mcp[cli]"],  # 需要安装的依赖
        "auto_restart": True,        # 是否自动重启意外终止的服务器
        "restart_delay": 5,          # 重启前等待时间(秒)
        "auth_token": "",            # API认证令牌
    }

    # 虚拟环境相关路径
    _venv_path = None
    _python_bin = None
    _health_check_url = None
    _server_script_path = None
    _downloader_helper = DownloaderHelper()

    def init_plugin(self, config: dict = None):
        """初始化插件"""
        if not config:
            return
        self._enable = config.get('enable', False)
        self._config.update(config.get('config', {}))

        # 设置当前模块所在目录
        self._plugin_dir = Path(__file__).parent.absolute()

        # 设置虚拟环境路径
        self._venv_path = self._plugin_dir / self._config["venv_dir"]

        # 设置Python解释器路径 (仅Linux)
        self._python_bin = self._venv_path / "bin" / "python"

        # 设置服务器脚本路径
        self._server_script_path = self._plugin_dir / "server.py"

        # 设置健康检查URL
        port = int(self._config["port"])
        self._health_check_url = f"http://localhost:{port}/mcp/"

        if not self._enable:
            # 如果插件被禁用，停止服务器
            self._stop_server()
            logger.info("插件已禁用，服务器已停止")
            return

        # 确保虚拟环境存在
        if not self._ensure_venv():
            logger.error("无法创建或验证虚拟环境，插件无法启动")
            return

        # 检查用户名和密码是否已配置
        username = self._config.get("mp_username", "")
        password = self._config.get("mp_password", "")

        if not username or not password:
            logger.error("未配置 MoviePilot 用户名或密码，无法启动服务器")
            logger.info("插件已启用，但服务器未启动，请在配置页面填写用户名和密码")
            return

        # 尝试获取 access_token
        access_token = self._get_moviepilot_access_token()
        if not access_token:
            logger.error("无法获取 MoviePilot 的 access token，无法启动服务器")
            logger.info("插件已启用，但服务器未启动，请检查用户名和密码是否正确")
            return

        # 保存 access_token 到配置
        self._config["access_token"] = access_token
        logger.info("已获取 MoviePilot 的 access token，将用于 API 请求")

        # 检查服务器是否已在运行
        server_status = self._get_server_status()
        if not server_status["running"] and self._enable:
            # 如果插件已启用且服务器未运行，则自动启动服务器
            logger.info("插件已启用，服务器未运行，正在自动启动服务器...")
            try:
                self._start_server()
                logger.info("服务器已自动启动")
            except Exception as e:
                logger.error(f"自动启动服务器失败: {str(e)}")
                logger.error(traceback.format_exc())

    def _ensure_venv(self) -> bool:
        """确保虚拟环境存在并安装了所需依赖"""
        try:
            # 检查虚拟环境是否存在
            if not self._python_bin.exists():
                logger.info(f"正在创建虚拟环境: {self._venv_path}")

                # 创建虚拟环境
                venv.create(self._venv_path, with_pip=True)

                if not self._python_bin.exists():
                    logger.error(f"创建虚拟环境失败，找不到Python解释器: {self._python_bin}")
                    return False

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

    def _start_server(self):
        """启动MCP服务器作为独立进程"""
        if (self._server_process is not None and
                self._server_process.poll() is None):
            logger.info("服务器已在运行中")
            return

        try:
            logger.info("正在启动MCP服务器作为独立进程...")

            # 先检查端口是否被占用
            self._check_and_clear_port()

            # 获取启动器脚本路径
            launcher_script = self._server_script_path
            if not launcher_script.exists():
                raise FileNotFoundError(f"启动器脚本不存在: {launcher_script}")

            # 确保脚本有执行权限
            try:
                launcher_script.chmod(0o755)
            except Exception as e:
                logger.warning(f"无法设置脚本执行权限: {e}")

            # 准备初始token
            auth_token = self._config.get("auth_token", "")
            if not auth_token:
                # 如果没有token则生成新token
                auth_token = generate_token(32)
                self._config["auth_token"] = auth_token
                # 保存新生成的token到配置
                self.update_config({
                    "enable": self._enable,
                    "config": self._config
                })
                logger.info("已生成新的API认证token")

            logger.info("API认证已启用，需要Bearer Token才能访问")

            # 获取已保存的 access_token
            access_token = self._config.get("access_token", "")

            # 获取日志文件路径
            log_file_path = str(Path(settings.LOG_PATH) / "plugins" / "mcpserver.log")
            logger.info(f"设置MCP服务器日志输出到: {log_file_path}")

            # 构建启动命令
            cmd = [
                str(self._python_bin),
                str(launcher_script),
                "--host", self._config["host"],
                "--port", str(self._config["port"]),
                "--log-level", self._config["log_level"],
                "--log-file", log_file_path
            ]

            # 添加认证参数
            if auth_token:
                cmd.extend(["--auth-token", auth_token])

            if access_token:
                cmd.extend(["--access-token", access_token])

            logger.info(f"启动命令: {' '.join(cmd)}")

            # 停止现有的线程
            self._stop_all_threads()

            # 创建新的停止事件
            self._monitor_stop_event = threading.Event()

            # 启动前确保进程引用为空
            self._server_process = None

            try:
                # 启动进程
                self._server_process = subprocess.Popen(
                    cmd,
                    cwd=str(self._plugin_dir)
                )

                if self._server_process is None:
                    raise RuntimeError("进程启动失败，Popen返回None")

                logger.info(f"服务器进程已启动，PID: {self._server_process.pid}")

                # 检查服务器是否成功启动
                startup_success = False
                try:
                    startup_success = self._wait_for_server_startup()
                except Exception as e:
                    logger.error(f"等待服务器启动时出错: {str(e)}")
                    logger.error(traceback.format_exc())
                    startup_success = False

                if startup_success:
                    logger.info(
                        f"MCP服务器已启动 - {self._config['host']}:{self._config['port']}"
                    )

                    # 启动进程监控线程
                    if self._config["auto_restart"]:
                        self._start_monitor_thread()
                else:
                    # 终止进程
                    logger.error("服务器启动失败，尝试停止进程")
                    self._stop_server()
                    error_msg = "服务器启动超时或健康检查失败，请检查日志"
                    logger.error(error_msg)
                    raise Exception(error_msg)
            except Exception as e:
                logger.error(f"启动服务器进程时出错: {str(e)}")
                logger.error(traceback.format_exc())

                # 确保进程被终止
                if self._server_process is not None:
                    try:
                        self._stop_server()
                    except Exception as stop_error:
                        logger.error(f"停止失败的服务器进程时出错: {str(stop_error)}")

                # 清除进程引用
                self._server_process = None
                raise

        except Exception as e:
            logger.error(f"启动MCP服务器失败: {str(e)}")
            logger.error(traceback.format_exc())
            self._server_process = None

    def _stop_all_threads(self):
        """停止所有线程"""
        self._stop_monitor_thread()

    def _start_monitor_thread(self):
        """启动进程监控线程"""
        self._monitor_thread = threading.Thread(
            target=self._monitor_process_thread,
            args=(self._monitor_stop_event,),
            daemon=True
        )
        self._monitor_thread.start()
        logger.info("进程监控线程已启动，将自动重启意外终止的服务器")

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

        # 尝试使用 SO_REUSEADDR 选项
        s = socket.socket(family, sock_type)
        try:
            # 设置 SO_REUSEADDR 选项，允许重用处于 TIME_WAIT 状态的端口
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            logger.info("已设置 SO_REUSEADDR 选项，允许重用 TIME_WAIT 状态的端口")
            s.bind((host, port))
            s.close()
            logger.info(f"端口 {port}（{host}）未被占用或已成功重用")
            return
        except socket.error as e:
            logger.warning(f"端口 {port}（{host}）已被占用且无法重用，尝试处理: {e}")
            s.close()

        # 如果设置 SO_REUSEADDR 后仍然无法绑定，说明端口被其他进程占用
        # 尝试再次检查，确认是否真的被占用
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # 再次尝试设置 SO_REUSEADDR
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((host, port))
            s.close()
            logger.info(f"端口 {port} 未被占用或已成功重用")
            return  # 端口未被占用，直接返回
        except Exception as e:
            logger.warning(f"端口 {port} 已被占用且无法重用 {str(e)}，尝试处理")
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
            # 尝试导入psutil
            import psutil
            logger.info(f"使用psutil查找占用端口 {port} 的进程")

            # 查找占用端口的进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    for conn in proc.connections(kind='inet'):
                        # 检查是否是指定端口的连接
                        is_target_port = conn.laddr.port == port
                        is_bind_addr = (conn.laddr.ip == host or
                                        conn.laddr.ip == '0.0.0.0' or
                                        conn.laddr.ip == '::')

                        if is_target_port and is_bind_addr:
                            pid = proc.pid
                            logger.info(f"找到占用端口的进程 PID: {pid}")

                            # 检查是否为Python进程和MCP服务器
                            cmd_line = " ".join(
                                proc.cmdline() if proc.cmdline() else []
                            )
                            logger.info(f"进程命令行: {cmd_line}")

                            # 判断是否为MCP服务器进程
                            is_python = "python" in cmd_line.lower()
                            is_server = "server.py" in cmd_line

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
            gone, alive = psutil.wait_procs([proc], timeout=3)

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
        logger.info(f"等待端口 {port} 释放...")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((host, port))
                s.close()
                logger.info(f"端口 {port} 已释放，可以启动服务器")
                return True
            except socket.error:
                time.sleep(0.5)

        logger.error("等待端口释放超时")
        return False

    def _monitor_process_thread(self, stop_event):
        """监控服务器进程并在意外终止时重启"""
        try:
            logger.info("进程监控线程开始运行")

            while not stop_event.is_set():
                # 检查进程是否仍在运行
                has_process = self._server_process is not None
                terminated = (
                    has_process and self._server_process.poll() is not None)

                if has_process and terminated:
                    exitcode = self._server_process.poll()
                    logger.warning(f"服务器进程意外终止，返回码: {exitcode}，准备重启")

                    # 等待一段时间后重启
                    delay = self._config["restart_delay"]
                    logger.info(f"将在{delay}秒后重启服务器")

                    # 使用事件等待，以便能响应停止信号
                    if stop_event.wait(delay):
                        logger.info("收到停止信号，取消重启")
                        break

                    # 重启服务器
                    logger.info("正在重启MCP服务器...")
                    self._start_server()
                    logger.info("服务器重启完成")

                    # 如果启动失败，避免立即重试
                    no_process = self._server_process is None
                    failed = (
                        has_process and self._server_process.poll() is not None)

                    if no_process or failed:
                        logger.error("服务器重启失败，将暂停监控一段时间")
                        if stop_event.wait(60):  # 暂停监控60秒
                            break

                # 每隔5秒检查一次
                if stop_event.wait(5):
                    break

        except Exception as e:
            logger.error(f"进程监控线程发生异常: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            logger.info("进程监控线程已结束")

    def _stop_monitor_thread(self):
        """停止进程监控线程"""
        if self._monitor_stop_event and self._monitor_thread:
            logger.info("正在停止进程监控线程...")
            self._monitor_stop_event.set()

            # 等待线程结束，但设置超时以避免阻塞
            self._monitor_thread.join(timeout=3)
            if self._monitor_thread.is_alive():
                logger.warning("进程监控线程未能在3秒内正常停止")
            else:
                logger.info("进程监控线程已正常停止")

            self._monitor_thread = None
            self._monitor_stop_event = None

    def _wait_for_server_startup(self) -> bool:
        """等待服务器启动并进行健康检查"""
        start_time = time.time()
        check_count = 0
        max_time = self._config["max_startup_time"]
        interval = self._config["health_check_interval"]

        logger.info(f"等待服务器启动，最长等待{max_time}秒")

        while time.time() - start_time < max_time:
            # 检查进程是否存在且仍在运行
            if self._server_process is None:
                logger.error("服务器进程引用丢失，可能已意外终止")
                return False

            if self._server_process.poll() is not None:
                exitcode = self._server_process.poll()
                logger.error(f"服务器进程已退出，返回码: {exitcode}")
                # 清除进程引用，防止后续访问出错
                self._server_process = None
                return False

            # 尝试连接服务器
            try:
                check_count += 1
                url = self._health_check_url
                logger.info(f"健康检查 #{check_count}: 请求 {url}")

                # 在请求中加入token
                headers = {}
                auth_token = self._config.get("auth_token")
                if auth_token:
                    headers["Authorization"] = f"Bearer {auth_token}"

                response = requests.get(url, headers=headers, timeout=2)
                status = response.status_code
                logger.info(f"健康检查返回: HTTP {status}")

                # MCP端点会返回404或406状态码表示存在但未找到路由
                if status in [404, 406]:
                    logger.info("健康检查通过: 服务器正在运行")
                    return True
            except requests.RequestException as e:
                logger.info(f"健康检查失败: {str(e)}")

            # 等待一段时间后再次检查
            time.sleep(interval)

        logger.error(f"等待服务器启动超时 ({max_time})秒")
        return False

    def _stop_server(self):
        """停止MCP服务器进程"""
        # 先停止所有线程
        self._stop_all_threads()

        if self._server_process is not None:
            try:
                logger.info("正在停止MCP服务器进程...")

                # 检查进程是否已经终止
                if self._server_process.poll() is not None:
                    exitcode = self._server_process.poll()
                    logger.info(f"服务器进程已经终止，返回码: {exitcode}")
                    self._server_process = None
                    logger.info("MCP服务器进程已停止")
                    return

                try:
                    # 优雅地终止进程 (Linux)
                    self._server_process.send_signal(signal.SIGTERM)
                except Exception as e:
                    logger.error(f"发送SIGTERM信号失败: {str(e)}")
                    # 如果发送信号失败，尝试直接kill
                    try:
                        self._server_process.kill()
                        logger.info("已直接强制终止进程")
                    except Exception as kill_error:
                        logger.error(f"强制终止进程失败: {str(kill_error)}")

                    # 无论如何清除进程引用
                    self._server_process = None
                    logger.info("MCP服务器进程引用已清除")
                    return

                # 给进程一些时间来优雅地关闭
                process_exited = False
                for i in range(5):  # 等待最多5秒
                    try:
                        if self._server_process.poll() is not None:
                            exitcode = self._server_process.poll()
                            logger.info(f"服务器进程已优雅退出，返回码: {exitcode}")
                            process_exited = True
                            break
                        logger.info(f"等待服务器进程退出... ({i+1}/5)")
                        time.sleep(1)
                    except Exception as poll_error:
                        logger.error(f"检查进程状态失败: {str(poll_error)}")
                        process_exited = False
                        break

                # 如果进程仍在运行，强制终止
                if not process_exited:
                    try:
                        if self._server_process and self._server_process.poll() is None:
                            logger.info("优雅终止失败，强制终止进程")
                            self._server_process.kill()
                    except Exception as kill_error:
                        logger.error(f"强制终止进程失败: {str(kill_error)}")

                # 清除进程引用
                self._server_process = None
                logger.info("MCP服务器进程已停止")
            except Exception as e:
                logger.error(f"停止MCP服务器进程失败: {str(e)}")
                logger.error(traceback.format_exc())
                # 确保进程引用被清除
                self._server_process = None

    def _get_server_status(self) -> Dict[str, Any]:
        """获取服务器详细状态"""
        # 初始化状态信息
        status = {
            "running": False,
            "pid": None,
            "url": None,
            "health": False,
            "venv_path": str(self._venv_path) if self._venv_path else None,
            "python_bin": str(self._python_bin) if self._python_bin else None,
            "auth_token": self._mask_token(self._config.get("auth_token", "")),
            "requires_auth": True
        }

        # 设置服务URL
        port = int(self._config["port"])
        host = self._config["host"]
        status["url"] = f"http://{host}:{port}/mcp/"

        # 检查内部进程引用
        process_running = False
        if self._server_process and self._server_process.poll() is None:
            process_running = True
            status["running"] = True
            status["pid"] = self._server_process.pid
            logger.info(f"内部进程引用检查: 服务器进程正在运行，PID: {self._server_process.pid}")

        # 如果内部进程引用不存在，使用psutil查找进程
        if not process_running:
            try:
                import psutil

                # 方法1: 通过端口查找进程
                for conn in psutil.net_connections(kind='inet'):
                    if conn.laddr.port == port and conn.status == 'LISTEN' and conn.pid:
                        try:
                            proc = psutil.Process(conn.pid)
                            cmd_line = " ".join(proc.cmdline() or [])

                            # 判断是否为MCP服务器进程
                            if "python" in cmd_line.lower() and "server.py" in cmd_line:
                                status["running"] = True
                                status["pid"] = conn.pid
                                process_running = True
                                logger.info(
                                    f"通过端口 {port} 找到服务器进程，PID: {conn.pid}")
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                # 方法2: 如果方法1未找到，通过进程名和命令行查找
                if not process_running:
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            cmd_line = " ".join(proc.cmdline() or [])
                            if "python" in cmd_line.lower() and "server.py" in cmd_line and f"--port {port}" in cmd_line:
                                status["running"] = True
                                status["pid"] = proc.pid
                                process_running = True
                                logger.info(f"通过命令行找到服务器进程，PID: {proc.pid}")
                                break
                        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                            continue
            except ImportError:
                logger.warning("psutil模块未安装，无法查找进程")
            except Exception as e:
                logger.error(f"使用psutil查找进程失败: {str(e)}")

        # 进行健康检查
        try:
            # 在请求中加入token
            headers = {}
            auth_token = self._config.get("auth_token")
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            # 发送健康检查请求
            response = requests.get(
                self._health_check_url,
                headers=headers,
                timeout=3
            )

            # MCP端点通常返回404或406
            health_ok = response.status_code in [404, 406]
            status["health"] = health_ok

            # 如果健康检查通过，服务器一定在运行
            if health_ok:
                status["running"] = True
                logger.info(f"健康检查成功: 服务器运行中 (HTTP {response.status_code})")
        except requests.RequestException as e:
            logger.debug(f"健康检查请求失败: {str(e)}")

            # 如果进程正在运行，我们仍然认为服务器是运行的
            if process_running:
                logger.info("虽然健康检查请求失败，但进程正在运行，标记为运行状态")

        # 最终状态日志
        logger.info(
            "服务器状态: running=%s, health=%s, pid=%s",
            status['running'], status['health'], status['pid']
        )
        return status

    def _try_recover_process_reference(self, port: int) -> bool:
        """尝试恢复进程引用"""
        try:
            # 尝试导入psutil
            import psutil
            logger.info(f"尝试恢复端口 {port} 的进程引用")

            # 获取所有网络连接
            connections = psutil.net_connections(kind='inet')

            # 查找占用指定端口的连接
            target_conns = [
                conn for conn in connections
                if (hasattr(conn, 'laddr') and
                    conn.laddr.port == port and
                    conn.status == 'LISTEN')
            ]

            if not target_conns:
                logger.info(f"未找到占用端口 {port} 的连接")
                return False

            # 查找对应的进程
            for conn in target_conns:
                if not conn.pid:
                    continue

                try:
                    proc = psutil.Process(conn.pid)
                    pid = proc.pid
                    logger.info(f"找到占用端口的进程 PID: {pid}")

                    # 检查是否为Python进程和MCP服务器
                    cmd_line = " ".join(proc.cmdline() or [])
                    logger.info(f"进程命令行: {cmd_line}")

                    # 判断是否为MCP服务器进程
                    is_python = "python" in cmd_line.lower()
                    is_server = "server.py" in cmd_line

                    if is_python and is_server:
                        logger.info(f"确认为MCP服务器进程: PID={pid}")
                        # 这里不能直接恢复进程引用，因为需要subprocess.Popen对象
                        # 但我们可以记录这个信息，供后续使用
                        return True
                except (psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess):
                    continue

            logger.info("未找到符合条件的MCP服务器进程")
            return False
        except ImportError:
            logger.warning("psutil模块未安装，无法恢复进程引用")
            return False
        except Exception as e:
            logger.error(f"恢复进程引用时出错: {str(e)}")
            logger.error(traceback.format_exc())
            return False

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
            if self._server_process and self._server_process.poll() is None:
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
        """获取服务器状态"""
        # 使用_get_server_status方法获取完整状态，保持一致性
        status = self._get_server_status()
        # 如果服务器正在运行，返回True
        if status["running"]:
            return True
        # 否则返回插件启用状态
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
            # 保存当前启用状态，用于检测变化
            previous_enable = self._enable

            # 更新配置
            new_enable = config_payload.get('enable', self._enable)
            if 'config' in config_payload:
                self._config.update(config_payload['config'])

            # 准备保存的配置
            config_to_save = {
                "enable": new_enable,
                "config": self._config
            }

            # 保存配置
            self.update_config(config_to_save)

            # 检测启用状态变化
            enable_changed = previous_enable != new_enable
            self._enable = new_enable

            # 根据启用状态变化处理服务器进程
            if enable_changed:
                if new_enable:
                    # 从禁用变为启用，尝试启动服务器
                    logger.info("插件从禁用变为启用，尝试启动服务器")

                    # 检查用户名和密码是否已配置
                    username = self._config.get("mp_username", "")
                    password = self._config.get("mp_password", "")

                    if not username or not password:
                        logger.error("未配置 MoviePilot 用户名或密码，无法启动服务器")
                        return {
                            "message": "配置已保存，但未配置 MoviePilot 用户名或密码，无法启动服务器",
                            "saved_config": self._get_config()
                        }

                    # 尝试获取 access_token
                    access_token = self._get_moviepilot_access_token()
                    if not access_token:
                        logger.error("无法获取 MoviePilot 的 access token，无法启动服务器")
                        return {
                            "message": "配置已保存，但无法获取 MoviePilot 的 access token，无法启动服务器",
                            "saved_config": self._get_config()
                        }

                    # 保存 access_token 到配置
                    self._config["access_token"] = access_token
                    logger.info("已获取 MoviePilot 的 access token，将用于 API 请求")

                    # 启动服务器
                    self._start_server()
                    logger.info("服务器已启动")

                    return {
                        "message": "配置已保存，服务器已启动",
                        "saved_config": self._get_config()
                    }
                else:
                    # 从启用变为禁用，停止服务器
                    logger.info("插件从启用变为禁用，停止服务器")
                    self._stop_server()
                    logger.info("服务器已停止")

                    return {
                        "message": "配置已保存，服务器已停止",
                        "saved_config": self._get_config()
                    }

            # 如果启用状态没有变化，只返回保存成功的消息
            logger.info(f"{self.plugin_name}: 配置已保存")

            # 返回最终状态
            return {
                "message": "配置已成功保存",
                "saved_config": self._get_config()
            }

        except Exception as e:
            logger.error(f"{self.plugin_name}: 保存配置时发生错误: {e}", exc_info=True)
            return {
                "message": f"保存配置失败: {e}",
                "error": True,
                "saved_config": self._get_config()
            }

    def _restart_server(self) -> Dict[str, Any]:
        """API Endpoint: 重启服务器"""
        try:
            logger.info("正在执行服务器重启...")

            # 先停止服务器
            logger.info("正在停止服务器进程...")
            self._stop_server()
            logger.info("服务器进程已停止，等待端口释放...")
            time.sleep(2)  # 增加等待时间，确保端口完全释放

            # 检查用户名和密码是否已配置
            username = self._config.get("mp_username", "")
            password = self._config.get("mp_password", "")

            if not username or not password:
                logger.error("未配置 MoviePilot 用户名或密码，无法重启服务器")
                return {
                    "message": "服务器已停止，但未配置 MoviePilot 用户名或密码，无法重新启动",
                    "error": True,
                    "server_status": self._get_server_status()
                }

            # 尝试获取 access_token
            access_token = self._get_moviepilot_access_token()
            if not access_token:
                logger.error("无法获取 MoviePilot 的 access token，无法重启服务器")
                return {
                    "message": "服务器已停止，但无法获取 MoviePilot 的 access token，无法重新启动",
                    "error": True,
                    "server_status": self._get_server_status()
                }

            # 保存 access_token 到配置
            self._config["access_token"] = access_token
            logger.info("已获取 MoviePilot 的 access token，将用于 API 请求")

            # 启动服务器
            logger.info("正在重新启动服务器进程...")
            self._start_server()

            # 等待服务器启动
            time.sleep(3)

            # 获取最新状态
            current_status = self._get_server_status()

            if current_status["running"]:
                logger.info("服务器已成功重启")
                return {
                    "message": "服务器已成功重启",
                    "server_status": current_status
                }
            else:
                logger.warning("服务器重启后状态检查失败，可能需要手动刷新状态")
                return {
                    "message": "服务器重启过程完成，但状态检查未通过，请手动刷新状态",
                    "server_status": current_status
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
            }
        ]

    def _start_server_api(self) -> Dict[str, Any]:
        """API Endpoint: 启动服务器"""
        try:
            # 检查服务器是否已经在运行
            status = self._get_server_status()
            if status["running"]:
                return {
                    "message": "服务器已经在运行中",
                    "server_status": status
                }

            # 检查用户名和密码是否已配置
            username = self._config.get("mp_username", "")
            password = self._config.get("mp_password", "")

            if not username or not password:
                logger.error("未配置 MoviePilot 用户名或密码，无法启动服务器")
                logger.error("请在插件配置页面填写 MoviePilot 用户名和密码")
                return {
                    "message": "未配置 MoviePilot 用户名或密码，无法启动服务器",
                    "error": True,
                    "server_status": self._get_server_status()
                }

            # 尝试获取 access_token
            access_token = self._get_moviepilot_access_token()
            if not access_token:
                logger.error("无法获取 MoviePilot 的 access token，无法启动服务器")
                logger.error("请检查 MoviePilot 用户名和密码是否正确")
                return {
                    "message": "无法获取 MoviePilot 的 access token，无法启动服务器",
                    "error": True,
                    "server_status": self._get_server_status()
                }

            # 保存 access_token 到配置
            self._config["access_token"] = access_token
            logger.info("已获取 MoviePilot 的 access token，将用于 API 请求")

            # 启动服务器
            self._start_server()

            # 等待服务器完全启动
            time.sleep(3)

            # 获取最新状态
            current_status = self._get_server_status()

            # 记录启动结果
            if current_status["running"]:
                logger.info(f"服务器已成功启动，PID: {current_status['pid']}")
                return {
                    "message": "服务器已成功启动",
                    "server_status": current_status
                }
            else:
                logger.warning("服务器启动后状态检查失败，可能需要手动刷新状态")
                return {
                    "message": "服务器已启动，但状态检查未通过，请手动刷新状态",
                    "server_status": current_status
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
            status = self._get_server_status()
            if not status["running"]:
                return {
                    "message": "服务器已经停止",
                    "server_status": status
                }

            # 停止服务器
            self._stop_server()

            # 等待服务器完全停止
            time.sleep(2)

            # 获取最新状态
            current_status = self._get_server_status()

            # 记录停止结果
            if not current_status["running"]:
                logger.info("服务器已成功停止")
                return {
                    "message": "服务器已成功停止",
                    "server_status": current_status
                }
            else:
                logger.warning("服务器停止后状态检查失败，可能需要手动刷新状态")
                return {
                    "message": "服务器停止失败，请手动刷新状态",
                    "server_status": current_status
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
                "message": "获取服务器状态成功!!!"
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
            from app.helper.downloader import DownloaderHelper
            from app.schemas import ServiceInfo

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
        """停止服务"""
        self._stop_server()

    def get_dashboard_meta(self) -> Optional[List[Dict[str, str]]]:
        """获取插件仪表盘元信息"""
        return [
            {
                "key": "dashboard1",
                "name": "MCP Server"
            }
        ]

    def get_dashboard(
        self, _key: str, **_kwargs
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """
        获取插件仪表盘页面

        参数:
            _key: 仪表盘键名，未使用
            _kwargs: 额外参数，未使用
        """
        return {
            "cols": 12,
            "md": 6
        }, {
            "refresh": 10,
            "border": True,
            "title": "MCP Server",
            "subtitle": "启动MCP服务器实现大模型操作MoviePilot"
        }, None


if __name__ == "__main__":
    plugin = MCPServer()
    config = {
        "enable": True,
        "config": {
            "host": "127.0.0.1",
            "port": 3111
        }
    }
    plugin.init_plugin(config)
