import logging
import anyio
import datetime
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
        elif tool_name == "search-media":
            return await self._search_media_tool(arguments)
        elif tool_name == "person-credits":
            return await self._person_credits_tool(arguments)
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

    async def _search_media_tool(self, arguments: dict) -> list[types.TextContent]:
        """
        搜索媒体信息工具，返回匹配的媒体列表供用户选择
        参数:
            - keyword: 搜索关键词
            - type: 媒体类型(可选)，默认为"media"，可选值："media"(媒体)、"person"(人物)
            - page: 页码(可选)，默认为1
            - count: 每页结果数(可选)，默认为8
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
        media_type = arguments.get("type", "media")
        page = int(arguments.get("page", 1))
        count = int(arguments.get("count", 8))

        try:
            # 调用搜索API
            params = {
                "title": keyword,
                "type": media_type,
                "page": page,
                "count": count
            }

            logger.info(f"搜索媒体信息: {keyword}, 类型: {media_type}")

            response = await self._make_request(
                method="GET",
                endpoint="/api/v1/media/search",
                params=params
            )

            # 检查响应
            if not response or not isinstance(response, list):
                return [
                    types.TextContent(
                        type="text",
                        text=f"搜索媒体信息失败，未找到匹配的结果: {keyword}"
                    )
                ]

            # 如果没有结果
            if len(response) == 0:
                return [
                    types.TextContent(
                        type="text",
                        text=f"未找到与 '{keyword}' 匹配的媒体信息"
                    )
                ]

            # 格式化搜索结果
            result_text = self._format_search_results(response, keyword)

            # 添加使用说明
            if response and isinstance(response[0], dict):
                # 检查是否为人物结果
                if "name" in response[0] and "type" in response[0] and isinstance(response[0]["type"], int):
                    # 人物搜索结果的使用说明
                    result_text += "\n使用说明：\n"
                    result_text += "1. 您可以使用person-credits工具查询该人物的参演作品\n"

                    # 如果只有一个结果，提供具体的person_id
                    if len(response) == 1 and "id" in response[0]:
                        person_id = response[0].get("id")
                        if person_id:
                            result_text += f"2. 例如：person-credits工具，参数 person_id=\"{person_id}\"\n"
                    else:
                        result_text += "2. 例如：选择一个人物，使用其Person ID作为person-credits工具的参数\n"
                else:
                    # 媒体搜索结果的使用说明
                    result_text += "\n使用说明：\n"
                    result_text += "1. 请选择一个媒体项目，然后使用search-movie工具进行资源搜索\n"
                    if len(response) == 1 and "tmdb_id" in response[0]:
                        # 如果只有一个结果，直接提供使用示例
                        tmdb_id = response[0].get("tmdb_id")
                        if tmdb_id:
                            result_text += f"2. 由于只有一个结果，您可以直接使用 'tmdb:{tmdb_id}' 作为search-movie工具的mediaid参数\n"
                    else:
                        # 多个结果，提供一般性使用示例
                        result_text += "2. 例如：选择第1项，使用其TMDB ID作为search-movie工具的mediaid参数\n"

            return [
                types.TextContent(
                    type="text",
                    text=result_text
                )
            ]

        except Exception as e:
            logger.error(f"搜索媒体信息时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"搜索媒体信息时出错: {str(e)}"
                )
            ]

    def _format_search_results(self, results: list, keyword: str) -> str:
        """
        格式化媒体或人物搜索结果

        参数:
            results: 搜索结果列表
            keyword: 搜索关键词

        返回:
            格式化后的文本
        """
        if not results:
            return f"未找到与 '{keyword}' 匹配的信息"

        # 检查结果类型 - 人物还是媒体
        is_person_results = False
        if results and isinstance(results[0], dict):
            # 检查是否为人物结果 - 人物结果有name字段和整数类型的type字段
            if "name" in results[0] and "type" in results[0] and isinstance(results[0]["type"], int):
                is_person_results = True

        if is_person_results:
            return self._format_person_results(results, keyword)
        else:
            return self._format_media_results(results, keyword)

    def _format_person_results(self, results: list, keyword: str) -> str:
        """
        格式化人物搜索结果

        参数:
            results: 人物搜索结果列表
            keyword: 搜索关键词

        返回:
            格式化后的文本
        """
        result_text = f"找到 {len(results)} 个与 '{keyword}' 相关的人物信息：\n\n"

        for i, item in enumerate(results, 1):
            # 提取基本信息
            source = item.get("source", "未知来源")
            name = item.get("name", "未知姓名")
            original_name = item.get("original_name")
            person_id = item.get("id", "")
            gender = item.get("gender")
            known_for = item.get("known_for_department", "")
            popularity = item.get("popularity", 0)
            profile_path = item.get("profile_path", "")

            # 构建姓名行
            result_text += f"{i}. {name} [{source}]\n"

            # 添加原始姓名（如果有且与姓名不同）
            if original_name and original_name != name:
                result_text += f"   原名: {original_name}\n"

            # 添加性别信息
            gender_text = ""
            if gender == 1:
                gender_text = "女"
            elif gender == 2:
                gender_text = "男"

            # 添加基本信息
            info_parts = []
            if gender_text:
                info_parts.append(f"性别: {gender_text}")
            if known_for:
                info_parts.append(f"职业: {known_for}")
            if popularity:
                info_parts.append(f"热度: {popularity}")
            if person_id:
                info_parts.append(f"Person ID: {person_id}")

            if info_parts:
                result_text += f"   {' | '.join(info_parts)}\n"

            # 添加照片链接
            if profile_path:
                if not profile_path.startswith("http"):
                    profile_path = f"https://image.tmdb.org/t/p/original{profile_path}"
                result_text += f"   照片: {profile_path}\n"

            result_text += "\n"

        return result_text

    def _format_media_results(self, results: list, keyword: str) -> str:
        """
        格式化媒体搜索结果

        参数:
            results: 媒体搜索结果列表
            keyword: 搜索关键词

        返回:
            格式化后的文本
        """
        result_text = f"找到 {len(results)} 个与 '{keyword}' 相关的媒体信息：\n\n"

        for i, item in enumerate(results, 1):
            # 提取基本信息
            source = item.get("source", "未知来源")
            title = item.get("title", "未知标题")
            original_title = item.get("original_title")
            year = item.get("year", "")
            media_type = item.get("type", "未知类型")
            tmdb_id = item.get("tmdb_id", "")
            douban_id = item.get("douban_id", "")

            # 构建标题行
            title_line = f"{i}. {title} [{source}]"
            if year:
                title_line += f" ({year})"
            result_text += f"{title_line}\n"

            # 添加原始标题（如果有且与标题不同）
            if original_title and original_title != title:
                result_text += f"   原始标题: {original_title}\n"

            # 添加类型和ID信息
            result_text += f"   类型: {media_type}"

            # 添加ID信息
            id_info = []
            if tmdb_id:
                id_info.append(f"TMDB: {tmdb_id}")
            if douban_id:
                id_info.append(f"豆瓣: {douban_id}")

            if id_info:
                result_text += f" | {' | '.join(id_info)}"
            result_text += f"评分：{item.get('vote_average')}"
            result_text += "\n"

            # 添加简短描述（如果有）
            overview = item.get("overview")
            if overview:
                # 截取简介的前100个字符
                short_overview = overview[:100] + "..." if len(overview) > 100 else overview
                result_text += f"   简介: {short_overview}\n"

            result_text += "\n"

        return result_text

    async def _person_credits_tool(self, arguments: dict) -> list[types.TextContent]:
        """
        查询演员参演作品工具
        参数:
            - person_id: 人物ID (整数)
            - page: 页码 (可选，默认为1)
            - year: 年份 (可选，筛选特定年份的作品)
        """
        # 获取并验证person_id参数
        person_id = arguments.get("person_id")
        if not person_id:
            return [
                types.TextContent(
                    type="text",
                    text="错误：请提供人物ID"
                )
            ]

        # 尝试将person_id转换为整数
        try:
            person_id = int(person_id)
        except ValueError:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：人物ID必须是整数，而不是 '{person_id}'"
                )
            ]

        # 获取页码参数
        page = arguments.get("page", 1)
        try:
            page = int(page)
        except ValueError:
            page = 1

        # 获取年份参数
        year = arguments.get("year")
        if year:
            try:
                year = int(year)
            except ValueError:
                return [
                    types.TextContent(
                        type="text",
                        text=f"错误：年份必须是整数，而不是 '{year}'"
                    )
                ]

        try:
            # 如果指定了年份，获取所有页面的结果
            if year:
                logger.info(f"查询人物参演作品(所有页): person_id={person_id}, year={year}")

                # 存储所有页面的结果
                all_results = []
                current_page = 1

                # 循环获取所有页面的结果，直到返回空列表
                while True:
                    # 构建请求参数
                    params = {"page": current_page}

                    # 调用API获取人物参演作品
                    response = await self._make_request(
                        method="GET",
                        endpoint=f"/api/v1/tmdb/person/credits/{person_id}",
                        params=params
                    )

                    # 检查响应
                    if not response or not isinstance(response, list) or len(response) == 0:
                        # 没有更多结果，退出循环
                        break

                    # 将当前页面的结果添加到总结果中
                    all_results.extend(response)

                    # 增加页码，继续获取下一页
                    current_page += 1

                # 如果没有找到任何结果
                if not all_results:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"未找到人物(ID: {person_id})的参演作品"
                        )
                    ]

                # 格式化结果，传入1作为页码，因为我们已经获取了所有页面
                result_text = self._format_person_credits(all_results, person_id, 1, year)

                return [
                    types.TextContent(
                        type="text",
                        text=result_text
                    )
                ]
            else:
                # 如果没有指定年份，使用常规分页方式
                logger.info(f"查询人物参演作品: person_id={person_id}, page={page}")

                # 构建请求参数
                params = {"page": page}

                # 调用API获取人物参演作品
                response = await self._make_request(
                    method="GET",
                    endpoint=f"/api/v1/tmdb/person/credits/{person_id}",
                    params=params
                )

                # 检查响应
                if not response:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"查询人物参演作品失败: person_id={person_id}"
                        )
                    ]

                # 确保响应格式正确
                if not isinstance(response, list):
                    return [
                        types.TextContent(
                            type="text",
                            text=f"查询人物参演作品返回格式错误: 预期列表，实际为 {type(response).__name__}"
                        )
                    ]

                # 如果列表为空，表示没有找到作品
                if len(response) == 0:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"未找到人物(ID: {person_id})的参演作品"
                        )
                    ]

                # 格式化结果
                result_text = self._format_person_credits(response, person_id, page, year)

                return [
                    types.TextContent(
                        type="text",
                        text=result_text
                    )
                ]

        except Exception as e:
            logger.error(f"查询人物参演作品时出错: {str(e)}")
            return [
                types.TextContent(
                    type="text",
                    text=f"查询人物参演作品时出错: {str(e)}"
                )
            ]

    def _format_person_credits(self, credits_list: list, person_id: int, page: int = 1, year: int = None) -> str:
        """
        格式化人物参演作品信息

        参数:
            credits_list: 参演作品信息列表
            person_id: 人物ID
            page: 当前页码，默认为1
            year: 筛选的年份，默认为None表示所有年份

        返回:
            格式化后的文本
        """
        # 如果列表为空，返回提示信息
        if not credits_list:
            return f"未找到人物(ID: {person_id})的参演作品"

        # 获取第一个作品的人物信息
        first_credit = credits_list[0] if credits_list else {}
        person_name = first_credit.get("name", "未知姓名") if "name" in first_credit else "未知姓名"

        # 分类整理作品
        movie_cast = []
        tv_cast = []

        # 记录过滤前的作品数量
        total_items = len(credits_list)
        filtered_items = 0

        for item in credits_list:
            # 获取作品年份
            item_year = item.get("year", "")

            # 如果指定了年份且作品年份不匹配，则跳过
            if year and str(year) != str(item_year):
                filtered_items += 1
                continue

            # 根据类型分类
            media_type = item.get("type", "")
            if media_type == "电影":
                movie_cast.append(item)
            elif media_type == "电视剧":
                tv_cast.append(item)

        # 构建标题，包含年份信息和过滤信息
        if year:
            # 当指定年份时，我们获取了所有页面的结果
            result_text = f"人物 {person_name} (ID: {person_id}) 的 {year}年 参演作品 (全部)：\n\n"
            if filtered_items > 0:
                result_text += f"注意：已过滤掉 {filtered_items} 个非 {year}年 的作品\n\n"
        else:
            result_text = f"人物 {person_name} (ID: {person_id}) 的参演作品 (第{page}页)：\n\n"

        # 添加电影作品
        if movie_cast:
            result_text += "## 电影作品\n\n"
            # 按年份排序（新的在前）
            movie_cast = sorted(movie_cast, key=lambda x: x.get("year", "0"), reverse=True)
            # 显示所有作品
            for i, movie in enumerate(movie_cast, 1):
                title = movie.get("title", "未知标题")
                original_title = movie.get("original_title")

                # 获取年份信息
                movie_year = movie.get("year", "")

                # 获取TMDB ID
                tmdb_id = movie.get("tmdb_id", "")

                # 获取海报和详情链接
                poster_path = movie.get("poster_path", "")
                detail_link = movie.get("detail_link", "")

                # 构建标题行
                result_text += f"{i}. {title}"
                if movie_year:
                    result_text += f" ({movie_year})"
                result_text += "\n"

                # 添加原始标题（如果有且与标题不同）
                if original_title and original_title != title:
                    result_text += f"   原始标题: {original_title}\n"

                # 添加TMDB ID（如果有）
                if tmdb_id:
                    result_text += f"   TMDB ID: {tmdb_id}\n"

                # 添加海报链接（如果有）
                if poster_path:
                    result_text += f"   海报: {poster_path}\n"

                # 添加详情链接（如果有）
                if detail_link:
                    result_text += f"   详情: {detail_link}\n"

                # 添加简介（如果有）
                overview = movie.get("overview")
                if overview:
                    # 显示完整简介
                    result_text += f"   简介: {overview}\n"

                result_text += "\n"

        # 添加电视剧作品
        if tv_cast:
            result_text += "## 电视剧作品\n\n"
            # 按年份排序（新的在前）
            tv_cast = sorted(tv_cast, key=lambda x: x.get("year", "0"), reverse=True)
            # 显示所有作品
            for i, tv in enumerate(tv_cast, 1):
                # 获取标题
                title = tv.get("title", "未知标题")
                original_title = tv.get("original_title")

                # 获取年份信息
                tv_year = tv.get("year", "")

                # 获取TMDB ID
                tmdb_id = tv.get("tmdb_id", "")

                # 获取海报和详情链接
                poster_path = tv.get("poster_path", "")
                detail_link = tv.get("detail_link", "")

                # 构建标题行
                result_text += f"{i}. {title}"
                if tv_year:
                    result_text += f" ({tv_year})"
                result_text += "\n"

                # 添加原始标题（如果有且与标题不同）
                if original_title and original_title != title:
                    result_text += f"   原始标题: {original_title}\n"

                # 添加TMDB ID（如果有）
                if tmdb_id:
                    result_text += f"   TMDB ID: {tmdb_id}\n"

                # 添加海报链接（如果有）
                if poster_path:
                    result_text += f"   海报: {poster_path}\n"

                # 添加详情链接（如果有）
                if detail_link:
                    result_text += f"   详情: {detail_link}\n"

                # 添加简介（如果有）
                overview = tv.get("overview")
                if overview:
                    # 显示完整简介
                    result_text += f"   简介: {overview}\n"

                result_text += "\n"

        # 如果没有任何作品
        if not movie_cast and not tv_cast:
            result_text += "未找到该人物的参演作品信息。\n"

        # 添加分页导航提示
        if credits_list:  # 如果当前页有结果
            # 构建基本参数
            filter_year = year  # 使用传入的年份参数，而不是被覆盖的变量

            # 如果指定了年份，我们已经获取了所有页面，不需要显示分页导航
            if not filter_year:
                result_text += f"\n## 分页导航\n\n"

                year_param = ""

                if page > 1:
                    result_text += f"查看上一页: person-credits工具，参数 person_id={person_id}, page={page-1}{year_param}\n"

                # 如果当前页有结果，可能还有下一页
                next_page = page + 1
                result_text += f"查看下一页: person-credits工具，参数 person_id={person_id}, page={next_page}{year_param}\n"
                result_text += f"(如果下一页没有结果，则表示已经获取全部作品)\n"

                # 提示用户可以按年份筛选
                result_text += f"\n## 年份筛选\n\n"
                result_text += f"您可以通过添加year参数来筛选特定年份的作品，例如：\n"
                current_year = datetime.datetime.now().year  # 获取当前年份
                result_text += f"- 查看{current_year}年作品: person-credits工具，参数 person_id={person_id}, year={current_year}\n"
                result_text += f"- 查看{current_year-1}年作品: person-credits工具，参数 person_id={person_id}, year={current_year-1}\n"
                result_text += f"- 查看{current_year-2}年作品: person-credits工具，参数 person_id={person_id}, year={current_year-2}\n"
                result_text += f"(当指定年份时，将自动获取该年份的所有作品，无需分页)\n"

        return result_text

    @property
    def tool_info(self) -> list[types.Tool]:
        """返回工具的描述信息"""
        return [
            types.Tool(
                name="recognize-media",
                description="识别媒体信息，根据标题和年份识别电影、电视剧等媒体的详细信息。",
                inputSchema={
                    "type": "object",
                    "required": ["title"],
                    "properties": {
                        "title": {
                            "type": "string",
                        },
                        "year": {
                            "type": "string",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["电影", "电视剧"]
                        }
                    },
                },
            ),
            types.Tool(
                name="search-media",
                description="搜索媒体（media）或人物（person）信息，返回匹配的列表供用户选择。",
                inputSchema={
                    "type": "object",
                    "required": ["keyword"],
                    "properties": {
                        "keyword": {
                            "type": "string",
                        },
                        "type": {
                            "type": "string",
                            "enum": ["media", "person"],
                            "default": "media"
                        },
                        "page": {
                            "type": "integer",
                            "default": 1
                        },
                        "count": {
                            "type": "integer",
                            "default": 8
                        }
                    },
                },
            ),
            types.Tool(
                name="person-credits",
                description="查询演员、导演等人物参演的作品列表。",
                inputSchema={
                    "type": "object",
                    "required": ["person_id"],
                    "properties": {
                        "person_id": {
                            "type": "integer",
                            "description": "可通过search-media工具获取"
                        },
                        "page": {
                            "type": "integer",
                            "default": 1
                        },
                        "year": {
                            "type": "integer",
                        }
                    },
                },
            )
        ]
