#!/usr/bin/env python3
"""
Echo MCP Server
一个简单的MCP服务器，提供echo工具：输入什么返回什么
"""

import asyncio
import mcp
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent


# 创建服务器实例
app = Server("echo-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """
    列出可用的工具
    """
    return [
        Tool(
            name="echo",
            description="输入什么就返回什么的echo工具。可以用来测试MCP连接或简单地回显文本。",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {
                        "type": "string",
                        "description": "要回显的消息内容"
                    },
                    "delay": {
                        "type": "integer",
                        "description": "延迟秒数，用于测试并发场景",
                        "default": 0,
                        "minimum": 0
                    }
                },
                "required": ["message"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    处理工具调用
    """
    if name == "echo":
        message = arguments.get("message", "")
        delay = arguments.get("delay", 0)
        
        # 如果设置了延迟，则等待指定的秒数
        if delay > 0:
            await asyncio.sleep(delay)
        
        return [
            TextContent(
                type="text",
                text=message
            )
        ]
    else:
        raise ValueError(f"未知的工具: {name}")


def main():
    """
    主函数：运行stdio服务器
    """
    async def run():
        async with stdio_server() as (read_stream, write_stream):
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )
    
    asyncio.run(run())


if __name__ == "__main__":
    main()
