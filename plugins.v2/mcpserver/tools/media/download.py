import json
import logging
import anyio
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class MovieDownloadTool(BaseTool):
    """电影搜索和下载工具"""

    async def execute(self, tool_name: str, arguments: dict) -> list[types.TextContent | types.ImageContent]:
        """执行工具逻辑"""
        if tool_name == "search-movie":
            return await self._search_movie(arguments)
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
            media_info = await self._recognize_media(keyword, year, media_type)
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
                "mtype": "电影" if media_type == "电影" else "电视剧"
            }

            # 添加可选参数
            if sites:
                # 尝试获取站点信息，将站点名称转换为站点ID
                try:
                    sites_info = await self._get_sites_info()
                    if sites_info:
                        # 如果用户提供的是站点名称而不是ID，尝试转换
                        site_ids = []
                        site_names = [s.strip() for s in sites.split(',')]

                        for site_name in site_names:
                            # 尝试直接使用站点名称
                            site_found = False
                            for site in sites_info:
                                if isinstance(site, dict):
                                    # 检查站点名称或别名是否匹配
                                    site_name_lower = site_name.lower()
                                    site_name_db = site.get('name', '').lower()
                                    site_id_db = site.get('id', '').lower()
                                    name_match = (
                                        site_name_db == site_name_lower
                                    )
                                    id_match = site_id_db == site_name_lower
                                    if name_match or id_match:
                                        site_ids.append(site.get('id', ''))
                                        site_found = True
                                        break

                            # 如果没找到匹配的站点，仍然添加原始名称
                            if not site_found:
                                site_ids.append(site_name)

                        # 更新参数
                        if site_ids:
                            params["sites"] = ','.join(site_ids)
                        else:
                            params["sites"] = sites
                    else:
                        # 如果无法获取站点信息，使用原始站点参数
                        params["sites"] = sites
                except Exception as e:
                    logger.warning(f"处理站点参数时出错: {str(e)}")
                    # 出错时仍使用原始站点参数
                    params["sites"] = sites

            # 记录搜索参数
            logger.info(f"搜索参数: {json.dumps(params, ensure_ascii=False)}")

            # 调用搜索API
            try:
                response = await self._make_request(
                    method="GET",
                    endpoint=f"/api/v1/search/media/{media_id}",
                    params=params
                )

                # 记录完整响应以便调试
                response_json = json.dumps(response, ensure_ascii=False)
                logger.info(f"搜索API响应: {response_json}")
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

            # 记录种子数据结构
            if not torrents:
                return [
                    types.TextContent(
                        type="text",
                        text=f"未找到符合条件的资源：{keyword} {year or ''}"
                    )
                ]

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
                if not torrent_info and "meta_info" in torrent:
                    # 可能是Context对象的直接序列化
                    torrent_info = torrent

                # 从torrent_info中提取数据
                title = torrent_info.get("title", "未知标题")
                if not title or title == "未知标题":
                    # 尝试从meta_info中获取标题
                    meta_info = torrent.get("meta_info", {})
                    if meta_info:
                        title = meta_info.get("title", "未知标题")

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

                # 从meta_info中提取更多信息
                meta_info = torrent.get("meta_info", {})

                # 提取分辨率
                resolution = "未知分辨率"
                if meta_info:
                    # 尝试直接从标题中提取分辨率
                    title_str = meta_info.get("org_string", "")
                    if title_str:
                        import re
                        # 合并分辨率模式为一个正则表达式，提高效率
                        res_pattern = (
                            r'(4K|1080[pi]|720[pi]|2160[pi]|UHD|'
                            r'MINIBD1080P|BD1080P|HD1080P|BD720P|HD720P)'
                        )
                        res_match = re.search(
                            res_pattern, title_str, re.IGNORECASE)
                        if res_match:
                            resolution = res_match.group(1)

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

                seeders = torrent_info.get("seeders", 0)
                peers = torrent_info.get("peers", 0)

                # 获取资源ID
                torrent_id = torrent_info.get("id")
                if not torrent_id:
                    # 尝试使用enclosure作为ID
                    torrent_id = torrent_info.get("enclosure")

                # 获取下载链接
                download_link = torrent_info.get("enclosure", "")

                # 格式化资源信息
                result_text += f"{i+1}. {title}\n"
                result_text += f"   站点: {site_name} | 大小: {size}\n"
                result_text += (
                    f"   分辨率: {resolution} | "
                    f"视频编码: {video_encode} | "
                    f"音频编码: {audio_encode}\n"
                )
                result_text += f"   资源类型: {resource_type}"
                if resource_team:
                    result_text += f" | 制作组: {resource_team}"
                result_text += "\n"
                result_text += f"   字幕: {subtitle_info} | 音轨: {audio_info}\n"
                result_text += f"   做种: {seeders} | 下载: {peers}\n"

                # 添加资源ID和下载链接
                result_text += f"   资源ID: {torrent_id}\n"
                if download_link:
                    # 截断过长的下载链接
                    short_link = download_link
                    if len(short_link) > 60:
                        short_link = short_link[:57] + "..."
                    result_text += f"   下载链接: {short_link}\n"

                    # 添加下载命令提示
                    result_text += (
                        f"   下载命令: download-torrent "
                        f"torrent_id=\"{download_link}\""
                    )
                    result_text += "\n"
                result_text += "\n"

            result_text += "要下载资源，请复制上面的下载命令或使用 download-torrent 工具并提供下载链接。"

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
            - torrent_id: 种子资源ID或下载链接
            - downloader: 下载器名称(可选)
            - save_path: 保存路径(可选)
            - is_paused: 是否暂停下载(可选)
        """
        torrent_url = arguments.get("torrent_id")
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
        is_paused = arguments.get("is_paused", False)

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
            if is_paused:
                payload["is_paused"] = is_paused

            # 调用mcpserver的下载API
            response = await self._make_request(
                method="POST",
                endpoint="/api/v1/plugin/MCPServer/download_torrent",
                json=payload
            )

            # 记录响应
            logger.info(f"下载API响应: {json.dumps(response, ensure_ascii=False)}")

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

    async def _recognize_media(self, title, year=None, _=None):
        """
        识别媒体信息

        参数:
            title: 媒体标题
            year: 年份（可选）
            _: 媒体类型（未使用）
        """
        params = {"title": title}
        if year:
            params["year"] = year

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
                    result_text += f"{i+1}. {name} ({type_name})\n"
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
                description="搜索电影资源，支持按名称、年份、清晰度等条件搜索",
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
                            "description": "站点ID列表，多个站点ID用逗号分隔"
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
                description="下载指定的种子资源",
                inputSchema={
                    "type": "object",
                    "required": ["torrent_id", "media_type"],
                    "properties": {
                        "torrent_id": {
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
                        },
                        "is_paused": {
                            "type": "boolean",
                            "description": "是否暂停下载"
                        }
                    },
                },
            )
        ]
