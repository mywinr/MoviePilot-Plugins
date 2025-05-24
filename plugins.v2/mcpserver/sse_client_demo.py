#!/usr/bin/env python3
"""
MCP SSE Client Demo
测试 SSE MCP 服务器的客户端
"""

import asyncio
import logging
from mcp.client.sse import sse_client
from mcp import ClientSession

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_sse_connection(sse_url, auth_token, test_name):
    """测试SSE连接的通用函数"""
    print(f"\n{'='*50}")
    print(f"测试: {test_name}")
    print(f"URL: {sse_url}")
    print(f"{'='*50}")

    # 设置请求头，包含认证信息
    headers = {
        "Authorization": f"Bearer {auth_token}"
    }

    try:
        # 连接到 SSE 服务器
        async with sse_client(sse_url, headers=headers) as (read_stream, write_stream):
            print("✓ SSE 连接已建立")

            # 创建客户端会话
            async with ClientSession(read_stream, write_stream) as session:
                print("✓ 正在初始化 MCP 会话...")

                # 初始化连接
                await session.initialize()
                print("✓ MCP 会话初始化完成")

                # 列出可用工具
                print("\n--- 可用工具列表 ---")
                try:
                    tools_result = await session.list_tools()
                    tools = tools_result.tools if hasattr(tools_result, 'tools') else tools_result
                    print(f"✓ 获取到 {len(tools)} 个工具:")

                    for i, tool in enumerate(tools[:3]):  # 只显示前3个工具
                        if hasattr(tool, 'name') and hasattr(tool, 'description'):
                            print(f"  {i+1}. {tool.name}: {tool.description[:50]}...")
                        else:
                            print(f"  {i+1}. {tool}")

                except Exception as e:
                    print(f"✗ 获取工具列表失败: {str(e)}")

                # 测试调用工具
                print("\n--- 测试调用工具 ---")
                try:
                    # 调用一个简单的工具
                    tool_result = await session.call_tool("user-info", {})
                    print("✓ 工具调用成功:")
                    for content in tool_result.content:
                        if hasattr(content, 'text'):
                            print(f"  {content.text[:100]}...")
                        else:
                            print(f"  {str(content)[:100]}...")

                except Exception as e:
                    print(f"✗ 工具调用失败: {str(e)}")

                print(f"\n✓ {test_name} 测试完成")
                return True

    except Exception as e:
        print(f"✗ {test_name} 连接失败: {str(e)}")
        logger.exception("连接异常")
        return False


async def main():
    # 认证令牌 - 需要与mcpserver配置中的auth_token一致
    auth_token = "tupqyd-wUbsys-4cokby"

    print("开始测试SSE服务器连接...")

    # 测试1: 局域网访问
    lan_url = "http://192.168.1.98:3111/sse"
    lan_success = await test_sse_connection(lan_url, auth_token, "局域网访问测试")

    # 测试2: 公网访问
    wan_url = "https://domain:4111/sse"
    wan_success = await test_sse_connection(wan_url, auth_token, "公网访问测试")

    # 总结测试结果
    print(f"\n{'='*50}")
    print("测试结果总结:")
    print(f"局域网访问 (http://192.168.1.98:3111): {'✓ 成功' if lan_success else '✗ 失败'}")
    print(f"公网访问 (https://domain:4111): {'✓ 成功' if wan_success else '✗ 失败'}")
    print(f"{'='*50}")




if __name__ == "__main__":
    asyncio.run(main())
