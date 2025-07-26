#!/usr/bin/env python3
"""
MCP时间工具服务器
支持stdio模式，提供时间相关的工具
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Optional

import pytz
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool

# 全局时区设置
SERVER_TIMEZONE: pytz.BaseTzInfo = pytz.timezone('Asia/Shanghai')

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建MCP服务器实例
server = Server("mcp-time-server")


def set_timezone(timezone_name: str) -> None:
    """设置服务器时区"""
    global SERVER_TIMEZONE
    try:
        SERVER_TIMEZONE = pytz.timezone(timezone_name)
        logger.info(f"时区已设置为: {timezone_name}")
    except pytz.exceptions.UnknownTimeZoneError:
        logger.error(f"未知时区: {timezone_name}, 使用默认时区 Asia/Shanghai")
        SERVER_TIMEZONE = pytz.timezone('Asia/Shanghai')


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """列出所有可用的工具"""
    return [
        Tool(
            name="get_current_time",
            description="获取当前时间，返回指定格式的时间字符串和时间戳",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="timestamp_to_string",
            description="将时间戳转换为指定格式的字符串",
            inputSchema={
                "type": "object",
                "properties": {
                    "timestamp": {
                        "type": "number",
                        "description": "时间戳（秒或毫秒）"
                    },
                    "format": {
                        "type": "string",
                        "description": "时间格式，默认为 'yyyy-MM-dd HH:mm:ss.SSS'",
                        "default": "yyyy-MM-dd HH:mm:ss.SSS"
                    },
                    "is_milliseconds": {
                        "type": "boolean",
                        "description": "时间戳是否为毫秒格式，默认为false（秒格式）",
                        "default": False
                    }
                },
                "required": ["timestamp"]
            }
        ),
        Tool(
            name="string_to_timestamp",
            description="将时间字符串转换为时间戳",
            inputSchema={
                "type": "object",
                "properties": {
                    "time_string": {
                        "type": "string",
                        "description": "时间字符串"
                    },
                    "format": {
                        "type": "string",
                        "description": "时间格式，默认为 'yyyy-MM-dd HH:mm:ss.SSS'",
                        "default": "yyyy-MM-dd HH:mm:ss.SSS"
                    },
                    "return_milliseconds": {
                        "type": "boolean",
                        "description": "是否返回毫秒时间戳，默认为false（返回秒时间戳）",
                        "default": False
                    }
                },
                "required": ["time_string"]
            }
        )
    ]


def format_datetime(dt: datetime, format_str: str) -> str:
    """格式化日期时间"""
    # 转换格式模式
    format_mapping = {
        'yyyy': '%Y',
        'MM': '%m',
        'dd': '%d',
        'HH': '%H',
        'mm': '%M',
        'ss': '%S',
        'SSS': '%f'
    }
    
    python_format = format_str
    for pattern, replacement in format_mapping.items():
        python_format = python_format.replace(pattern, replacement)
    
    # 特殊处理毫秒格式
    if 'SSS' in format_str:
        # 获取毫秒部分（前3位）
        formatted = dt.strftime(python_format)
        # Python的%f返回6位微秒，我们只要前3位毫秒
        formatted = formatted[:formatted.rfind('.') + 4] if '.' in formatted else formatted
        return formatted
    else:
        return dt.strftime(python_format)


def parse_datetime(time_string: str, format_str: str) -> datetime:
    """解析时间字符串"""
    # 转换格式模式
    format_mapping = {
        'yyyy': '%Y',
        'MM': '%m',
        'dd': '%d',
        'HH': '%H',
        'mm': '%M',
        'ss': '%S',
        'SSS': '%f'
    }
    
    python_format = format_str
    for pattern, replacement in format_mapping.items():
        python_format = python_format.replace(pattern, replacement)
    
    # 特殊处理毫秒格式
    if 'SSS' in format_str and '.' in time_string:
        # 确保毫秒部分是3位，如果不足则补零，如果超过则截取前3位
        parts = time_string.split('.')
        if len(parts) == 2:
            milliseconds = parts[1][:3].ljust(6, '0')  # 转换为6位微秒
            time_string = f"{parts[0]}.{milliseconds}"
    
    return datetime.strptime(time_string, python_format)


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list:
    """处理工具调用"""
    
    if name == "get_current_time":
        try:
            # 获取当前时间并转换到服务器时区
            now = datetime.now(SERVER_TIMEZONE)
            
            # 格式化时间字符串
            formatted_time = format_datetime(now, 'yyyy-MM-dd HH:mm:ss.SSS')
            
            # 获取时间戳（秒）
            timestamp = now.timestamp()
            
            result = {
                "formatted_time": formatted_time,
                "timestamp": timestamp,
                "timezone": str(SERVER_TIMEZONE)
            }
            
            return [{"type": "text", "text": f"当前时间信息：\n格式化时间: {formatted_time}\n时间戳: {timestamp}\n时区: {SERVER_TIMEZONE}"}]
            
        except Exception as e:
            logger.error(f"获取当前时间时发生错误: {e}")
            return [{"type": "text", "text": f"错误: {str(e)}"}]
    
    elif name == "timestamp_to_string":
        try:
            timestamp = arguments["timestamp"]
            format_str = arguments.get("format", "yyyy-MM-dd HH:mm:ss.SSS")
            is_milliseconds = arguments.get("is_milliseconds", False)
            
            # 转换时间戳
            if is_milliseconds:
                dt = datetime.fromtimestamp(timestamp / 1000, tz=SERVER_TIMEZONE)
            else:
                dt = datetime.fromtimestamp(timestamp, tz=SERVER_TIMEZONE)
            
            # 格式化时间
            formatted_time = format_datetime(dt, format_str)
            
            return [{"type": "text", "text": f"转换结果: {formatted_time}"}]
            
        except Exception as e:
            logger.error(f"时间戳转换字符串时发生错误: {e}")
            return [{"type": "text", "text": f"错误: {str(e)}"}]
    
    elif name == "string_to_timestamp":
        try:
            time_string = arguments["time_string"]
            format_str = arguments.get("format", "yyyy-MM-dd HH:mm:ss.SSS")
            return_milliseconds = arguments.get("return_milliseconds", False)
            
            # 解析时间字符串
            dt = parse_datetime(time_string, format_str)
            
            # 设置时区
            dt = SERVER_TIMEZONE.localize(dt)
            
            # 获取时间戳
            timestamp = dt.timestamp()
            
            if return_milliseconds:
                timestamp = int(timestamp * 1000)
            
            return [{"type": "text", "text": f"转换结果: {timestamp}"}]
            
        except Exception as e:
            logger.error(f"字符串转换时间戳时发生错误: {e}")
            return [{"type": "text", "text": f"错误: {str(e)}"}]
    
    else:
        return [{"type": "text", "text": f"未知工具: {name}"}]


async def main(timezone_name: Optional[str] = None) -> None:
    """主函数"""
    if timezone_name:
        set_timezone(timezone_name)
    
    logger.info(f"启动MCP时间服务器，时区: {SERVER_TIMEZONE}")
    
    # 使用stdio传输运行服务器
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def cli_main() -> None:
    """命令行入口点"""
    parser = argparse.ArgumentParser(description="MCP时间工具服务器")
    parser.add_argument(
        "--timezone",
        default="Asia/Shanghai",
        help="服务器时区，默认为Asia/Shanghai"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main(args.timezone))
    except KeyboardInterrupt:
        logger.info("服务器已停止")
    except Exception as e:
        logger.error(f"服务器运行时发生错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli_main() 