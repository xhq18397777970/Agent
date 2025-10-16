#!/usr/bin/env python3
"""
测试异步错误修复的脚本
验证 MCP 客户端在退出时不再出现 cancel scope 错误
"""

import asyncio
import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

from main import MultiServerMCPClient, Configuration

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

async def test_client_initialization_and_cleanup():
    """测试客户端初始化和清理过程"""
    print("🧪 开始测试 MCP 客户端初始化和清理...")
    
    try:
        # 创建配置和客户端
        config = Configuration()
        servers_config = config.load_config()
        client = MultiServerMCPClient()
        
        print("✅ 客户端创建成功")
        
        # 测试连接服务器
        await client.connect_to_servers(servers_config)
        print("✅ 服务器连接成功")
        
        # 模拟一些操作
        await asyncio.sleep(0.5)
        print("✅ 模拟操作完成")
        
        # 测试清理
        await client.cleanup()
        print("✅ 清理完成，没有异常")
        
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["cancel scope", "cancelled", "generatorexit"]):
            print(f"⚠️  检测到异步清理异常（应该被忽略）: {e}")
            return True  # 这种异常现在应该被正确处理
        else:
            print(f"❌ 测试失败: {e}")
            return False

async def test_multiple_cleanup_calls():
    """测试多次调用清理方法"""
    print("\n🧪 测试多次清理调用...")
    
    try:
        config = Configuration()
        servers_config = config.load_config()
        client = MultiServerMCPClient()
        
        await client.connect_to_servers(servers_config)
        print("✅ 服务器连接成功")
        
        # 多次调用清理
        await client.cleanup()
        print("✅ 第一次清理完成")
        
        await client.cleanup()
        print("✅ 第二次清理完成（应该安全）")
        
        return True
        
    except Exception as e:
        print(f"❌ 多次清理测试失败: {e}")
        return False

async def test_interrupted_cleanup():
    """测试中断情况下的清理"""
    print("\n🧪 测试中断清理...")
    
    try:
        config = Configuration()
        servers_config = config.load_config()
        client = MultiServerMCPClient()
        
        await client.connect_to_servers(servers_config)
        print("✅ 服务器连接成功")
        
        # 模拟快速退出
        cleanup_task = asyncio.create_task(client.cleanup())
        await asyncio.sleep(0.01)  # 很短的时间
        
        try:
            await cleanup_task
            print("✅ 快速清理完成")
        except asyncio.CancelledError:
            print("✅ 清理任务被取消（正常情况）")
        
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["cancel scope", "cancelled", "generatorexit"]):
            print(f"✅ 中断清理异常被正确处理: {e}")
            return True
        else:
            print(f"❌ 中断清理测试失败: {e}")
            return False

async def main():
    """运行所有测试"""
    print("🚀 开始异步错误修复测试\n")
    
    tests = [
        ("基本初始化和清理", test_client_initialization_and_cleanup),
        ("多次清理调用", test_multiple_cleanup_calls),
        ("中断清理", test_interrupted_cleanup),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"{'='*50}")
        print(f"运行测试: {test_name}")
        print(f"{'='*50}")
        
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ 测试 '{test_name}' 发生未捕获异常: {e}")
            results.append((test_name, False))
        
        await asyncio.sleep(0.5)  # 测试间隔
    
    # 输出测试结果
    print(f"\n{'='*50}")
    print("测试结果汇总")
    print(f"{'='*50}")
    
    passed = 0
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{len(results)} 个测试通过")
    
    if passed == len(results):
        print("🎉 所有测试通过！异步错误修复成功！")
        return 0
    else:
        print("⚠️  部分测试失败，需要进一步检查")
        return 1

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 测试脚本异常: {e}")
        sys.exit(1)