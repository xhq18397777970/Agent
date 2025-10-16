"""
Flask应用主入口文件
"""
import os
import sys
import logging
from app import create_app

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(__file__))

def main():
    """主函数"""
    try:
        # 创建Flask应用
        app = create_app()
        
        # 获取运行配置
        host = os.getenv('FLASK_HOST', '127.0.0.1')
        port = int(os.getenv('FLASK_PORT', 5000))
        debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        
        logging.info(f"🚀 启动Flask应用")
        logging.info(f"📍 地址: http://{host}:{port}")
        logging.info(f"🔧 调试模式: {debug}")
        
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True  # 支持多线程
        )
        
    except KeyboardInterrupt:
        logging.info("👋 应用被用户中断")
    except Exception as e:
        logging.error(f"❌ Flask应用启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()