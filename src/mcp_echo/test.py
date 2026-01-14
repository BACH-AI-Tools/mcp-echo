#!/usr/bin/env python3
"""
Echo MCP Server
一个简单的MCP服务器，提供echo工具：输入什么返回什么
无需外部依赖，可单文件独立运行

并发安全设计：
- 使用全局锁确保 读取-处理-写入 整个流程是原子性的
- 严格串行处理，确保请求和响应一一对应
- 详细的日志追踪，方便排查并发问题
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

# 全局锁：确保整个消息处理流程（读取-处理-写入）是原子性的
# 这样可以避免多个并发请求的响应混乱
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
        
        logger.info(f"[MSG] 开始处理: id={msg_id}, method={method}")
        
        try:
            # 处理不同的方法
            if method == "initialize":
                logger.info(f"[MSG] 处理初始化: id={msg_id}")
                result = await self.handle_initialize(params)
            elif method == "tools/list":
                logger.info(f"[MSG] 列出工具: id={msg_id}")
                result = await self.handle_list_tools(params)
            elif method == "tools/call":
                logger.info(f"[MSG] 调用工具: id={msg_id}")
                result = await self.handle_call_tool(params)
            elif method == "ping":
                logger.info(f"[MSG] Ping: id={msg_id}")
                result = {}
            else:
                raise ValueError(f"未知的方法: {method}")
            
            # 返回成功响应
            response = {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result
            }
            logger.info(f"[MSG] 处理成功: id={msg_id}, method={method}")
            return response
            
        except Exception as e:
            # 返回错误响应
            logger.error(f"[MSG] 处理失败: id={msg_id}, method={method}, error={str(e)}")
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
        logger.info(f"[TOOL] 调用工具: {name}, 参数: {arguments}, request_id={request_id}")
        
        try:
            if name == "echo":
                message = arguments.get("message", "")
                logger.info(f"[TOOL] 处理消息: {message}, request_id={request_id}")
                
                # 创建新的字符串对象，确保不共享引用
                message_copy = str(message)
                
                # 返回结果
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": message_copy
                        }
                    ]
                }
                
                logger.info(f"[TOOL] 返回结果: {message_copy}, request_id={request_id}")
                return result
            else:
                error_msg = f"未知的工具: {name}"
                logger.error(f"[TOOL] {error_msg}, request_id={request_id}")
                raise ValueError(error_msg)
                
        except Exception as e:
            logger.error(f"[TOOL] 处理失败: {str(e)}, request_id={request_id}")
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
        logger.info(f"[READ] 读取到消息: id={message.get('id')}, method={message.get('method')}")
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
        msg_id = message.get("id")
        has_error = "error" in message
        logger.info(f"[WRITE] 写入响应: id={msg_id}, error={has_error}")
        
        output = json.dumps(message, ensure_ascii=False)
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
        
        logger.info(f"[WRITE] 响应已发送: id={msg_id}")
    except Exception as e:
        logger.error(f"写入消息错误: {e}")


async def main_loop():
    """主事件循环 - 严格串行处理"""
    server = MCPServer("echo-server")
    logger.info("Echo MCP Server 启动成功（严格串行模式）")
    
    try:
        while True:
            # 使用全局锁确保整个 读取-处理-写入 流程是原子性的
            async with _request_lock:
                logger.info("=" * 60)
                logger.info("[LOOP] 等待新消息...")
                
                # 读取消息
                message = await read_message()
                
                if message is None:
                    # stdin 关闭，退出
                    logger.info("stdin 已关闭，服务器退出")
                    break
                
                # 处理消息
                logger.info(f"[LOOP] 开始处理消息: id={message.get('id')}")
                response = await server.handle_message(message)
                
                # 发送响应
                if response:
                    write_message(response)
                    logger.info(f"[LOOP] 消息处理完成: id={message.get('id')}")
                else:
                    logger.warning(f"[LOOP] 没有响应: id={message.get('id')}")
                
                logger.info("=" * 60)
                
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
