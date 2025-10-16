#!/usr/bin/env python3
"""
测试事件循环修复效果的脚本
"""

import asyncio
import logging
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from app.core.mcp_manager import MCPManager
from config.config_manager import get_config_manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class EventLoopFixTester:
    """事件循环修复测试器"""
    
    def __init__(self):
        self.mcp_manager = None
        self.test_results = []
        
    async def setup(self):
        """设置测试环境"""
        try:
            logger.info("🔧 设置测试环境...")
            self.mcp_manager = MCPManager()
            await self.mcp_manager.initialize()
            logger.info("✅ MCP管理器初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 设置失败: {e}")
            return False
    
    async def test_normal_tool_call(self):
        """测试正常工具调用"""
        logger.info("🧪 测试1: 正常工具调用")
        try:
            # 假设有天气查询工具
            available_tools = self.mcp_manager.get_available_tools()
            if not available_tools:
                self.test_results.append(("正常工具调用", False, "没有可用工具"))
                return
            
            # 尝试调用第一个可用工具
            tool_name = available_tools[0]['function']['name']
            logger.info(f"调用工具: {tool_name}")
            
            # 根据工具类型构造参数
            if "weather" in tool_name.lower():
                result = await self.mcp_manager.call_tool(tool_name, {"city": "Beijing", "lang": "zh_cn"})
            else:
                result = await self.mcp_manager.call_tool(tool_name, {})
            
            success = not result.startswith("❌")
            self.test_results.append(("正常工具调用", success, result[:100]))
            logger.info(f"{'✅' if success else '❌'} 结果: {result[:100]}...")
            
        except Exception as e:
            self.test_results.append(("正常工具调用", False, str(e)))
            logger.error(f"❌ 测试失败: {e}")
    
    async def test_event_loop_robustness(self):
        """测试事件循环健壮性"""
        logger.info("🧪 测试2: 事件循环健壮性")
        try:
            # 模拟高并发调用
            tasks = []
            for i in range(5):
                if self.mcp_manager.get_available_tools():
                    tool_name = self.mcp_manager.get_available_tools()[0]['function']['name']
                    if "weather" in tool_name.lower():
                        task = self.mcp_manager.call_tool(tool_name, {"city": f"City{i}", "lang": "zh_cn"})
                    else:
                        task = self.mcp_manager.call_tool(tool_name, {})
                    tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                success_count = sum(1 for r in results if isinstance(r, str) and not r.startswith("❌"))
                
                success = success_count > 0
                self.test_results.append(("并发调用", success, f"{success_count}/{len(results)} 成功"))
                logger.info(f"{'✅' if success else '❌'} 并发调用结果: {success_count}/{len(results)} 成功")
            else:
                self.test_results.append(("并发调用", False, "没有可用工具"))
                
        except Exception as e:
            self.test_results.append(("并发调用", False, str(e)))
            logger.error(f"❌ 并发测试失败: {e}")
    
    async def test_error_handling(self):
        """测试错误处理"""
        logger.info("🧪 测试3: 错误处理")
        try:
            # 测试无效工具名称
            result1 = await self.mcp_manager.call_tool("invalid_tool_name", {})
            success1 = result1.startswith("❌") and "无效的工具名称" in result1
            
            # 测试不存在的服务器
            result2 = await self.mcp_manager.call_tool("nonexistent_server_tool", {})
            success2 = result2.startswith("❌") and "找不到服务器" in result2
            
            overall_success = success1 and success2
            self.test_results.append(("错误处理", overall_success, "无效工具名称和不存在服务器测试"))
            logger.info(f"{'✅' if overall_success else '❌'} 错误处理测试完成")
            
        except Exception as e:
            self.test_results.append(("错误处理", False, str(e)))
            logger.error(f"❌ 错误处理测试失败: {e}")
    
    async def test_server_status(self):
        """测试服务器状态检查"""
        logger.info("🧪 测试4: 服务器状态检查")
        try:
            status = self.mcp_manager.get_server_status()
            connected_count = sum(1 for s in status.values() if s == "connected")
            
            success = connected_count > 0
            self.test_results.append(("服务器状态", success, f"{connected_count} 个服务器连接"))
            logger.info(f"{'✅' if success else '❌'} 服务器状态: {connected_count} 个连接")
            
        except Exception as e:
            self.test_results.append(("服务器状态", False, str(e)))
            logger.error(f"❌ 服务器状态测试失败: {e}")
    
    async def cleanup(self):
        """清理测试环境"""
        logger.info("🧹 清理测试环境...")
        try:
            if self.mcp_manager:
                await self.mcp_manager.cleanup()
            logger.info("✅ 清理完成")
        except Exception as e:
            logger.error(f"❌ 清理失败: {e}")
    
    def print_results(self):
        """打印测试结果"""
        logger.info("📊 测试结果汇总:")
        logger.info("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for _, success, _ in self.test_results if success)
        
        for test_name, success, details in self.test_results:
            status = "✅ 通过" if success else "❌ 失败"
            logger.info(f"{status} {test_name}: {details}")
        
        logger.info("=" * 50)
        logger.info(f"总计: {passed_tests}/{total_tests} 个测试通过")
        
        if passed_tests == total_tests:
            logger.info("🎉 所有测试通过！事件循环修复生效")
        else:
            logger.warning(f"⚠️ {total_tests - passed_tests} 个测试失败")


async def main():
    """主测试函数"""
    logger.info("🚀 开始事件循环修复测试...")
    
    tester = EventLoopFixTester()
    
    try:
        # 设置测试环境
        if not await tester.setup():
            logger.error("❌ 测试环境设置失败，退出测试")
            return
        
        # 运行测试
        await tester.test_normal_tool_call()
        await tester.test_event_loop_robustness()
        await tester.test_error_handling()
        await tester.test_server_status()
        
    except Exception as e:
        logger.error(f"❌ 测试过程中发生异常: {e}")
    
    finally:
        # 清理和打印结果
        await tester.cleanup()
        tester.print_results()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ 测试被用户中断")
    except Exception as e:
        logger.error(f"❌ 测试运行失败: {e}")