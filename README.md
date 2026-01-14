# Echo MCP Server

[![PyPI version](https://badge.fury.io/py/mcp-echo.svg)](https://badge.fury.io/py/mcp-echo)
[![Python Version](https://img.shields.io/pypi/pyversions/mcp-echo.svg)](https://pypi.org/project/mcp-echo/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个简单的MCP (Model Context Protocol) 服务器，提供echo功能：输入什么就返回什么。

## 项目信息

- **作者**: Bach Studio
- **GitHub**: https://github.com/BACH-AI-Tools/mcp-echo
- **PyPI**: https://pypi.org/project/mcp-echo/

## 功能特性

- **echo工具**: 接收一个消息参数，并原样返回该消息
- 简单易用，适合测试MCP连接
- 支持命令行直接运行

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install mcp-echo
```

### 从源码安装

```bash
git clone https://github.com/BACH-AI-Tools/mcp-echo.git
cd mcp-echo
pip install -e .
```

## 使用方法

### 命令行运行

安装后，可以直接使用命令行启动服务器：

```bash
mcp-echo
```

### 在 Cherry Studio 中使用

1. 打开 Cherry Studio
2. 进入设置 -> MCP服务器配置
3. 添加新的MCP服务器配置：

```json
{
  "mcpServers": {
    "echo": {
      "command": "mcp-echo"
    }
  }
}
```

或者使用完整Python路径（如果命令行不可用）：

```json
{
  "mcpServers": {
    "echo": {
      "command": "python",
      "args": [
        "-m",
        "mcp_echo.server"
      ]
    }
  }
}
```

### 在 Claude Desktop 中使用

编辑配置文件：
- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

添加配置：

```json
{
  "mcpServers": {
    "echo": {
      "command": "mcp-echo"
    }
  }
}
```

## 使用示例

在支持MCP的AI助手中，你可以这样使用echo工具：

- "请使用echo工具返回'Hello World'"
- "用echo工具测试一下：这是一条测试消息"

## 工具说明

### echo

- **描述**: 输入什么就返回什么
- **参数**:
  - `message` (string, 必需): 要回显的消息内容
- **返回**: 回显的消息文本，格式为 "Echo: {message}"

## 开发

### 克隆仓库

```bash
git clone https://github.com/BACH-AI-Tools/mcp-echo.git
cd mcp-echo
```

### 安装开发依赖

```bash
pip install -e .
```

### 本地测试

```bash
python -m mcp_echo.server
```

### 构建包

```bash
python -m build
```

## 技术栈

- Python 3.10+
- MCP SDK (mcp>=0.9.0)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- GitHub Issues: https://github.com/BACH-AI-Tools/mcp-echo/issues
- 组织主页: https://github.com/BACH-AI-Tools

---

Made with ❤️ by Bach Studio
