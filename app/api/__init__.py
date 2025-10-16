"""
API蓝图初始化
"""
from flask import Blueprint

# 创建API蓝图
api_bp = Blueprint('api', __name__)

# 导入所有API路由
from app.api import chat, tools, health