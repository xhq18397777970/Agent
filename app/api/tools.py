"""
工具管理API接口
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

@api_bp.route('/tools', methods=['GET'])
@async_route
async def get_tools():
    """
    获取所有可用工具
    
    GET /api/tools
    """
    try:
        service = await get_chat_service()
        tools = service.get_available_tools()
        
        # 格式化工具信息
        formatted_tools = []
        for tool in tools:
            if 'function' in tool:
                func_info = tool['function']
                tool_name = func_info.get('name', '')
                
                # 解析服务器名称
                server_name = tool_name.split('_')[0] if '_' in tool_name else 'unknown'
                
                formatted_tools.append({
                    "name": func_info.get('name', ''),
                    "description": func_info.get('description', ''),
                    "server": server_name,
                    "parameters": func_info.get('parameters', {})
                })
        
        return jsonify({
            "success": True,
            "data": {
                "tools": formatted_tools,
                "count": len(formatted_tools)
            }
        })
        
    except Exception as e:
        logging.error(f"❌ 获取工具列表错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "获取工具列表失败"
        }), 500

@api_bp.route('/tools/servers', methods=['GET'])
@async_route
async def get_tool_servers():
    """
    获取工具服务器状态
    
    GET /api/tools/servers
    """
    try:
        service = await get_chat_service()
        status = service.get_service_status()
        
        return jsonify({
            "success": True,
            "data": {
                "servers": status.get('mcp_servers', {}),
                "total_tools": status.get('available_tools', 0)
            }
        })
        
    except Exception as e:
        logging.error(f"❌ 获取服务器状态错误: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "获取服务器状态失败"
        }), 500