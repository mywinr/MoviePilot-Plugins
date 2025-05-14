import contextlib
import logging
from collections.abc import AsyncIterator
import json
from typing import Optional, Dict, Any

import click
import httpx
import anyio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from event_store import SQLiteEventStore

# Configure logging
logger = logging.getLogger(__name__)

# HTTP客户端管理
_http_client = None

# 配置
class Config:
    BASE_URL = "http://localhost:3001"
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # 基础重试延迟（秒）

config = Config()

# Token管理器
class TokenManager:
    def __init__(self, initial_token: str = None, access_token: str = None):
        self.token = initial_token
        self.access_token = access_token

        if not self.token:
            logger.warning("服务器启动时没有设置Token，API安全性无法保证")
        else:
            logger.info("Token管理器已初始化")

        if self.access_token:
            logger.info("MoviePilot access_token 已设置")
        else:
            logger.warning("未设置 MoviePilot access_token，访问 MoviePilot API 可能受限")

    def get_token(self) -> str:
        """获取当前token"""
        return self.token

    def get_access_token(self) -> str:
        """获取 MoviePilot access_token"""
        return self.access_token


# 认证中间件
class BearerAuthMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, token_manager: TokenManager):
        super().__init__(app)
        self.token_manager = token_manager

    async def dispatch(self, request, call_next):
        # 获取当前token
        current_token = self.token_manager.get_token()

        # 无token时拒绝所有请求（确保安全性）
        if not current_token:
            return JSONResponse(
                {"message": "服务器未设置认证Token，拒绝访问", "error": "unauthorized"},
                status_code=401
            )

        # 验证Authorization头
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                {"message": "认证失败，请提供Bearer Token", "error": "unauthorized"},
                status_code=401
            )

        token = auth_header.replace("Bearer ", "")
        if token != current_token:
            return JSONResponse(
                {"message": "认证失败，提供的Token无效", "error": "unauthorized"},
                status_code=401
            )

        # 认证通过
        return await call_next(request)



async def get_http_client() -> httpx.AsyncClient:
    """获取或创建HTTP客户端"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.AsyncClient(timeout=30.0)
    return _http_client

async def close_http_client():
    """关闭HTTP客户端"""
    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None

async def make_request(
    method: str,
    endpoint: str,
    token_manager: Optional[TokenManager] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    retry_count: int = 0,
) -> Dict[str, Any]:
    """发送请求到MoviePilot API，支持重试机制
    
    Args:
        method: HTTP请求方法 (GET, POST, etc.)
        endpoint: API端点路径
        token_manager: TokenManager实例，用于获取access_token
        params: URL查询参数
        data: 表单数据
        json_data: JSON请求体
        retry_count: 当前重试次数
        
    Returns:
        Dict[str, Any]: API响应数据或错误信息
    """
    # 处理认证
    headers = {}
    access_token = token_manager.get_access_token() if token_manager else None
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    else:
        logger.warning("未提供access_token，请求可能会失败")

    try:
        # 获取HTTP客户端
        client = await get_http_client()
        url = f"{config.BASE_URL.rstrip('/')}{endpoint}"
        
        # 记录请求信息
        logger.debug(f"发送请求: {method} {url}")
        if params:
            logger.debug(f"查询参数: {params}")
        if json_data:
            logger.debug(f"请求体: {json_data}")
        
        # 发送请求
        response = await client.request(
            method,
            url,
            params=params,
            data=data,
            json=json_data,
            headers=headers,
        )
        response.raise_for_status()
        # 处理响应
        if not response.content:
            return {}
            
        content_type = response.headers.get("content-type", "")
        print(f"content_type: {content_type}")
        print(f"response.json(): {response.json()}")
        if "application/json" in content_type:
            return response.json()
        return {"content": response.text}
        
    except httpx.HTTPStatusError as e:
        # 处理HTTP错误
        error_content = e.response.text
        try:
            error_content = e.response.json()
        except json.JSONDecodeError:
            pass
            
        # 处理401错误（未授权）
        if e.response.status_code == 401 and retry_count < config.MAX_RETRIES:
            logger.warning(f"Token可能已过期 (重试 {retry_count + 1}/{config.MAX_RETRIES})")
            await anyio.sleep(config.RETRY_DELAY * (retry_count + 1))
            return await make_request(
                method=method,
                endpoint=endpoint,
                token_manager=token_manager,
                params=params,
                data=data,
                json_data=json_data,
                retry_count=retry_count + 1
            )
            
        return {
            "error": f"HTTP {e.response.status_code}: {e.response.reason_phrase}",
            "details": error_content
        }
        
    except httpx.RequestError as e:
        # 处理网络错误
        if retry_count < config.MAX_RETRIES:
            logger.warning(f"请求失败 (重试 {retry_count + 1}/{config.MAX_RETRIES}): {str(e)}")
            await anyio.sleep(config.RETRY_DELAY * (retry_count + 1))
            return await make_request(
                method=method,
                endpoint=endpoint,
                token_manager=token_manager,
                params=params,
                data=data,
                json_data=json_data,
                retry_count=retry_count + 1
            )
        return {"error": f"网络错误: {str(e)}"}
        
    except Exception as e:
        logger.error("请求处理过程中发生错误", exc_info=True)
        return {"error": f"系统错误: {str(e)}"}


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
def main(
    host: str,
    port: int,
    log_level: str,
    json_response: bool,
    auth_token: str,
    access_token: str,
) -> int:
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info(f"正在启动MCP服务器于 {host}:{port}")

    # 创建Token管理器
    token_manager = TokenManager(auth_token, access_token)

    if auth_token:
        logger.info("API认证已启用，需要Bearer Token才能访问")
    else:
        logger.warning("未设置认证Token，API安全性无法保证！请尽快设置Token")

    app = Server("mcp-streamable-http-demo")

    @app.call_tool()
    async def call_tool(
        name: str, arguments: dict
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name == 'add-numbers':
            num1 = arguments.get("num1", 0)
            num2 = arguments.get("num2", 0)

            # 确保输入是数值类型
            try:
                num1 = float(num1)
                num2 = float(num2)
            except (ValueError, TypeError):
                return [
                    types.TextContent(
                        type="text",
                        text="错误：请提供有效的数字作为输入。",
                    )
                ]

            # 计算结果
            result = num1 + num2

            # 如果结果是整数，转换为整数输出
            if result.is_integer():
                result = int(result)

            return [
                types.TextContent(
                    type="text",
                    text=f"计算结果：{num1} + {num2} = {result}",
                )
            ]
        elif name == 'user-info':
            # 获取用户信息
            response = await make_request(
                method="GET",
                endpoint="/api/v1/user/current",
                token_manager=token_manager,
            )
        
            # 检查是否有错误
            if "error" in response:
                return [
                    types.TextContent(
                        type="text",
                        text=f"获取用户信息失败: {response['error']}",
                    )
                ]
  
            # 格式化用户信息
            user_info = []
            for key, value in response.items():
                if isinstance(value, (dict, list)):
                    value = json.dumps(value, ensure_ascii=False, indent=2)
                user_info.append(f"{key}: {value}")
                
            return [
                types.TextContent(
                    type="text",
                    text="用户信息:\n" + "\n".join(user_info)
                )
            ]

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name="add-numbers",
                description="计算两个数字的加法",
                inputSchema={
                    "type": "object",
                    "required": ["num1", "num2"],
                    "properties": {
                        "num1": {
                            "type": "number",
                            "description": "第一个数字",
                        },
                        "num2": {
                            "type": "number",
                            "description": "第二个数字",
                        },
                    },
                },
            ),
            types.Tool(
                name="user-info",
                description="获取当前用户信息",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            )
        ]

    # Create event store for resumability
    logger.info("初始化SQLite事件存储")
    # 创建SQLite事件存储，启用自动清理功能
    event_store = SQLiteEventStore(
        db_path="events.db",              # 数据存储在当前目录的events.db文件中
        max_events_per_stream=100,        # 每个流最多保留100条事件
        max_event_age_days=30,            # 事件保留30天
        auto_cleanup_interval_hours=24,   # 每24小时自动清理一次
        max_db_size_mb=100                # 数据库最大100MB
    )

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

    @contextlib.asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        """Context manager for managing session manager lifecycle."""
        logger.info("启动会话管理器")
        async with session_manager.run():
            logger.info(f"MCP服务器就绪，监听地址: {host}:{port}")
            # 启动事件存储的自动清理任务
            await event_store.start_cleanup()
            try:
                yield
            finally:
                # 停止清理任务
                logger.info("正在停止事件存储清理任务")
                await event_store.stop_cleanup()
                logger.info("服务器正在关闭...")

    # 创建中间件列表
    middleware = [
        Middleware(BearerAuthMiddleware, token_manager=token_manager)
    ]

    # 创建路由
    routes = [
        Mount("/mcp", app=handle_streamable_http),
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

    logger.info(f"启动Uvicorn服务器 - 监听于 {host}:{port}")
    uvicorn.run(
        starlette_app,
        host=host,
        port=port,
        log_level=log_level.lower()
    )

    logger.info("MCP服务器已关闭")
    return 0

if __name__ == "__main__":
    main()
