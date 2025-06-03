"""
共享的认证模块
包含TokenManager和BearerAuthMiddleware，供两种服务器类型使用
"""

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class TokenManager:
    """Token管理器，管理API认证token和MoviePilot access token"""

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
        """获取当前API认证token"""
        return self.token

    def get_access_token(self) -> str:
        """获取 MoviePilot access_token"""
        return self.access_token

    def set_token(self, token: str):
        """设置新的API认证token"""
        self.token = token
        logger.info("API认证token已更新")

    def set_access_token(self, access_token: str):
        """设置新的MoviePilot access_token"""
        self.access_token = access_token
        logger.info("MoviePilot access_token已更新")


class BearerAuthMiddleware(BaseHTTPMiddleware):
    """Bearer Token认证中间件"""

    def __init__(self, app, token_manager: TokenManager, exclude_paths: list = None, require_auth: bool = True):
        super().__init__(app)
        self.token_manager = token_manager
        self.exclude_paths = exclude_paths or ["/health"]
        self.require_auth = require_auth

    async def dispatch(self, request, call_next):
        # 检查是否是排除的路径（不需要认证）
        if request.url.path in self.exclude_paths:
            return await call_next(request)

        # 如果不需要认证，直接通过
        if not self.require_auth:
            logger.debug("认证已禁用，跳过Token验证")
            return await call_next(request)

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


def create_token_manager(auth_token: str = None, access_token: str = None) -> TokenManager:
    """创建TokenManager实例的工厂函数"""
    token_manager = TokenManager(auth_token, access_token)

    if auth_token:
        logger.info("API认证已启用，需要Bearer Token才能访问")
    else:
        logger.warning("未设置认证Token，API安全性无法保证！请尽快设置Token")

    return token_manager
