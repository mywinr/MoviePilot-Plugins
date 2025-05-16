import json
import logging
import mcp.types as types
from ..base import BaseTool
from .recognize import MediaRecognizeTool


# Configure logging
logger = logging.getLogger(__name__)


class MovieDownloadTool(BaseTool):
    """电影搜索和下载工具"""

    def __init__(self, token_manager=None):
        super().__init__(token_manager)
        # 创建媒体识别工具实例
        self._recognize_tool = MediaRecognizeTool(token_manager)

    async def execute(self, tool_name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """执行工具逻辑"""
        if tool_name == "search-movie":
            return await self._search_movie(arguments)
        elif tool_name == "fuzzy-search-movie":
            return await self._fuzzy_search_movie(arguments)
        elif tool_name == "download-torrent":
            return await self._download_torrent(arguments)
        elif tool_name == "get-downloaders":
            return await self._get_downloaders(arguments)
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    def _format_search_results(self, torrents: list, keyword: str, year: str = None, detailed: bool = True) -> str:
        """
        格式化搜索结果

        参数:
            torrents: 种子列表
            keyword: 搜索关键词
            year: 年份(可选)
            detailed: 是否显示详细信息(默认为True)

        返回:
            格式化后的文本
        """
        if not torrents:
            return f"未找到符合条件的资源：{keyword} {year or ''}"

        # 格式化搜索结果
        result_text = f"找到 {len(torrents)} 个资源：\n\n"
        for i, torrent in enumerate(torrents):
            # 检查torrent是否是字典类型
            if not isinstance(torrent, dict):
                logger.warning(f"种子数据不是字典类型: {type(torrent)}")
                continue

            # 提取需要的信息
            # 检查torrent_info字段
            torrent_info = torrent.get("torrent_info", {})
            meta_info = torrent.get("meta_info", {})
            if not torrent_info:
                # 可能是Context对象的直接序列化
                torrent_info = torrent

            # 从torrent_info中提取数据
            title = torrent_info.get("description", "未知标题")
            if not title or title == "未知标题":
                # 尝试从meta_info中获取标题
                if meta_info:
                    title = meta_info.get("subtitle", "未知标题")

            site_name = torrent_info.get("site_name", "未知站点")

            # 处理大小显示
            size_bytes = torrent_info.get("size", 0)
            if isinstance(size_bytes, (int, float)) and size_bytes > 0:
                # 转换为人类可读的大小
                if size_bytes < 1024:
                    size = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size = f"{size_bytes/1024:.2f} KB"
                elif size_bytes < 1024 * 1024 * 1024:
                    size = f"{size_bytes/(1024*1024):.2f} MB"
                else:
                    size = f"{size_bytes/(1024*1024*1024):.2f} GB"
            else:
                size = torrent_info.get("size", "未知大小")

            # 提取分辨率
            resolution = "未知分辨率"
            if meta_info:
                # 尝试直接从标题中提取分辨率
                title_str = meta_info.get("org_string", "")
                if title_str:
                    import re
                    res_pattern = (
                        r'(4K|1080[pi]|720[pi]|2160[pi]|UHD|'
                        r'MINIBD1080P|BD1080P|HD1080P|BD720P|HD720P)'
                    )
                    res_match = re.search(
                        res_pattern, title_str, re.IGNORECASE)
                    if res_match:
                        resolution = res_match.group(1)

            seeders = torrent_info.get("seeders", 0)
            peers = torrent_info.get("peers", 0)
            torrent_url = torrent_info.get("enclosure", "")

            # 格式化资源信息
            result_text += f"{i+1}. {title}\n"
            result_text += f"   站点: {site_name} | 大小: {size}\n"
            result_text += f"   分辨率: {resolution}\n"
            result_text += f"   做种: {seeders} | 下载: {peers}\n"

            # 如果需要详细信息，添加更多字段
            if detailed:
                # 是否H&R
                is_hr = torrent_info.get("hit_and_run", False)
                # 打折
                discount = torrent_info.get("volume_factor", 0)

                # 提取视频编码
                video_encode = meta_info.get("video_encode", "未知编码")
                # 提取音频编码
                audio_encode = meta_info.get("audio_encode", "未知音频")
                # 提取资源类型
                resource_type = meta_info.get("resource_type", "未知来源")
                # 提取制作组/字幕组
                resource_team = meta_info.get("resource_team", "")

                # 提取字幕信息
                subtitle_info = "无字幕信息"
                description = torrent_info.get("description", "")
                if description:
                    # 检查是否包含字幕信息
                    subtitle_keywords = [
                        "中字", "中文字幕", "简体", "繁体",
                        "双语", "特效字幕", "SUP", "SRT", "ASS"
                    ]
                    subtitle_matches = []
                    for keyword in subtitle_keywords:
                        if keyword in description:
                            subtitle_matches.append(keyword)

                    if subtitle_matches:
                        subtitle_info = "、".join(subtitle_matches)

                # 提取音轨信息
                audio_info = "未知音轨"
                audio_keywords = ["国语", "粤语", "英语", "双语", "多语", "国英双语", "中英双语"]
                audio_matches = []
                for keyword in audio_keywords:
                    if keyword in description:
                        audio_matches.append(keyword)

                if audio_matches:
                    audio_info = "、".join(audio_matches)

                # 添加详细信息
                result_text += (
                    f"   视频编码: {video_encode} | "
                    f"音频编码: {audio_encode}\n"
                )
                result_text += f"   资源类型: {resource_type}"
                if resource_team:
                    result_text += f" | 制作组: {resource_team}"
                result_text += "\n"
                result_text += f"   字幕: {subtitle_info} | 音轨: {audio_info}\n"
                if is_hr:
                    result_text += "   H&R: 是\n"
                result_text += f"   折扣: {discount}\n"

            # 添加资源下载链接
            result_text += f"   资源下载链接: {torrent_url}\n\n"

        return result_text

    async def _search_movie(self, arguments: dict) -> list[types.TextContent]:
        """
        搜索电影资源
        参数:
            - keyword: 电影名称关键词
            - year: 年份(可选)
            - resolution: 清晰度(可选)，如 1080p, 2160p, 4K 等
            - media_type: 媒体类型(可选)，默认为 "电影"
            - sites: 站点ID列表(可选)，多个站点ID用逗号分隔
        """
        keyword = arguments.get("keyword")
        if not keyword:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供电影名称关键词"
                )
            ]

        # 获取其他可选参数
        year = arguments.get("year")
        media_type = arguments.get("media_type", "电影")
        sites = arguments.get("sites")

        try:
            # 首先识别媒体信息
            media_info = await self._recognize_tool.recognize_media(keyword, year, media_type)
            if not media_info:
                return [
                    types.TextContent(
                        type="text",
                        text=f"无法识别媒体信息：{keyword} {year or ''}"
                    )
                ]

            # 获取媒体ID
            media_id = None
            if "tmdb_id" in media_info and media_info["tmdb_id"]:
                media_id = f"tmdb:{media_info['tmdb_id']}"
            elif "douban_id" in media_info and media_info["douban_id"]:
                media_id = f"douban:{media_info['douban_id']}"

            if not media_id:
                return [
                    types.TextContent(
                        type="text",
                        text=f"无法获取媒体ID：{keyword} {year or ''}"
                    )
                ]

            # 搜索资源
            params = {
                "mediaid": media_id,
                "mtype": "电影" if media_type == "电影" else "电视剧",
                "sites": sites,
                "sort": "seeders"
            }

            # 调用搜索API
            try:
                response = await self._make_request(
                    method="GET",
                    endpoint=f"/api/v1/search/media/{media_id}",
                    params=params
                )
            except Exception as e:
                logger.error(f"调用搜索API时出错: {str(e)}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"搜索资源时出错: {str(e)}"
                    )
                ]

            # 检查是否有错误
            is_error_response = (
                isinstance(response, dict) and
                not response.get("success", False)
            )
            if is_error_response:
                return [
                    types.TextContent(
                        type="text",
                        text=f"搜索资源失败: {response.get('message', '未知错误')}"
                    )
                ]

            # 获取搜索结果
            torrents = response.get("data", [])

            # 使用公共方法格式化结果
            result_text = self._format_search_results(torrents, keyword, year, detailed=True)

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"搜索电影资源时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"搜索电影资源时出错: {str(e)}"
                )
            ]

    async def _download_torrent(
        self, arguments: dict
    ) -> list[types.TextContent]:
        """
        下载指定的种子资源
        参数:
            - torrent_url: 种子资源下载链接
            - downloader: 下载器名称(可选)
            - save_path: 保存路径(可选)
        """
        torrent_url = arguments.get("torrent_url")
        if not torrent_url:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供要下载的资源链接"
                )
            ]

        # 获取其他可选参数
        downloader = arguments.get("downloader")
        save_path = arguments.get("save_path")

        try:
            logger.info(f"开始下载资源，URL: {torrent_url}")

            # 如果没有指定下载器，尝试获取可用的下载器列表
            if not downloader:
                logger.info("未指定下载器，尝试获取可用的下载器列表")

                # 获取下载器列表
                downloaders = await self._make_request(
                    method="GET",
                    endpoint="/api/v1/download/clients"
                )

                # 如果找到了下载器列表，尝试选择一个可用的下载器
                if downloaders:
                    for dl in downloaders:
                        if isinstance(dl, dict) and dl.get("status", True):
                            downloader = dl.get("name")
                            logger.info(f"自动选择下载器: {downloader}")
                            break

            # 准备请求参数
            payload = {
                "torrent_url": torrent_url,
                "downloader": downloader,
                "media_type": arguments.get("media_type")
            }

            # 添加其他可选参数
            if save_path:
                payload["save_path"] = save_path

            # 调用mcpserver的下载API
            response = await self._make_request(
                method="POST",
                endpoint="/api/v1/plugin/MCPServer/download_torrent",
                json=payload
            )

            # 记录响应
            # logger.info(f"下载API响应: {json.dumps(response, ensure_ascii=False)}")

            # 检查是否有错误
            is_error = (
                isinstance(response, dict) and
                not response.get("success", False)
            )
            if is_error:
                error_msg = response.get("message", "未知错误")
                logger.error(f"添加下载任务失败: {error_msg}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"添加下载任务失败: {error_msg}"
                    )
                ]

            # 下载成功
            site_name = response.get("site", "未知站点")
            save_path = response.get("save_path", "默认路径")
            success_msg = f"已成功添加下载任务：来自 {site_name} 的种子，保存至 {save_path}"
            logger.info(success_msg)
            return [
                types.TextContent(
                    type="text",
                    text=success_msg
                )
            ]

        except Exception as e:
            logger.error(f"下载资源时出错: {str(e)}", exc_info=True)
            return [
                types.TextContent(
                    type="text",
                    text=f"下载资源时出错: {str(e)}"
                )
            ]

    async def _get_sites_info(self):
        """获取所有站点信息"""
        try:
            # 调用站点API获取所有站点信息
            sites_response = await self._make_request(
                method="GET",
                endpoint="/api/v1/site/"
            )

            # 检查响应格式
            if isinstance(sites_response, list):
                return sites_response
            elif isinstance(sites_response, dict) and "data" in sites_response:
                return sites_response.get("data", [])
            return []
        except Exception as e:
            logger.warning(f"获取站点信息失败: {str(e)}")
            return []

    async def _fuzzy_search_movie(self, arguments: dict) -> list[types.TextContent]:
        """
        模糊搜索电影资源，不需要精确的媒体名称
        参数:
            - keyword: 电影名称关键词
            - page: 页码(可选)，默认为0
            - sites: 站点ID列表(可选)，多个站点ID用逗号分隔
            - detailed: 是否显示详细信息(可选)，默认为False
        """
        keyword = arguments.get("keyword")
        if not keyword:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供搜索关键词"
                )
            ]

        # 获取其他可选参数
        page = arguments.get("page", 0)
        sites = arguments.get("sites")
        detailed = arguments.get("detailed", False)

        try:
            logger.info(f"开始模糊搜索资源，关键词：{keyword}")

            # 构建请求参数
            params = {
                "keyword": keyword,
                "page": page
            }

            if sites:
                params["sites"] = sites

            # 调用模糊搜索API
            response = await self._make_request(
                method="GET",
                endpoint="/api/v1/search/title",
                params=params
            )

            # 检查是否有错误
            is_error_response = (
                isinstance(response, dict) and
                not response.get("success", False)
            )

            if is_error_response:
                error_msg = response.get("message", "未知错误")
                return [
                    types.TextContent(
                        type="text",
                        text=f"模糊搜索资源失败: {error_msg}"
                    )
                ]

            # 获取搜索结果
            torrents = response.get("data", [])

            # 使用公共方法格式化结果
            result_text = self._format_search_results(torrents, keyword, detailed=detailed)

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"模糊搜索资源时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"模糊搜索资源时出错: {str(e)}"
                )
            ]

    async def _get_downloaders(
        self, _: dict = None
    ) -> list[types.TextContent]:
        """
        获取可用的下载器列表工具
        参数:
            - _: 工具参数（当前未使用）
        """
        try:
            # 获取下载器列表
            downloaders = await self._make_request(
                method="GET",
                endpoint="/api/v1/download/clients"
            )

            # 格式化下载器信息
            result_text = "可用的下载器列表：\n\n"

            if not downloaders:
                # 如果没有找到下载器，显示默认下载器
                result_text += "没有找到可用的下载器，使用默认下载器：\n\n"
            else:
                # 显示找到的下载器
                for i, downloader in enumerate(downloaders):
                    name = downloader.get("name", "未知")
                    type_name = downloader.get("type", "未知")
                    result_text += f"{i+1}. name: {name}, type: {type_name}\n"
            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"获取下载器列表时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"获取下载器列表时出错: {str(e)}"
                )
            ]

    @property
    def tool_info(self) -> list[types.Tool]:
        """返回工具的描述信息"""
        return [
            types.Tool(
                name="search-movie",
                description="搜索电影资源，支持按名称、年份、清晰度等条件搜索。处理用户模糊的搜索请求时，建议先调用get-media-prompt工具获取处理指南，再调用recognize-media工具识别媒体信息。",
                inputSchema={
                    "type": "object",
                    "required": ["keyword"],
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "电影名称关键词"
                        },
                        "year": {
                            "type": "string",
                            "description": "电影年份，如 2023"
                        },
                        "resolution": {
                            "type": "string",
                            "description": "期望的清晰度，如 1080p, 2160p, 4K 等"
                        },
                        "media_type": {
                            "type": "string",
                            "description": "媒体类型，默认为'电影'，可选'电视剧'"
                        },
                        "sites": {
                            "type": "string",
                            "description": "站点ID列表，多个站点ID用逗号分隔，是数字ID不是站点名称，若没有站点ID可以通过工具get-sites获取"
                        }
                    },
                },
            ),
            types.Tool(
                name="fuzzy-search-movie",
                description="模糊搜索电影资源，当精确搜索无法识别媒体信息时使用此工具。直接在站点中搜索关键词，不需要精确的媒体名称",
                inputSchema={
                    "type": "object",
                    "required": ["keyword"],
                    "properties": {
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词，模糊的影视名字"
                        },
                        "page": {
                            "type": "integer",
                            "description": "页码，默认为0"
                        },
                        "sites": {
                            "type": "string",
                            "description": "站点ID列表，多个站点ID用逗号分隔，是数字ID不是站点名称，若没有站点ID可以通过工具get-sites获取"
                        },
                        "detailed": {
                            "type": "boolean",
                            "description": "是否显示详细信息，默认为false，设置为true会显示更多资源详情"
                        }
                    },
                },
            ),
            types.Tool(
                name="get-downloaders",
                description="获取可用的下载器列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="download-torrent",
                description="下载指定的种子资源。处理用户下载请求时，建议先调用get-media-prompt工具获取处理指南，再调用search-movie工具找到合适的资源。",
                inputSchema={
                    "type": "object",
                    "required": ["torrent_url", "media_type"],
                    "properties": {
                        "torrent_url": {
                            "type": "string",
                            "description": "要下载的种子资源链接"
                        },
                        "downloader": {
                            "type": "string",
                            "description": "下载器名称"
                        },
                        "save_path": {
                            "type": "string",
                            "description": "保存路径"
                        },
                        "media_type": {
                            "type": "string",
                            "description": "电影 or 电视剧"
                        }
                    },
                },
            )
        ]
