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
            )
        ]

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> types.GetPromptResult:
        """Get prompt messages for the specified prompt name and arguments"""
        if name == "search-movie-strategy":
            return await self._get_search_movie_strategy(arguments)
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
                f"1. **一次只搜索一个站点**：不要同时从多个站点搜索资源，这会导致效率低下。\n"
                f"2. **逐个站点搜索**：先从一个站点开始搜索，如果找不到满足需求的资源，再尝试下一个站点。\n"
                f"3. **使用站点ID**：使用`sites`参数指定单个站点ID进行搜索，例如`sites=\"1\"`。\n"
                f"4. **评估搜索结果**：\n"
                f"   - 检查资源的分辨率（优先选择1080p或更高）\n"
                f"   - 检查做种人数（做种人数越多下载速度越快）\n"
                f"   - 检查资源大小（通常大小适中的资源质量更好）\n"
                f"   - 检查字幕信息（优先选择带有中文字幕的资源）\n"
                f"5. **找到合适资源后停止**：一旦找到满足需求的资源，不要继续搜索其他站点。\n\n"
                f"## 搜索失败时的策略\n\n"
                f"如果使用`search-movie`工具无法找到资源，可能是因为：\n"
                f"1. 电影名称不准确或无法识别\n"
                f"2. 站点中没有该资源\n\n"
                f"此时，可以尝试：\n"
                f"1. 使用`fuzzy-search-movie`工具进行模糊搜索\n"
                f"2. 尝试使用不同的电影名称变体\n"
                f"3. 尝试使用原始语言的电影名称\n\n"
                f"记住：高效的搜索策略是一次只搜索一个站点，找到合适资源后立即停止搜索。"
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
