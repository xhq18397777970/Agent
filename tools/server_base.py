"""
MCP 服务器基类和工具模板
提供统一的服务器开发框架和标准化接口
"""

import os
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseMCPServer(ABC):
    """
    MCP 服务器基类
    
    提供统一的服务器初始化、配置管理和工具注册框架
    所有新的 MCP 服务器都应该继承此基类
    """
    
    def __init__(self, server_name: str, description: str = ""):
        """
        初始化 MCP 服务器
        
        Args:
            server_name: 服务器名称
            description: 服务器描述
        """
        self.server_name = server_name
        self.description = description
        self.mcp = FastMCP(server_name)
        self.tools_registered = 0
        
        # 初始化服务器
        self._initialize_server()
        
    def _initialize_server(self):
        """内部初始化方法"""
        logger.info(f"🚀 初始化 MCP 服务器: {self.server_name}")
        if self.description:
            logger.info(f"📝 服务器描述: {self.description}")
            
        # 注册工具
        self._register_tools()
        
        logger.info(f"✅ 服务器 {self.server_name} 初始化完成，已注册 {self.tools_registered} 个工具")
    
    @abstractmethod
    def _register_tools(self):
        """
        注册服务器工具的抽象方法
        子类必须实现此方法来注册具体的工具
        """
        pass
    
    def register_tool(self, func):
        """
        注册工具的装饰器方法
        
        Args:
            func: 要注册的工具函数
            
        Returns:
            装饰后的函数
        """
        decorated_func = self.mcp.tool()(func)
        self.tools_registered += 1
        logger.info(f"🔧 已注册工具: {func.__name__}")
        return decorated_func
    
    def run(self):
        """启动 MCP 服务器"""
        logger.info(f"🌟 启动 MCP 服务器: {self.server_name}")
        self.mcp.run(transport="stdio")
    
    @staticmethod
    def format_success_response(message: str, data: Dict[str, Any] = None) -> str:
        """
        格式化成功响应
        
        Args:
            message: 成功消息
            data: 附加数据
            
        Returns:
            格式化的响应字符串
        """
        response = f"✅ {message}\n"
        if data:
            for key, value in data.items():
                response += f"📊 {key}: {value}\n"
        response += f"🕒 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return response
    
    @staticmethod
    def format_error_response(error: str, details: str = None) -> str:
        """
        格式化错误响应
        
        Args:
            error: 错误消息
            details: 错误详情
            
        Returns:
            格式化的错误响应字符串
        """
        response = f"❌ 错误: {error}\n"
        if details:
            response += f"📋 详情: {details}\n"
        response += f"🕒 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        return response
    
    @staticmethod
    def validate_env_var(var_name: str, required: bool = True) -> Optional[str]:
        """
        验证环境变量
        
        Args:
            var_name: 环境变量名
            required: 是否必需
            
        Returns:
            环境变量值或 None
            
        Raises:
            ValueError: 当必需的环境变量不存在时
        """
        value = os.getenv(var_name)
        if required and not value:
            raise ValueError(f"缺少必需的环境变量: {var_name}")
        return value


class ToolTemplate:
    """
    工具模板类
    提供常用的工具开发模板和工具函数
    """
    
    @staticmethod
    def create_file_tool_template(server: BaseMCPServer, tool_name: str, 
                                 description: str, base_dir: str = None):
        """
        创建文件操作工具模板
        
        Args:
            server: MCP 服务器实例
            tool_name: 工具名称
            description: 工具描述
            base_dir: 基础目录
        """
        if not base_dir:
            base_dir = os.path.join(os.path.dirname(__file__), "..", "output")
        
        async def file_tool(content: str, filename: str = None) -> str:
            """文件操作工具"""
            try:
                os.makedirs(base_dir, exist_ok=True)
                
                if not filename:
                    filename = f"{tool_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                file_path = os.path.join(base_dir, filename)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                return server.format_success_response(
                    f"{tool_name} 操作完成",
                    {
                        "文件路径": os.path.abspath(file_path),
                        "文件大小": f"{len(content)} 字符"
                    }
                )
            except Exception as e:
                return server.format_error_response(f"{tool_name} 操作失败", str(e))
        
        # 设置工具属性
        file_tool.__name__ = tool_name
        file_tool.__doc__ = description
        
        return server.register_tool(file_tool)
    
    @staticmethod
    def create_api_tool_template(server: BaseMCPServer, tool_name: str,
                               description: str, api_key_env: str = None):
        """
        创建 API 调用工具模板
        
        Args:
            server: MCP 服务器实例
            tool_name: 工具名称
            description: 工具描述
            api_key_env: API Key 环境变量名
        """
        import httpx
        
        async def api_tool(**kwargs) -> str:
            """API 调用工具"""
            try:
                if api_key_env:
                    api_key = server.validate_env_var(api_key_env, required=True)
                
                # 这里添加具体的 API 调用逻辑
                # 示例代码，需要根据具体 API 进行修改
                async with httpx.AsyncClient() as client:
                    # response = await client.get("API_URL", headers={"Authorization": f"Bearer {api_key}"})
                    pass
                
                return server.format_success_response(f"{tool_name} 调用成功")
                
            except Exception as e:
                return server.format_error_response(f"{tool_name} 调用失败", str(e))
        
        # 设置工具属性
        api_tool.__name__ = tool_name
        api_tool.__doc__ = description
        
        return server.register_tool(api_tool)


# 工具创建助手函数
def create_simple_server(server_name: str, description: str = "") -> BaseMCPServer:
    """
    创建简单的 MCP 服务器
    
    Args:
        server_name: 服务器名称
        description: 服务器描述
        
    Returns:
        MCP 服务器实例
    """
    class SimpleServer(BaseMCPServer):
        def _register_tools(self):
            # 简单服务器默认不注册任何工具
            pass
    
    return SimpleServer(server_name, description)


if __name__ == "__main__":
    # 示例用法
    print("MCP 服务器基类和工具模板已加载")
    print("使用方法:")
    print("1. 继承 BaseMCPServer 类")
    print("2. 实现 _register_tools 方法")
    print("3. 使用 ToolTemplate 创建常用工具")