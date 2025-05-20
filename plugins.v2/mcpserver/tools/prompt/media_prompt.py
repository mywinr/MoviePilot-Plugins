import logging
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class MediaPromptTool(BaseTool):
    """媒体处理提示工具，用于生成处理模糊影视资源名称的提示"""

    async def execute(self, tool_name: str, arguments: dict) -> list[types.TextContent]:
        """执行工具逻辑"""
        if tool_name == "get-media-prompt":
            return await self._get_media_prompt(arguments)
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _get_media_prompt(self, arguments: dict) -> list[types.TextContent]:
        """
        获取处理媒体资源的提示
        参数:
            - prompt_type: 提示类型，如 'subscribe', 'search', 'download' 等
        """
        prompt_type = arguments.get("prompt_type", "subscribe")

        # 根据不同的提示类型返回不同的提示内容
        if prompt_type == "subscribe":
            return self._get_subscribe_prompt()
        elif prompt_type == "search":
            return self._get_search_prompt()
        elif prompt_type == "download":
            return self._get_download_prompt()
        elif prompt_type == "recognize":
            return self._get_recognize_prompt()
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的提示类型 '{prompt_type}'"
                )
            ]

    def _get_subscribe_prompt(self) -> list[types.TextContent]:
        """获取订阅媒体资源的提示"""
        prompt = """
# 媒体资源订阅处理指南

将用户模糊的影视资源名称转换为订阅参数：

1. **提取关键信息**：名称、年份、类型(电影/电视剧/动漫)、季数
2. **处理流程**：
   - 调用recognize-media工具识别媒体
   - 构建订阅参数(name, type, year, season等)
   - 向用户确认订阅信息
   - 用户确认后，调用add-subscribe工具
   - 除非用户明确指定的参数和必填的参数外，其余参数留空

## 示例
用户输入: "订阅权力的游戏第八季"
处理后:
```
{
  "name": "权力的游戏",
  "type": "电视剧",
  "season": 8
}
```

## 重要提示
- 在执行订阅操作前，必须向用户展示识别结果并获取确认
- 确认格式: "我已识别到[媒体名称][类型][年份]，确认要订阅吗？"
- 只有用户明确同意后才执行订阅操作
"""

        return [
            types.TextContent(
                type="text",
                text=prompt
            )
        ]

    def _get_search_prompt(self) -> list[types.TextContent]:
        """获取搜索媒体资源的提示"""
        prompt = """
# 媒体资源搜索处理指南

将用户的搜索请求转换为搜索参数：

1. **提取搜索信息**：
   - 关键词(keyword)：影视作品名称（必需）
   - sites：站点ID列表（必需），必须指定1-3个站点ID，按照优先级高到低依次选取，可通过get-sites工具获取
   - 年份(year)：发行年份（可选）
   - 清晰度(resolution)：如1080p、4K等（可选）
   - 媒体类型(media_type)：电影或电视剧（可选）

2. **选择搜索工具**：
   - 【重要】必须使用sites参数指定1-3个站点ID进行搜索，这是强制要求
   - 如果不知道站点ID，先调用get-sites工具获取站点列表
   - 明确资源：使用search-movie工具
   - 模糊搜索：使用fuzzy-search-movie工具

3. **分批搜索策略**：
   - 如果第一批站点没有找到满意的资源，可以使用不同的站点ID再次搜索
   - 例如：先搜索站点1,2,3，如果没有满意结果，再搜索站点4,5,6

4. **停止条件**
   - 一旦找到满意的资源，立即停止搜索
   - 3次搜索均为找到资源立即停止搜索

## 示例
用户输入: "找一下阿凡达高清资源"
处理后:
```
工具: search-movie
参数: {
  "keyword": "阿凡达",
  "resolution": "1080p",
  "sites": "1,2,3"  // 必须指定1-3个站点ID
}
```

## 处理流程
1. 调用recognize-media工具识别媒体
2. 根据识别结果选择合适的搜索工具
3. 展示搜索结果给用户
"""

        return [
            types.TextContent(
                type="text",
                text=prompt
            )
        ]

    def _get_download_prompt(self) -> list[types.TextContent]:
        """获取下载媒体资源的提示"""
        prompt = """
# 媒体资源下载处理指南

处理用户下载请求的简要流程：

1. **下载参数**：
   - 种子链接(torrent_url)：必需
   - 媒体类型(media_type)：电影或电视剧，必需
   - 下载器(downloader)：可选
   - 保存路径(save_path)：可选

2. **处理流程**：
   - 识别媒体：调用recognize-media工具
   - 搜索资源：使用search-movie工具
   - 确认下载：向用户展示资源信息并获取确认
   - 执行下载：用户确认后调用download-torrent工具

## 示例
```
工具: download-torrent
参数: {
  "torrent_url": "https://example.com/torrent/12345",
  "media_type": "电影"
}
```

## 重要提示
- 下载前必须向用户确认，格式："我找到了[媒体名称][清晰度]资源，确认下载吗？"
- 只有用户明确同意后才执行下载操作
- 如无法确定媒体类型，默认使用"电影"
"""

        return [
            types.TextContent(
                type="text",
                text=prompt
            )
        ]

    def _get_recognize_prompt(self) -> list[types.TextContent]:
        """获取识别媒体资源的提示"""
        prompt = """
# 媒体资源识别指南

将用户模糊的影视资源名称转换为识别参数：

1. **识别参数**：
   - title(必需)：媒体标题，尽量准确
   - year(可选)：发行年份，四位数字
   - type(可选)：媒体类型，"电影"或"电视剧"

2. **处理技巧**：
   - 根据你的知识库，使用资源的真实名称
   - 提取核心名称，去除无关词汇
   - 区分同名作品：通过年份区分
   - 系列作品：确定具体哪一部

## 示例
用户输入: "我想看去年的新蝙蝠侠"
处理后:
```
工具: recognize-media
参数: {
  "title": "蝙蝠侠",
  "year": "2022",
  "type": "电影"
}
```

## 识别结果包含
- 标准化的标题和年份
- TMDB/豆瓣/IMDB ID
- 媒体类型和评分
- 季集信息(电视剧)
- 简介

识别结果可用于后续搜索、下载或订阅操作。
"""

        return [
            types.TextContent(
                type="text",
                text=prompt
            )
        ]

    @property
    def tool_info(self) -> list[types.Tool]:
        """返回工具信息"""
        return [
            types.Tool(
                name="get-media-prompt",
                description="【重要】获取处理媒体资源的详细指南，包含如何限制搜索结果数量避免token超限。在使用search-movie或fuzzy-search-movie工具前，请先调用此工具获取搜索指南。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "prompt_type": {
                            "type": "string",
                            "description": "提示类型: subscribe(订阅)/search(搜索)/download(下载)/recognize(识别)",
                            "enum": ["subscribe", "search", "download", "recognize"]
                        }
                    }
                },
            )
        ]
