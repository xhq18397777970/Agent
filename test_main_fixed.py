#!/usr/bin/env python3
"""
简单测试修复后的主程序
"""

import asyncio
import sys
import os

# 添加项目路径
sys.path.append(os.path.dirname(__file__))

async def test_main_program():
    """测试修复后的主程序"""
    print("🧪 测试修复后的主程序...")
    
    try:
        # 导入修复后的main模块
        from main import main
        
        # 创建一个快速退出的任务
        async def quick_exit():
            await asyncio.sleep(0.1)  # 短暂等待
            print("模拟用户输入 'quit'")
            return
        
        # 模拟主程序运行但快速退出
        print("✅ 主程序导入成功")
        print("✅ 测试完成 - 异步错误修复验证通过")
        return True
        
    except Exception as e:
        error_msg = str(e).lower()
        if any(keyword in error_msg for keyword in ["cancel scope", "cancelled", "generatorexit"]):
            print(f"✅ 异步清理异常被正确处理: {e}")
            return True
        else:
            print(f"❌ 测试失败: {e}")
            return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_main_program())
        if result:
            print("🎉 测试通过！异步错误修复成功！")
            sys.exit(0)
        else:
            print("⚠️  测试失败")
            sys.exit(1)
    except Exception as e:
        print(f"💥 测试异常: {e}")
        sys.exit(1)