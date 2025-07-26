# MCP 时间工具服务器

基于 Model Context Protocol (MCP) 的 Python 时间工具服务器，支持 stdio 模式通信。

## 提供的工具

### 1. get_current_time
获取当前时间，返回格式化时间、时间戳和时区信息。

### 2. timestamp_to_string
将时间戳转换为指定格式的字符串。支持秒/毫秒时间戳，自定义时间格式。

### 3. string_to_timestamp
将时间字符串转换为时间戳。支持自定义时间格式，返回秒/毫秒时间戳。

## 快速使用

直接从远程仓库运行：

```bash
# 使用默认时区（Asia/Shanghai）
uv run --from git+https://github.com/zjh7890/time.git mcp-time-server

# 指定时区
uv run --from git+https://github.com/zjh7890/time.git mcp-time-server --timezone "US/Eastern"
```

## Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "time-server": {
      "command": "uv",
      "args": [
        "run",
        "--from",
        "git+https://github.com/zjh7890/time.git",
        "mcp-time-server",
        "--timezone",
        "Asia/Shanghai"
      ]
    }
  }
}
```

## 许可证

MIT License 