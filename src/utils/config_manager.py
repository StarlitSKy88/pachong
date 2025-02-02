"""配置管理器模块"""

import os
import json
import yaml
from typing import Any, Dict, Optional
from pathlib import Path
from dotenv import load_dotenv

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self, config_dir: str = "config"):
        """初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}
        self.env_loaded = False
        
    def load_env(self, env_file: str = ".env") -> None:
        """加载环境变量
        
        Args:
            env_file: 环境变量文件路径
        """
        if not self.env_loaded:
            load_dotenv(env_file)
            self.env_loaded = True
            
    def load_yaml(self, filename: str) -> Dict[str, Any]:
        """加载YAML配置文件
        
        Args:
            filename: 配置文件名
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
            
    def load_json(self, filename: str) -> Dict[str, Any]:
        """加载JSON配置文件
        
        Args:
            filename: 配置文件名
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
            
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
            
    def load_config(self, filename: str) -> None:
        """加载配置文件
        
        Args:
            filename: 配置文件名
        """
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            config_data = self.load_yaml(filename)
        elif filename.endswith(".json"):
            config_data = self.load_json(filename)
        else:
            raise ValueError(f"不支持的配置文件格式: {filename}")
            
        self.config.update(config_data)
        
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
        
    def set(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
        
    def save(self, filename: str) -> None:
        """保存配置到文件
        
        Args:
            filename: 配置文件名
        """
        filepath = self.config_dir / filename
        
        # 创建配置目录
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        if filename.endswith(".yml") or filename.endswith(".yaml"):
            with open(filepath, "w", encoding="utf-8") as f:
                yaml.dump(self.config, f, allow_unicode=True)
        elif filename.endswith(".json"):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"不支持的配置文件格式: {filename}")
            
    def get_env(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量值
        
        Args:
            key: 环境变量名
            default: 默认值
            
        Returns:
            Optional[str]: 环境变量值
        """
        return os.getenv(key, default)
        
    def validate_required(self, keys: list) -> None:
        """验证必需的配置项
        
        Args:
            keys: 必需的配置键列表
            
        Raises:
            ValueError: 当缺少必需的配置项时
        """
        missing = []
        for key in keys:
            if key not in self.config:
                missing.append(key)
                
        if missing:
            raise ValueError(f"缺少必需的配置项: {', '.join(missing)}")
            
    def get_nested(self, key_path: str, default: Any = None) -> Any:
        """获取嵌套的配置值
        
        Args:
            key_path: 以点分隔的配置键路径
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        keys = key_path.split(".")
        value = self.config
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
                
        return value
        
    def merge_config(self, other_config: Dict[str, Any]) -> None:
        """合并其他配置
        
        Args:
            other_config: 要合并的配置
        """
        def merge_dict(d1: Dict[str, Any], d2: Dict[str, Any]) -> Dict[str, Any]:
            """递归合并字典"""
            for k, v in d2.items():
                if k in d1 and isinstance(d1[k], dict) and isinstance(v, dict):
                    merge_dict(d1[k], v)
                else:
                    d1[k] = v
            return d1
            
        self.config = merge_dict(self.config, other_config)
        
    def clear(self) -> None:
        """清除所有配置"""
        self.config.clear()
        
    def __getitem__(self, key: str) -> Any:
        """通过下标访问配置
        
        Args:
            key: 配置键
            
        Returns:
            Any: 配置值
        """
        return self.config[key]
        
    def __setitem__(self, key: str, value: Any) -> None:
        """通过下标设置配置
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
        
    def __contains__(self, key: str) -> bool:
        """检查配置键是否存在
        
        Args:
            key: 配置键
            
        Returns:
            bool: 是否存在
        """
        return key in self.config 