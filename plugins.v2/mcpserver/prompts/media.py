"""
Media-related prompts for MCP Server.
"""
import logging
from typing import List, Dict, Any, Optional

import mcp.types as types

from .base import BasePrompt

# Configure logging
logger = logging.getLogger(__name__)


class MediaPrompt(BasePrompt):
    """Media-related prompts"""

    @property
    def prompt_info(self) -> List[types.Prompt]:
        """Return prompt description information"""
        return [
            types.Prompt(
                name="search-movie-strategy",
                description="指导如何高效地搜索电影资源",
                arguments=[
                    types.PromptArgument(
                        name="keyword",
                        description="电影名称关键词",
                        required=True
                    ),
                    types.PromptArgument(
                        name="year",
                        description="电影年份，如 2023",
                        required=False
                    )
                ]
            ),
            types.Prompt(
                name="person-credits-strategy",
                description="指导如何搜索和展示演员、导演等人物的参演作品",
                arguments=[
                    types.PromptArgument(
                        name="name",
                        description="人物姓名",
                        required=True
                    ),
                    types.PromptArgument(
                        name="year",
                        description="筛选特定年份的作品",
                        required=False
                    )
                ]
            )
        ]

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """Get prompt messages for the specified prompt name and arguments"""
        if name == "search-movie-strategy":
            return await self._get_search_movie_strategy(arguments)
        elif name == "person-credits-strategy":
            return await self._get_person_credits_strategy(arguments)
        else:
            raise ValueError(f"Unknown prompt: '{name}'")

    async def _get_search_movie_strategy(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """Get search movie strategy prompt"""
        try:
            keyword = arguments.get("keyword", "未知电影") if arguments else "未知电影"
            year = arguments.get("year", "") if arguments else ""

            search_strategy = (
                f"# 电影资源搜索策略\n\n"
                f"你正在搜索电影 \"{keyword}\" {year or ''}的资源。为了高效地找到合适的资源，请遵循以下策略：\n\n"
                f"## 搜索策略\n\n"
                f"1. **首先使用search-media工具**：\n"
                f"   - 使用`search-media`工具获取可能的资源列表供用户选择\n"
                f"   - 如果返回结果仅有一条，则直接使用该资源的mediaid进行后续操作\n"
                f"   - 如果返回多条结果，让用户选择最匹配的一条\n"
                f"2. **搜索站点**：若用户没有指定站点则依次从优先级高到低选择5个站点搜索，站点id可通过get-sites工具获取。\n"
                f"3. **停止条件**：如果搜索到符合条件的资源或者搜索了3轮仍没有合适的资源也停止\n"
                f"4. **参数**：如果用户没有指定年份、分辨率等参数则保持空\n"
                f"5. **评估搜索结果**：\n"
                f"   - 检查资源的分辨率\n"
                f"   - 检查做种人数（做种人数越多下载速度越快）\n"
                f"   - 检查资源大小（通常大小适中的资源质量更好）\n"
                f"   - 检查字幕信息（优先选择带有中文字幕的资源）\n\n"
                f"## 搜索失败时的策略\n\n"
                f"如果使用`search-movie`工具无法找到资源，可能是因为：\n"
                f"1. 电影名称不准确或无法识别\n"
                f"2. 站点中没有该资源\n\n"
                f"此时，可以尝试：\n"
                f"1. 使用`fuzzy-search-movie`工具进行模糊搜索\n"
                f"2. 尝试使用不同的电影名称变体\n"
                f"3. 尝试使用原始语言的电影名称\n"
            )

            # 创建并返回提示结果
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=search_strategy
                        )
                    )
                ]
            )
        except Exception as e:
            logger.error(f"生成搜索策略提示时出错: {str(e)}")
            # 返回一个简单的错误提示
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text="生成搜索策略提示时出错，请使用search-movie工具时一次只搜索一个站点，找到合适资源后停止搜索。"
                        )
                    )
                ]
            )

    async def _get_person_credits_strategy(
        self, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """Get person credits strategy prompt"""
        try:
            name = arguments.get("name", "未知人物") if arguments else "未知人物"
            year = arguments.get("year") if arguments else None
            year_text = f"（{year}年）" if year else ""

            person_credits_strategy = (
                f"# 人物作品搜索与展示策略\n\n"
                f"你正在搜索 \"{name}\"{year_text} 的参演作品。为了高效展示该人物的作品信息，请遵循以下策略：\n\n"
                f"## 搜索策略\n\n"
                f"1. **首先使用search-media工具搜索人物**：\n"
                f"   - 使用`search-media`工具，参数 keyword=\"{name}\"，type=\"person\" 搜索该人物\n"
                f"   - 如果返回多个结果，请向用户展示这些结果，并请用户确认是哪一个人物\n"
                f"   - 如果只返回一个结果，可以直接使用该结果的person_id进行下一步\n\n"
                f"2. **使用person-credits工具获取作品列表**：\n"
                f"   - 使用`person-credits`工具，参数 person_id=获取到的ID值，page=1\n"
                f"   {f'- 添加 year={year} 参数筛选{year}年的作品' if year else '- 可以添加year参数按年份筛选，例如 year=2023 只显示2023年的作品'}\n"
                f"   - **如果用户指定了year参数**：可以遍历所有页面直到返回空结果\n"
                f"   - **如果用户没有指定year参数**：展示第一页后，询问用户是否需要查看下一页\n"
                f"   - 不要在没有年份限制的情况下一次性查询所有页面，这会浪费token\n\n"
                f"3. **展示详细信息**：\n"
                f"   - 展示每部作品的完整信息，包括标题、年份、简介等\n"
                f"   - **以Markdown格式展示海报**：使用`![电影标题](海报链接)`格式显示海报图片\n"
                f"   - 将详情链接格式化为可点击的Markdown链接：`[详情](详情链接)`\n"
                f"   - 按年份排序，最新的作品排在前面\n"
                f"   - 分类展示电影和电视剧作品\n\n"
                f"4. **提供进一步操作建议**：\n"
                f"   - 询问用户是否对某部作品感兴趣\n"
                f"   - 如果用户对某部作品感兴趣，可以使用search-movie工具搜索该作品的资源\n"
                f"   - 提示用户可以使用tmdb_id作为mediaid参数进行精确搜索\n"
                f"   - 提示用户可以通过指定year参数来筛选特定年份的作品\n\n"
                f"## 注意事项\n\n"
                f"1. **查询策略**：\n"
                f"   - 有年份限制时：可以遍历所有页面获取完整作品列表\n"
                f"   - 无年份限制时：分页展示，询问用户是否继续查看下一页\n"
                f"2. 展示**完整的**作品信息，包括海报和详情链接\n"
                f"3. 如果作品数量很多，建议用户使用year参数按年份筛选\n"
                f"4. 对于重要作品或用户可能感兴趣的作品，可以重点推荐\n"
            )

            # 创建并返回提示结果
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text=person_credits_strategy
                        )
                    )
                ]
            )
        except Exception as e:
            logger.error(f"生成人物作品搜索策略提示时出错: {str(e)}")
            # 返回一个简单的错误提示
            return types.GetPromptResult(
                messages=[
                    types.PromptMessage(
                        role="user",
                        content=types.TextContent(
                            type="text",
                            text="生成人物作品搜索策略提示时出错，请先使用search-media工具搜索人物，然后使用person-credits工具获取作品信息。"
                        )
                    )
                ]
            )
