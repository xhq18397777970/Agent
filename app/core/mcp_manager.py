"""
MCP管理器 - 重构自原main.py中的MultiServerMCPClient
负责管理多个MCP服务器连接和工具调用
"""
import asyncio
import json
import logging
import os
import sys
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config.config_manager import get_config_manager


class Server:
    """管理单个 MCP 服务器连接和工具调用"""

    def __init__(self, name: str, config: Dict[str, Any]) -> None:
        self.name: str = name
        self.config: Dict[str, Any] = config
        self.session: Optional[ClientSession] = None
        self.exit_stack: Optional[AsyncExitStack] = None
        self._cleanup_lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self) -> None:
        """初始化与 MCP 服务器的连接"""
        if self._initialized:
            return
            
        command = self.config["command"]
        if command is None:
            raise ValueError("command 不能为空")

        self.exit_stack = AsyncExitStack()
        
        server_params = StdioServerParameters(
            command=command,
            args=self.config["args"],
            env={**os.environ, **self.config["env"]} if self.config.get("env") else os.environ,
        )
        try:
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            read_stream, write_stream = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            await session.initialize()
            self.session = session
            self._initialized = True
        except Exception as e:
            logging.error(f"Error initializing server {self.name}: {e}")
            await self.cleanup()
            raise

    async def list_tools(self) -> List[Any]:
        """获取服务器可用的工具列表"""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        tools_response = await self.session.list_tools()
        tools = []
        for item in tools_response:
            if isinstance(item, tuple) and item[0] == "tools":
                for tool in item[1]:
                    tools.append(Tool(tool.name, tool.description, tool.inputSchema))
        return tools

    async def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], retries: int = 2, delay: float = 1.0
    ) -> Any:
        """执行指定工具，并支持重试机制"""
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        
        # 检查服务器是否仍然初始化
        if not self._initialized:
            raise RuntimeError(f"Server {self.name} has been cleaned up")
            
        attempt = 0
        last_exception = None
        
        while attempt < retries:
            try:
                # 在每次尝试前检查事件循环和会话状态
                if not self._initialized or not self.session:
                    raise RuntimeError(f"Server {self.name} is no longer available")
                
                # 检查当前事件循环是否可用
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_closed():
                        raise RuntimeError("Event loop is closed")
                except RuntimeError as e:
                    if "no running event loop" in str(e).lower():
                        raise RuntimeError("No running event loop available")
                    raise
                
                logging.info(f"Executing {tool_name} on server {self.name}...")
                result = await self.session.call_tool(tool_name, arguments)
                return result
                
            except Exception as e:
                attempt += 1
                last_exception = e
                error_msg = str(e).lower()
                
                # 检查是否是不可恢复的错误
                unrecoverable_errors = [
                    "event loop is closed",
                    "no running event loop",
                    "server has been cleaned up",
                    "is no longer available"
                ]
                
                if any(err in error_msg for err in unrecoverable_errors):
                    logging.error(f"Unrecoverable error executing tool {tool_name}: {e}")
                    raise e
                
                logging.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    try:
                        await asyncio.sleep(delay)
                    except Exception as sleep_error:
                        logging.error(f"Error during retry delay: {sleep_error}")
                        raise last_exception
                else:
                    logging.error("Max retries reached. Failing.")
                    raise last_exception

    async def cleanup(self) -> None:
        """清理服务器资源"""
        async with self._cleanup_lock:
            if not self._initialized:
                return
                
            self._initialized = False
            
            try:
                # 检查事件循环状态
                try:
                    loop = asyncio.get_running_loop()
                    if loop.is_closed():
                        logging.warning(f"Event loop is closed during cleanup of server {self.name}")
                        # 直接清理状态，不执行异步操作
                        self.session = None
                        self.exit_stack = None
                        return
                except RuntimeError:
                    # 没有运行中的事件循环
                    logging.warning(f"No running event loop during cleanup of server {self.name}")
                    self.session = None
                    self.exit_stack = None
                    return
                
                if self.session:
                    try:
                        await asyncio.wait_for(self.session.close(), timeout=0.5)
                    except (asyncio.TimeoutError, AttributeError):
                        pass
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "event loop is closed" in error_msg:
                            logging.debug(f"Event loop closed during session cleanup for {self.name}")
                        else:
                            logging.debug(f"Session cleanup warning for {self.name}: {e}")
                    finally:
                        self.session = None
                    
                if self.exit_stack:
                    try:
                        # 检查是否可以安全执行异步清理
                        loop = asyncio.get_running_loop()
                        if not loop.is_closed():
                            cleanup_task = asyncio.create_task(self._safe_exit_stack_cleanup())
                            await asyncio.wait_for(cleanup_task, timeout=2.0)
                        else:
                            logging.debug(f"Skipping exit_stack cleanup due to closed loop for server {self.name}")
                    except asyncio.TimeoutError:
                        logging.info(f"Exit stack cleanup timed out for server {self.name}")
                        if 'cleanup_task' in locals():
                            cleanup_task.cancel()
                            try:
                                await cleanup_task
                            except asyncio.CancelledError:
                                pass
                    except Exception as e:
                        error_msg = str(e).lower()
                        expected_errors = ["cancel", "scope", "generatorexit", "different task", "event loop is closed"]
                        if any(keyword in error_msg for keyword in expected_errors):
                            logging.debug(f"Ignoring expected async cleanup error for server {self.name}: {e}")
                        else:
                            logging.warning(f"Unexpected error during exit_stack cleanup of server {self.name}: {e}")
                    finally:
                        self.exit_stack = None
                        
            except Exception as e:
                error_msg = str(e).lower()
                expected_errors = ["cancel", "scope", "generatorexit", "different task", "event loop is closed"]
                if any(keyword in error_msg for keyword in expected_errors):
                    logging.debug(f"Ignoring expected async cleanup error during server {self.name} cleanup: {e}")
                else:
                    logging.error(f"Unexpected error during cleanup of server {self.name}: {e}")
            finally:
                self.session = None
                self.exit_stack = None
                self._initialized = False

    async def _safe_exit_stack_cleanup(self) -> None:
        """安全地清理exit_stack，在独立的任务中运行"""
        if self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                error_msg = str(e).lower()
                if not any(keyword in error_msg for keyword in ["cancel", "scope", "generatorexit", "different task"]):
                    raise


class Tool:
    """封装 MCP 返回的工具信息"""

    def __init__(self, name: str, description: str, input_schema: Dict[str, Any]) -> None:
        self.name: str = name
        self.description: str = description
        self.input_schema: Dict[str, Any] = input_schema

    def format_for_llm(self) -> str:
        """生成用于 LLM 提示的工具描述"""
        args_desc = []
        if "properties" in self.input_schema:
            for param_name, param_info in self.input_schema["properties"].items():
                arg_desc = f"- {param_name}: {param_info.get('description', 'No description')}"
                if param_name in self.input_schema.get("required", []):
                    arg_desc += " (required)"
                args_desc.append(arg_desc)
        return f"""
Tool: {self.name}
Description: {self.description}
Arguments:
{chr(10).join(args_desc)}
"""


class MCPManager:
    """MCP管理器 - 管理多个MCP服务器连接"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.servers: Dict[str, Server] = {}
        self.tools_by_server: Dict[str, List[Any]] = {}
        self.all_tools: List[Dict[str, Any]] = []
        self._initialized = False

    async def initialize(self) -> None:
        """初始化MCP管理器，加载服务器配置并连接"""
        if self._initialized:
            return
            
        try:
            # 加载服务器配置
            servers_config = self.config_manager.load_servers_config()
            await self.connect_to_servers(servers_config)
            self._initialized = True
            logging.info("✅ MCP管理器初始化完成")
        except Exception as e:
            logging.error(f"❌ MCP管理器初始化失败: {e}")
            raise

    async def connect_to_servers(self, servers_config: Dict[str, Any]) -> None:
        """根据配置文件同时启动多个服务器并获取工具"""
        mcp_servers = servers_config.get("mcpServers", {})
        for server_name, srv_config in mcp_servers.items():
            server = Server(server_name, srv_config)
            await server.initialize()
            self.servers[server_name] = server
            tools = await server.list_tools()
            self.tools_by_server[server_name] = tools

            for tool in tools:
                # 统一重命名：serverName_toolName
                function_name = f"{server_name}_{tool.name}"
                self.all_tools.append({
                    "type": "function",
                    "function": {
                        "name": function_name,
                        "description": tool.description,
                        "input_schema": tool.input_schema
                    }
                })

        # 转换为 OpenAI Function Calling 所需格式
        self.all_tools = await self.transform_json(self.all_tools)

        logging.info("\n✅ 已连接到下列服务器:")
        for name in self.servers:
            srv_cfg = mcp_servers[name]
            logging.info(f"  - {name}: command={srv_cfg['command']}, args={srv_cfg['args']}")
        logging.info("\n汇总的工具:")
        for t in self.all_tools:
            logging.info(f"  - {t['function']['name']}")

    async def transform_json(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """将工具的 input_schema 转换为 OpenAI 所需的 parameters 格式"""
        result = []
        for item in json_data:
            if not isinstance(item, dict) or "type" not in item or "function" not in item:
                continue
            old_func = item["function"]
            if not isinstance(old_func, dict) or "name" not in old_func or "description" not in old_func:
                continue
            new_func = {
                "name": old_func["name"],
                "description": old_func["description"],
                "parameters": {}
            }
            if "input_schema" in old_func and isinstance(old_func["input_schema"], dict):
                old_schema = old_func["input_schema"]
                new_func["parameters"]["type"] = old_schema.get("type", "object")
                new_func["parameters"]["properties"] = old_schema.get("properties", {})
                new_func["parameters"]["required"] = old_schema.get("required", [])
            new_item = {
                "type": item["type"],
                "function": new_func
            }
            result.append(new_item)
        return result

    async def call_tool(self, tool_full_name: str, tool_args: Dict[str, Any]) -> str:
        """根据 "serverName_toolName" 格式调用相应 MCP 工具"""
        try:
            # 检查事件循环状态
            try:
                loop = asyncio.get_running_loop()
                if loop.is_closed():
                    return f"❌ 工具调用失败: 事件循环已关闭"
            except RuntimeError:
                return f"❌ 工具调用失败: 没有运行中的事件循环"
            
            # 解析工具名称
            parts = tool_full_name.split("_", 1)
            if len(parts) != 2:
                return f"❌ 无效的工具名称: {tool_full_name}"
            
            server_name, tool_name = parts
            
            # 检查服务器是否存在
            server = self.servers.get(server_name)
            if not server:
                return f"❌ 找不到服务器: {server_name}"
            
            # 检查服务器状态
            if not server._initialized:
                return f"❌ 服务器 {server_name} 未初始化或已关闭"
            
            # 执行工具
            resp = await server.execute_tool(tool_name, tool_args)
            return resp.content if resp.content else "✅ 工具执行完成，无输出内容"
            
        except Exception as e:
            error_msg = str(e).lower()
            if "event loop is closed" in error_msg:
                return f"❌ 工具调用失败: 事件循环已关闭"
            elif "no running event loop" in error_msg:
                return f"❌ 工具调用失败: 没有运行中的事件循环"
            elif "server has been cleaned up" in error_msg or "is no longer available" in error_msg:
                return f"❌ 工具调用失败: 服务器不可用"
            else:
                return f"❌ 工具调用失败: {str(e)}"

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """获取所有可用工具"""
        return self.all_tools

    def get_server_status(self) -> Dict[str, str]:
        """获取所有服务器状态"""
        status = {}
        for server_name, server in self.servers.items():
            status[server_name] = "connected" if server._initialized else "disconnected"
        return status

    async def cleanup(self) -> None:
        """清理所有资源"""
        if not self._initialized:
            return
            
        logging.info("开始清理MCP管理器资源...")
        
        cleanup_tasks = []
        for server_name, server in list(self.servers.items()):
            task = asyncio.create_task(self._cleanup_single_server(server_name, server))
            cleanup_tasks.append(task)
        
        if cleanup_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*cleanup_tasks, return_exceptions=True),
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logging.info("服务器清理超时，取消剩余任务")
                for task in cleanup_tasks:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        self.servers.clear()
        self.tools_by_server.clear()
        self.all_tools.clear()
        self._initialized = False
        logging.info("MCP管理器资源清理完成")

    async def _cleanup_single_server(self, server_name: str, server) -> None:
        """清理单个服务器"""
        try:
            logging.info(f"正在清理服务器: {server_name}")
            await asyncio.wait_for(server.cleanup(), timeout=3.0)
            logging.debug(f"服务器 {server_name} 清理成功")
        except asyncio.TimeoutError:
            logging.info(f"服务器 {server_name} 清理超时")
        except Exception as e:
            error_msg = str(e).lower()
            if any(keyword in error_msg for keyword in ["cancel", "scope", "generatorexit", "subprocess", "different task"]):
                logging.debug(f"忽略服务器 {server_name} 的预期清理异常: {e}")
            else:
                logging.warning(f"清理服务器 {server_name} 时出错: {e}")