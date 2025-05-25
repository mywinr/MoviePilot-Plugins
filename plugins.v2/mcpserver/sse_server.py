#!/usr/bin/env python3
"""
MCP Server with SSE (Server-Sent Events) Transport
基于SSE传输的MCP服务器实现
"""

import argparse
import asyncio
import contextlib
import logging
import os
import socket
import sys
import traceback
from pathlib import Path
from typing import AsyncIterator

from mcp.server.sse import SseServerTransport
from mcp.server import Server
from mcp import types
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.routing import Route, Mount
from starlette.responses import JSONResponse, Response

# 添加当前目录到Python路径
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

# 导入工具和提示管理器
from tools import ToolManager
from prompts import PromptManager

# 导入共享的认证模块
from auth import BearerAuthMiddleware, create_token_manager

# 配置日志
def setup_logging(log_level: str = "INFO", log_file: str = None):
    """设置日志配置"""
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 配置根日志记录器
    logger = logging.getLogger()
    logger.setLevel(level)

    # 清除现有的处理器
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果指定了日志文件，添加文件处理器
    if log_file:
        try:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"无法创建日志文件 {log_file}: {e}")

    return logger

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="MCP Server with SSE Transport")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=3111, help="Port to bind to")
    parser.add_argument("--log-level", default="INFO", help="Log level")
    parser.add_argument("--log-file", help="Log file path")
    parser.add_argument("--moviepilot-port", type=int, default=3001, help="MoviePilot port")
    parser.add_argument("--auth-token", help="Authentication token")
    parser.add_argument("--access-token", help="MoviePilot access token")

    args = parser.parse_args()

    # 设置日志
    logger = setup_logging(args.log_level, args.log_file)

    # 运行服务器
    try:
        return asyncio.run(run_server(
            host=args.host,
            port=args.port,
            log_level=args.log_level,
            moviepilot_port=args.moviepilot_port,
            auth_token=args.auth_token,
            access_token=args.access_token
        ))
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在关闭服务器...")
        return 0
    except Exception as e:
        logger.error(f"服务器运行失败: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

async def run_server(
    host: str = "0.0.0.0",
    port: int = 3111,
    log_level: str = "INFO",
    moviepilot_port: int = 3001,
    auth_token: str = None,
    access_token: str = None
):
    """运行SSE MCP服务器"""
    logger = logging.getLogger(__name__)

    logger.info(f"正在启动MCP SSE服务器于 {host}:{port}")

    # 设置MoviePilot端口号
    from utils import set_moviepilot_port
    set_moviepilot_port(moviepilot_port)

    # 创建Token管理器
    token_manager = create_token_manager(auth_token, access_token)

    # 创建Server实例
    app = Server("moviepilot-mcp-server")

    # 初始化工具管理器
    tool_manager = ToolManager(token_manager)

    # 初始化提示管理器
    prompt_manager = PromptManager(token_manager)

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        return await tool_manager.call_tool(name, arguments)

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return tool_manager.list_tools()

    @app.list_prompts()
    async def list_prompts() -> list[types.Prompt]:
        return prompt_manager.list_prompts()

    @app.get_prompt()
    async def get_prompt(
        name: str, arguments: dict | None = None
    ) -> types.GetPromptResult:
        return await prompt_manager.get_prompt(name, arguments)

    # 创建SSE传输
    sse_transport = SseServerTransport("/messages/")

    # SSE连接处理器 - 使用ASGI格式
    async def handle_sse(scope, receive, send):
        """处理SSE连接"""
        try:
            async with sse_transport.connect_sse(scope, receive, send) as streams:
                await app.run(
                    streams[0],
                    streams[1],
                    app.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"SSE连接处理失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # 消息处理器 - 这个需要保持ASGI格式，因为使用Mount
    async def handle_messages(scope, receive, send):
        """处理POST消息"""
        try:
            await sse_transport.handle_post_message(scope, receive, send)
        except Exception as e:
            logger.error(f"消息处理失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # 健康检查端点
    async def health_check(request):
        """健康检查端点"""
        return JSONResponse({"status": "healthy", "server": "mcp-sse"})

    @contextlib.asynccontextmanager
    async def lifespan(_: Starlette) -> AsyncIterator[None]:
        """应用生命周期管理"""
        logger.info("启动SSE MCP服务器")
        try:
            logger.info(f"MCP SSE服务器就绪，监听地址: {host}:{port}")
            # SSE传输不需要额外的事件存储管理
            logger.info("SSE传输已就绪")

            try:
                yield
            finally:
                logger.info("SSE服务器正在关闭...")
        except Exception as e:
            logger.error(f"SSE服务器启动失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # 创建中间件列表
    middleware = [
        Middleware(BearerAuthMiddleware, token_manager=token_manager)
    ]

    # SSE端点处理器 - 使用ASGI格式
    async def sse_endpoint(scope, receive, send):
        """SSE端点处理器"""
        try:
            # 直接调用SSE传输的connect_sse方法
            async with sse_transport.connect_sse(scope, receive, send) as streams:
                await app.run(
                    streams[0],
                    streams[1],
                    app.create_initialization_options()
                )
        except Exception as e:
            logger.error(f"SSE连接处理失败: {str(e)}")
            logger.error(traceback.format_exc())
            raise

    # 创建路由
    routes = [
        Mount("/sse", app=sse_endpoint),  # SSE端点使用Mount
        Mount("/messages", app=handle_messages),  # 消息处理使用Mount
        Route("/health", endpoint=health_check),
    ]

    # 创建Starlette应用
    logger.info("初始化Starlette SSE应用")
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

    logger.info(f"启动Uvicorn SSE服务器 - 监听于 {host}:{port}")
    try:
        # 创建自定义配置
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
        await server.serve()
        logger.info("MCP SSE服务器已正常关闭")
    except Exception as e:
        logger.error(f"Uvicorn SSE服务器启动或运行过程中出错: {str(e)}")
        logger.error(traceback.format_exc())
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
