import logging
import os
import time
from typing import Dict, Any, Optional
import mcp.types as types

from ..base import BaseTool

logger = logging.getLogger(__name__)


class ProcessMonitorTool(BaseTool):
    """进程监控工具，用于获取MCP服务器进程的资源占用情况"""

    def __init__(self, token_manager=None):
        super().__init__(token_manager)

    async def execute(self, tool_name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """执行工具逻辑"""
        if tool_name == "get-process-stats":
            return await self._get_process_stats(arguments)
        elif tool_name == "get-system-stats":
            return await self._get_system_stats(arguments)
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _get_process_stats(self, arguments: dict) -> list[types.TextContent]:
        """
        获取指定进程的资源占用统计
        参数:
            - pid: 进程ID(可选)，如果不提供则尝试自动查找MCP服务器进程
        """
        pid = arguments.get("pid")

        try:
            # 如果没有提供PID，尝试自动查找MCP服务器进程
            if not pid:
                pid = await self._find_mcp_server_pid()
                if not pid:
                    return [
                        types.TextContent(
                            type="text",
                            text="错误：未找到MCP服务器进程，请手动提供进程ID"
                        )
                    ]

            # 获取进程统计信息
            stats = await self._get_process_resource_stats(pid)
            if not stats:
                return [
                    types.TextContent(
                        type="text",
                        text=f"错误：无法获取进程 {pid} 的统计信息，进程可能不存在或无权限访问"
                    )
                ]

            # 格式化输出
            result_text = f"进程资源占用统计 (PID: {pid}):\n\n"
            result_text += f"进程名称: {stats.get('name', '未知')}\n"
            result_text += f"进程状态: {stats.get('status', '未知')}\n"
            result_text += f"CPU使用率: {stats.get('cpu_percent', 0):.2f}%\n"
            result_text += f"内存使用: {stats.get('memory_mb', 0):.2f} MB\n"
            result_text += f"内存占用率: {stats.get('memory_percent', 0):.2f}%\n"
            result_text += f"虚拟内存: {stats.get('virtual_memory_mb', 0):.2f} MB\n"
            result_text += f"创建时间: {stats.get('create_time', '未知')}\n"
            result_text += f"运行时长: {stats.get('runtime', '未知')}\n"
            result_text += f"线程数: {stats.get('num_threads', 0)}\n"
            result_text += f"文件描述符: {stats.get('num_fds', 0)}\n"

            if stats.get('connections'):
                result_text += f"网络连接数: {len(stats['connections'])}\n"
                for conn in stats['connections'][:3]:  # 只显示前3个连接
                    result_text += f"  - {conn.get('laddr', '')} -> {conn.get('raddr', '')} ({conn.get('status', '')})\n"
                if len(stats['connections']) > 3:
                    result_text += f"  ... 还有 {len(stats['connections']) - 3} 个连接\n"

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"获取进程统计信息时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"获取进程统计信息时出错: {str(e)}"
                )
            ]

    async def _get_system_stats(self, arguments: dict) -> list[types.TextContent]:
        """
        获取系统资源占用统计
        参数:
            - _: 工具参数（当前未使用）
        """
        try:
            stats = await self._get_system_resource_stats()
            if not stats:
                return [
                    types.TextContent(
                        type="text",
                        text="错误：无法获取系统统计信息"
                    )
                ]

            result_text = "系统资源占用统计:\n\n"

            # CPU信息
            cpu_info = stats.get('cpu', {})
            result_text += f"CPU使用率: {cpu_info.get('percent', 0):.2f}%\n"
            result_text += f"CPU核心数: {cpu_info.get('count', 0)}\n"
            result_text += f"负载平均值: {cpu_info.get('load_avg', 'N/A')}\n\n"

            # 内存信息
            memory_info = stats.get('memory', {})
            result_text += f"内存总量: {memory_info.get('total_gb', 0):.2f} GB\n"
            result_text += f"内存使用: {memory_info.get('used_gb', 0):.2f} GB\n"
            result_text += f"内存可用: {memory_info.get('available_gb', 0):.2f} GB\n"
            result_text += f"内存使用率: {memory_info.get('percent', 0):.2f}%\n\n"

            # 磁盘信息
            disk_info = stats.get('disk', {})
            result_text += f"磁盘总量: {disk_info.get('total_gb', 0):.2f} GB\n"
            result_text += f"磁盘使用: {disk_info.get('used_gb', 0):.2f} GB\n"
            result_text += f"磁盘可用: {disk_info.get('free_gb', 0):.2f} GB\n"
            result_text += f"磁盘使用率: {disk_info.get('percent', 0):.2f}%\n\n"

            # 网络信息
            network_info = stats.get('network', {})
            result_text += f"网络发送: {network_info.get('bytes_sent_mb', 0):.2f} MB\n"
            result_text += f"网络接收: {network_info.get('bytes_recv_mb', 0):.2f} MB\n"

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"获取系统统计信息时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"获取系统统计信息时出错: {str(e)}"
                )
            ]

    async def _find_mcp_server_pid(self) -> Optional[int]:
        """自动查找MCP服务器进程ID"""
        try:
            import psutil

            # 方法1: 通过端口查找（假设默认端口3111）
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == 3111 and conn.status == 'LISTEN' and conn.pid:
                    try:
                        proc = psutil.Process(conn.pid)
                        cmd_line = " ".join(proc.cmdline() or [])

                        # 判断是否为MCP服务器进程
                        if "python" in cmd_line.lower() and "server.py" in cmd_line:
                            logger.info(f"通过端口找到MCP服务器进程: PID={conn.pid}")
                            return conn.pid
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue

            # 方法2: 通过进程名和命令行查找
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmd_line = " ".join(proc.cmdline() or [])
                    if ("python" in cmd_line.lower() and
                        "server.py" in cmd_line and
                        "mcp" in cmd_line.lower()):
                        logger.info(f"通过命令行找到MCP服务器进程: PID={proc.pid}")
                        return proc.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            return None

        except ImportError:
            logger.error("psutil模块未安装，无法自动查找进程")
            return None
        except Exception as e:
            logger.error(f"查找MCP服务器进程时出错: {str(e)}")
            return None

    async def _get_process_resource_stats(self, pid: int) -> Optional[Dict[str, Any]]:
        """获取指定进程的资源统计信息"""
        try:
            import psutil

            proc = psutil.Process(pid)

            # 获取进程信息
            with proc.oneshot():
                # 基本信息
                name = proc.name()
                status = proc.status()
                create_time_timestamp = proc.create_time()  # 保持原始时间戳

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

                # 网络连接 - 兼容不同版本的psutil
                try:
                    connections = []
                    # 尝试使用新版本的方法
                    try:
                        proc_connections = proc.net_connections()
                    except AttributeError:
                        # 如果不存在，使用旧版本的方法
                        proc_connections = proc.connections()

                    for conn in proc_connections:
                        connections.append({
                            'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else "",
                            'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else "",
                            'status': conn.status
                        })
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    connections = []

                # 计算运行时长
                runtime_seconds = time.time() - create_time_timestamp
                runtime_hours = runtime_seconds / 3600
                if runtime_hours < 1:
                    runtime = f"{runtime_seconds / 60:.1f} 分钟"
                elif runtime_hours < 24:
                    runtime = f"{runtime_hours:.1f} 小时"
                else:
                    runtime = f"{runtime_hours / 24:.1f} 天"

                return {
                    'name': name,
                    'status': status,
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

        except ImportError:
            logger.error("psutil模块未安装")
            return None
        except psutil.NoSuchProcess:
            logger.error(f"进程 {pid} 不存在")
            return None
        except psutil.AccessDenied:
            logger.error(f"无权限访问进程 {pid}")
            return None
        except Exception as e:
            logger.error(f"获取进程 {pid} 信息时出错: {str(e)}")
            return None

    async def _get_system_resource_stats(self) -> Optional[Dict[str, Any]]:
        """获取系统资源统计信息"""
        try:
            import psutil

            # CPU信息
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            try:
                load_avg = os.getloadavg()
                load_avg_str = f"{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}"
            except (AttributeError, OSError):
                load_avg_str = "N/A"

            # 内存信息
            memory = psutil.virtual_memory()

            # 磁盘信息
            disk = psutil.disk_usage('/')

            # 网络信息
            network = psutil.net_io_counters()

            return {
                'cpu': {
                    'percent': cpu_percent,
                    'count': cpu_count,
                    'load_avg': load_avg_str
                },
                'memory': {
                    'total_gb': memory.total / 1024 / 1024 / 1024,
                    'used_gb': memory.used / 1024 / 1024 / 1024,
                    'available_gb': memory.available / 1024 / 1024 / 1024,
                    'percent': memory.percent
                },
                'disk': {
                    'total_gb': disk.total / 1024 / 1024 / 1024,
                    'used_gb': disk.used / 1024 / 1024 / 1024,
                    'free_gb': disk.free / 1024 / 1024 / 1024,
                    'percent': (disk.used / disk.total) * 100
                },
                'network': {
                    'bytes_sent_mb': network.bytes_sent / 1024 / 1024,
                    'bytes_recv_mb': network.bytes_recv / 1024 / 1024
                }
            }

        except ImportError:
            logger.error("psutil模块未安装")
            return None
        except Exception as e:
            logger.error(f"获取系统信息时出错: {str(e)}")
            return None

    @property
    def tool_info(self) -> list[types.Tool]:
        """返回工具的描述信息"""
        return [
            types.Tool(
                name="get-process-stats",
                description="获取指定进程的资源占用统计信息，包括CPU、内存、线程数等。如果不提供PID则自动查找MCP服务器进程。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "pid": {
                            "type": "integer",
                            "description": "进程ID，可选。如果不提供则自动查找MCP服务器进程"
                        }
                    },
                },
            ),
            types.Tool(
                name="get-system-stats",
                description="获取系统整体资源占用统计信息，包括CPU、内存、磁盘、网络等。",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            )
        ]
