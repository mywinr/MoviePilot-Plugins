import contextlib
import logging
import os
import socket
import sys
import traceback
from collections.abc import AsyncIterator
from typing import Optional, Dict, Any

import click
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.types import Receive, Scope, Send
from starlette.middleware import Middleware
from starlette.responses import JSONResponse


# 设置详细的异常处理
sys.excepthook = lambda exctype, value, tb: print(f"全局异常: {exctype.__name__}: {value}\n{''.join(traceback.format_tb(tb))}")

try:
    from event_store import SQLiteEventStore
except Exception as e:
    print(f"导入SQLiteEventStore失败: {str(e)}\n{traceback.format_exc()}")
    # 定义一个简单的内存事件存储作为备用
    from mcp.server.streamable_http import EventCallback, EventId, EventMessage, EventStore, StreamId
    class SimpleMemoryEventStore(EventStore):
        """简单的内存事件存储，作为SQLiteEventStore的备用"""
        def __init__(self):
            self.events = {}
            print("使用简单内存事件存储作为备用")

        async def store_event(self, stream_id: StreamId, message: Any) -> EventId:
            event_id = f"event_{len(self.events) + 1}"
            self.events[event_id] = (stream_id, message)
            return event_id

        async def replay_events_after(self, last_event_id: EventId, send_callback: EventCallback) -> StreamId | None:
            return None

        async def start_cleanup(self):
            pass

        async def stop_cleanup(self):
            pass

# Configure logging
logger = logging.getLogger(__name__)

# 导入工具管理器和提示管理器
from tools import ToolManager
from prompts import PromptManager

# 导入共享的认证模块
from auth import BearerAuthMiddleware, create_token_manager

def _start_plugin_tool_monitor(tool_manager):
    """启动插件工具监控线程"""
    import threading
    import time
    import json
    import os

    def monitor_plugin_tools():
        """监控插件工具文件变化"""
        tools_file = os.path.join(os.path.dirname(__file__), "plugin_tools.json")
        last_modified = 0

        while True:
            try:
                if os.path.exists(tools_file):
                    current_modified = os.path.getmtime(tools_file)

                    if current_modified > last_modified:
                        last_modified = current_modified

                        # 读取工具文件
                        try:
                            # 导入安全文件操作工具
                            import sys
                            import os
                            sys.path.append(os.path.dirname(__file__))
                            from utils.file_operations import safe_read_json
                            from pathlib import Path

                            plugin_tools = safe_read_json(Path(tools_file), default_value={})

                            # 更新工具管理器
                            _update_plugin_tools(tool_manager, plugin_tools)

                        except Exception as e:
                            logger.error(f"读取插件工具文件失败: {str(e)}")

                time.sleep(5)  # 每5秒检查一次

            except Exception as e:
                logger.error(f"监控插件工具文件时发生异常: {str(e)}")
                time.sleep(10)  # 出错时等待更长时间

    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_plugin_tools, daemon=True)
    monitor_thread.start()
    logger.info("插件工具监控线程已启动")


def _start_plugin_prompt_monitor(prompt_manager):
    """启动插件提示监控线程"""
    import threading
    import time
    import json
    import os

    def monitor_plugin_prompts():
        """监控插件提示文件变化"""
        prompts_file = os.path.join(os.path.dirname(__file__), "plugin_prompts.json")
        last_modified = 0

        while True:
            try:
                # 检查文件是否存在且有修改
                if os.path.exists(prompts_file):
                    current_modified = os.path.getmtime(prompts_file)
                    if current_modified > last_modified:
                        last_modified = current_modified
                        logger.info("检测到插件提示文件变化，正在更新...")

                        # 读取提示文件
                        # 导入安全文件操作工具
                        import sys
                        import os
                        sys.path.append(os.path.dirname(__file__))
                        from utils.file_operations import safe_read_json
                        from pathlib import Path

                        plugin_prompts = safe_read_json(Path(prompts_file), default_value={})

                        # 更新插件提示
                        _update_plugin_prompts(prompt_manager, plugin_prompts)

                # 每5秒检查一次
                time.sleep(5)

            except Exception as e:
                logger.error(f"监控插件提示文件时发生异常: {str(e)}")
                time.sleep(10)  # 出错时等待更长时间

    # 启动监控线程
    monitor_thread = threading.Thread(target=monitor_plugin_prompts, daemon=True)
    monitor_thread.start()
    logger.info("插件提示监控线程已启动")


def _update_plugin_prompts(prompt_manager, plugin_prompts):
    """更新插件提示"""
    try:
        # 获取当前已注册的插件提示统计
        current_stats = prompt_manager.get_plugin_prompt_registry().get_registry_stats()
        current_plugins = set(current_stats.get("prompts_by_plugin", {}).keys())

        # 获取新的插件列表
        new_plugins = set(plugin_prompts.keys())

        # 找出需要注销的插件（在当前注册中但不在新列表中）
        plugins_to_unregister = current_plugins - new_plugins
        for plugin_id in plugins_to_unregister:
            result = prompt_manager.unregister_plugin_prompts(plugin_id)
            logger.info(f"注销插件提示: {plugin_id}, 结果: {result}")

        # 注册或更新插件提示
        for plugin_id, plugin_data in plugin_prompts.items():
            prompts = plugin_data.get("prompts", [])
            if prompts:
                # 先注销现有提示（如果存在）
                if plugin_id in current_plugins:
                    prompt_manager.unregister_plugin_prompts(plugin_id)

                # 注册新提示
                result = prompt_manager.register_plugin_prompts(plugin_id, prompts)
                logger.info(f"注册插件提示: {plugin_id}, 结果: {result}")

        # 记录最新统计
        updated_stats = prompt_manager.get_plugin_prompt_registry().get_registry_stats()
        logger.info(f"插件提示更新完成: {updated_stats}")

    except Exception as e:
        logger.error(f"更新插件提示时发生异常: {str(e)}")

def _update_plugin_tools(tool_manager, plugin_tools):
    """更新插件工具"""
    try:
        # 获取当前已注册的插件工具统计
        current_stats = tool_manager.get_plugin_registry_stats()
        current_plugins = set(current_stats.get("tools_by_plugin", {}).keys())

        # 获取新的插件列表
        new_plugins = set(plugin_tools.keys())

        # 找出需要注销的插件（在当前注册中但不在新列表中）
        plugins_to_unregister = current_plugins - new_plugins
        for plugin_id in plugins_to_unregister:
            result = tool_manager.unregister_plugin_tools(plugin_id)
            logger.info(f"注销插件工具: {plugin_id}, 结果: {result}")

        # 注册或更新插件工具
        for plugin_id, plugin_data in plugin_tools.items():
            tools = plugin_data.get("tools", [])
            if tools:
                # 先注销现有工具（如果存在）
                if plugin_id in current_plugins:
                    tool_manager.unregister_plugin_tools(plugin_id)

                # 注册新工具
                result = tool_manager.register_plugin_tools(plugin_id, tools)
                logger.info(f"注册插件工具: {plugin_id}, 结果: {result}")

        # 记录最新统计
        updated_stats = tool_manager.get_plugin_registry_stats()
        logger.info(f"插件工具更新完成: {updated_stats}")

    except Exception as e:
        logger.error(f"更新插件工具时发生异常: {str(e)}")
        logger.error(traceback.format_exc())

@click.command()
@click.option("--host", default="127.0.0.1", help="Host address to listen on")
@click.option("--port", default=3111, help="Port to listen on for HTTP")
@click.option(
    "--log-level",
    default="INFO",
    help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
)
@click.option(
    "--json-response",
    is_flag=True,
    default=False,
    help="Enable JSON responses instead of SSE streams",
)
@click.option(
    "--auth-token",
    default="",
    help="Initial Bearer authentication token for API security",
)
@click.option(
    "--access-token",
    default="",
    help="MoviePilot access token for API requests",
)
@click.option(
    "--log-file",
    default="",
    help="Log file path to write logs to",
)
@click.option(
    "--require-auth",
    is_flag=True,
    default=False,
    help="Enable Bearer token authentication (default: disabled)",
)
@click.option(
    "--no-auth",
    is_flag=True,
    default=False,
    help="Disable Bearer token authentication",
)
@click.option(
    "--moviepilot-port",
    default=3001,
    help="MoviePilot main program port number",
)
def main(
    host: str,
    port: int,
    log_level: str,
    json_response: bool,
    auth_token: str,
    access_token: str,
    log_file: str,
    moviepilot_port: int,
    require_auth: bool,
    no_auth: bool,
) -> int:
    # Configure logging
    log_handlers = []

    # 控制台日志处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log_handlers.append(console_handler)

    # 如果提供了日志文件路径，添加文件日志处理器
    if log_file:
        try:
            # 确保日志目录存在
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                os.makedirs(log_dir, exist_ok=True)

            # 创建文件处理器
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
            log_handlers.append(file_handler)

            logger.info(f"日志将同时输出到文件: {log_file}")
        except Exception as e:
            print(f"设置日志文件失败: {str(e)}")
            print(traceback.format_exc())

    # 配置根日志记录器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=log_handlers
    )

    logger.info(f"正在启动MCP服务器于 {host}:{port}")

    # 设置MoviePilot端口号
    from utils import set_moviepilot_port
    set_moviepilot_port(moviepilot_port)

    # 确定认证配置
    auth_enabled = require_auth and not no_auth
    if no_auth:
        logger.info("认证已禁用 (--no-auth)")
    elif require_auth:
        logger.info("认证已启用 (--require-auth)")
    else:
        logger.info("认证已禁用 (默认)")

    # 创建Token管理器
    token_manager = create_token_manager(auth_token, access_token)

    # 创建Server实例
    app = Server("moviepilot-mcp-server")

    # 初始化工具管理器
    tool_manager = ToolManager(token_manager)

    # 启动插件工具监控
    _start_plugin_tool_monitor(tool_manager)

    # 初始化提示管理器
    prompt_manager = PromptManager(token_manager)

    # 启动插件提示监控
    _start_plugin_prompt_monitor(prompt_manager)

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        return await tool_manager.call_tool(name, arguments)

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        tools = tool_manager.list_tools()
        logger.info(f"列出工具列表: {[tool.name for tool in tools]}")
        return tools

    # 注册prompts功能
    @app.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        prompts = prompt_manager.list_prompts()
        logger.info(f"列出提示列表: {len(prompts)} 个提示")
        return prompts

    @app.get_prompt()
    async def get_prompt(
        name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        logger.info(f"获取提示: {name} 参数: {arguments}")
        return await prompt_manager.get_prompt(name, arguments)

    # Create event store for resumability
    logger.info("初始化事件存储")
    try:
        # 检查当前目录是否可写
        current_dir = os.path.dirname(os.path.abspath(__file__))
        test_file_path = os.path.join(current_dir, "test_write_permission.tmp")
        try:
            with open(test_file_path, 'w') as f:
                f.write("test")
            os.remove(test_file_path)
            logger.info(f"当前目录 {current_dir} 可写")
        except Exception as e:
            logger.error(f"当前目录 {current_dir} 不可写: {str(e)}")
            raise RuntimeError(f"当前目录不可写，无法创建事件存储: {str(e)}")

        # 尝试创建SQLite事件存储
        logger.info("创建SQLite事件存储")
        event_store = SQLiteEventStore(
            db_path=os.path.join(current_dir, "events.db"),  # 使用绝对路径
            max_events_per_stream=100,        # 每个流最多保留100条事件
            max_event_age_days=30,            # 事件保留30天
            auto_cleanup_interval_hours=24,   # 每24小时自动清理一次
            max_db_size_mb=100                # 数据库最大100MB
        )
        logger.info("SQLite事件存储创建成功")
    except Exception as e:
        logger.error(f"创建SQLite事件存储失败，使用内存存储作为备用: {str(e)}")
        logger.error(traceback.format_exc())
        # 使用内存存储作为备用
        event_store = SimpleMemoryEventStore()

    # Create the session manager with our app and event store
    logger.info("创建会话管理器")
    session_manager = StreamableHTTPSessionManager(
        app=app,
        event_store=event_store,  # Enable resumability with SQLite persistence
        json_response=json_response,
    )

    # ASGI handler for streamable HTTP connections
    async def handle_streamable_http(
        scope: Scope, receive: Receive, send: Send
    ) -> None:
        await session_manager.handle_request(scope, receive, send)

    # 健康检查端点
    async def health_check(request):
        """健康检查端点"""
        return JSONResponse({"status": "healthy", "server": "mcp-http"})

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        logger.info("启动会话管理器")
        try:
            async with session_manager.run():
                logger.info(f"MCP服务器就绪，监听地址: {host}:{port}")
                # 启动事件存储的自动清理任务
                try:
                    logger.info("启动事件存储自动清理任务")
                    await event_store.start_cleanup()
                    logger.info("事件存储自动清理任务启动成功")
                except Exception as e:
                    logger.error(f"启动事件存储自动清理任务失败: {str(e)}")
                    logger.error(traceback.format_exc())

                try:
                    yield
                finally:
                    # 停止清理任务
                    try:
                        logger.info("正在停止事件存储清理任务")
                        await event_store.stop_cleanup()
                        logger.info("事件存储清理任务已停止")
                    except Exception as e:
                        logger.error(f"停止事件存储清理任务失败: {str(e)}")
                        logger.error(traceback.format_exc())

                    logger.info("服务器正在关闭...")
        except Exception as e:
            logger.error(f"会话管理器启动失败: {str(e)}")
            logger.error(traceback.format_exc())
            # 重新抛出异常，让服务器知道启动失败
            raise

    # 创建中间件列表
    middleware = [
        Middleware(BearerAuthMiddleware, token_manager=token_manager, require_auth=auth_enabled)
    ]

    # 创建路由
    routes = [
        Mount("/mcp", app=handle_streamable_http),
        Route("/health", endpoint=health_check),
    ]

    # Create an ASGI application using the transport
    logger.info("初始化Starlette应用")
    starlette_app = Starlette(
        debug=True,
        routes=routes,
        lifespan=lifespan,
        middleware=middleware,
    )

    # 在应用状态中存储token管理器
    starlette_app.state.token_manager = token_manager

    import uvicorn
    from uvicorn.config import Config
    from uvicorn.server import Server as UvicornServer

    logger.info(f"启动Uvicorn服务器 - 监听于 {host}:{port}")
    try:
        # 创建自定义配置，以便我们可以设置socket选项
        config = Config(
            app=starlette_app,
            host=host,
            port=port,
            log_level=log_level.lower(),
            timeout_keep_alive=120,  # 增加keep-alive超时时间
            access_log=True,         # 启用访问日志
            loop="auto",             # 自动选择事件循环
            reload=False,            # 禁用热重载
            workers=1                # 单进程模式
        )

        # 创建服务器实例
        server = UvicornServer(config=config)

        # 添加一个钩子来设置socket选项
        original_startup = server.startup

        async def custom_startup(**kwargs):
            # 调用原始的启动方法，传递所有参数
            await original_startup(**kwargs)

            # 设置SO_REUSEADDR选项，允许重用处于TIME_WAIT状态的端口
            if hasattr(server, 'servers'):
                for s in server.servers:
                    if hasattr(s, 'sockets'):
                        for sock in s.sockets:
                            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                            logger.info("已设置SO_REUSEADDR选项，允许重用TIME_WAIT状态的端口")

        # 替换启动方法
        server.startup = custom_startup

        # 启动服务器
        server.run()
        logger.info("MCP服务器已正常关闭")
    except Exception as e:
        logger.error(f"Uvicorn服务器启动或运行过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

    return 0

if __name__ == "__main__":
    main()
