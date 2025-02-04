import os
import pytest
import json
from pathlib import Path
from typing import Dict, Any

from src.config import ConfigManager
from src.utils.errors import ConfigError

@pytest.fixture
def config_file(tmp_path) -> Path:
    """创建测试配置文件"""
    config_data = {
        "version": "1.0",
        "formats": {
            "html": {
                "enabled": True,
                "templates": {
                    "article": "templates/html/article.html",
                    "post": "templates/html/post.html",
                    "video": "templates/html/video.html"
                },
                "options": {
                    "minify": True,
                    "image_quality": 85,
                    "video_quality": "high"
                }
            }
        },
        "storage": {
            "local": {
                "enabled": True,
                "path": "exports",
                "max_size": "1GB",
                "cleanup_threshold": "800MB"
            },
            "s3": {
                "enabled": False,
                "bucket": "exports",
                "prefix": "content",
                "max_size": "10GB",
                "cleanup_threshold": "8GB"
            }
        }
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config_data, indent=2))
    return config_path

@pytest.fixture
def env_vars():
    """设置测试环境变量"""
    os.environ["EXPORT_STORAGE_LOCAL_PATH"] = "/custom/path"
    os.environ["EXPORT_FORMATS_HTML_ENABLED"] = "false"
    yield
    del os.environ["EXPORT_STORAGE_LOCAL_PATH"]
    del os.environ["EXPORT_FORMATS_HTML_ENABLED"]

class TestConfigManager:
    """配置管理器测试类"""
    
    def test_load_config_file(self, config_file: Path):
        """测试配置文件加载"""
        config = ConfigManager.load(config_file)
        assert config.version == "1.0"
        assert config.formats["html"]["enabled"] is True
        assert config.storage["local"]["path"] == "exports"

    def test_env_override(self, config_file: Path, env_vars):
        """测试环境变量覆盖"""
        config = ConfigManager.load(config_file)
        assert config.storage["local"]["path"] == "/custom/path"
        assert config.formats["html"]["enabled"] is False

    def test_default_values(self, tmp_path: Path):
        """测试默认值处理"""
        minimal_config = {
            "version": "1.0",
            "formats": {"html": {"enabled": True}},
            "storage": {"local": {"enabled": True}}
        }
        config_path = tmp_path / "minimal_config.json"
        config_path.write_text(json.dumps(minimal_config))
        
        config = ConfigManager.load(config_path)
        assert config.formats["html"]["options"]["image_quality"] == 85
        assert config.storage["local"]["max_size"] == "1GB"

    def test_config_validation(self, tmp_path: Path):
        """测试配置验证"""
        invalid_config = {
            "version": "1.0",
            "formats": {"html": {"enabled": "invalid"}},
            "storage": {"local": {"enabled": True}}
        }
        config_path = tmp_path / "invalid_config.json"
        config_path.write_text(json.dumps(invalid_config))
        
        with pytest.raises(ConfigError):
            ConfigManager.load(config_path)

    def test_missing_required_fields(self, tmp_path: Path):
        """测试缺少必填字段"""
        incomplete_config = {
            "version": "1.0",
            "formats": {}
        }
        config_path = tmp_path / "incomplete_config.json"
        config_path.write_text(json.dumps(incomplete_config))
        
        with pytest.raises(ConfigError):
            ConfigManager.load(config_path)

    def test_invalid_file_path(self):
        """测试无效文件路径"""
        with pytest.raises(ConfigError):
            ConfigManager.load(Path("nonexistent.json"))

    def test_invalid_json(self, tmp_path: Path):
        """测试无效JSON格式"""
        config_path = tmp_path / "invalid.json"
        config_path.write_text("{invalid json")
        
        with pytest.raises(ConfigError):
            ConfigManager.load(config_path)

    def test_config_update(self, config_file: Path):
        """测试配置更新"""
        config = ConfigManager.load(config_file)
        config.update({
            "formats": {
                "html": {
                    "options": {
                        "image_quality": 90
                    }
                }
            }
        })
        assert config.formats["html"]["options"]["image_quality"] == 90

    def test_config_save(self, tmp_path: Path, config_file: Path):
        """测试配置保存"""
        config = ConfigManager.load(config_file)
        save_path = tmp_path / "saved_config.json"
        config.save(save_path)
        
        loaded_config = ConfigManager.load(save_path)
        assert loaded_config.version == config.version
        assert loaded_config.formats == config.formats
        assert loaded_config.storage == config.storage 