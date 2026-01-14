#!/usr/bin/env python3
"""
Echo MCP Server
一个简单的MCP服务器，提供echo工具：输入什么返回什么
"""

import asyncio
import logging
from typing import Any
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("echo-server")

# 创建服务器实例
app = Server("echo-server")

# 用于确保请求按顺序处理的锁
_request_lock = asyncio.Lock()


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
    使用锁确保并发请求不会相互干扰
    """
    # 生成请求标识用于日志追踪
    request_id = id(arguments)
    logger.info(f"[请求 {request_id}] 收到工具调用: {name}, 参数: {arguments}")
    
    # 使用锁确保请求按顺序处理，避免并发时的响应混乱
    async with _request_lock:
        try:
            if name == "echo":
                message = arguments.get("message", "")
                logger.info(f"[请求 {request_id}] 处理消息: {message}")
                
                # 复制消息内容，确保不共享引用
                result = [
                    TextContent(
                        type="text",
                        text=str(message)  # 确保是新的字符串对象
                    )
                ]
                
                logger.info(f"[请求 {request_id}] 返回结果: {message}")
                return result
            else:
                error_msg = f"未知的工具: {name}"
                logger.error(f"[请求 {request_id}] {error_msg}")
                raise ValueError(error_msg)
        except Exception as e:
            logger.error(f"[请求 {request_id}] 处理失败: {str(e)}")
            raise


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
