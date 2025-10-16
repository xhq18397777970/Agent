#!/usr/bin/env python3
"""
Conda 环境管理脚本
提供 Conda 环境的创建、激活、更新和删除功能
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CondaManager:
    """Conda 环境管理器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.env_file = self.project_root / "environment.yml"
        self.env_name = "mcp-proj"
    
    def check_conda_installed(self) -> bool:
        """检查 Conda 是否已安装"""
        try:
            result = subprocess.run(["conda", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"✅ Conda 已安装: {result.stdout.strip()}")
                return True
            else:
                logger.error("❌ Conda 未安装或不在 PATH 中")
                return False
        except FileNotFoundError:
            logger.error("❌ Conda 未安装或不在 PATH 中")
            return False
    
    def env_exists(self) -> bool:
        """检查环境是否已存在"""
        try:
            result = subprocess.run(
                ["conda", "env", "list"], 
                capture_output=True, 
                text=True
            )
            return self.env_name in result.stdout
        except Exception as e:
            logger.error(f"❌ 检查环境失败: {e}")
            return False
    
    def create_environment(self) -> bool:
        """创建 Conda 环境"""
        if not self.check_conda_installed():
            return False
        
        if self.env_exists():
            logger.info(f"⚠️ 环境 {self.env_name} 已存在")
            return True
        
        if not self.env_file.exists():
            logger.error(f"❌ 环境配置文件不存在: {self.env_file}")
            return False
        
        try:
            logger.info(f"🔨 创建 Conda 环境: {self.env_name}")
            result = subprocess.run([
                "conda", "env", "create", "-f", str(self.env_file)
            ], cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info(f"✅ 环境创建成功: {self.env_name}")
                return True
            else:
                logger.error("❌ 环境创建失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 创建环境时发生异常: {e}")
            return False
    
    def update_environment(self) -> bool:
        """更新 Conda 环境"""
        if not self.check_conda_installed():
            return False
        
        if not self.env_exists():
            logger.error(f"❌ 环境 {self.env_name} 不存在，请先创建")
            return False
        
        try:
            logger.info(f"🔄 更新 Conda 环境: {self.env_name}")
            result = subprocess.run([
                "conda", "env", "update", "-f", str(self.env_file)
            ], cwd=self.project_root)
            
            if result.returncode == 0:
                logger.info(f"✅ 环境更新成功: {self.env_name}")
                return True
            else:
                logger.error("❌ 环境更新失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新环境时发生异常: {e}")
            return False
    
    def remove_environment(self) -> bool:
        """删除 Conda 环境"""
        if not self.check_conda_installed():
            return False
        
        if not self.env_exists():
            logger.info(f"⚠️ 环境 {self.env_name} 不存在")
            return True
        
        try:
            logger.info(f"🗑️ 删除 Conda 环境: {self.env_name}")
            result = subprocess.run([
                "conda", "env", "remove", "-n", self.env_name, "-y"
            ])
            
            if result.returncode == 0:
                logger.info(f"✅ 环境删除成功: {self.env_name}")
                return True
            else:
                logger.error("❌ 环境删除失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 删除环境时发生异常: {e}")
            return False
    
    def get_activation_command(self) -> str:
        """获取环境激活命令"""
        return f"conda activate {self.env_name}"
    
    def show_environment_info(self):
        """显示环境信息"""
        if not self.check_conda_installed():
            return
        
        try:
            logger.info("📋 Conda 环境信息:")
            
            # 显示环境列表
            result = subprocess.run(
                ["conda", "env", "list"], 
                capture_output=True, 
                text=True
            )
            
            if self.env_name in result.stdout:
                logger.info(f"✅ 环境 {self.env_name} 已存在")
                
                # 显示环境中的包
                logger.info(f"📦 环境 {self.env_name} 中的包:")
                pkg_result = subprocess.run([
                    "conda", "list", "-n", self.env_name
                ], capture_output=True, text=True)
                
                if pkg_result.returncode == 0:
                    lines = pkg_result.stdout.strip().split('\n')
                    for line in lines[-10:]:  # 显示最后10个包
                        if line and not line.startswith('#'):
                            logger.info(f"  {line}")
            else:
                logger.info(f"❌ 环境 {self.env_name} 不存在")
                
        except Exception as e:
            logger.error(f"❌ 获取环境信息失败: {e}")
    
    def export_environment(self) -> bool:
        """导出当前环境配置"""
        if not self.env_exists():
            logger.error(f"❌ 环境 {self.env_name} 不存在")
            return False
        
        try:
            logger.info(f"📤 导出环境配置: {self.env_name}")
            
            # 导出到 environment.yml
            with open(self.env_file, 'w') as f:
                result = subprocess.run([
                    "conda", "env", "export", "-n", self.env_name
                ], stdout=f, text=True)
            
            if result.returncode == 0:
                logger.info(f"✅ 环境配置已导出到: {self.env_file}")
                return True
            else:
                logger.error("❌ 环境配置导出失败")
                return False
                
        except Exception as e:
            logger.error(f"❌ 导出环境配置时发生异常: {e}")
            return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Conda 环境管理工具")
    parser.add_argument("action", choices=[
        "create", "update", "remove", "info", "export", "check"
    ], help="要执行的操作")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = CondaManager()
    
    try:
        if args.action == "create":
            success = manager.create_environment()
            if success:
                print(f"\n🎉 环境创建成功！")
                print(f"💡 使用以下命令激活环境:")
                print(f"   {manager.get_activation_command()}")
                print(f"   python main.py")
        
        elif args.action == "update":
            success = manager.update_environment()
            if success:
                print(f"\n✅ 环境更新成功！")
        
        elif args.action == "remove":
            success = manager.remove_environment()
            if success:
                print(f"\n🗑️ 环境删除成功！")
        
        elif args.action == "info":
            manager.show_environment_info()
            if manager.env_exists():
                print(f"\n💡 激活环境命令:")
                print(f"   {manager.get_activation_command()}")
        
        elif args.action == "export":
            success = manager.export_environment()
            if success:
                print(f"\n📤 环境配置导出成功！")
        
        elif args.action == "check":
            conda_ok = manager.check_conda_installed()
            env_exists = manager.env_exists()
            
            print(f"\n📋 环境检查结果:")
            print(f"  Conda 安装: {'✅' if conda_ok else '❌'}")
            print(f"  环境存在: {'✅' if env_exists else '❌'}")
            
            if conda_ok and not env_exists:
                print(f"\n💡 创建环境命令:")
                print(f"   python scripts/conda_setup.py create")
        
        return 0 if locals().get('success', True) else 1
        
    except KeyboardInterrupt:
        logger.info("\n⚠️ 操作被用户中断")
        return 1
    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())