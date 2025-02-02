"""数据库配置"""

import os
from typing import Dict, Any

# 数据库配置
DATABASE_CONFIG = {
    "default": {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "database": os.getenv("DB_NAME", "crawler"),
        "username": os.getenv("DB_USER", "root"),
        "password": os.getenv("DB_PASS", ""),
        "charset": "utf8mb4",
        "connect_timeout": 10,
        "pool_size": 5,
        "pool_timeout": 30,
        "pool_recycle": 3600
    }
}

# SQLite配置（用于测试）
SQLITE_CONFIG = {
    "url": "sqlite:///crawler.db",
    "connect_args": {
        "check_same_thread": False,
        "timeout": 30
    },
    "echo": False
}

def get_database_config(name: str = "default") -> Dict[str, Any]:
    """获取数据库配置
    
    Args:
        name: 配置名称
        
    Returns:
        Dict[str, Any]: 数据库配置
    """
    if name == "sqlite":
        return SQLITE_CONFIG
    return DATABASE_CONFIG.get(name, DATABASE_CONFIG["default"]) 