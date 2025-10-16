"""
配置管理系统
提供统一的配置加载、验证和管理功能
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    """
    配置管理器
    
    负责加载和管理项目的所有配置信息
    包括环境变量、服务器配置、应用配置等
    """
    
    def __init__(self, config_dir: str = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录，默认为当前文件所在目录
        """
        if config_dir is None:
            config_dir = os.path.dirname(__file__)
        
        self.config_dir = Path(config_dir)
        self.project_root = self.config_dir.parent
        
        # 加载环境变量
        self._load_env_vars()
        
        # 配置缓存
        self._config_cache = {}
        
        logger.info(f"🔧 配置管理器初始化完成，配置目录: {self.config_dir}")
    
    def _load_env_vars(self):
        """加载环境变量"""
        env_files = [
            self.project_root / ".env",
            self.project_root / ".env.local",
            self.config_dir / ".env"
        ]
        
        for env_file in env_files:
            if env_file.exists():
                load_dotenv(env_file)
                logger.info(f"📄 已加载环境变量文件: {env_file}")
    
    def load_servers_config(self) -> Dict[str, Any]:
        """
        加载服务器配置
        
        Returns:
            服务器配置字典
        """
        config_file = self.config_dir / "servers_config.json"
        return self._load_json_config(config_file, "servers_config")
    
    def load_app_config(self) -> Dict[str, Any]:
        """
        加载应用配置
        
        Returns:
            应用配置字典
        """
        config_file = self.config_dir / "app_config.json"
        return self._load_json_config(config_file, "app_config", create_if_missing=True)
    
    def _load_json_config(self, config_file: Path, config_name: str, 
                         create_if_missing: bool = False) -> Dict[str, Any]:
        """
        加载 JSON 配置文件
        
        Args:
            config_file: 配置文件路径
            config_name: 配置名称（用于缓存）
            create_if_missing: 如果文件不存在是否创建默认配置
            
        Returns:
            配置字典
        """
        # 检查缓存
        if config_name in self._config_cache:
            return self._config_cache[config_name]
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                logger.info(f"✅ 已加载配置文件: {config_file}")
            else:
                if create_if_missing:
                    config = self._create_default_config(config_name)
                    self.save_config(config_file, config)
                    logger.info(f"📝 已创建默认配置文件: {config_file}")
                else:
                    raise FileNotFoundError(f"配置文件不存在: {config_file}")
            
            # 缓存配置
            self._config_cache[config_name] = config
            return config
            
        except Exception as e:
            logger.error(f"❌ 加载配置文件失败 {config_file}: {e}")
            raise
    
    def _create_default_config(self, config_name: str) -> Dict[str, Any]:
        """
        创建默认配置
        
        Args:
            config_name: 配置名称
            
        Returns:
            默认配置字典
        """
        if config_name == "app_config":
            return {
                "app": {
                    "name": "MCP Multi-Server Client",
                    "version": "1.0.0",
                    "debug": False
                },
                "logging": {
                    "level": "INFO",
                    "format": "%(asctime)s - %(levelname)s - %(message)s"
                },
                "client": {
                    "max_retries": 3,
                    "timeout": 30,
                    "concurrent_servers": 10
                }
            }
        return {}
    
    def save_config(self, config_file: Path, config: Dict[str, Any]):
        """
        保存配置到文件
        
        Args:
            config_file: 配置文件路径
            config: 配置字典
        """
        try:
            config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 已保存配置文件: {config_file}")
        except Exception as e:
            logger.error(f"❌ 保存配置文件失败 {config_file}: {e}")
            raise
    
    def get_env_var(self, var_name: str, default: Any = None, required: bool = False) -> Any:
        """
        获取环境变量
        
        Args:
            var_name: 环境变量名
            default: 默认值
            required: 是否必需
            
        Returns:
            环境变量值
            
        Raises:
            ValueError: 当必需的环境变量不存在时
        """
        value = os.getenv(var_name, default)
        
        if required and value is None:
            raise ValueError(f"缺少必需的环境变量: {var_name}")
        
        return value
    
    def get_deepseek_config(self) -> Dict[str, str]:
        """
        获取 DeepSeek 配置
        
        Returns:
            DeepSeek 配置字典
        """
        return {
            "api_key": self.get_env_var("DEEPSEEK_API_KEY", required=True),
            "base_url": self.get_env_var("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
            "model": self.get_env_var("DEEPSEEK_MODEL", "deepseek-chat"),
            "timeout": int(self.get_env_var("DEEPSEEK_TIMEOUT", "30")),
            "max_retries": int(self.get_env_var("DEEPSEEK_MAX_RETRIES", "3"))
        }
    
    def get_server_config(self, server_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定服务器的配置
        
        Args:
            server_name: 服务器名称
            
        Returns:
            服务器配置字典或 None
        """
        servers_config = self.load_servers_config()
        return servers_config.get("mcpServers", {}).get(server_name)
    
    def list_available_servers(self) -> List[str]:
        """
        列出所有可用的服务器
        
        Returns:
            服务器名称列表
        """
        servers_config = self.load_servers_config()
        return list(servers_config.get("mcpServers", {}).keys())
    
    def add_server_config(self, server_name: str, server_config: Dict[str, Any]):
        """
        添加服务器配置
        
        Args:
            server_name: 服务器名称
            server_config: 服务器配置
        """
        servers_config = self.load_servers_config()
        
        if "mcpServers" not in servers_config:
            servers_config["mcpServers"] = {}
        
        servers_config["mcpServers"][server_name] = server_config
        
        # 保存配置
        config_file = self.config_dir / "servers_config.json"
        self.save_config(config_file, servers_config)
        
        # 更新缓存
        self._config_cache["servers_config"] = servers_config
        
        logger.info(f"➕ 已添加服务器配置: {server_name}")
    
    def remove_server_config(self, server_name: str):
        """
        移除服务器配置
        
        Args:
            server_name: 服务器名称
        """
        servers_config = self.load_servers_config()
        
        if server_name in servers_config.get("mcpServers", {}):
            del servers_config["mcpServers"][server_name]
            
            # 保存配置
            config_file = self.config_dir / "servers_config.json"
            self.save_config(config_file, servers_config)
            
            # 更新缓存
            self._config_cache["servers_config"] = servers_config
            
            logger.info(f"➖ 已移除服务器配置: {server_name}")
        else:
            logger.warning(f"⚠️ 服务器配置不存在: {server_name}")
    
    def validate_server_config(self, server_config: Dict[str, Any]) -> bool:
        """
        验证服务器配置
        
        Args:
            server_config: 服务器配置
            
        Returns:
            是否有效
        """
        required_fields = ["command", "args"]
        
        for field in required_fields:
            if field not in server_config:
                logger.error(f"❌ 服务器配置缺少必需字段: {field}")
                return False
        
        return True
    
    def clear_cache(self):
        """清除配置缓存"""
        self._config_cache.clear()
        logger.info("🗑️ 已清除配置缓存")


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config_manager() -> ConfigManager:
    """
    获取全局配置管理器实例
    
    Returns:
        ConfigManager 实例
    """
    return config_manager


if __name__ == "__main__":
    # 测试配置管理器
    cm = ConfigManager()
    
    print("🔧 测试配置管理器")
    print(f"📁 配置目录: {cm.config_dir}")
    print(f"📁 项目根目录: {cm.project_root}")
    
    try:
        servers = cm.list_available_servers()
        print(f"🖥️ 可用服务器: {servers}")
        
        deepseek_config = cm.get_deepseek_config()
        print(f"🤖 DeepSeek 配置: {deepseek_config}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")