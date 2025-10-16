"""
健康检查API接口
"""
import asyncio
import logging
from flask import jsonify
from functools import wraps

from app.api import api_bp
from app.api.chat import get_chat_service

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

@api_bp.route('/health', methods=['GET'])
@async_route
async def health_check():
    """
    健康检查接口
    
    GET /api/health
    """
    try:
        service = await get_chat_service()
        status = service.get_service_status()
        
        # 检查服务器连接状态
        mcp_servers = status.get('mcp_servers', {})
        all_connected = all(
            server_status == 'connected' 
            for server_status in mcp_servers.values()
        )
        
        # 检查LLM配置
        llm_config = status.get('llm_config', {})
        llm_configured = llm_config.get('api_key_configured', False)
        
        # 确定整体健康状态
        overall_status = "healthy" if (
            status.get('initialized', False) and 
            all_connected and 
            llm_configured
        ) else "unhealthy"
        
        response_data = {
            "success": True,
            "data": {
                "status": overall_status,
                "timestamp": None,  # 可以添加时间戳
                "services": {
                    "chat_service": "initialized" if status.get('initialized', False) else "not_initialized",
                    "mcp_servers": mcp_servers,
                    "llm_client": "configured" if llm_configured else "not_configured"
                },
                "statistics": {
                    "active_sessions": status.get('active_sessions', 0),
                    "available_tools": status.get('available_tools', 0),
                    "connected_servers": sum(1 for s in mcp_servers.values() if s == 'connected')
                }
            }
        }
        
        # 根据健康状态返回适当的HTTP状态码
        status_code = 200 if overall_status == "healthy" else 503
        
        return jsonify(response_data), status_code
        
    except Exception as e:
        logging.error(f"❌ 健康检查错误: {e}")
        return jsonify({
            "success": False,
            "data": {
                "status": "error",
                "error": str(e),
                "message": "健康检查失败"
            }
        }), 500

@api_bp.route('/health/detailed', methods=['GET'])
@async_route
async def detailed_health_check():
    """
    详细健康检查接口
    
    GET /api/health/detailed
    """
    try:
        service = await get_chat_service()
        status = service.get_service_status()
        
        return jsonify({
            "success": True,
            "data": {
                "service_status": status,
                "environment": {
                    "python_version": None,  # 可以添加Python版本信息
                    "flask_version": None,   # 可以添加Flask版本信息
                }
            }
        })
        
    except Exception as e:
        logging.error(f"❌ 详细健康检查错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "详细健康检查失败"
        }), 500