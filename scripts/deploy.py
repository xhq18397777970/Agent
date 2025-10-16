#!/usr/bin/env python3
"""
MCP 项目部署脚本
提供项目的安装、配置、测试和部署功能
"""

import os
import sys
import subprocess
import shutil
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config_manager import get_config_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ProjectDeployer:
    """项目部署器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.config_manager = get_config_manager()
        
    def check_python_version(self) -> bool:
        """检查 Python 版本"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error(f"❌ Python 版本过低: {version.major}.{version.minor}, 需要 Python 3.8+")
            return False
        
        logger.info(f"✅ Python 版本检查通过: {version.major}.{version.minor}.{version.micro}")
        
        # 检查是否在 Conda 环境中
        if os.environ.get('CONDA_DEFAULT_ENV'):
            conda_env = os.environ.get('CONDA_DEFAULT_ENV')
            logger.info(f"🐍 检测到 Conda 环境: {conda_env}")
        elif os.environ.get('VIRTUAL_ENV'):
            venv_path = os.environ.get('VIRTUAL_ENV')
            logger.info(f"📦 检测到虚拟环境: {venv_path}")
        else:
            logger.warning("⚠️ 未检测到虚拟环境，建议使用 Conda 或 venv")
        
        return True
    
    def install_dependencies(self) -> bool:
        """安装项目依赖"""
        requirements_file = self.project_root / "requirements.txt"
        
        if not requirements_file.exists():
            logger.error("❌ requirements.txt 文件不存在")
            return False
        
        try:
            logger.info("📦 安装项目依赖...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file)
            ], capture_output=True, text=True, cwd=self.project_root)
            
            if result.returncode != 0:
                logger.error(f"❌ 依赖安装失败: {result.stderr}")
                return False
            
            logger.info("✅ 依赖安装成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 依赖安装异常: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """设置环境配置"""
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        # 如果 .env 不存在但 .env.example 存在，则复制
        if not env_file.exists() and env_example.exists():
            shutil.copy(env_example, env_file)
            logger.info("📄 已创建 .env 文件（从 .env.example 复制）")
        
        # 检查必需的环境变量
        required_vars = ["DEEPSEEK_API_KEY"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.warning(f"⚠️ 缺少环境变量: {', '.join(missing_vars)}")
            logger.info("请在 .env 文件中配置这些变量")
            return False
        
        logger.info("✅ 环境配置检查通过")
        return True
    
    def create_directories(self) -> bool:
        """创建必需的目录"""
        directories = [
            "output",
            "logs",
            "temp"
        ]
        
        try:
            for dir_name in directories:
                dir_path = self.project_root / dir_name
                dir_path.mkdir(exist_ok=True)
                logger.info(f"📁 已创建目录: {dir_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建目录失败: {e}")
            return False
    
    def validate_configuration(self) -> bool:
        """验证项目配置"""
        try:
            # 验证服务器配置
            servers_config = self.config_manager.load_servers_config()
            if not servers_config.get("mcpServers"):
                logger.warning("⚠️ 没有配置任何 MCP 服务器")
                return False
            
            # 验证每个服务器
            for server_name, config in servers_config["mcpServers"].items():
                if not self.config_manager.validate_server_config(config):
                    logger.error(f"❌ 服务器配置无效: {server_name}")
                    return False
                
                # 检查服务器文件是否存在
                server_file = self.project_root / config["args"][0]
                if not server_file.exists():
                    logger.error(f"❌ 服务器文件不存在: {server_file}")
                    return False
            
            logger.info("✅ 配置验证通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 配置验证失败: {e}")
            return False
    
    def run_tests(self) -> bool:
        """运行项目测试"""
        tests_dir = self.project_root / "tests"
        
        if not tests_dir.exists():
            logger.info("📋 没有找到测试目录，跳过测试")
            return True
        
        try:
            logger.info("🧪 运行项目测试...")
            
            # 查找测试文件
            test_files = list(tests_dir.glob("test_*.py"))
            if not test_files:
                logger.info("📋 没有找到测试文件，跳过测试")
                return True
            
            # 运行测试
            for test_file in test_files:
                logger.info(f"🔍 运行测试: {test_file.name}")
                result = subprocess.run([
                    sys.executable, str(test_file)
                ], capture_output=True, text=True, cwd=self.project_root)
                
                if result.returncode != 0:
                    logger.error(f"❌ 测试失败: {test_file.name}")
                    logger.error(result.stderr)
                    return False
            
            logger.info("✅ 所有测试通过")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试运行异常: {e}")
            return False
    
    def create_startup_script(self) -> bool:
        """创建启动脚本"""
        scripts = {
            "start.py": """#!/usr/bin/env python3
\"\"\"项目启动脚本\"\"\"
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    from main import main
    import asyncio
    asyncio.run(main())
""",
            "start.sh": """#!/bin/bash
# MCP 项目启动脚本

echo "🚀 启动 MCP 多服务器客户端..."

# 检查 Python 版本
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python 版本: $python_version"

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "📦 虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠️  警告: 未检测到虚拟环境"
fi

# 启动主程序
python3 main.py
""",
            "start.bat": """@echo off
REM MCP 项目启动脚本 (Windows)

echo 🚀 启动 MCP 多服务器客户端...

REM 检查 Python 版本
python --version

REM 启动主程序
python main.py

pause
"""
        }
        
        try:
            for script_name, content in scripts.items():
                script_path = self.project_root / script_name
                with open(script_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                # 为 Unix 脚本添加执行权限
                if script_name.endswith('.sh'):
                    script_path.chmod(0o755)
                
                logger.info(f"📜 已创建启动脚本: {script_name}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 创建启动脚本失败: {e}")
            return False
    
    def generate_deployment_info(self) -> Dict:
        """生成部署信息"""
        info = {
            "deployment_time": str(Path(__file__).stat().st_mtime),
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "project_root": str(self.project_root),
            "configured_servers": self.config_manager.list_available_servers(),
            "environment_variables": {
                "DEEPSEEK_API_KEY": "已配置" if os.getenv("DEEPSEEK_API_KEY") else "未配置",
                "DEEPSEEK_BASE_URL": os.getenv("DEEPSEEK_BASE_URL", "默认"),
                "DEEPSEEK_MODEL": os.getenv("DEEPSEEK_MODEL", "默认")
            }
        }
        
        # 保存部署信息
        info_file = self.project_root / "deployment_info.json"
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2, ensure_ascii=False)
        
        logger.info("📋 已生成部署信息文件")
        return info
    
    def full_deploy(self) -> bool:
        """完整部署流程"""
        logger.info("🚀 开始完整部署流程...")
        
        steps = [
            ("检查 Python 版本", self.check_python_version),
            ("安装依赖", self.install_dependencies),
            ("设置环境", self.setup_environment),
            ("创建目录", self.create_directories),
            ("验证配置", self.validate_configuration),
            ("运行测试", self.run_tests),
            ("创建启动脚本", self.create_startup_script),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 执行步骤: {step_name}")
            if not step_func():
                logger.error(f"❌ 步骤失败: {step_name}")
                return False
        
        # 生成部署信息
        self.generate_deployment_info()
        
        logger.info("🎉 部署完成！")
        logger.info("💡 使用以下命令启动项目:")
        logger.info("   python main.py")
        logger.info("   或使用启动脚本: python start.py")
        
        return True
    
    def quick_setup(self) -> bool:
        """快速设置（仅基本配置）"""
        logger.info("⚡ 快速设置模式...")
        
        steps = [
            ("检查 Python 版本", self.check_python_version),
            ("安装依赖", self.install_dependencies),
            ("创建目录", self.create_directories),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"📋 执行步骤: {step_name}")
            if not step_func():
                logger.error(f"❌ 步骤失败: {step_name}")
                return False
        
        logger.info("⚡ 快速设置完成！")
        logger.info("💡 请手动配置 .env 文件后运行: python main.py")
        
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP 项目部署工具")
    parser.add_argument("action", choices=[
        "full", "quick", "deps", "env", "test", "validate", "info"
    ], help="部署操作")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    deployer = ProjectDeployer()
    
    try:
        if args.action == "full":
            success = deployer.full_deploy()
        elif args.action == "quick":
            success = deployer.quick_setup()
        elif args.action == "deps":
            success = deployer.install_dependencies()
        elif args.action == "env":
            success = deployer.setup_environment()
        elif args.action == "test":
            success = deployer.run_tests()
        elif args.action == "validate":
            success = deployer.validate_configuration()
        elif args.action == "info":
            info = deployer.generate_deployment_info()
            print("📋 部署信息:")
            print(json.dumps(info, indent=2, ensure_ascii=False))
            success = True
        else:
            logger.error(f"❌ 未知操作: {args.action}")
            success = False
        
        return 0 if success else 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ 部署被用户中断")
        return 1
    except Exception as e:
        logger.error(f"❌ 部署失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())