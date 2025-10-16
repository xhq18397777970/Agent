#!/usr/bin/env python3
"""
MCP 服务器管理脚本
提供服务器的动态加载、启动、停止和管理功能
"""

import os
import sys
import json
import subprocess
import signal
import time
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import psutil

# 添加项目根目录到 Python 路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from config.config_manager import get_config_manager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ServerManager:
    """MCP 服务器管理器"""
    
    def __init__(self):
        self.config_manager = get_config_manager()
        self.project_root = Path(__file__).parent.parent
        self.servers_dir = self.project_root / "servers"
        self.running_servers = {}  # server_name -> process
        
    def list_available_servers(self) -> List[str]:
        """列出所有可用的服务器"""
        return self.config_manager.list_available_servers()
    
    def get_server_info(self, server_name: str) -> Optional[Dict]:
        """获取服务器信息"""
        config = self.config_manager.get_server_config(server_name)
        if not config:
            return None
        
        server_file = self.servers_dir / config["args"][0].replace("servers/", "")
        
        return {
            "name": server_name,
            "config": config,
            "file_path": str(server_file),
            "exists": server_file.exists(),
            "running": server_name in self.running_servers
        }
    
    def discover_servers(self) -> List[str]:
        """自动发现服务器目录中的服务器文件"""
        discovered = []
        
        if not self.servers_dir.exists():
            logger.warning(f"服务器目录不存在: {self.servers_dir}")
            return discovered
        
        for server_file in self.servers_dir.glob("*_server.py"):
            if server_file.name != "__init__.py":
                server_name = server_file.stem.replace("_server", "")
                discovered.append(server_name)
        
        return discovered
    
    def auto_register_servers(self) -> int:
        """自动注册发现的服务器"""
        discovered = self.discover_servers()
        registered_count = 0
        
        for server_name in discovered:
            if not self.config_manager.get_server_config(server_name):
                server_config = {
                    "command": "python",
                    "args": [f"servers/{server_name}_server.py"],
                    "description": f"自动发现的 {server_name} 服务器"
                }
                
                self.config_manager.add_server_config(server_name, server_config)
                registered_count += 1
                logger.info(f"✅ 自动注册服务器: {server_name}")
        
        return registered_count
    
    def validate_server(self, server_name: str) -> Tuple[bool, str]:
        """验证服务器配置和文件"""
        config = self.config_manager.get_server_config(server_name)
        if not config:
            return False, f"服务器配置不存在: {server_name}"
        
        if not self.config_manager.validate_server_config(config):
            return False, f"服务器配置无效: {server_name}"
        
        # 检查服务器文件
        server_file = self.servers_dir / config["args"][0].replace("servers/", "")
        if not server_file.exists():
            return False, f"服务器文件不存在: {server_file}"
        
        return True, "验证通过"
    
    def start_server(self, server_name: str) -> bool:
        """启动指定服务器"""
        if server_name in self.running_servers:
            logger.warning(f"服务器已在运行: {server_name}")
            return True
        
        # 验证服务器
        is_valid, message = self.validate_server(server_name)
        if not is_valid:
            logger.error(f"服务器验证失败: {message}")
            return False
        
        config = self.config_manager.get_server_config(server_name)
        
        try:
            # 构建命令
            cmd = [config["command"]] + config["args"]
            
            # 启动进程
            process = subprocess.Popen(
                cmd,
                cwd=str(self.project_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )
            
            # 等待一小段时间检查进程是否正常启动
            time.sleep(1)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                logger.error(f"服务器启动失败: {server_name}")
                logger.error(f"错误输出: {stderr.decode()}")
                return False
            
            self.running_servers[server_name] = process
            logger.info(f"✅ 服务器启动成功: {server_name} (PID: {process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"启动服务器失败 {server_name}: {e}")
            return False
    
    def stop_server(self, server_name: str) -> bool:
        """停止指定服务器"""
        if server_name not in self.running_servers:
            logger.warning(f"服务器未在运行: {server_name}")
            return True
        
        process = self.running_servers[server_name]
        
        try:
            # 尝试优雅关闭
            process.terminate()
            
            # 等待进程结束
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # 强制杀死进程
                process.kill()
                process.wait()
            
            del self.running_servers[server_name]
            logger.info(f"🛑 服务器已停止: {server_name}")
            return True
            
        except Exception as e:
            logger.error(f"停止服务器失败 {server_name}: {e}")
            return False
    
    def restart_server(self, server_name: str) -> bool:
        """重启指定服务器"""
        logger.info(f"🔄 重启服务器: {server_name}")
        
        if not self.stop_server(server_name):
            return False
        
        time.sleep(1)  # 等待一秒
        
        return self.start_server(server_name)
    
    def start_all_servers(self) -> Dict[str, bool]:
        """启动所有配置的服务器"""
        results = {}
        servers = self.list_available_servers()
        
        logger.info(f"🚀 启动所有服务器 ({len(servers)} 个)")
        
        for server_name in servers:
            results[server_name] = self.start_server(server_name)
        
        return results
    
    def stop_all_servers(self) -> Dict[str, bool]:
        """停止所有运行中的服务器"""
        results = {}
        running_servers = list(self.running_servers.keys())
        
        logger.info(f"🛑 停止所有服务器 ({len(running_servers)} 个)")
        
        for server_name in running_servers:
            results[server_name] = self.stop_server(server_name)
        
        return results
    
    def get_server_status(self, server_name: str) -> Dict:
        """获取服务器状态"""
        info = self.get_server_info(server_name)
        if not info:
            return {"error": f"服务器不存在: {server_name}"}
        
        status = {
            "name": server_name,
            "running": server_name in self.running_servers,
            "config_valid": info["exists"],
            "file_exists": info["exists"]
        }
        
        if server_name in self.running_servers:
            process = self.running_servers[server_name]
            status.update({
                "pid": process.pid,
                "running_time": time.time() - psutil.Process(process.pid).create_time()
            })
        
        return status
    
    def get_all_status(self) -> Dict:
        """获取所有服务器状态"""
        servers = self.list_available_servers()
        discovered = self.discover_servers()
        
        return {
            "configured_servers": len(servers),
            "discovered_servers": len(discovered),
            "running_servers": len(self.running_servers),
            "servers": {name: self.get_server_status(name) for name in servers},
            "discovered_not_configured": [s for s in discovered if s not in servers]
        }
    
    def cleanup(self):
        """清理资源"""
        logger.info("🧹 清理服务器管理器资源")
        self.stop_all_servers()


def main():
    """主函数 - 命令行接口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP 服务器管理工具")
    parser.add_argument("action", choices=[
        "list", "discover", "auto-register", "start", "stop", "restart", 
        "start-all", "stop-all", "status", "validate"
    ], help="要执行的操作")
    parser.add_argument("server", nargs="?", help="服务器名称（某些操作需要）")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    manager = ServerManager()
    
    try:
        if args.action == "list":
            servers = manager.list_available_servers()
            print(f"📋 配置的服务器 ({len(servers)} 个):")
            for server in servers:
                info = manager.get_server_info(server)
                status = "🟢 运行中" if info["running"] else "🔴 已停止"
                print(f"  - {server}: {status}")
        
        elif args.action == "discover":
            discovered = manager.discover_servers()
            print(f"🔍 发现的服务器文件 ({len(discovered)} 个):")
            for server in discovered:
                print(f"  - {server}")
        
        elif args.action == "auto-register":
            count = manager.auto_register_servers()
            print(f"✅ 自动注册了 {count} 个服务器")
        
        elif args.action == "start":
            if not args.server:
                print("❌ 请指定服务器名称")
                return 1
            
            if manager.start_server(args.server):
                print(f"✅ 服务器启动成功: {args.server}")
            else:
                print(f"❌ 服务器启动失败: {args.server}")
                return 1
        
        elif args.action == "stop":
            if not args.server:
                print("❌ 请指定服务器名称")
                return 1
            
            if manager.stop_server(args.server):
                print(f"🛑 服务器停止成功: {args.server}")
            else:
                print(f"❌ 服务器停止失败: {args.server}")
                return 1
        
        elif args.action == "restart":
            if not args.server:
                print("❌ 请指定服务器名称")
                return 1
            
            if manager.restart_server(args.server):
                print(f"🔄 服务器重启成功: {args.server}")
            else:
                print(f"❌ 服务器重启失败: {args.server}")
                return 1
        
        elif args.action == "start-all":
            results = manager.start_all_servers()
            success_count = sum(results.values())
            total_count = len(results)
            print(f"🚀 启动结果: {success_count}/{total_count} 个服务器启动成功")
            
            for server, success in results.items():
                status = "✅" if success else "❌"
                print(f"  {status} {server}")
        
        elif args.action == "stop-all":
            results = manager.stop_all_servers()
            success_count = sum(results.values())
            total_count = len(results)
            print(f"🛑 停止结果: {success_count}/{total_count} 个服务器停止成功")
        
        elif args.action == "status":
            if args.server:
                status = manager.get_server_status(args.server)
                print(f"📊 服务器状态: {args.server}")
                print(json.dumps(status, indent=2, ensure_ascii=False))
            else:
                status = manager.get_all_status()
                print("📊 所有服务器状态:")
                print(json.dumps(status, indent=2, ensure_ascii=False))
        
        elif args.action == "validate":
            if not args.server:
                print("❌ 请指定服务器名称")
                return 1
            
            is_valid, message = manager.validate_server(args.server)
            if is_valid:
                print(f"✅ 服务器验证通过: {args.server}")
            else:
                print(f"❌ 服务器验证失败: {message}")
                return 1
    
    except KeyboardInterrupt:
        print("\n⚠️ 操作被用户中断")
    except Exception as e:
        print(f"❌ 操作失败: {e}")
        return 1
    finally:
        manager.cleanup()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())