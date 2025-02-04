"""配置模块。"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseModel

class DatabaseConfig(BaseModel):
    """数据库配置"""
    type: str = "sqlite"
    name: str = "crawler"
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None

class Config(BaseModel):
    """配置类"""
    database: DatabaseConfig = DatabaseConfig()
    debug: bool = False
    log_level: str = "INFO"
    proxy_enabled: bool = False
    proxy_url: Optional[str] = None
    cookie_enabled: bool = False
    cookie_file: Optional[str] = None
    rate_limit: int = 1
    retry_times: int = 3
    retry_interval: int = 1
    timeout: int = 30
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    @classmethod
    def from_env(cls) -> "Config":
        """从环境变量加载配置"""
        database_config = DatabaseConfig(
            type=os.getenv("DB_TYPE", "sqlite"),
            name=os.getenv("DB_NAME", "crawler"),
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "0")) or None,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
        )

        return cls(
            database=database_config,
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            proxy_enabled=os.getenv("PROXY_ENABLED", "false").lower() == "true",
            proxy_url=os.getenv("PROXY_URL"),
            cookie_enabled=os.getenv("COOKIE_ENABLED", "false").lower() == "true",
            cookie_file=os.getenv("COOKIE_FILE"),
            rate_limit=int(os.getenv("RATE_LIMIT", "1")),
            retry_times=int(os.getenv("RETRY_TIMES", "3")),
            retry_interval=int(os.getenv("RETRY_INTERVAL", "1")),
            timeout=int(os.getenv("TIMEOUT", "30")),
            user_agent=os.getenv(
                "USER_AGENT",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ),
        ) 