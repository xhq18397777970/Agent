#!/usr/bin/env python3
"""
Flask应用启动脚本
"""
import os
import sys
import logging
import argparse

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from app import create_app

def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动MCP Agent Flask后端服务')
    parser.add_argument('--port', type=int, help='服务端口号')
    parser.add_argument('--host', type=str, help='服务主机地址')
    parser.add_argument('--debug', action='store_true', help='启用调试模式')
    args = parser.parse_args()
    
    print("🚀 启动MCP Agent Flask后端服务")
    print("=" * 50)
    
    try:
        # 检查环境变量
        env_file = os.path.join(project_root, '.env')
        if not os.path.exists(env_file):
            print("⚠️  警告: .env文件不存在，请确保已配置环境变量")
        
        # 创建Flask应用
        app = create_app()
        
        # 获取运行配置（命令行参数优先）
        host = args.host or os.getenv('FLASK_HOST', '127.0.0.1')
        port = args.port or int(os.getenv('FLASK_PORT', 5000))
        debug = args.debug or os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
        
        print(f"📍 服务地址: http://{host}:{port}")
        print(f"🔧 调试模式: {debug}")
        print(f"🌐 前端页面: http://{host}:{port}")
        print(f"📡 API接口: http://{host}:{port}/api")
        print("=" * 50)
        print("💡 使用说明:")
        print("  - 访问 http://127.0.0.1:5000 打开Web界面")
        print("  - 使用 Ctrl+C 停止服务")
        print("  - API文档请查看 README_FLASK.md")
        print("=" * 50)
        
        # 启动应用
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务已停止")
    except Exception as e:
        print(f"❌ 服务启动失败: {e}")
        print("💡 请检查:")
        print("  1. 是否安装了所有依赖: pip install -r requirements_flask.txt")
        print("  2. 是否配置了.env文件中的API密钥")
        print("  3. 端口是否被占用")
        sys.exit(1)

if __name__ == '__main__':
    main()