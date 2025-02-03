"""测试配置模块。"""

from pathlib import Path
from typing import Dict, Any

from src.config.settings import Settings

class TestSettings(Settings):
    """测试配置类。"""
    
    class Config:
        env_file = ".env.test"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"  # 允许额外的字段

    def __init__(self, **kwargs):
        """初始化测试配置"""
        # 设置测试环境的默认值
        test_values = {
            "APP_ENV": "test",
            "DEBUG": True,
            "OPENAI_API_KEY": "sk-test",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "SECRET_KEY": "test-secret-key",
            "SQLITE_URL": "sqlite:///:memory:",
            "MONGO_URL": "mongodb://localhost:27017",
            "MONGO_DB": "test_crawler",
            "REDIS_URL": "redis://localhost:6379/1",
            "MONITOR_INTERVAL": 1,
            "ALERT_LEVELS": ["INFO", "WARNING", "ERROR"],
            "CRAWL_INTERVAL": 1,
            "MAX_RETRIES": 1,
            "TIMEOUT": 1,
            "CACHE_TTL": 1,
            "LOG_DIR": Path("tests/logs"),
            "BASE_DIR": Path(__file__).parent
        }
        
        # 更新配置
        kwargs.update(test_values)
        super().__init__(**kwargs)
        
        # 创建测试目录
        self._create_test_directories()
    
    def _create_test_directories(self):
        """创建测试目录"""
        dirs = [
            self.LOG_DIR,
            self.BASE_DIR / "data",
            self.BASE_DIR / "output"
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)
    
    def get_test_database_config(self) -> Dict[str, Any]:
        """获取测试数据库配置"""
        return {
            'sqlite': {
                'url': 'sqlite:///:memory:',
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

test_settings = TestSettings() 