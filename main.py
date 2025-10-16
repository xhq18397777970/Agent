import asyncio
import json
import logging
import os
import shutil
import sys
from contextlib import AsyncExitStack
from typing import Any, Dict, List, Optional

import httpx
from dotenv import load_dotenv
from openai import OpenAI  # OpenAI Python SDK
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
 
# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
 
 
# =============================
# 配置加载类（支持环境变量及配置文件）
# =============================
# 导入配置管理器
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
from config_manager import get_config_manager

class Configuration:
    """管理 MCP 客户端的环境变量和配置文件"""
 
    def __init__(self) -> None:
        self.config_manager = get_config_manager()
        
        # 从配置管理器获取 DeepSeek 配置
        try:
            deepseek_config = self.config_manager.get_deepseek_config()
            self.api_key = deepseek_config["api_key"]
            self.base_url = deepseek_config["base_url"]
            self.model = deepseek_config["model"]
        except ValueError as e:
            raise ValueError(f"❌ DeepSeek 配置错误: {e}")

    def load_config(self, file_path: str = None) -> Dict[str, Any]:
        """
        从配置管理器加载服务器配置
        
        Args:
            file_path: 配置文件路径（可选，兼容旧版本）
        
        Returns:
            包含服务器配置的字典
        """
        if file_path:
            # 兼容旧版本的文件路径方式
            with open(file_path, "r") as f:
                return json.load(f)
        else:
            # 使用配置管理器
            return self.config_manager.load_servers_config()
 
 
# =============================
# MCP 服务器客户端类
# =============================
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
            
        # command 字段直接从配置获取
        command = self.config["command"]
        if command is None:
            raise ValueError("command 不能为空")
 
        # 创建新的 AsyncExitStack
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
        """获取服务器可用的工具列表
        Returns:
            工具列表
        """
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
        """执行指定工具，并支持重试机制
        Args:
            tool_name: 工具名称
            arguments: 工具参数
            retries: 重试次数
            delay: 重试间隔秒数
        Returns:
            工具调用结果
        """
        if not self.session:
            raise RuntimeError(f"Server {self.name} not initialized")
        attempt = 0
        while attempt < retries:
            try:
                logging.info(f"Executing {tool_name} on server {self.name}...")
                result = await self.session.call_tool(tool_name, arguments)
                return result
            except Exception as e:
                attempt += 1
                logging.warning(
                    f"Error executing tool: {e}. Attempt {attempt} of {retries}."
                )
                if attempt < retries:
                    logging.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    logging.error("Max retries reached. Failing.")
                    raise
 
    async def cleanup(self) -> None:
        """清理服务器资源"""
        async with self._cleanup_lock:
            if not self._initialized:
                return
                
            # 标记为未初始化状态，防止重复清理
            self._initialized = False
            
            try:
                # 先清理session
                if self.session:
                    try:
                        # 尝试优雅关闭session，但不等待太久
                        await asyncio.wait_for(self.session.close(), timeout=0.5)
                    except (asyncio.TimeoutError, AttributeError):
                        # session可能没有close方法或已经关闭
                        pass
                    except Exception as e:
                        logging.debug(f"Session cleanup warning for {self.name}: {e}")
                    finally:
                        self.session = None
                    
                # 清理exit_stack - 使用更保守的方法
                if self.exit_stack:
                    try:
                        # 创建一个新的任务来处理清理，避免跨任务范围问题
                        cleanup_task = asyncio.create_task(self._safe_exit_stack_cleanup())
                        await asyncio.wait_for(cleanup_task, timeout=2.0)
                    except asyncio.TimeoutError:
                        logging.info(f"Exit stack cleanup timed out for server {self.name}")
                        cleanup_task.cancel()
                        try:
                            await cleanup_task
                        except asyncio.CancelledError:
                            pass
                    except Exception as e:
                        error_msg = str(e).lower()
                        if any(keyword in error_msg for keyword in ["cancel", "scope", "generatorexit", "different task"]):
                            logging.debug(f"Ignoring expected async cleanup error for server {self.name}: {e}")
                        else:
                            logging.warning(f"Unexpected error during exit_stack cleanup of server {self.name}: {e}")
                    finally:
                        self.exit_stack = None
                        
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ["cancel", "scope", "generatorexit", "different task"]):
                    logging.debug(f"Ignoring expected async cleanup error during server {self.name} cleanup: {e}")
                else:
                    logging.error(f"Unexpected error during cleanup of server {self.name}: {e}")
            finally:
                # 确保状态被重置
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
 
 
# =============================
# 工具封装类
# =============================
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
 
 
# =============================
# LLM 客户端封装类（使用 OpenAI SDK）
# =============================
class LLMClient:
    """使用 OpenAI SDK 与大模型交互"""
 
    def __init__(self, api_key: str, base_url: Optional[str], model: str) -> None:
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
 
    def get_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """
        发送消息给大模型 API，支持传入工具参数（function calling 格式）
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tools,
        }
        try:
            response = self.client.chat.completions.create(**payload)
            return response
        except Exception as e:
            logging.error(f"Error during LLM call: {e}")
            raise
 
 
# =============================
# 多服务器 MCP 客户端类（集成配置文件、工具格式转换与 OpenAI SDK 调用）
# =============================
class MultiServerMCPClient:
    def __init__(self) -> None:
        """
        管理多个 MCP 服务器，并使用 OpenAI Function Calling 风格的接口调用大模型
        """
        self.exit_stack = AsyncExitStack()
        config = Configuration()
        self.openai_api_key = config.api_key
        self.base_url = config.base_url
        self.model = config.model
        self.client = LLMClient(self.openai_api_key, self.base_url, self.model)
        # (server_name -> Server 对象)
        self.servers: Dict[str, Server] = {}
        # 各个 server 的工具列表
        self.tools_by_server: Dict[str, List[Any]] = {}
        self.all_tools: List[Dict[str, Any]] = []
 
    async def connect_to_servers(self, servers_config: Dict[str, Any]) -> None:
        """
        根据配置文件同时启动多个服务器并获取工具
        servers_config 的格式为：
        {
          "mcpServers": {
              "sqlite": { "command": "uvx", "args": [ ... ] },
              "puppeteer": { "command": "npx", "args": [ ... ] },
              ...
          }
        }
        """
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
        """
        将工具的 input_schema 转换为 OpenAI 所需的 parameters 格式，并删除多余字段
        """
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
 
    async def chat_base(self, messages: List[Dict[str, Any]]) -> Any:
        """
        使用 OpenAI 接口进行对话，并支持多次工具调用（Function Calling）。
        如果返回 finish_reason 为 "tool_calls"，则进行工具调用后再发起请求。
        """
        response = self.client.get_response(messages, tools=self.all_tools)
        # 如果模型返回工具调用
        if response.choices[0].finish_reason == "tool_calls":
            while True:
                messages = await self.create_function_response_messages(messages, response)
                response = self.client.get_response(messages, tools=self.all_tools)
                if response.choices[0].finish_reason != "tool_calls":
                    break
        return response
 
    async def create_function_response_messages(self, messages: List[Dict[str, Any]], response: Any) -> List[Dict[str, Any]]:
        """
        将模型返回的工具调用解析执行，并将结果追加到消息队列中
        """
        function_call_messages = response.choices[0].message.tool_calls
        # 修复：正确格式化助手消息
        assistant_message = {
            "role": "assistant",
            "content": response.choices[0].message.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                } for tc in function_call_messages
            ]
        }
        messages.append(assistant_message)
        
        for function_call_message in function_call_messages:
            tool_name = function_call_message.function.name
            tool_args = json.loads(function_call_message.function.arguments)
            # 调用 MCP 工具
            function_response = await self._call_mcp_tool(tool_name, tool_args)
            messages.append({
                "role": "tool",
                "content": str(function_response),  # 确保内容是字符串
                "tool_call_id": function_call_message.id,
            })
        return messages
 
    async def process_query(self, user_query: str) -> str:
        """
        OpenAI Function Calling 流程：
         1. 发送用户消息 + 工具信息
         2. 若模型返回 finish_reason 为 "tool_calls"，则解析并调用 MCP 工具
         3. 将工具调用结果返回给模型，获得最终回答
        """
        messages = [{"role": "user", "content": user_query}]
        response = self.client.get_response(messages, tools=self.all_tools)
        content = response.choices[0]
        logging.info(content)
        if content.finish_reason == "tool_calls":
            tool_call = content.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            logging.info(f"\n[ 调用工具: {tool_name}, 参数: {tool_args} ]\n")
            result = await self._call_mcp_tool(tool_name, tool_args)
            
            # 修复：正确格式化助手消息
            assistant_message = {
                "role": "assistant",
                "content": content.message.content,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": tool_call.type,
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                ]
            }
            messages.append(assistant_message)
            messages.append({
                "role": "tool",
                "content": str(result),  # 确保内容是字符串
                "tool_call_id": tool_call.id,
            })
            response = self.client.get_response(messages, tools=self.all_tools)
            return response.choices[0].message.content
        return content.message.content
 
    async def _call_mcp_tool(self, tool_full_name: str, tool_args: Dict[str, Any]) -> str:
        """
        根据 "serverName_toolName" 格式调用相应 MCP 工具
        """
        parts = tool_full_name.split("_", 1)
        if len(parts) != 2:
            return f"无效的工具名称: {tool_full_name}"
        server_name, tool_name = parts
        server = self.servers.get(server_name)
        if not server:
            return f"找不到服务器: {server_name}"
        resp = await server.execute_tool(tool_name, tool_args)
        return resp.content if resp.content else "工具执行无输出"
 
    async def chat_loop(self) -> None:
        """多服务器 MCP + OpenAI Function Calling 客户端主循环"""
        logging.info("\n🤖 多服务器 MCP + Function Calling 客户端已启动！输入 'quit' 退出。")
        messages: List[Dict[str, Any]] = []
        while True:
            query = input("\n你: ").strip()
            if query.lower() == "quit":
                break
            try:
                messages.append({"role": "user", "content": query})
                messages = messages[-20:]  # 保持最新 20 条上下文
                response = await self.chat_base(messages)
                messages.append(response.choices[0].message.model_dump())
                result = response.choices[0].message.content
                # logging.info(f"\nAI: {result}")
                print(f"\nAI: {result}")
            except Exception as e:
                print(f"\n⚠️  调用过程出错: {e}")
 
    async def cleanup(self) -> None:
        """关闭所有资源"""
        logging.info("开始清理MCP客户端资源...")
        
        # 首先清理所有服务器，使用并发但有限制的方式
        cleanup_tasks = []
        for server_name, server in list(self.servers.items()):
            task = asyncio.create_task(self._cleanup_single_server(server_name, server))
            cleanup_tasks.append(task)
        
        # 等待所有服务器清理完成，但设置总体超时
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
                # 等待取消完成
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        # 清理主要的 exit_stack - 使用独立任务避免跨任务范围问题
        if hasattr(self, 'exit_stack') and self.exit_stack:
            try:
                cleanup_task = asyncio.create_task(self._safe_main_exit_stack_cleanup())
                await asyncio.wait_for(cleanup_task, timeout=2.0)
            except asyncio.TimeoutError:
                logging.info("主exit_stack清理超时")
                cleanup_task.cancel()
                try:
                    await cleanup_task
                except asyncio.CancelledError:
                    pass
            except Exception as e:
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ["cancel", "scope", "generatorexit", "different task"]):
                    logging.debug(f"忽略预期的主清理异常: {e}")
                else:
                    logging.warning(f"主清理过程中的意外错误: {e}")
        
        # 清理状态
        self.servers.clear()
        self.tools_by_server.clear()
        self.all_tools.clear()
        logging.info("MCP客户端资源清理完成")

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

    async def _safe_main_exit_stack_cleanup(self) -> None:
        """安全地清理主exit_stack"""
        if hasattr(self, 'exit_stack') and self.exit_stack:
            try:
                await self.exit_stack.aclose()
            except Exception as e:
                error_msg = str(e).lower()
                if not any(keyword in error_msg for keyword in ["cancel", "scope", "generatorexit", "different task"]):
                    raise
 
 
# =============================
# 主函数
# =============================
async def main() -> None:
    """主函数 - 改进的异常处理和资源清理"""
    client = None
    
    try:
        # 使用配置管理器加载服务器配置
        config = Configuration()
        servers_config = config.load_config()  # 使用配置管理器
        client = MultiServerMCPClient()
        
        # 连接服务器
        await client.connect_to_servers(servers_config)
        
        # 开始聊天循环
        await client.chat_loop()
        
    except KeyboardInterrupt:
        logging.info("收到中断信号，正在退出...")
    except Exception as e:
        logging.error(f"程序运行出错: {e}")
        import traceback
        logging.debug(f"详细错误信息: {traceback.format_exc()}")
    finally:
        # 资源清理 - 使用更健壮的方法
        if client is not None:
            logging.info("正在清理资源...")
            
            # 创建一个新的事件循环任务来处理清理，避免跨任务问题
            cleanup_task = None
            try:
                # 给正在运行的任务一点时间完成
                await asyncio.sleep(0.1)
                
                # 创建清理任务
                cleanup_task = asyncio.create_task(client.cleanup())
                
                # 等待清理完成，设置合理的超时
                await asyncio.wait_for(cleanup_task, timeout=8.0)
                logging.info("资源清理完成")
                
            except asyncio.TimeoutError:
                logging.info("资源清理超时，正在强制清理...")
                if cleanup_task and not cleanup_task.done():
                    cleanup_task.cancel()
                    try:
                        await cleanup_task
                    except asyncio.CancelledError:
                        logging.info("清理任务已取消")
                        
            except Exception as e:
                # 处理各种可能的清理异常
                error_msg = str(e).lower()
                expected_errors = [
                    "cancel", "scope", "generatorexit", "subprocess",
                    "wait", "different task", "runtimeerror"
                ]
                
                if any(keyword in error_msg for keyword in expected_errors):
                    logging.debug(f"退出时检测到预期的异步清理异常（已忽略）: {e}")
                else:
                    logging.warning(f"清理资源时发生意外错误: {e}")
            
            # 最终状态清理
            try:
                # 给系统一点时间完成最后的清理
                await asyncio.sleep(0.05)
            except:
                pass
                
        logging.info("程序退出")


def run_main():
    """运行主函数的包装器，处理事件循环相关的异常"""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("程序被用户中断")
    except Exception as e:
        error_msg = str(e).lower()
        expected_errors = [
            "cancel", "scope", "generatorexit", "runtimeerror",
            "attempted to exit cancel scope", "different task"
        ]
        
        if any(keyword in error_msg for keyword in expected_errors):
            logging.debug(f"程序退出时的预期异常（已忽略）: {e}")
        else:
            logging.error(f"程序异常退出: {e}")


if __name__ == "__main__":
    run_main()