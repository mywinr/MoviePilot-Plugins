import logging
import json
from typing import Optional, Dict, Any

import httpx
import anyio

logger = logging.getLogger(__name__)

# HTTP客户端管理
_http_client = None

# 配置


class Config:
    BASE_URL = "http://localhost:3001"  # 基础URL，不要在这里添加/api/v1前缀
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # 基础重试延迟（秒）
    REQUEST_TIMEOUT = 600  # 请求超时时间（秒）


config = Config()


async def get_http_client() -> httpx.AsyncClient:
    """获取或创建HTTP客户端"""
    global _http_client
    if _http_client is None:
        # 增加超时时间，避免长时间请求导致连接断开
        _http_client = httpx.AsyncClient(
            timeout=config.REQUEST_TIMEOUT
        )
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
    access_token: Optional[str] = None,
    params: Optional[Dict[str, Any]] = None,
    data: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    retry_count: int = 0,
) -> Dict[str, Any]:
    """发送请求到MoviePilot API，支持重试机制

    Args:
        method: HTTP请求方法 (GET, POST, etc.)
        endpoint: API端点路径
        access_token: MoviePilot access token
        params: URL查询参数
        data: 表单数据
        json_data: JSON请求体
        retry_count: 当前重试次数

    Returns:
        Dict[str, Any]: API响应数据或错误信息
    """
    # 处理认证
    headers = {}
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"
    else:
        logger.warning("未提供access_token，请求可能会失败")

    try:
        # 获取HTTP客户端
        client = await get_http_client()
        url = f"{config.BASE_URL.rstrip('/')}{endpoint}"

        # 记录请求信息
        logger.info(f"发送请求: {method} {url}")
        if params:
            logger.info(f"查询参数: {params}")
        if json_data:
            logger.info(f"请求体: {json_data}")

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
        if "application/json" in content_type:
            try:
                return response.json()
            except Exception as e:
                logger.error(f"解析JSON响应失败: {str(e)}")
                return {"error": f"解析响应失败: {str(e)}", "content": response.text}
        return {"content": response.text}

    except httpx.HTTPStatusError as e:
        # 处理HTTP错误
        error_content = e.response.text
        try:
            error_content = json.loads(e.response.text)
        except Exception:
            pass

        # 处理401错误（未授权）
        if e.response.status_code == 401 and retry_count < config.MAX_RETRIES:
            logger.warning(
                f"Token可能已过期 (重试 {retry_count + 1}/{config.MAX_RETRIES})"
            )
            await anyio.sleep(config.RETRY_DELAY * (retry_count + 1))
            return await make_request(
                method=method,
                endpoint=endpoint,
                access_token=access_token,
                params=params,
                data=data,
                json_data=json_data,
                retry_count=retry_count + 1
            )

        status_code = e.response.status_code
        reason = e.response.reason_phrase
        error_msg = f"HTTP {status_code}: {reason}"
        logger.error(f"请求失败: {error_msg}")
        return {
            "error": error_msg,
            "details": error_content
        }

    except httpx.RequestError as e:
        # 处理网络错误
        if retry_count < config.MAX_RETRIES:
            logger.warning(
                f"请求失败 (重试 {retry_count + 1}/{config.MAX_RETRIES}): {str(e)}"
            )
            await anyio.sleep(config.RETRY_DELAY * (retry_count + 1))
            return await make_request(
                method=method,
                endpoint=endpoint,
                access_token=access_token,
                params=params,
                data=data,
                json_data=json_data,
                retry_count=retry_count + 1
            )

        error_msg = f"网络错误: {str(e)}"
        logger.error(f"请求失败: {error_msg}")
        return {"error": error_msg}

    except Exception as e:
        logger.error(f"请求处理过程中发生错误: {str(e)}", exc_info=True)
        return {"error": f"系统错误: {str(e)}"}
