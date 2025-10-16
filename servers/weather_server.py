import os
import httpx
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("WeatherServer")

@mcp.tool()
async def query_weather(city: str, units: str = "metric", lang: str = "zh_cn") -> str:
    """
    查询指定城市的天气信息
    
    重要说明：此工具需要英文城市名称才能正确工作。
    如果用户提供了非英文城市名称（如中文、日文、韩文等），请先将其翻译为英文再调用此工具。
    
    参数:
    - city: 城市名称（必须是英文，例如：Beijing, Tokyo, Paris, New York）
    - units: 温度单位，默认 metric（摄氏度），可选 imperial（华氏度）
    - lang: 返回结果的语言，默认 zh_cn（中文），可选 en（英文）
    
    返回:
    - 天气信息的详细描述
    
    示例:
    - 正确：query_weather("Beijing")
    - 错误：query_weather("北京")
    """
    try:
        api_key = os.getenv("OPENWEATHER_API_KEY")
        base_url = os.getenv("OPENWEATHER_API_BASE", "https://api.openweathermap.org/data/2.5/weather")
        
        if not api_key:
            return "❌ 错误：未找到 OPENWEATHER_API_KEY 环境变量"
        
        params = {
            "q": city,
            "appid": api_key,
            "units": units,
            "lang": lang
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # 格式化天气信息
                weather_info = f"""🌤️ {data['name']} 天气信息

📍 位置：{data['name']}, {data['sys']['country']}
🌡️ 温度：{data['main']['temp']}°C (体感 {data['main']['feels_like']}°C)
☁️ 天气：{data['weather'][0]['description']}
💧 湿度：{data['main']['humidity']}%
🌬️ 风速：{data['wind'].get('speed', 0)} m/s
🔽 气压：{data['main']['pressure']} hPa
👁️ 能见度：{data.get('visibility', 'N/A')} 米

🌅 日出：{data['sys']['sunrise']}
🌇 日落：{data['sys']['sunset']}"""
                
                return weather_info
            else:
                return f"❌ 获取天气信息失败：{response.status_code} - {response.text}\n💡 提示：请检查城市名称是否为正确的英文名称"
                
    except Exception as e:
        return f"❌ 查询天气时发生错误：{str(e)}"

if __name__ == "__main__":
    mcp.run(transport="stdio")