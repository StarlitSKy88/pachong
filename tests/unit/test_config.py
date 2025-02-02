"""配置模块测试"""

import pytest
import json
import os
from pathlib import Path
from src.config import Config

@pytest.fixture
def temp_config_dir(tmp_path):
    """创建临时配置目录"""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    return config_dir

@pytest.fixture
def config(temp_config_dir):
    """创建配置实例"""
    Config.set_config_dir(temp_config_dir)
    Config._instance = None  # 重置单例
    return Config()

def test_config_initialization(config, temp_config_dir):
    """测试配置初始化"""
    # 验证配置文件是否创建
    config_file = temp_config_dir / "config.json"
    assert config_file.exists()
    
    # 验证配置内容
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    
    # 验证默认配置
    assert config_data["image"]["width"] == 390
    assert config_data["image"]["max_height"] == 1200
    assert config_data["video"]["fps"] == 24
    assert config_data["theme"]["current"] == "default"
    assert "output" in config_data["paths"]

def test_config_get(config):
    """测试获取配置"""
    # 测试获取存在的配置
    assert config.get("image.width") == 390
    assert config.get("video.fps") == 24
    assert config.get("theme.current") == "default"
    
    # 测试获取不存在的配置
    assert config.get("not.exists") is None
    assert config.get("not.exists", "default") == "default"
    
    # 测试获取嵌套配置
    watermark = config.get("image.watermark")
    assert isinstance(watermark, dict)
    assert watermark["text"] == "关注我，了解更多精彩内容"
    assert watermark["font_size"] == 20

def test_config_set(config, temp_config_dir):
    """测试设置配置"""
    # 测试设置已存在的配置
    config.set("image.width", 800)
    assert config.get("image.width") == 800
    
    # 测试设置新配置
    config.set("custom.key", "value")
    assert config.get("custom.key") == "value"
    
    # 测试设置嵌套配置
    config.set("custom.nested.key", "value")
    assert config.get("custom.nested.key") == "value"
    
    # 验证配置文件是否更新
    config_file = temp_config_dir / "config.json"
    with open(config_file, 'r', encoding='utf-8') as f:
        config_data = json.load(f)
    assert config_data["image"]["width"] == 800
    assert config_data["custom"]["key"] == "value"
    assert config_data["custom"]["nested"]["key"] == "value"

def test_config_file_handling(temp_config_dir):
    """测试配置文件处理"""
    # 测试配置文件不存在时的处理
    Config.set_config_dir(temp_config_dir)
    Config._instance = None
    config = Config()
    config_file = temp_config_dir / "config.json"
    assert config_file.exists()
    
    # 测试配置文件损坏时的处理
    with open(config_file, 'w', encoding='utf-8') as f:
        f.write("invalid json")
    
    Config._instance = None
    with pytest.raises(json.JSONDecodeError):
        config = Config()

def test_config_error_handling(config):
    """测试错误处理"""
    # 测试设置无效类型
    with pytest.raises(TypeError):
        config.set("key", object())
    
    # 测试获取无效路径
    assert config.get("") is None
    assert config.get(".") is None
    assert config.get("..") is None
    
    # 测试设置无效路径
    with pytest.raises(ValueError):
        config.set("", "value")
    with pytest.raises(ValueError):
        config.set(".", "value")
    with pytest.raises(ValueError):
        config.set("..", "value")

def test_config_type_validation(config):
    """测试类型验证"""
    # 测试设置不同类型的值
    test_values = [
        ("string.value", "test"),
        ("int.value", 123),
        ("float.value", 3.14),
        ("bool.value", True),
        ("list.value", [1, 2, 3]),
        ("dict.value", {"key": "value"}),
        ("none.value", None)
    ]
    
    for key, value in test_values:
        config.set(key, value)
        assert config.get(key) == value
        
    # 验证类型保持不变
    for key, value in test_values:
        assert isinstance(config.get(key), type(value) if value is not None else type(None))

def test_config_persistence(temp_config_dir):
    """测试配置持久化"""
    # 创建并修改配置
    Config.set_config_dir(temp_config_dir)
    Config._instance = None
    config1 = Config()
    config1.set("test.key", "value")
    
    # 创建新的配置实例
    config2 = Config()
    assert config2.get("test.key") == "value"
    
    # 修改第二个实例
    config2.set("test.key2", "value2")
    
    # 验证第一个实例是否看到更改
    assert config1.get("test.key2") == "value2"

def test_config_environment_override(config, monkeypatch):
    """测试环境变量覆盖"""
    # 设置环境变量
    monkeypatch.setenv("APP_IMAGE_WIDTH", "1000")
    monkeypatch.setenv("APP_CUSTOM_KEY", "env_value")
    
    # 重新加载配置
    config.reload()
    
    # 验证环境变量是否覆盖配置
    assert config.get("image.width") == 1000
    assert config.get("custom.key") == "env_value" 