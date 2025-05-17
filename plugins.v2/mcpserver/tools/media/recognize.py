import logging
import anyio
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class MediaRecognizeTool(BaseTool):
    """媒体识别工具，用于识别电影、电视剧等媒体信息"""

    async def execute(self, tool_name: str, arguments: dict) -> list[types.TextContent]:
        """执行工具逻辑"""
        if tool_name == "recognize-media":
            return await self._recognize_media_tool(arguments)
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _recognize_media_tool(self, arguments: dict) -> list[types.TextContent]:
        """
        识别媒体信息工具
        参数:
            - title: 媒体标题
            - year: 年份(可选)
            - type: 媒体类型(可选)，如：电影、电视剧
        """
        title = arguments.get("title")
        if not title:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供媒体标题"
                )
            ]

        # 获取其他可选参数
        year = arguments.get("year")
        media_type = arguments.get("type")

        try:
            # 调用识别方法
            media_info = await self.recognize_media(title, year, media_type)

            if not media_info:
                return [
                    types.TextContent(
                        type="text",
                        text=f"无法识别媒体信息：{title} {year or ''}"
                    )
                ]

            # 格式化媒体信息
            result_text = self._format_media_info(media_info, title, year)

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"识别媒体信息时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"识别媒体信息时出错: {str(e)}"
                )
            ]

    def _format_media_info(self, media_info: dict, title: str, year: str = None) -> str:
        """
        格式化媒体信息

        参数:
            media_info: 媒体信息字典
            title: 原始查询标题
            year: 原始查询年份

        返回:
            格式化后的文本
        """
        if not media_info:
            return f"未找到媒体信息：{title} {year or ''}"

        # 提取基本信息
        media_title = media_info.get("title", "未知标题")
        media_year = media_info.get("year", "未知年份")
        media_type = media_info.get("type", "未知类型")
        tmdb_id = media_info.get("tmdb_id", "无")
        douban_id = media_info.get("douban_id", "无")
        imdb_id = media_info.get("imdb_id", "无")
        overview = media_info.get("overview", "无简介")

        # 格式化输出
        result = f"媒体识别结果：\n\n"
        result += f"标题: {media_title}\n"
        result += f"年份: {media_year}\n"
        result += f"类型: {media_type}\n"
        result += f"TMDB ID: {tmdb_id}\n"
        result += f"豆瓣 ID: {douban_id}\n"
        result += f"IMDB ID: {imdb_id}\n"

        # 添加评分信息
        vote = media_info.get("vote", 0)
        if vote:
            result += f"评分: {vote}\n"

        # 添加季数信息（如果是电视剧）
        if media_type == "电视剧":
            seasons = media_info.get("seasons", {})
            if seasons:
                season_info = []
                for season_num, episodes in seasons.items():
                    season_info.append(f"第{season_num}季: {len(episodes)}集")
                result += f"季信息: {', '.join(season_info)}\n"

        # 添加简介
        result += f"\n简介: {overview}\n"

        return result

    async def recognize_media(self, title, year=None, media_type=None):
        """
        识别媒体信息

        参数:
            title: 媒体标题
            year: 年份（可选）
            media_type: 媒体类型（可选）

        返回:
            媒体信息字典，如果识别失败则返回None
        """
        params = {"title": title}
        if year:
            params["year"] = year
        if media_type:
            params["type"] = media_type

        try:
            logger.info(f"识别媒体信息: {title} {year or ''}")

            # 增加重试机制
            max_retries = 3
            retry_delay = 2  # 秒

            for retry in range(max_retries):
                try:
                    response = await self._make_request(
                        method="GET",
                        endpoint="/api/v1/media/recognize",
                        params=params
                    )

                    # 检查响应是否包含错误
                    if response and isinstance(response, dict):
                        if "error" in response:
                            error_msg = response.get("error", "未知错误")
                            logger.error(f"识别媒体信息失败: {error_msg}")

                            # 如果不是最后一次重试，则等待后重试
                            if retry < max_retries - 1:
                                logger.info(
                                    f"将在 {retry_delay} 秒后重试 "
                                    f"({retry + 1}/{max_retries})")
                                await anyio.sleep(retry_delay)
                                retry_delay *= 2  # 指数退避
                                continue
                            return None

                        # 成功获取媒体信息
                        if "media_info" in response:
                            logger.info(f"成功识别媒体: {title}")
                            return response["media_info"]

                    # 响应格式不正确
                    logger.warning(f"媒体识别响应格式不正确: {response}")
                    return None

                except Exception as e:
                    logger.error(f"识别媒体时发生异常: {str(e)}")

                    # 如果不是最后一次重试，则等待后重试
                    if retry < max_retries - 1:
                        logger.info(
                            f"将在 {retry_delay} 秒后重试 "
                            f"({retry + 1}/{max_retries})")
                        await anyio.sleep(retry_delay)
                        retry_delay *= 2  # 指数退避
                    else:
                        logger.error(f"识别媒体失败，已达到最大重试次数: {title}")
                        return None

            return None

        except Exception as e:
            logger.error(f"识别媒体过程中发生错误: {str(e)}")
            return None

    @property
    def tool_info(self) -> list[types.Tool]:
        """返回工具的描述信息"""
        return [
            types.Tool(
                name="recognize-media",
                description="识别媒体信息，根据标题和年份识别电影、电视剧等媒体的详细信息。处理技巧：1)使用资源的真实名称；2)提取核心名称，去除无关词汇；3)通过年份区分同名作品；4)确定系列作品的具体哪一部。识别结果包含标准化的标题和年份、TMDB/豆瓣/IMDB ID、媒体类型和评分、季集信息(电视剧)、简介等，可用于后续搜索、下载或订阅操作。其他工具如search-movie等需要先调用此工具获取媒体信息。",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "媒体标题"
                        },
                        "year": {
                            "type": "string",
                            "description": "媒体年份，如 2023"
                        },
                        "type": {
                            "type": "string",
                            "description": "媒体类型，如：电影、电视剧",
                            "enum": ["电影", "电视剧"]
                        }
                    },
                },
            )
        ]
