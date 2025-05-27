import json
import logging
import mcp.types as types
from ..base import BaseTool


# Configure logging
logger = logging.getLogger(__name__)


class SubscribeTool(BaseTool):
    async def execute(
        self, tool_name: str, arguments: dict
    ) -> list[types.TextContent]:
        """执行工具逻辑"""
        if tool_name == "list-subscribes":
            return await self._list_subscribes()
        elif tool_name == "add-subscribe":
            return await self._add_subscribe(arguments)
        elif tool_name == "delete-subscribe":
            return await self._delete_subscribe(arguments)
        elif tool_name == "get-subscribe-detail":
            return await self._get_subscribe_detail(arguments)
        elif tool_name == "update-subscribe":
            return await self._update_subscribe(arguments)
        elif tool_name == "get-subscribe-by-media":
            return await self._get_subscribe_by_media(arguments)
        else:
            return [
                types.TextContent(
                    type="text",
                    text=f"错误：未知的工具 '{tool_name}'"
                )
            ]

    async def _list_subscribes(self) -> list[types.TextContent]:
        """获取所有订阅资源列表"""
        response = await self._make_request(
            method="GET",
            endpoint="/api/v1/subscribe/"
        )

        # 检查是否有错误
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取订阅资源失败: {response['error']}"
                )
            ]

        # 格式化订阅信息
        if not response:
            return [
                types.TextContent(
                    type="text",
                    text="暂无订阅资源"
                )
            ]

        # 提取关键信息，使结果更易读
        formatted_subscribes = []
        for item in response:
            sub_info = {
                "id": item.get("id"),
                "name": item.get("name"),
                "year": item.get("year"),
                "type": item.get("type"),
                "tmdbid": item.get("tmdbid"),
                "doubanid": item.get("doubanid"),
                "season": item.get("season"),
                "state": item.get("state"),
                "vote": item.get("vote"),
                "total_episode": item.get("total_episode"),
                "lack_episode": item.get("lack_episode"),
                "username": item.get("username"),
                "date": item.get("date")
            }
            formatted_subscribes.append(json.dumps(
                sub_info, ensure_ascii=False, indent=2))

        return [
            types.TextContent(
                type="text",
                text="订阅资源列表:\n" + "\n".join(formatted_subscribes)
            )
        ]

    async def _add_subscribe(self, arguments: dict) -> list[types.TextContent]:
        """添加新的订阅"""
        # 提取必要参数
        name = arguments.get("name")
        if not name:
            return [
                types.TextContent(
                    type="text",
                    text="错误：缺少必要参数 'name'"
                )
            ]

        # 构建请求参数
        payload = {
            "name": name,
            "type": arguments.get("type", "电影"),  # 默认为电影类型
        }

        # 添加可选参数
        optional_fields = [
            "year", "season", "tmdbid", "doubanid", "keyword",
            "username", "sites", "downloader", "quality",
            "resolution", "effect", "filter", "include", "exclude"
        ]

        for field in optional_fields:
            if field in arguments and arguments[field] is not None:
                payload[field] = arguments[field]

        # 发送请求
        response = await self._make_request(
            method="POST",
            endpoint="/api/v1/subscribe/",
            json_data=payload
        )
        logger.info(f"添加订阅请求参数: {payload}")
        logger.info(f"添加订阅响应: {response}")
        # 处理响应
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"添加订阅失败: {response.get('error')}"
                )
            ]

        # 检查响应中的success字段
        if "success" in response:
            if response.get("success") is True:
                # 成功添加
                return [
                    types.TextContent(
                        type="text",
                        text=f"成功添加订阅: {name}\n" +
                             f"详细信息: {json.dumps(response.get('data', {}), ensure_ascii=False, indent=2)}"
                    )
                ]
            else:
                # 添加失败
                return [
                    types.TextContent(
                        type="text",
                        text=f"添加订阅失败: {response.get('message', '未知错误')}"
                    )
                ]
        else:
            # 未知响应格式，尝试提取有用信息
            logger.warning(f"未知的响应格式: {response}")
            if "data" in response and response.get("data"):
                # 假设成功
                return [
                    types.TextContent(
                        type="text",
                        text=f"成功添加订阅: {name}\n" +
                             f"详细信息: {json.dumps(response.get('data', {}), ensure_ascii=False, indent=2)}"
                    )
                ]
            else:
                # 假设失败
                return [
                    types.TextContent(
                        type="text",
                        text=f"添加订阅状态未知，请检查是否成功: {json.dumps(response, ensure_ascii=False)}"
                    )
                ]

    async def _delete_subscribe(self, arguments: dict) -> list[types.TextContent]:
        """删除订阅"""
        # 提取必要参数
        subscribe_id = arguments.get("id")
        if not subscribe_id:
            return [
                types.TextContent(
                    type="text",
                    text="错误：缺少必要参数 'id'"
                )
            ]

        # 发送请求
        response = await self._make_request(
            method="DELETE",
            endpoint=f"/api/v1/subscribe/{subscribe_id}"
        )
        logger.info(f"删除订阅响应: {response}")

        # 处理响应
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"删除订阅失败: {response.get('error')}"
                )
            ]

        # 检查响应中的success字段
        if "success" in response:
            if response.get("success") is True:
                # 成功删除
                return [
                    types.TextContent(
                        type="text",
                        text=f"成功删除订阅ID: {subscribe_id}"
                    )
                ]
            else:
                # 删除失败，但不显示None
                error_msg = response.get("message")
                if error_msg:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"删除订阅失败: {error_msg}"
                        )
                    ]
                else:
                    # 如果message为None，仍然认为是成功的
                    return [
                        types.TextContent(
                            type="text",
                            text=f"成功删除订阅ID: {subscribe_id}"
                        )
                    ]
        else:
            # 未知响应格式，但大多数情况下删除是成功的
            logger.warning(f"未知的响应格式: {response}")
            # 如果响应为空或者是空对象，认为删除成功
            if not response or (isinstance(response, dict) and not response):
                return [
                    types.TextContent(
                        type="text",
                        text=f"成功删除订阅ID: {subscribe_id}"
                    )
                ]
            else:
                return [
                    types.TextContent(
                        type="text",
                        text=f"删除订阅状态未知，请检查是否成功: {json.dumps(response, ensure_ascii=False)}"
                    )
                ]

    async def _get_subscribe_detail(self, arguments: dict) -> list[types.TextContent]:
        """获取订阅详情"""
        # 提取必要参数
        subscribe_id = arguments.get("id")
        if not subscribe_id:
            return [
                types.TextContent(
                    type="text",
                    text="错误：缺少必要参数 'id'"
                )
            ]

        # 发送请求
        response = await self._make_request(
            method="GET",
            endpoint=f"/api/v1/subscribe/{subscribe_id}"
        )

        # 处理响应
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取订阅详情失败: {response.get('error')}"
                )
            ]

        # 检查响应中的success字段
        if "success" in response:
            if response.get("success") is True:
                # 获取详情数据
                subscribe_data = response.get("data", {})
                if not subscribe_data:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"未找到ID为 {subscribe_id} 的订阅信息"
                        )
                    ]

                # 格式化输出
                formatted_detail = json.dumps(
                    subscribe_data, ensure_ascii=False, indent=2
                )
                return [
                    types.TextContent(
                        type="text",
                        text=f"订阅详情:\n{formatted_detail}"
                    )
                ]
            else:
                # 获取失败
                return [
                    types.TextContent(
                        type="text",
                        text=f"获取订阅详情失败: {response.get('message', '未知错误')}"
                    )
                ]
        else:
            # 未知响应格式，尝试提取有用信息
            logger.warning(f"未知的响应格式: {response}")
            if "data" in response and response.get("data"):
                # 假设成功
                subscribe_data = response.get("data", {})
                formatted_detail = json.dumps(
                    subscribe_data, ensure_ascii=False, indent=2
                )
                return [
                    types.TextContent(
                        type="text",
                        text=f"订阅详情:\n{formatted_detail}"
                    )
                ]
            else:
                # 假设失败
                return [
                    types.TextContent(
                        type="text",
                        text=f"获取订阅详情状态未知: {json.dumps(response, ensure_ascii=False)}"
                    )
                ]

    async def _update_subscribe(self, arguments: dict) -> list[types.TextContent]:
        """更新订阅信息"""
        # 提取必要参数
        subscribe_id = arguments.get("id")
        if not subscribe_id:
            return [
                types.TextContent(
                    type="text",
                    text="错误：缺少必要参数 'id'"
                )
            ]

        # 构建更新参数
        update_fields = [
            "name", "year", "season", "type", "keyword", "tmdbid", "doubanid",
            "sites", "downloader", "quality", "resolution", "effect",
            "filter", "include", "exclude", "state"
        ]

        # 创建包含id的payload
        payload = {"id": subscribe_id}
        for field in update_fields:
            if field in arguments and arguments[field] is not None:
                payload[field] = arguments[field]

        if len(payload) <= 1:  # 只有id字段
            return [
                types.TextContent(
                    type="text",
                    text="错误：未提供任何需要更新的字段"
                )
            ]

        # 发送请求 - 使用正确的端点和方法
        response = await self._make_request(
            method="PUT",
            endpoint="/api/v1/subscribe/",
            json_data=payload
        )
        logger.info(f"更新订阅请求参数: {payload}")
        logger.info(f"更新订阅响应: {response}")

        # 处理响应
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"更新订阅失败: {response.get('error')}"
                )
            ]

        # 检查响应中的success字段
        if "success" in response:
            if response.get("success") is True:
                # 成功更新
                return [
                    types.TextContent(
                        type="text",
                        text=(f"成功更新订阅ID: {subscribe_id}\n"
                              f"更新内容: {json.dumps(payload, ensure_ascii=False, indent=2)}")
                    )
                ]
            else:
                # 更新失败
                return [
                    types.TextContent(
                        type="text",
                        text=f"更新订阅失败: {response.get('message', '未知错误')}"
                    )
                ]
        else:
            # 未知响应格式
            logger.warning(f"未知的响应格式: {response}")
            return [
                types.TextContent(
                    type="text",
                    text=f"更新订阅状态未知: {json.dumps(response, ensure_ascii=False)}"
                )
            ]

    async def _get_subscribe_by_media(self, arguments: dict) -> list[types.TextContent]:
        """通过媒体ID获取订阅信息"""
        # 提取必要参数
        media_id = arguments.get("media_id")
        if not media_id:
            return [
                types.TextContent(
                    type="text",
                    text="错误：缺少必要参数 'media_id'"
                )
            ]

        # 发送请求
        response = await self._make_request(
            method="GET",
            endpoint=f"/api/v1/subscribe/media/{media_id}"
        )
        logger.info(f"获取媒体订阅信息响应: {response}")

        # 处理响应
        if "error" in response:
            return [
                types.TextContent(
                    type="text",
                    text=f"获取媒体订阅信息失败: {response.get('error')}"
                )
            ]

        # 检查响应中的success字段 (新API格式)
        if "success" in response:
            if response.get("success") is True:
                # 获取订阅数据
                subscribe_data = response.get("data", {})
                if not subscribe_data:
                    return [
                        types.TextContent(
                            type="text",
                            text=f"未找到媒体ID为 {media_id} 的订阅信息"
                        )
                    ]

                # 格式化输出
                formatted_detail = json.dumps(
                    subscribe_data, ensure_ascii=False, indent=2
                )
                return [
                    types.TextContent(
                        type="text",
                        text=f"媒体订阅信息:\n{formatted_detail}"
                    )
                ]
            else:
                # 获取失败
                return [
                    types.TextContent(
                        type="text",
                        text=f"获取媒体订阅信息失败: {response.get('message', '未知错误')}"
                    )
                ]
        else:
            # 直接返回Subscribe对象 (旧API格式)
            # 检查是否为空对象或None
            if not response or (isinstance(response, dict) and not response):
                return [
                    types.TextContent(
                        type="text",
                        text=f"未找到媒体ID为 {media_id} 的订阅信息"
                    )
                ]

            # 检查是否有id字段，如果有则认为是有效的Subscribe对象
            if isinstance(response, dict) and "id" in response:
                formatted_detail = json.dumps(
                    response, ensure_ascii=False, indent=2
                )
                return [
                    types.TextContent(
                        type="text",
                        text=f"媒体订阅信息:\n{formatted_detail}"
                    )
                ]
            else:
                # 未知格式
                logger.warning(f"未知的响应格式: {response}")
                return [
                    types.TextContent(
                        type="text",
                        text=f"获取媒体订阅信息状态未知: {json.dumps(response, ensure_ascii=False)}"
                    )
                ]

    @property
    def tool_info(self) -> list[types.Tool]:
        """返回工具信息"""
        return [
            types.Tool(
                name="list-subscribes",
                description="获取当前所有已订阅的资源列表",
                inputSchema={
                    "type": "object",
                    "properties": {},
                },
            ),
            types.Tool(
                name="get-subscribe-by-media",
                description="通过媒体ID获取订阅信息。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "media_id": {
                            "type": "string",
                            "description": "媒体ID，可以是TMDB ID、豆瓣ID或BangumiId等"
                        }
                    },
                    "required": ["media_id"]
                },
            ),
            types.Tool(
                name="add-subscribe",
                description="添加新的影视资源订阅。",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "影视资源名称，必填"
                        },
                        "type": {
                            "type": "string",
                            "description": "资源类型，如：电影、电视剧、动漫等",
                            "enum": ["电影", "电视剧", "动漫"]
                        },
                        "year": {
                            "type": "string",
                            "description": "资源年份，如：2023"
                        },
                        "season": {
                            "type": "integer",
                            "description": "季数，仅电视剧类型需要"
                        },
                        "tmdbid": {
                            "type": "integer",
                            "description": "TMDB ID"
                        },
                        "doubanid": {
                            "type": "string",
                            "description": "豆瓣ID"
                        },
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词，用于精确匹配"
                        },
                        "sites": {
                            "type": "array",
                            "description": "站点列表，指定从哪些站点搜索资源",
                            "items": {
                                "type": "string"
                            }
                        },
                        "downloader": {
                            "type": "string",
                            "description": "下载器名称"
                        },
                        "quality": {
                            "type": "string",
                            "description": "质量要求，如：1080p, 2160p等"
                        },
                        "resolution": {
                            "type": "string",
                            "description": "分辨率要求"
                        },
                        "effect": {
                            "type": "string",
                            "description": "特效要求，如：HDR, DV等"
                        },
                        "filter": {
                            "type": "string",
                            "description": "过滤规则"
                        },
                        "include": {
                            "type": "string",
                            "description": "包含规则"
                        },
                        "exclude": {
                            "type": "string",
                            "description": "排除规则"
                        }
                    },
                    "required": ["name"]
                },
            ),
            types.Tool(
                name="delete-subscribe",
                description="删除指定ID的订阅，",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "订阅ID，必填"
                        }
                    },
                    "required": ["id"]
                },
            ),
            types.Tool(
                name="get-subscribe-detail",
                description="获取某资源订阅详细信息，如更新集数、站点、下载状态等",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "订阅ID，必填"
                        }
                    },
                    "required": ["id"]
                },
            ),
            types.Tool(
                name="update-subscribe",
                description="更新指定ID的订阅信息",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "id": {
                            "type": "integer",
                            "description": "订阅ID，必填"
                        },
                        "name": {
                            "type": "string",
                            "description": "影视资源名称"
                        },
                        "type": {
                            "type": "string",
                            "enum": ["电影", "电视剧", "动漫"]
                        },
                        "year": {
                            "type": "string",
                        },
                        "season": {
                            "type": "integer",
                            "description": "季数，仅电视剧类型需要"
                        },
                        "tmdbid": {
                            "type": "integer",
                            "description": "TMDB ID"
                        },
                        "doubanid": {
                            "type": "string",
                            "description": "豆瓣ID"
                        },
                        "keyword": {
                            "type": "string",
                            "description": "搜索关键词，用于精确匹配"
                        },
                        "sites": {
                            "type": "array",
                            "description": "站点列表，指定从哪些站点搜索资源",
                            "items": {
                                "type": "string"
                            }
                        },
                        "downloader": {
                            "type": "string",
                            "description": "下载器名称"
                        },
                        "quality": {
                            "type": "string",
                            "description": "质量要求，如：1080p, 2160p等"
                        },
                        "resolution": {
                            "type": "string",
                            "description": "分辨率要求"
                        },
                        "effect": {
                            "type": "string",
                            "description": "特效要求，如：HDR, DV等"
                        },
                        "filter": {
                            "type": "string",
                            "description": "过滤规则"
                        },
                        "include": {
                            "type": "string",
                            "description": "包含规则"
                        },
                        "exclude": {
                            "type": "string",
                            "description": "排除规则"
                        },
                        "state": {
                            "type": "string",
                            "description": "订阅状态：N-新建 R-订阅中 P-待定 S-暂停",
                            "enum": ["N", "R", "P", "S"]
                        }
                    },
                    "required": ["id"]
                },
            )
        ]
