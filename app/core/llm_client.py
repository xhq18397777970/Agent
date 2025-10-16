"""
LLM客户端 - 重构自原main.py中的LLMClient
负责与DeepSeek API进行交互
"""
import logging
import os
import sys
from typing import Any, Dict, List, Optional

from openai import OpenAI

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))
from config.config_manager import get_config_manager


class LLMClient:
    """使用 OpenAI SDK 与大模型交互"""

    def __init__(self):
        """初始化LLM客户端，从配置管理器获取配置"""
        self.config_manager = get_config_manager()
        
        try:
            deepseek_config = self.config_manager.get_deepseek_config()
            self.api_key = deepseek_config["api_key"]
            self.base_url = deepseek_config["base_url"]
            self.model = deepseek_config["model"]
            
            # 创建OpenAI客户端
            self.client = OpenAI(
                api_key=self.api_key, 
                base_url=self.base_url
            )
            
            logging.info(f"✅ LLM客户端初始化成功，模型: {self.model}")
        except ValueError as e:
            logging.error(f"❌ LLM客户端初始化失败: {e}")
            raise

    def get_response(self, messages: List[Dict[str, Any]], tools: Optional[List[Dict[str, Any]]] = None) -> Any:
        """
        发送消息给大模型 API，支持传入工具参数（function calling 格式）
        
        Args:
            messages: 对话消息列表
            tools: 可用工具列表
            
        Returns:
            模型响应
        """
        payload = {
            "model": self.model,
            "messages": messages,
        }
        
        # 只有在有工具时才添加tools参数
        if tools:
            payload["tools"] = tools
            
        try:
            response = self.client.chat.completions.create(**payload)
            return response
        except Exception as e:
            logging.error(f"❌ LLM API调用失败: {e}")
            raise

    def create_simple_response(self, user_message: str) -> str:
        """
        创建简单的对话响应（不使用工具）
        
        Args:
            user_message: 用户消息
            
        Returns:
            模型响应文本
        """
        try:
            messages = [{"role": "user", "content": user_message}]
            response = self.get_response(messages)
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"❌ 简单对话失败: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"

    def validate_connection(self) -> bool:
        """
        验证与LLM API的连接
        
        Returns:
            连接是否正常
        """
        try:
            test_response = self.create_simple_response("测试连接")
            return bool(test_response and len(test_response) > 0)
        except Exception as e:
            logging.error(f"❌ LLM连接验证失败: {e}")
            return False

    def get_config_info(self) -> Dict[str, Any]:
        """
        获取当前配置信息
        
        Returns:
            配置信息字典
        """
        return {
            "model": self.model,
            "base_url": self.base_url,
            "api_key_configured": bool(self.api_key and len(self.api_key) > 10)
        }