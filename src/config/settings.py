"""配置管理模块。"""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """应用配置类。"""

    # 应用配置
    APP_ENV: str = Field("development", env="APP_ENV")
    APP_NAME: str = Field("content-crawler", env="APP_NAME")
    APP_VERSION: str = Field("0.1.0", env="APP_VERSION")
    DEBUG: bool = Field(True, env="DEBUG")

    # 服务器配置
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    WORKERS: int = Field(4, env="WORKERS")

    # 数据库配置
    DB_TYPE: str = Field("sqlite", env="DB_TYPE")
    DB_HOST: str = Field("localhost", env="DB_HOST")
    DB_PORT: int = Field(3306, env="DB_PORT")
    DB_NAME: str = Field("content_crawler", env="DB_NAME")
    DB_USER: str = Field("root", env="DB_USER")
    DB_PASSWORD: str = Field("password", env="DB_PASSWORD")

    # Redis配置
    REDIS_HOST: str = Field("localhost", env="REDIS_HOST")
    REDIS_PORT: int = Field(6379, env="REDIS_PORT")
    REDIS_DB: int = Field(0, env="REDIS_DB")
    REDIS_PASSWORD: Optional[str] = Field(None, env="REDIS_PASSWORD")

    # LLM配置
    OPENAI_API_KEY: str = Field("sk-dummy", env="OPENAI_API_KEY")  # 开发环境使用虚拟key
    ANTHROPIC_API_KEY: str = Field("sk-ant-dummy", env="ANTHROPIC_API_KEY")  # 开发环境使用虚拟key
    LLM_PROVIDER: str = Field("openai", env="LLM_PROVIDER")

    # 爬虫配置
    MAX_CONCURRENT_TASKS: int = Field(3, env="MAX_CONCURRENT_TASKS")
    REQUEST_TIMEOUT: int = Field(30, env="REQUEST_TIMEOUT")
    RETRY_TIMES: int = Field(3, env="RETRY_TIMES")
    RETRY_DELAY: int = Field(5, env="RETRY_DELAY")

    # 代理配置
    USE_PROXY: bool = Field(False, env="USE_PROXY")
    PROXY_API_URL: Optional[str] = Field(None, env="PROXY_API_URL")
    PROXY_API_KEY: Optional[str] = Field(None, env="PROXY_API_KEY")

    # 监控配置
    ENABLE_METRICS: bool = Field(True, env="ENABLE_METRICS")
    METRICS_PORT: int = Field(9090, env="METRICS_PORT")

    # 日志配置
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field("json", env="LOG_FORMAT")
    LOG_FILE: str = Field("logs/app.log", env="LOG_FILE")

    # 安全配置
    SECRET_KEY: str = Field("dev-secret-key", env="SECRET_KEY")  # 开发环境使用固定key
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ALLOWED_ORIGINS: List[str] = Field(
        ["http://localhost:3000", "http://localhost:8080"],
        env="ALLOWED_ORIGINS",
    )

    # 存储配置
    STORAGE_TYPE: str = Field("local", env="STORAGE_TYPE")
    STORAGE_PATH: str = Field("storage", env="STORAGE_PATH")
    AWS_ACCESS_KEY_ID: Optional[str] = Field(None, env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = Field(None, env="AWS_SECRET_ACCESS_KEY")
    AWS_REGION: Optional[str] = Field(None, env="AWS_REGION")
    AWS_BUCKET: Optional[str] = Field(None, env="AWS_BUCKET")

    # 告警配置
    ENABLE_ALERTS: bool = Field(True, env="ENABLE_ALERTS")
    ALERT_EMAIL: Optional[str] = Field(None, env="ALERT_EMAIL")
    SMTP_HOST: Optional[str] = Field(None, env="SMTP_HOST")
    SMTP_PORT: Optional[int] = Field(None, env="SMTP_PORT")
    SMTP_USER: Optional[str] = Field(None, env="SMTP_USER")
    SMTP_PASSWORD: Optional[str] = Field(None, env="SMTP_PASSWORD")

    # 新增数据库配置
    SQLITE_URL: str = Field("sqlite:///data/crawler.db", env="SQLITE_URL")
    MONGO_URL: str = Field("mongodb://localhost:27017", env="MONGO_URL")
    MONGO_DB: str = Field("crawler", env="MONGO_DB")
    REDIS_URL: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    MONITOR_INTERVAL: int = Field(60, env="MONITOR_INTERVAL")
    ALERT_LEVELS: List[str] = Field(["INFO", "WARNING", "ERROR"], env="ALERT_LEVELS")
    CRAWL_INTERVAL: int = Field(300, env="CRAWL_INTERVAL")
    MAX_RETRIES: int = Field(3, env="MAX_RETRIES")
    TIMEOUT: int = Field(30, env="TIMEOUT")
    CACHE_TTL: int = Field(3600, env="CACHE_TTL")
    LOG_DIR: Path = Field(Path("logs"), env="LOG_DIR")

    # 项目路径
    BASE_DIR: Path = Field(default=Path(__file__).parent.parent.parent)

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """验证日志级别。"""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of {valid_levels}")
        return v.upper()

    @validator("DB_TYPE")
    def validate_db_type(cls, v: str) -> str:
        """验证数据库类型。"""
        valid_types = ["sqlite", "mysql"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid database type. Must be one of {valid_types}")
        return v.lower()

    @validator("LLM_PROVIDER")
    def validate_llm_provider(cls, v: str) -> str:
        """验证LLM提供商。"""
        valid_providers = ["openai", "anthropic"]
        if v.lower() not in valid_providers:
            raise ValueError(f"Invalid LLM provider. Must be one of {valid_providers}")
        return v.lower()

    @validator("STORAGE_TYPE")
    def validate_storage_type(cls, v: str) -> str:
        """验证存储类型。"""
        valid_types = ["local", "s3"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid storage type. Must be one of {valid_types}")
        return v.lower()

    @validator("LOG_FORMAT")
    def validate_log_format(cls, v: str) -> str:
        """验证日志格式。"""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Invalid log format. Must be one of {valid_formats}")
        return v.lower()

    @validator("ALLOWED_ORIGINS", pre=True)
    def validate_allowed_origins(cls, v: Union[str, List[str]]) -> List[str]:
        """验证允许的源。"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    def __init__(self, **kwargs):
        """初始化配置"""
        super().__init__(**kwargs)
        
        # 设置SQLite URL
        if not self.SQLITE_URL:
            self.SQLITE_URL = f"sqlite:///{self.BASE_DIR}/data/crawler.db"
            
        # 设置日志目录
        self.LOG_DIR = self.BASE_DIR / "logs"
        
        # 创建必要的目录
        self._create_directories()
        
    def _create_directories(self):
        """创建必要的目录"""
        dirs = [
            self.LOG_DIR,
            self.BASE_DIR / "data",
            self.BASE_DIR / "output"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def get_log_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return {
            "handlers": [
                {
                    "sink": self.LOG_DIR / "app.log",
                    "format": self.LOG_FORMAT,
                    "rotation": "1 day",
                    "retention": "7 days",
                    "level": self.LOG_LEVEL
                },
                {
                    "sink": self.LOG_DIR / "error.log",
                    "format": self.LOG_FORMAT,
                    "rotation": "1 day",
                    "retention": "7 days",
                    "level": "ERROR"
                }
            ]
        }

    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置"""
        return {
            'sqlite': {
                'url': self.SQLITE_URL,
                'echo': False
            },
            'mongo': {
                'url': self.MONGO_URL,
                'db': self.MONGO_DB
            },
            'redis': {
                'url': self.REDIS_URL,
                'ttl': self.CACHE_TTL
            }
        }

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # 允许额外的字段
    )


settings = Settings()  # type: ignore 

def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return settings.get_database_config()