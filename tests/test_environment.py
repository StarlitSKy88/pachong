"""环境测试"""

import os
import pytest
import logging
from pathlib import Path

def test_python_version():
    """测试Python版本"""
    import sys
    assert sys.version_info >= (3, 8), "Python版本必须大于等于3.8"

def test_test_data_dir(test_data_dir):
    """测试数据目录"""
    assert test_data_dir.exists(), "测试数据目录不存在"
    assert test_data_dir.is_dir(), "测试数据目录不是目录"

def test_logging(caplog):
    """测试日志配置"""
    with caplog.at_level(logging.INFO):
        logging.info("测试日志")
        assert "测试日志" in caplog.text

def test_db_config(test_db_config):
    """测试数据库配置"""
    assert "url" in test_db_config
    assert "connect_args" in test_db_config
    assert "encoding" in test_db_config
    assert test_db_config["encoding"] == "utf8"

def test_crawler_config(test_crawler_config):
    """测试爬虫配置"""
    assert "concurrent_limit" in test_crawler_config
    assert "retry_limit" in test_crawler_config
    assert "timeout" in test_crawler_config
    assert "proxy" in test_crawler_config
    assert "cookie" in test_crawler_config

def test_monitor_config(test_monitor_config):
    """测试监控配置"""
    assert "metrics" in test_monitor_config
    assert "alert" in test_monitor_config
    assert test_monitor_config["metrics"]["enabled"] is True
    assert test_monitor_config["alert"]["enabled"] is True 