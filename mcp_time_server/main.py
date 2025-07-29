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
            name="convert_time",
            description="时间格式转换工具：支持时间戳与固定格式字符串(yyyy-MM-dd HH:mm:ss.SSS)之间的相互转换",
            inputSchema={
                "type": "object",
                "properties": {
                    "input_value": {
                        "type": "string",
                        "description": "输入值：可以是时间戳(字符串格式的数字)或时间字符串(yyyy-MM-dd HH:mm:ss.SSS格式)"
                    },
                    "convert_to": {
                        "type": "string",
                        "enum": ["timestamp", "string"],
                        "description": "转换目标类型：timestamp(转为时间戳) 或 string(转为yyyy-MM-dd HH:mm:ss.SSS格式)"
                    },
                    "timestamp_precision": {
                        "type": "string",
                        "enum": ["seconds", "milliseconds"],
                        "description": "时间戳精度：seconds(秒级时间戳) 或 milliseconds(毫秒级时间戳)，默认为milliseconds"
                    }
                },
                "required": ["input_value", "convert_to"]
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
            
            # 获取时间戳（毫秒）
            timestamp = int(now.timestamp() * 1000)
            
            result = {
                "formatted_time": formatted_time,
                "timestamp": timestamp,
                "timezone": str(SERVER_TIMEZONE)
            }
            
            return [{"type": "text", "text": f"当前时间信息：\n格式化时间: {formatted_time}\n时间戳: {timestamp}\n时区: {SERVER_TIMEZONE}"}]
            
        except Exception as e:
            logger.error(f"获取当前时间时发生错误: {e}")
            return [{"type": "text", "text": f"错误: {str(e)}"}]
    
    elif name == "convert_time":
        try:
            input_value = arguments["input_value"]
            convert_to = arguments["convert_to"]
            # 获取时间戳精度参数，默认为毫秒级
            timestamp_precision = arguments.get("timestamp_precision", "milliseconds")
            
            if convert_to == "timestamp":
                # 字符串转时间戳：输入必须是时间字符串格式 yyyy-MM-dd HH:mm:ss.SSS
                input_str = str(input_value).strip()
                
                # 解析时间字符串为datetime对象
                dt = parse_datetime(input_str, "yyyy-MM-dd HH:mm:ss.SSS")
                
                # 设置时区
                dt = SERVER_TIMEZONE.localize(dt)
                
                # 根据精度参数获取时间戳
                if timestamp_precision == "seconds":
                    timestamp = int(dt.timestamp())
                else:  # milliseconds
                    timestamp = int(dt.timestamp() * 1000)
                
                precision_text = "秒级" if timestamp_precision == "seconds" else "毫秒级"
                return [{"type": "text", "text": f"转换结果: {timestamp} ({precision_text}时间戳)"}]
                
            elif convert_to == "string":
                # 时间戳转字符串：输入是字符串格式的时间戳
                input_str = str(input_value).strip()
                
                try:
                    timestamp = float(input_str)
                except ValueError:
                    raise ValueError("转换为字符串时，输入值必须是有效的时间戳字符串")
                
                # 根据精度参数处理时间戳
                if timestamp_precision == "seconds":
                    dt = datetime.fromtimestamp(timestamp, tz=SERVER_TIMEZONE)
                else:  # milliseconds
                    dt = datetime.fromtimestamp(timestamp / 1000, tz=SERVER_TIMEZONE)
                
                # 格式化时间为固定格式
                formatted_time = format_datetime(dt, "yyyy-MM-dd HH:mm:ss.SSS")
                
                precision_text = "秒级" if timestamp_precision == "seconds" else "毫秒级"
                return [{"type": "text", "text": f"转换结果: {formatted_time} (从{precision_text}时间戳转换)"}]
                
            else:
                return [{"type": "text", "text": f"未知转换目标: {convert_to}"}]
            
        except Exception as e:
            logger.error(f"时间格式转换时发生错误: {e}")
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