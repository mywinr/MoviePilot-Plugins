import subprocess
import time
import signal
import requests
import venv
import traceback
import threading
import socket
import os
from typing import List, Tuple, Dict, Any, Optional
from pathlib import Path

from app.log import logger
from app.plugins import _PluginBase


# --- Plugin Class ---


class MCPServer(_PluginBase):
    # 插件名称
    plugin_name = "MCP Server"
    # 插件描述
    plugin_desc = "启动MCP服务器实现大模型操作MoviePilot"
    # 插件图标
    plugin_icon = "https://avatars.githubusercontent.com/u/182288589?s=200&v=4"
    # 插件版本
    plugin_version = "1.2"
    # 插件作者
    plugin_author = "DzAvril"
    # 作者主页
    author_url = "https://github.com/DzAvril"
    # 插件配置项ID前缀
    plugin_config_prefix = "mcpserver_"
    # 加载顺序
    plugin_order = 50
    # 可使用的用户级别
    auth_level = 1

    _enable = False
    _server_process = None
    _log_thread = None
    _log_stop_event = None
    _monitor_thread = None
    _monitor_stop_event = None
    _config = {
        "host": "0.0.0.0",  # 使用127.0.0.1用于同一容器内通信
        "port": 3111,
        "log_level": "INFO",
        "health_check_interval": 3,  # 健康检查间隔(秒)
        "max_startup_time": 60,      # 最大启动等待时间(秒)
        "venv_dir": "venv",          # 虚拟环境目录名
        "dependencies": ["mcp[cli]"],  # 需要安装的依赖
        "auto_restart": True,        # 是否自动重启意外终止的服务器
        "restart_delay": 5           # 重启前等待时间(秒)
    }

    # 虚拟环境相关路径
    _venv_path = None
    _python_bin = None
    _health_check_url = None
    _server_script_path = None

    def init_plugin(self, config: dict = None):
        if config:
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
            host = self._config["host"]
            port = self._config["port"]
            self._health_check_url = f"http://{host}:{port}/mcp"

            if self._enable:
                # 确保虚拟环境存在
                if not self._ensure_venv():
                    logger.error("无法创建或验证虚拟环境，插件无法启动")
                    self._enable = False
                    return

                self._start_server()
            else:
                self._stop_server()

    def _ensure_venv(self) -> bool:
        """确保虚拟环境存在并安装了所需依赖"""
        try:
            # 检查虚拟环境是否存在
            if not self._python_bin.exists():
                logger.info(f"正在创建虚拟环境: {self._venv_path}")

                # 创建虚拟环境
                venv.create(self._venv_path, with_pip=True)

                if not self._python_bin.exists():
                    logger.error(
                        f"创建虚拟环境失败，找不到Python解释器: {self._python_bin}"
                    )
                    return False

                # 安装依赖
                deps = self._config["dependencies"]
                deps_str = " ".join([f"'{dep}'" for dep in deps])
                logger.info(f"正在安装依赖: {deps_str}")

                # 构建安装命令
                install_cmd = [
                    str(self._python_bin),
                    "-m",
                    "pip",
                    "install",
                    "--upgrade",
                    "-i https://mirrors.aliyun.com/pypi/simple/"
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

                logger.info("虚拟环境创建并安装依赖成功")
            else:
                logger.info(f"虚拟环境已存在: {self._venv_path}")

            return True

        except Exception as e:
            logger.error(f"设置虚拟环境失败: {str(e)}")
            logger.error(traceback.format_exc())
            return False

    def _start_server(self):
        """启动MCP服务器作为独立进程"""
        if self._server_process is None or \
                self._server_process.poll() is not None:
            try:
                logger.info("正在启动MCP服务器作为独立进程...")

                # 先检查端口是否被占用
                self._check_and_clear_port()

                # 获取启动器脚本路径
                launcher_script = self._plugin_dir / "server.py"
                if not launcher_script.exists():
                    raise FileNotFoundError(
                        f"启动器脚本不存在: {launcher_script}"
                    )

                # 确保脚本有执行权限
                try:
                    launcher_script.chmod(0o755)
                except Exception as e:
                    logger.warning(f"无法设置脚本执行权限: {e}")

                # 构建启动命令
                cmd = [
                    str(self._python_bin),
                    str(launcher_script),
                    "--host", self._config["host"],
                    "--port", str(self._config["port"]),
                    "--log-level", self._config["log_level"]
                ]

                logger.info(f"启动命令: {' '.join(cmd)}")

                # 停止现有的日志线程(如果有)
                self._stop_log_thread()

                # 停止现有的监控线程(如果有)
                self._stop_monitor_thread()

                # 创建新的停止事件
                self._log_stop_event = threading.Event()
                self._monitor_stop_event = threading.Event()

                # 启动进程 - 使用pipe获取输出
                self._server_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # 行缓冲
                    cwd=str(self._plugin_dir)
                )

                logger.info(f"服务器进程已启动，PID: {self._server_process.pid}")

                # 启动日志读取线程
                self._log_thread = threading.Thread(
                    target=self._log_reader_thread,
                    args=(self._server_process, self._log_stop_event),
                    daemon=True
                )
                self._log_thread.start()
                logger.info("日志读取线程已启动")

                # 检查服务器是否成功启动
                max_time = self._config['max_startup_time']
                logger.info("等待服务器启动，最长等待{}秒".format(max_time))
                startup_successful = self._wait_for_server_startup()

                if startup_successful:
                    host = self._config['host']
                    port = self._config['port']
                    logger.info(f"MCP服务器已启动 - {host}:{port}")

                    # 启动进程监控线程
                    if self._config["auto_restart"]:
                        self._monitor_thread = threading.Thread(
                            target=self._monitor_process_thread,
                            args=(self._monitor_stop_event,),
                            daemon=True
                        )
                        self._monitor_thread.start()
                        logger.info("进程监控线程已启动，将自动重启意外终止的服务器")
                else:
                    # 终止进程
                    self._stop_server()
                    error_msg = "服务器启动超时或健康检查失败，请检查日志"
                    logger.error(error_msg)
                    raise Exception(error_msg)

            except Exception as e:
                logger.error(f"启动MCP服务器失败: {str(e)}")
                logger.error(traceback.format_exc())
                self._enable = False
                self._server_process = None

    def _check_and_clear_port(self):
        """检查端口是否被占用，如果被占用则尝试停止占用进程"""
        port = self._config["port"]
        host = self._config["host"]

        # 检查端口是否被占用
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind((host, port))
            s.close()
            logger.info("端口 {} 未被占用".format(port))
            return  # 端口未被占用，直接返回
        except socket.error:
            logger.warning("端口 {} 已被占用，尝试处理".format(port))
            s.close()

        # 端口被占用，尝试终止占用进程
        try:
            # 尝试终止占用进程
            if self._try_kill_process_with_cmd():
                # 成功终止进程，等待端口释放
                if self._wait_for_port_release(port, host):
                    return

            # 如果无法释放端口，报告错误
            logger.error("无法清理端口，请尝试以下操作:")
            logger.error("1. 检查是否有其他程序占用了端口 {}".format(port))
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
                                    "占用端口 {} 的进程: PID={}, 名称={}, 命令行={}".format(
                                        port, conn.pid, proc.name(), " ".join(proc.cmdline() or [])
                                    )
                                )
                            except psutil.NoSuchProcess:
                                logger.error(
                                    "占用端口 {} 的进程: PID={}（进程不存在）".format(port, conn.pid))
                        else:
                            logger.error(
                                "占用端口 {} 的连接信息: {}".format(port, conn))
            except ImportError:
                pass

            raise RuntimeError(
                "端口 {} 被占用且无法清理，请手动终止占用进程或修改端口配置"
                .format(port)
            )

        except Exception as e:
            logger.error("检查和清理端口时出错: {}".format(str(e)))
            logger.error(traceback.format_exc())
            raise RuntimeError("无法启动MCP服务器: {}".format(str(e)))

    def _try_kill_process_with_cmd(self) -> bool:
        """尝试查找并终止占用端口的进程，使用psutil库"""
        port = self._config["port"]
        host = self._config["host"]

        try:
            # 尝试导入psutil
            import psutil
            logger.info("使用psutil查找占用端口 {} 的进程".format(port))

            # 查找占用端口的进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == port and (conn.laddr.ip == host
                                                        or conn.laddr.ip == '0.0.0.0'
                                                        or conn.laddr.ip == '::'):
                            pid = proc.pid
                            logger.info("找到占用端口的进程 PID: {}".format(pid))

                            # 检查是否为Python进程和MCP服务器
                            cmd_line = " ".join(
                                proc.cmdline() if proc.cmdline() else [])
                            logger.info("进程命令行: {}".format(cmd_line))

                            # 判断是否为MCP服务器进程
                            is_python = "python" in cmd_line.lower()
                            is_server = "server.py" in cmd_line

                            if is_python and is_server:
                                logger.info("确认是MCP服务器进程，尝试终止")
                                proc.terminate()
                                gone, alive = psutil.wait_procs(
                                    [proc], timeout=3)
                                if proc in alive:
                                    logger.warning("进程未响应终止信号，尝试强制终止")
                                    proc.kill()
                                logger.info("成功终止占用端口的进程")
                                return True
                            else:
                                logger.warning("占用端口的不是MCP服务器进程，不自动终止")
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            logger.warning("未找到占用端口 {} 的MCP服务器进程".format(port))
            return False

        except ImportError:
            logger.error("psutil模块未安装，无法查找和终止占用端口的进程")
            return False
        except Exception as e:
            logger.error("使用psutil查找和终止进程时出错: {}".format(str(e)))
            return False

    def _wait_for_port_release(self, port, host, timeout=10) -> bool:
        """等待端口释放"""
        logger.info("等待端口 {} 释放...".format(port))
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.bind((host, port))
                s.close()
                logger.info("端口 {} 已释放，可以启动服务器".format(port))
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
                terminated = (has_process and
                              self._server_process.poll() is not None)

                if has_process and terminated:
                    exitcode = self._server_process.poll()
                    logger.warning(
                        "服务器进程意外终止，返回码: {}，准备重启".format(exitcode)
                    )

                    # 等待一段时间后重启
                    delay = self._config["restart_delay"]
                    logger.info("将在{}秒后重启服务器".format(delay))

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
                    failed = (has_process and
                              self._server_process.poll() is not None)

                    if no_process or failed:
                        logger.error("服务器重启失败，将暂停监控一段时间")
                        if stop_event.wait(60):  # 暂停监控60秒
                            break

                # 每隔5秒检查一次
                if stop_event.wait(5):
                    break

        except Exception as e:
            logger.error("进程监控线程发生异常: {}".format(str(e)))
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

    def _log_reader_thread(self, process, stop_event):
        """持续读取进程输出的线程函数"""
        try:
            logger.info("日志读取线程开始运行")

            # 同时读取stdout和stderr
            while not stop_event.is_set() and process.poll() is None:
                # 检查stdout是否有数据
                stdout_line = process.stdout.readline()
                if stdout_line:
                    # 记录标准输出
                    logger.info("MCP服务器: {}".format(stdout_line.rstrip()))

                # 检查stderr是否有数据
                stderr_line = process.stderr.readline()
                if stderr_line:
                    # 记录错误输出
                    logger.error("MCP服务器错误: {}".format(stderr_line.rstrip()))

                # 如果两个流都没有读到数据，短暂休眠避免CPU占用
                if not stdout_line and not stderr_line:
                    time.sleep(0.1)

            # 进程已结束，尝试读取剩余输出
            remaining_stdout, remaining_stderr = process.communicate()

            if remaining_stdout:
                for line in remaining_stdout.splitlines():
                    if line:
                        logger.info("MCP服务器(结束): {}".format(line))

            if remaining_stderr:
                for line in remaining_stderr.splitlines():
                    if line:
                        logger.error("MCP服务器错误(结束): {}".format(line))

            # 记录进程退出状态
            exitcode = process.poll()
            logger.info("MCP服务器进程已退出，返回码: {}".format(exitcode))

        except Exception as e:
            logger.error("日志读取线程发生异常: {}".format(str(e)))
            logger.error(traceback.format_exc())
        finally:
            logger.info("日志读取线程已结束")

    def _stop_log_thread(self):
        """停止日志读取线程"""
        if self._log_stop_event and self._log_thread:
            logger.info("正在停止日志读取线程...")
            self._log_stop_event.set()

            # 等待线程结束，但设置超时以避免阻塞
            self._log_thread.join(timeout=3)
            if self._log_thread.is_alive():
                logger.warning("日志读取线程未能在3秒内正常停止")
            else:
                logger.info("日志读取线程已正常停止")

            self._log_thread = None
            self._log_stop_event = None

    def _wait_for_server_startup(self) -> bool:
        """等待服务器启动并进行健康检查"""
        start_time = time.time()
        check_count = 0

        while time.time() - start_time < self._config["max_startup_time"]:
            # 检查进程是否仍在运行
            if self._server_process.poll() is not None:
                exitcode = self._server_process.poll()
                logger.error(f"服务器进程已退出，返回码: {exitcode}")
                return False

            # 尝试连接服务器
            try:
                check_count += 1
                url = self._health_check_url
                logger.info("健康检查 #{}: 请求 {}".format(check_count, url))

                response = requests.get(url, timeout=2)
                logger.info("健康检查返回: HTTP {}".format(response.status_code))

                # MCP端点会返回404或406状态码表示存在但未找到路由
                if response.status_code in [404, 406]:
                    logger.info("健康检查通过: 服务器正在运行")
                    return True
            except requests.RequestException as e:
                logger.info("健康检查失败: {}".format(str(e)))

            # 等待一段时间后再次检查
            time.sleep(self._config["health_check_interval"])

        max_time = self._config["max_startup_time"]
        logger.error("等待服务器启动超时 ({})秒".format(max_time))
        return False

    def _stop_server(self):
        """停止MCP服务器进程"""
        # 先停止监控线程
        self._stop_monitor_thread()

        # 然后停止日志读取线程
        self._stop_log_thread()

        if self._server_process is not None:
            try:
                logger.info("正在停止MCP服务器进程...")

                # 优雅地终止进程 (Linux)
                self._server_process.send_signal(signal.SIGTERM)

                # 给进程一些时间来优雅地关闭
                for i in range(5):  # 等待最多5秒
                    if self._server_process.poll() is not None:
                        exitcode = self._server_process.poll()
                        logger.info(f"服务器进程已优雅退出，返回码: {exitcode}")
                        break
                    logger.info(f"等待服务器进程退出... ({i+1}/5)")
                    time.sleep(1)

                # 如果进程仍在运行，强制终止
                if self._server_process.poll() is None:
                    logger.info("优雅终止失败，强制终止进程")
                    self._server_process.kill()

                self._server_process = None
                logger.info("MCP服务器进程已停止")
            except Exception as e:
                logger.error(f"停止MCP服务器进程失败: {str(e)}")
                logger.error(traceback.format_exc())

    def _get_server_status(self) -> Dict[str, Any]:
        """获取服务器详细状态"""
        status = {
            "running": False,
            "pid": None,
            "url": None,
            "health": False,
            "venv_path": str(self._venv_path) if self._venv_path else None,
            "python_bin": str(self._python_bin) if self._python_bin else None
        }

        if self._server_process and self._server_process.poll() is None:
            status["running"] = True
            status["pid"] = self._server_process.pid
            host = self._config['host']
            port = self._config['port']
            status["url"] = f"http://{host}:{port}/mcp"

            # 尝试进行健康检查
            try:
                response = requests.get(self._health_check_url, timeout=2)
                # MCP端点通常返回404
                status["health"] = response.status_code == 404
            except requests.RequestException:
                status["health"] = False

        return status

    def get_state(self) -> bool:
        """获取服务器状态"""
        # 如果进程存在且正在运行，返回True
        if self._server_process and self._server_process.poll() is None:
            return True
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
            # 更新配置
            self._enable = config_payload.get('enable', self._enable)
            if 'config' in config_payload:
                self._config.update(config_payload['config'])

            # 准备保存的配置
            config_to_save = {
                "enable": self._enable,
                "config": self._config
            }

            # 保存配置
            self.update_config(config_to_save)

            # 重新初始化插件
            self.init_plugin(self.get_config())

            logger.info(f"{self.plugin_name}: 配置已保存并重新初始化")

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
            self._stop_server()
            time.sleep(1)  # 等待端口释放
            self._start_server()
            return {
                "message": "服务器已重启",
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
            }
        ]

    # --- V2 Vue Interface Method ---
    @staticmethod
    def get_render_mode() -> Tuple[str, Optional[str]]:
        """Declare Vue rendering mode and assets path."""
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
        self, key: str, **kwargs
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any], Optional[List[dict]]]]:
        """获取插件仪表盘页面"""
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
