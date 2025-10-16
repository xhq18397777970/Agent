#!/usr/bin/env python3
"""
测试环境变量加载脚本
用于验证 .env 文件中的 API 密钥是否能正确加载
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def test_env_loading():
    """测试环境变量加载"""
    print("🔍 测试环境变量加载...")
    
    # 获取项目根目录
    project_root = Path(__file__).parent
    env_file = project_root / ".env"
    
    print(f"📁 项目根目录: {project_root}")
    print(f"📄 .env 文件路径: {env_file}")
    print(f"📄 .env 文件是否存在: {env_file.exists()}")
    
    if env_file.exists():
        print("\n📖 .env 文件内容:")
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.strip().split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip() and not line.startswith('#'):
                    # 隐藏 API 密钥的敏感部分
                    if '=' in line:
                        key, value = line.split('=', 1)
                        if 'KEY' in key.upper() or 'SECRET' in key.upper():
                            masked_value = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '*' * len(value)
                            print(f"  {i:2d}: {key}={masked_value}")
                        else:
                            print(f"  {i:2d}: {line}")
                    else:
                        print(f"  {i:2d}: {line}")
                else:
                    print(f"  {i:2d}: {line}")
    
    # 加载环境变量
    print(f"\n🔄 加载 .env 文件...")
    load_dotenv(env_file)
    
    # 检查关键环境变量
    env_vars_to_check = [
        'OPENWEATHER_API_KEY',
        'API_KEY',
        'OPENWEATHER_API_BASE',
        'DEEPSEEK_API_KEY',
        'DEEPSEEK_BASE_URL'
    ]
    
    print("\n✅ 环境变量检查结果:")
    for var_name in env_vars_to_check:
        value = os.getenv(var_name)
        if value:
            # 隐藏敏感信息
            if 'KEY' in var_name.upper() or 'SECRET' in var_name.upper():
                masked_value = value[:8] + '*' * (len(value) - 12) + value[-4:] if len(value) > 12 else '*' * len(value)
                print(f"  ✓ {var_name}: {masked_value}")
            else:
                print(f"  ✓ {var_name}: {value}")
        else:
            print(f"  ❌ {var_name}: 未设置")
    
    # 测试天气服务器的 API 密钥获取
    print("\n🌤️ 天气服务器 API 密钥测试:")
    openweather_key = os.getenv("OPENWEATHER_API_KEY")
    if openweather_key:
        masked_key = openweather_key[:8] + '*' * (len(openweather_key) - 12) + openweather_key[-4:] if len(openweather_key) > 12 else '*' * len(openweather_key)
        print(f"  ✅ OPENWEATHER_API_KEY 已加载: {masked_key}")
        print(f"  📏 密钥长度: {len(openweather_key)} 字符")
        
        # 验证密钥格式（OpenWeather API 密钥通常是32字符的十六进制字符串）
        if len(openweather_key) == 32 and all(c in '0123456789abcdef' for c in openweather_key.lower()):
            print("  ✅ 密钥格式看起来正确")
        else:
            print("  ⚠️ 密钥格式可能不正确（应该是32字符的十六进制字符串）")
    else:
        print("  ❌ OPENWEATHER_API_KEY 未找到")
    
    return openweather_key is not None

def test_weather_server_import():
    """测试天气服务器模块导入"""
    print("\n🌤️ 测试天气服务器模块导入...")
    
    try:
        # 添加服务器目录到路径
        servers_dir = Path(__file__).parent / "servers"
        if servers_dir.exists():
            sys.path.insert(0, str(servers_dir))
        
        # 尝试导入天气服务器
        import weather_server
        print("  ✅ weather_server 模块导入成功")
        
        # 检查模块中的关键函数
        if hasattr(weather_server, 'query_weather'):
            print("  ✅ query_weather 函数存在")
        else:
            print("  ❌ query_weather 函数不存在")
            
        return True
    except ImportError as e:
        print(f"  ❌ 导入 weather_server 失败: {e}")
        return False
    except Exception as e:
        print(f"  ❌ 其他错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("🧪 环境变量和天气服务器测试")
    print("=" * 60)
    
    # 测试环境变量加载
    env_ok = test_env_loading()
    
    # 测试模块导入
    import_ok = test_weather_server_import()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"  环境变量加载: {'✅ 成功' if env_ok else '❌ 失败'}")
    print(f"  模块导入测试: {'✅ 成功' if import_ok else '❌ 失败'}")
    
    if env_ok and import_ok:
        print("  🎉 所有测试通过！天气服务应该可以正常工作。")
    else:
        print("  ⚠️ 部分测试失败，可能影响天气服务功能。")
    
    print("=" * 60)

if __name__ == "__main__":
    main()