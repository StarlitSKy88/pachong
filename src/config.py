"""配置模块"""

from pathlib import Path
import json
import os
from typing import Dict, Any, Optional

# 项目根目录
ROOT_DIR = Path(__file__).parent.parent

# 数据目录
DATA_DIR = ROOT_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 日志目录
LOG_DIR = ROOT_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

class Config:
    """配置管理类"""
    
    _instance = None  # 单例实例
    _config_dir = Path("config")  # 默认配置目录
    _env_dir = Path("config/env")  # 环境变量配置目录
    _data_dir = Path("data")  # 数据目录
    
    def __new__(cls):
        """实现单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化配置管理器"""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._ensure_dirs()
            self._load_config()
    
    @classmethod
    def set_config_dir(cls, path: Path):
        """设置配置目录
        
        Args:
            path: 配置目录路径
        """
        cls._config_dir = path
        cls._env_dir = path / "env"
        
    @classmethod
    def set_data_dir(cls, path: Path):
        """设置数据目录
        
        Args:
            path: 数据目录路径
        """
        cls._data_dir = path
    
    def _ensure_dirs(self):
        """确保必要的目录存在"""
        # 确保配置目录存在
        self._config_dir.mkdir(exist_ok=True)
        self._env_dir.mkdir(exist_ok=True)
        
        # 确保数据目录存在
        self._data_dir.mkdir(exist_ok=True)
        (self._data_dir / "logs").mkdir(exist_ok=True)
        (self._data_dir / "output").mkdir(exist_ok=True)
        (self._data_dir / "cache").mkdir(exist_ok=True)
        (self._data_dir / "downloads").mkdir(exist_ok=True)
        
        # 设置配置文件路径
        self.config_file = self._config_dir / "config.json"
        self.env_file = self._env_dir / ".env"

    def _load_config(self):
        """加载配置文件"""
        if not self.config_file.exists():
            self._create_default_config()
        
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 从环境变量加载配置
            self._load_env_config()
        except Exception as e:
            self.config = self._create_default_config()
            
    def _load_env_config(self):
        """从环境变量文件加载配置"""
        if self.env_file.exists():
            with open(self.env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
                        
    def _create_default_config(self) -> Dict[str, Any]:
        """创建默认配置
        
        Returns:
            Dict[str, Any]: 默认配置字典
        """
        default_config = {
            "paths": {
                "data_dir": str(self._data_dir),
                "logs_dir": str(self._data_dir / "logs"),
                "output_dir": str(self._data_dir / "output"),
                "cache_dir": str(self._data_dir / "cache"),
                "downloads_dir": str(self._data_dir / "downloads")
            },
            "database": {
                "url": "sqlite:///data/db.sqlite3"
            },
            "logging": {
                "level": "INFO",
                "format": "json"
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, indent=4, ensure_ascii=False)
            
        return default_config
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        try:
            value = self.config
            for k in key.split('.'):
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
            
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
            
    def reload(self):
        """重新加载配置"""
        self._load_config()

# 创建全局配置实例
config = Config() 

# 数据库配置
def get_database_config() -> Dict[str, Any]:
    """获取数据库配置

    Returns:
        Dict[str, Any]: 数据库配置
    """
    return {
        "url": os.getenv("DATABASE_URL", "sqlite:///data/crawler.db"),
        "engine_kwargs": {
            "echo": False,
            "pool_pre_ping": True,
            "pool_recycle": 3600
        }
    }

# 爬虫配置
CRAWLER_CONFIG = {
    "rate_limit": 1,  # 每秒请求数
    "timeout": 30,  # 请求超时时间(秒)
    "retry": {  # 重试配置
        "max_retries": 3,  # 最大重试次数
        "delay": 1,  # 重试延迟(秒)
        "backoff": 2  # 重试延迟倍数
    },
    "proxy": {  # 代理配置
        "enabled": False,  # 是否启用代理
        "url": None,  # 代理服务器URL
        "auth": None  # 代理认证信息
    }
}

# 监控配置
MONITOR_CONFIG = {
    "enabled": True,  # 是否启用监控
    "interval": 60,  # 监控间隔(秒)
    "metrics": {  # 监控指标
        "request_count": True,  # 请求数
        "error_count": True,  # 错误数
        "response_time": True  # 响应时间
    },
    "alert": {  # 告警配置
        "enabled": False,  # 是否启用告警
        "threshold": {  # 告警阈值
            "error_rate": 0.1,  # 错误率
            "response_time": 5  # 响应时间(秒)
        }
    }
}

# 日志配置
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "default",
            "filename": str(LOG_DIR / "crawler.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "level": "DEBUG"
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "file"]
    }
} 