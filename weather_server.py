import os
import json
import httpx
from typing import Any
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
 
# 初始化 MCP 服务器
mcp = FastMCP("WeatherServer")
 
# OpenWeather API 配置
# 显式加载同目录下的 .env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
OPENWEATHER_API_BASE = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = os.getenv("OPENWEATHER_API_KEY")
USER_AGENT = "weather-app/1.0"
 
"""
异步获取城市天气。
:param city: 英文城市名
:return: 天气字典或含 error 的字典
"""
async def fetch_weather(city: str) -> dict[str, Any] | None:
    """
    从 OpenWeather API 获取天气信息。
    :param city: 城市名称（需使用英文，如 Beijing）
    :return: 天气数据字典；若出错返回包含 error 信息的字典
    """
    # 如果缺少 API Key，直接返回错误
    if not API_KEY:
        return {"error": "Missing OPENWEATHER_API_KEY in environment"}

    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric",
        "lang": "zh_cn"
    }
    headers = {"User-Agent": USER_AGENT}
 
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(OPENWEATHER_API_BASE, params=params, headers=headers, timeout=30.0)
            response.raise_for_status()
            return response.json()  # 返回字典类型
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP 错误: {e.response.status_code}"}
        except Exception as e:
            return {"error": f"请求失败: {str(e)}"}
 
def format_weather(data: dict[str, Any] | str) -> str:
    """
    将天气数据格式化为易读文本。
    :param data: 天气数据（可以是字典或 JSON 字符串）
    :return: 格式化后的天气信息字符串
    """
    # 如果传入的是字符串，则先转换为字典
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception as e:
            return f"无法解析天气数据: {e}"
 
    # 如果数据中包含错误信息，直接返回错误提示
    if "error" in data:
        return f"⚠️ {data['error']}"
 
    # 提取数据时做容错处理
    city = data.get("name", "未知")
    country = data.get("sys", {}).get("country", "未知")
    temp = data.get("main", {}).get("temp", "N/A")
    humidity = data.get("main", {}).get("humidity", "N/A")
    wind_speed = data.get("wind", {}).get("speed", "N/A")
    # weather 可能为空列表，因此用 [0] 前先提供默认字典
    weather_list = data.get("weather", [{}])
    description = weather_list[0].get("description", "未知")
 
    return (
        f"🌍 {city}, {country}\n"
        f"🌡 温度: {temp}°C\n"
        f"💧 湿度: {humidity}%\n"
        f"🌬 风速: {wind_speed} m/s\n"
        f"🌤 天气: {description}\n"
    )
 
 
"""
异步查询英文城市今日天气。
:param city: 英文城市名
:return: 格式化的天气信息
"""
@mcp.tool()
async def query_weather(city: str) -> str:
    """
    输入指定城市的英文名称，返回今日天气查询结果。

    使用说明（重要）:
    - 如果用户输入的城市名称不是英文，请先将城市名称翻译为英文再调用本工具。
    - 示例映射：'长沙' -> 'Changsha'，'慕尼黑' -> 'Munich'，'東京' -> 'Tokyo'，'Москва' -> 'Moscow'。
    - 本工具仅接受英文城市名作为参数，接口返回文案为中文（lang=zh_cn）。

    :param city: 城市名称（必须为英文，若非英文请先转换为英文）
    :return: 格式化后的天气信息
    """
    data = await fetch_weather(city)
    return format_weather(data)
 
if __name__ == "__main__":
    # 以标准 I/O 方式运行 MCP 服务器（仅输出 JSON-RPC 到 STDOUT）
    mcp.run(transport="stdio")