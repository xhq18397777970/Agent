"""
Flask应用工厂模式
"""
import asyncio
import logging
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def create_app():
    """Flask应用工厂函数"""
    # 加载环境变量
    load_dotenv()
    
    # 创建Flask应用
    app = Flask(__name__)
    
    # 配置CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # 配置应用
    app.config['SECRET_KEY'] = 'mcp-agent-flask-secret-key'
    app.config['JSON_AS_ASCII'] = False  # 支持中文JSON响应
    
    # 注册蓝图
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # 注册静态文件路由
    @app.route('/')
    def index():
        return app.send_static_file('index.html')
    
    # 全局错误处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "服务器内部错误"
        }, 500
    
    return app