#!/usr/bin/env python3
"""
直接测试天气查询功能
"""

import os
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 添加服务器目录到路径
sys.path.append('servers')

async def test_weather_direct():
    """直接测试天气查询功能"""
    print("🌤️ 直接测试天气查询功能...")
    
    # 加载环境变量
    load_dotenv()
    
    # 检查API密钥
    api_key = os.getenv("OPENWEATHER_API_KEY")
    print(f"API密钥状态: {'已设置' if api_key else '未设置'}")
    
    if api_key:
        masked_key = api_key[:8] + '*' * (len(api_key) - 12) + api_key[-4:] if len(api_key) > 12 else '*' * len(api_key)
        print(f"API密钥: {masked_key}")
    
    try:
        # 导入天气服务器模块
        from weather_server import query_weather
        print("✅ 成功导入 weather_server 模块")
        
        # 测试查询北京天气
        print("\n🔍 查询北京天气...")
        result = await query_weather('Beijing')
        print("✅ 天气查询成功:")
        print(result)
        
        return True
        
    except ImportError as e:
        print(f"❌ 导入模块失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 天气查询失败: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_weather_direct())
    if success:
        print("\n🎉 天气查询功能测试成功！")
    else:
        print("\n❌ 天气查询功能测试失败！")