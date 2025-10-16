"""
对话API接口
"""
import asyncio
import logging
from flask import request, jsonify
from functools import wraps

from app.api import api_bp
from app.core.chat_service import ChatService

# 全局对话服务实例
chat_service = None

def async_route(f):
    """装饰器：支持异步路由"""
    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(f(*args, **kwargs))
        finally:
            loop.close()
    return wrapper

async def get_chat_service():
    """获取对话服务实例（单例模式）"""
    global chat_service
    if chat_service is None:
        chat_service = ChatService()
        await chat_service.initialize()
    return chat_service

@api_bp.route('/chat', methods=['POST'])
@async_route
async def chat():
    """
    对话接口
    
    POST /api/chat
    {
        "message": "用户消息",
        "session_id": "可选的会话ID"
    }
    """
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "请求数据为空",
                "message": "请提供JSON格式的请求数据"
            }), 400
        
        message = data.get('message')
        if not message:
            return jsonify({
                "success": False,
                "error": "消息不能为空",
                "message": "请提供message字段"
            }), 400
        
        session_id = data.get('session_id')
        
        # 获取对话服务
        service = await get_chat_service()
        
        # 处理对话
        result = await service.chat(message, session_id)
        
        # 返回成功响应
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        logging.error(f"❌ 对话API错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "对话处理失败"
        }), 500

@api_bp.route('/chat/history/<session_id>', methods=['GET'])
@async_route
async def get_chat_history(session_id):
    """
    获取对话历史
    
    GET /api/chat/history/<session_id>
    """
    try:
        service = await get_chat_service()
        history = service.get_session_history(session_id)
        
        return jsonify({
            "success": True,
            "data": {
                "session_id": session_id,
                "history": history,
                "message_count": len(history)
            }
        })
        
    except Exception as e:
        logging.error(f"❌ 获取对话历史错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "获取对话历史失败"
        }), 500

@api_bp.route('/chat/clear/<session_id>', methods=['DELETE'])
@async_route
async def clear_chat_history(session_id):
    """
    清除对话历史
    
    DELETE /api/chat/clear/<session_id>
    """
    try:
        service = await get_chat_service()
        success = service.clear_session(session_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"会话 {session_id} 历史已清除"
            })
        else:
            return jsonify({
                "success": False,
                "message": f"会话 {session_id} 不存在"
            }), 404
            
    except Exception as e:
        logging.error(f"❌ 清除对话历史错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "清除对话历史失败"
        }), 500

@api_bp.route('/chat/status', methods=['GET'])
@async_route
async def get_chat_status():
    """
    获取对话服务状态
    
    GET /api/chat/status
    """
    try:
        service = await get_chat_service()
        status = service.get_service_status()
        
        return jsonify({
            "success": True,
            "data": status
        })
        
    except Exception as e:
        logging.error(f"❌ 获取对话状态错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "获取对话状态失败"
        }), 500