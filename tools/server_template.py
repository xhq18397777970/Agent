#!/usr/bin/env python3
"""
新 MCP 服务器模板
使用此模板快速创建新的 MCP 服务器

使用方法:
1. 复制此文件并重命名
2. 修改 SERVER_NAME 和 SERVER_DESCRIPTION
3. 在 _register_tools 方法中添加你的工具
4. 实现具体的工具函数
"""

import os
import sys
from typing import Optional

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from tools.server_base import BaseMCPServer, ToolTemplate

# 服务器配置
SERVER_NAME = "TemplateServer"  # 修改为你的服务器名称
SERVER_DESCRIPTION = "这是一个 MCP 服务器模板"  # 修改为你的服务器描述


class TemplateServer(BaseMCPServer):
    """
    模板服务器类
    
    继承 BaseMCPServer 并实现具体的工具注册逻辑
    """
    
    def _register_tools(self):
        """
        注册服务器工具
        在这里添加你的工具注册代码
        """
        
        # 示例 1: 注册一个简单的文本处理工具
        @self.register_tool
        async def process_text(text: str, operation: str = "upper") -> str:
            """
            文本处理工具
            
            参数:
            - text: 要处理的文本
            - operation: 操作类型 (upper, lower, reverse)
            
            返回:
            - 处理后的文本
            """
            try:
                if operation == "upper":
                    result = text.upper()
                elif operation == "lower":
                    result = text.lower()
                elif operation == "reverse":
                    result = text[::-1]
                else:
                    return self.format_error_response("不支持的操作类型", f"支持的操作: upper, lower, reverse")
                
                return self.format_success_response(
                    "文本处理完成",
                    {
                        "原文本": text,
                        "操作": operation,
                        "结果": result
                    }
                )
            except Exception as e:
                return self.format_error_response("文本处理失败", str(e))
        
        # 示例 2: 使用工具模板创建文件工具
        ToolTemplate.create_file_tool_template(
            self,
            "save_template_data",
            "保存模板数据到文件"
        )
        
        # 示例 3: 注册一个需要环境变量的工具
        @self.register_tool
        async def get_config_info() -> str:
            """
            获取配置信息工具
            
            返回:
            - 当前配置信息
            """
            try:
                # 验证可选的环境变量
                custom_config = self.validate_env_var("TEMPLATE_CONFIG", required=False)
                
                config_info = {
                    "服务器名称": self.server_name,
                    "服务器描述": self.description,
                    "已注册工具数": self.tools_registered,
                    "自定义配置": custom_config or "未设置"
                }
                
                return self.format_success_response("配置信息获取成功", config_info)
                
            except Exception as e:
                return self.format_error_response("获取配置信息失败", str(e))


def main():
    """主函数"""
    try:
        # 创建并启动服务器
        server = TemplateServer(SERVER_NAME, SERVER_DESCRIPTION)
        server.run()
    except KeyboardInterrupt:
        print(f"\n🛑 {SERVER_NAME} 服务器已停止")
    except Exception as e:
        print(f"❌ 服务器启动失败: {e}")


if __name__ == "__main__":
    main()