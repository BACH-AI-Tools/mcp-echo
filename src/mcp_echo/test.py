#!/usr/bin/env python3
"""
Echo MCP Server
一个简单的MCP服务器，提供echo工具：输入什么返回什么
无需外部依赖，可单文件独立运行
"""

import sys
import json
import asyncio
import logging
from typing import Any, Dict, Optional

# 配置日志（输出到 stderr，避免干扰 stdio 通信）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger("echo-server")

# 用于确保请求按顺序处理的锁
_request_lock = asyncio.Lock()


class MCPServer:
    """简化的 MCP 服务器实现"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个 MCP 消息"""
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        
        logger.info(f"[消息 {msg_id}] 收到请求: {method}")
        
        try:
            # 处理不同的方法
            if method == "initialize":
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                result = await self.handle_call_tool(params)
            elif method == "ping":
                result = {}
            else:
                raise ValueError(f"未知的方法: {method}")
            
            # 返回成功响应
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            logger.info(f"[消息 {msg_id}] 处理成功")
            return response
            
        except Exception as e:
            # 返回错误响应
            logger.error(f"[消息 {msg_id}] 处理失败: {str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }
    
    async def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理初始化请求"""
        self.initialized = True
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": self.name,
                "version": "0.1.2"
            }
        }
    
    async def handle_list_tools(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """列出可用的工具"""
        return {
            "tools": [
                {
                    "name": "echo",
                    "description": "输入什么就返回什么的echo工具。可以用来测试MCP连接或简单地回显文本。",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "要回显的消息内容"
                            }
                        },
                        "required": ["message"]
                    }
                }
            ]
        }
    
    async def handle_call_tool(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """处理工具调用"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        # 生成请求标识用于日志追踪
        request_id = id(arguments)
        logger.info(f"[请求 {request_id}] 调用工具: {name}, 参数: {arguments}")
        
        # 使用锁确保请求按顺序处理，避免并发时的响应混乱
        async with _request_lock:
            try:
                if name == "echo":
                    message = arguments.get("message", "")
                    logger.info(f"[请求 {request_id}] 处理消息: {message}")
                    
                    # 返回结果
                    result = {
                        "content": [
                            {
                                "type": "text",
                                "text": str(message)  # 确保是新的字符串对象
                            }
                        ]
                    }
                    
                    logger.info(f"[请求 {request_id}] 返回结果: {message}")
                    return result
                else:
                    error_msg = f"未知的工具: {name}"
                    logger.error(f"[请求 {request_id}] {error_msg}")
                    raise ValueError(error_msg)
                    
            except Exception as e:
                logger.error(f"[请求 {request_id}] 处理失败: {str(e)}")
                raise


async def read_message() -> Optional[Dict[str, Any]]:
    """从 stdin 读取一条 JSON-RPC 消息"""
    loop = asyncio.get_event_loop()
    
    try:
        # 异步读取一行
        line = await loop.run_in_executor(None, sys.stdin.readline)
        
        if not line:
            return None
        
        line = line.strip()
        if not line:
            return None
        
        # 解析 JSON
        message = json.loads(line)
        return message
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}, 内容: {line}")
        return None
    except Exception as e:
        logger.error(f"读取消息错误: {e}")
        return None


def write_message(message: Dict[str, Any]) -> None:
    """向 stdout 写入一条 JSON-RPC 消息"""
    try:
        output = json.dumps(message, ensure_ascii=False)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
    except Exception as e:
        logger.error(f"写入消息错误: {e}")


async def main_loop():
    """主事件循环"""
    server = MCPServer("echo-server")
    logger.info("Echo MCP Server 启动成功")
    
    try:
        while True:
            # 读取消息
            message = await read_message()
            
            if message is None:
                # stdin 关闭，退出
                logger.info("stdin 已关闭，服务器退出")
                break
            
            # 处理消息
            response = await server.handle_message(message)
            
            # 发送响应
            if response:
                write_message(response)
                
    except KeyboardInterrupt:
        logger.info("收到中断信号，服务器退出")
    except Exception as e:
        logger.error(f"服务器错误: {e}", exc_info=True)


def main():
    """主函数"""
    try:
        asyncio.run(main_loop())
    except Exception as e:
        logger.error(f"启动失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
