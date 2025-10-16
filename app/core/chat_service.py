"""
对话服务 - 核心业务逻辑
整合MCP管理器和LLM客户端，提供完整的对话功能
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.mcp_manager import MCPManager
from app.core.llm_client import LLMClient


class ChatService:
    """对话服务 - 处理用户对话和工具调用的核心逻辑"""
    
    def __init__(self):
        self.mcp_manager = MCPManager()
        self.llm_client = LLMClient()
        self._initialized = False
        self.sessions: Dict[str, List[Dict[str, Any]]] = {}  # 会话管理

    async def initialize(self) -> None:
        """初始化对话服务"""
        if self._initialized:
            return
            
        try:
            # 初始化MCP管理器
            await self.mcp_manager.initialize()
            
            # 验证LLM连接
            if not self.llm_client.validate_connection():
                raise RuntimeError("LLM连接验证失败")
            
            self._initialized = True
            logging.info("✅ 对话服务初始化完成")
        except Exception as e:
            logging.error(f"❌ 对话服务初始化失败: {e}")
            raise

    async def chat(self, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        处理用户对话
        
        Args:
            message: 用户消息
            session_id: 会话ID（可选）
            
        Returns:
            包含响应和会话信息的字典
        """
        if not self._initialized:
            await self.initialize()
        
        # 处理会话ID
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # 获取或创建会话历史
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        messages = self.sessions[session_id].copy()
        messages.append({"role": "user", "content": message})
        
        try:
            # 使用Function Calling进行对话
            response = await self.chat_with_tools(messages)
            
            # 更新会话历史
            self.sessions[session_id] = messages[-20:]  # 保持最新20条消息
            
            # 提取工具调用信息
            tool_calls = []
            if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls:
                for tool_call in response.choices[0].message.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": json.loads(tool_call.function.arguments)
                    })
            
            return {
                "reply": response.choices[0].message.content or "",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "tool_calls": tool_calls,
                "message_count": len(self.sessions[session_id])
            }
            
        except Exception as e:
            logging.error(f"❌ 对话处理失败: {e}")
            return {
                "reply": f"抱歉，处理您的请求时出现错误: {str(e)}",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "tool_calls": [],
                "error": str(e)
            }

    async def chat_with_tools(self, messages: List[Dict[str, Any]]) -> Any:
        """
        使用工具进行对话 - 支持Function Calling
        
        Args:
            messages: 对话消息列表
            
        Returns:
            LLM响应
        """
        # 获取可用工具
        tools = self.mcp_manager.get_available_tools()
        
        # 调用LLM
        response = self.llm_client.get_response(messages, tools=tools)
        
        # 处理工具调用
        if response.choices[0].finish_reason == "tool_calls":
            while True:
                messages = await self.create_function_response_messages(messages, response)
                response = self.llm_client.get_response(messages, tools=tools)
                if response.choices[0].finish_reason != "tool_calls":
                    break
        
        return response

    async def create_function_response_messages(self, messages: List[Dict[str, Any]], response: Any) -> List[Dict[str, Any]]:
        """
        处理工具调用并将结果添加到消息历史中
        
        Args:
            messages: 当前消息列表
            response: LLM响应（包含工具调用）
            
        Returns:
            更新后的消息列表
        """
        function_call_messages = response.choices[0].message.tool_calls
        
        # 添加助手消息
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
        
        # 执行工具调用并添加结果
        for function_call_message in function_call_messages:
            tool_name = function_call_message.function.name
            tool_args = json.loads(function_call_message.function.arguments)
            
            logging.info(f"🔧 调用工具: {tool_name}, 参数: {tool_args}")
            
            # 调用MCP工具
            try:
                function_response = await self.mcp_manager.call_tool(tool_name, tool_args)
            except Exception as e:
                function_response = f"工具调用失败: {str(e)}"
                logging.error(f"❌ 工具调用失败 {tool_name}: {e}")
            
            messages.append({
                "role": "tool",
                "content": str(function_response),
                "tool_call_id": function_call_message.id,
            })
        
        return messages

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        获取会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话消息列表
        """
        return self.sessions.get(session_id, [])

    def clear_session(self, session_id: str) -> bool:
        """
        清除会话历史
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否成功清除
        """
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def get_available_tools(self) -> List[Dict[str, Any]]:
        """
        获取可用工具列表
        
        Returns:
            工具列表
        """
        return self.mcp_manager.get_available_tools()

    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            服务状态信息
        """
        return {
            "initialized": self._initialized,
            "mcp_servers": self.mcp_manager.get_server_status(),
            "llm_config": self.llm_client.get_config_info(),
            "active_sessions": len(self.sessions),
            "available_tools": len(self.get_available_tools())
        }

    async def cleanup(self) -> None:
        """清理服务资源"""
        if not self._initialized:
            return
            
        try:
            await self.mcp_manager.cleanup()
            self.sessions.clear()
            self._initialized = False
            logging.info("✅ 对话服务清理完成")
        except Exception as e:
            logging.error(f"❌ 对话服务清理失败: {e}")