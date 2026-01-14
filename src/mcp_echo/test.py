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
import time
import copy
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

# 全局请求序列号，用于追踪和调试
_request_sequence = 0


class MCPServer:
    """简化的 MCP 服务器实现"""
    
    def __init__(self, name: str):
        self.name = name
        self.initialized = False
    
    async def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理单个 MCP 消息"""
        # 深拷贝消息，确保不共享引用
        message = copy.deepcopy(message)
        
        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})
        
        logger.info(f"[MSG] 开始处理: id={msg_id}, method={method}, params={params}")
        
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
                result = await self.handle_call_tool(params, msg_id)
            elif method == "ping":
                logger.info(f"[MSG] Ping: id={msg_id}")
                result = {}
            else:
                raise ValueError(f"未知的方法: {method}")
            
            # 创建完全独立的响应对象
            response = {
                "jsonrpc": "2.0",
                "id": copy.deepcopy(msg_id),  # 确保 id 也是独立的
                "result": copy.deepcopy(result)  # 确保 result 也是独立的
            }
            logger.info(f"[MSG] 处理成功: id={msg_id}, method={method}, result_keys={list(result.keys()) if isinstance(result, dict) else 'not-dict'}")
            return response
            
        except Exception as e:
            # 返回错误响应
            logger.error(f"[MSG] 处理失败: id={msg_id}, method={method}, error={str(e)}")
            return {
                "jsonrpc": "2.0",
                "id": copy.deepcopy(msg_id),
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
                    "description": "输入ct什么就返回什么的echo工具。可以用来测试MCP连接或简单地回显文本。",
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
    
    async def handle_call_tool(self, params: Dict[str, Any], msg_id: Any) -> Dict[str, Any]:
        """处理工具调用"""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        # 生成请求标识用于日志追踪
        timestamp = time.time()
        logger.info(f"[TOOL] 调用工具: name={name}, msg_id={msg_id}, arguments={arguments}, timestamp={timestamp}")
        
        try:
            if name == "echo":
                message = arguments.get("message", "")
                logger.info(f"[TOOL] 处理消息: msg_id={msg_id}, message={message}")
                
                # 创建完全新的字符串对象
                # 使用字符串拼接确保是新对象
                message_result = "" + str(message)
                
                # 创建全新的返回结果，每次都构建新的字典和列表
                result = {
                    "content": [
                        {
                            "type": "text",
                            "text": message_result
                        }
                    ]
                }
                
                logger.info(f"[TOOL] 返回结果: msg_id={msg_id}, text={message_result}, result_id={id(result)}")
                return result
            else:
                error_msg = f"未知的工具: {name}"
                logger.error(f"[TOOL] {error_msg}, msg_id={msg_id}")
                raise ValueError(error_msg)
                
        except Exception as e:
            logger.error(f"[TOOL] 处理失败: msg_id={msg_id}, error={str(e)}")
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
        # 深拷贝消息，确保写入的是独立副本
        message_to_write = copy.deepcopy(message)
        
        msg_id = message_to_write.get("id")
        has_error = "error" in message_to_write
        has_result = "result" in message_to_write
        
        # 如果有 result 且包含 content，记录内容摘要
        content_preview = ""
        if has_result and isinstance(message_to_write.get("result"), dict):
            result = message_to_write["result"]
            if "content" in result and isinstance(result["content"], list) and len(result["content"]) > 0:
                first_content = result["content"][0]
                if "text" in first_content:
                    text = first_content["text"]
                    content_preview = f", content={text[:50]}"
        
        logger.info(f"[WRITE] 准备写入: id={msg_id}, has_error={has_error}, has_result={has_result}{content_preview}")
        
        # 序列化为 JSON
        output = json.dumps(message_to_write, ensure_ascii=False, separators=(',', ':'))
        
        logger.info(f"[WRITE] JSON 长度: {len(output)} 字符")
        
        # 写入 stdout
        sys.stdout.write(output + "\n")
        sys.stdout.flush()
        
        logger.info(f"[WRITE] ✓ 响应已发送: id={msg_id}")
    except Exception as e:
        logger.error(f"[WRITE] ✗ 写入消息错误: {e}", exc_info=True)


async def main_loop():
    """主事件循环 - 严格串行处理"""
    global _request_sequence
    
    server = MCPServer("echo-server")
    logger.info("Echo MCP Server 启动成功（严格串行模式 + 深拷贝隔离）")
    
    try:
        while True:
            # 使用全局锁确保整个 读取-处理-写入 流程是原子性的
            async with _request_lock:
                _request_sequence += 1
                seq = _request_sequence
                
                logger.info("=" * 80)
                logger.info(f"[LOOP-{seq}] 等待新消息...")
                
                # 读取消息
                message = await read_message()
                
                if message is None:
                    # stdin 关闭，退出
                    logger.info("stdin 已关闭，服务器退出")
                    break
                
                msg_id = message.get('id')
                method = message.get('method')
                logger.info(f"[LOOP-{seq}] 收到消息: id={msg_id}, method={method}, message_obj_id={id(message)}")
                
                # 处理消息
                logger.info(f"[LOOP-{seq}] 开始处理: id={msg_id}")
                response = await server.handle_message(message)
                
                # 发送响应
                if response:
                    response_id = response.get('id')
                    logger.info(f"[LOOP-{seq}] 准备发送响应: id={response_id}, response_obj_id={id(response)}")
                    
                    # 验证 id 匹配
                    if response_id != msg_id:
                        logger.error(f"[LOOP-{seq}] ⚠️  ID 不匹配！请求 id={msg_id}, 响应 id={response_id}")
                    else:
                        logger.info(f"[LOOP-{seq}] ✓ ID 匹配: {msg_id}")
                    
                    write_message(response)
                    logger.info(f"[LOOP-{seq}] 消息处理完成: id={msg_id}")
                else:
                    logger.warning(f"[LOOP-{seq}] 没有响应: id={msg_id}")
                
                logger.info("=" * 80)
                
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
