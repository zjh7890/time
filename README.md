# MCP 时间工具服务器

基于 Model Context Protocol (MCP) 的 Python 时间工具服务器，支持 stdio 模式通信。

## 提供的工具

### 1. get_current_time
获取当前时间，返回格式化时间字符串、时间戳和时区信息。

**返回格式：**
- 格式化时间：`yyyy-MM-dd HH:mm:ss.SSS`
- 时间戳：秒级时间戳
- 时区：服务器设置的时区

### 2. convert_time
时间格式转换工具，支持毫秒时间戳与固定格式字符串之间的相互转换。

**支持的转换：**
- **字符串 → 时间戳**：将 `yyyy-MM-dd HH:mm:ss.SSS` 格式的字符串转换为毫秒时间戳
- **时间戳 → 字符串**：将毫秒时间戳转换为 `yyyy-MM-dd HH:mm:ss.SSS` 格式的字符串

**参数：**
- `input_value`：输入值，可以是毫秒时间戳（数字）或时间字符串
- `convert_to`：转换目标类型
  - `"timestamp"`：转换为毫秒时间戳
  - `"string"`：转换为固定格式字符串

**使用示例：**
```json
// 字符串转时间戳
{
  "input_value": "2024-12-19 15:30:45.123",
  "convert_to": "timestamp"
}

// 时间戳转字符串
{
  "input_value": 1734599445123,
  "convert_to": "string"
}
```

## 快速使用

直接从远程仓库运行：

```bash
# 使用默认时区（Asia/Shanghai）
uv tool run --from git+https://github.com/zjh7890/time.git mcp-time-server

# 指定时区
uv tool run --from git+https://github.com/zjh7890/time.git mcp-time-server --timezone "US/Eastern"
```

## Claude Desktop 配置

在 `claude_desktop_config.json` 中添加：

```json
{
  "mcpServers": {
    "time-server": {
      "command": "uv",
      "args": [
        "tool",
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

## 时区支持

服务器支持任何有效的时区名称（如 `Asia/Shanghai`、`US/Eastern`、`Europe/London` 等）。如果未指定或指定的时区无效，将默认使用 `Asia/Shanghai`。

## 许可证

MIT License 