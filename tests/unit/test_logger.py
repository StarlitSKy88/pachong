"""日志模块测试"""

import pytest
import json
import logging
import os
from pathlib import Path
from datetime import datetime
from src.utils.logger import LogFormatter, LogManager, get_logger

@pytest.fixture
def temp_log_dir(tmp_path):
    """创建临时日志目录"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

@pytest.fixture
def log_manager(temp_log_dir):
    """创建日志管理器"""
    return LogManager(
        name="test",
        level="DEBUG",
        log_dir=str(temp_log_dir),
        console=True,
        json_format=True
    )

def test_log_formatter():
    """测试日志格式化器"""
    formatter = LogFormatter(fmt="%(timestamp)s %(level)s %(name)s %(message)s")
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg="test message",
        args=(),
        exc_info=None
    )
    
    log_entry = json.loads(formatter.format(record))
    assert "timestamp" in log_entry
    assert log_entry["level"] == "INFO"
    assert log_entry["module"] == "test"
    assert "process" in log_entry
    assert "thread" in log_entry

def test_log_manager_initialization(temp_log_dir):
    """测试日志管理器初始化"""
    manager = LogManager(
        name="test",
        level="INFO",
        log_dir=str(temp_log_dir)
    )
    
    # 验证日志目录创建
    assert temp_log_dir.exists()
    
    # 验证日志文件创建
    assert (temp_log_dir / "test.log").exists()
    assert (temp_log_dir / "test_error.log").exists()
    
    # 验证日志器配置
    logger = manager.get_logger()
    assert logger.name == "test"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 3  # 文件、错误、控制台

def test_log_levels(log_manager):
    """测试日志级别"""
    logger = log_manager.get_logger()
    
    # 测试不同级别的日志
    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # 验证日志文件内容
    log_file = log_manager.log_dir / "test.log"
    with open(log_file, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f]
    
    assert len(logs) == 5
    assert logs[0]["level"] == "DEBUG"
    assert logs[1]["level"] == "INFO"
    assert logs[2]["level"] == "WARNING"
    assert logs[3]["level"] == "ERROR"
    assert logs[4]["level"] == "CRITICAL"

def test_error_log_file(log_manager):
    """测试错误日志文件"""
    logger = log_manager.get_logger()
    
    # 记录不同级别的日志
    logger.info("Info message")
    logger.error("Error message")
    logger.critical("Critical message")
    
    # 验证错误日志文件只包含错误和严重级别的日志
    error_file = log_manager.log_dir / "test_error.log"
    with open(error_file, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f]
    
    assert len(logs) == 2
    assert logs[0]["level"] == "ERROR"
    assert logs[1]["level"] == "CRITICAL"

def test_log_format_options(temp_log_dir):
    """测试日志格式选项"""
    # 测试JSON格式
    json_manager = LogManager(
        name="json_test",
        log_dir=str(temp_log_dir),
        json_format=True
    )
    json_manager.get_logger().info("JSON message")
    
    # 测试普通格式
    text_manager = LogManager(
        name="text_test",
        log_dir=str(temp_log_dir),
        json_format=False
    )
    text_manager.get_logger().info("Text message")
    
    # 验证JSON格式日志
    with open(temp_log_dir / "json_test.log", "r", encoding="utf-8") as f:
        json_log = f.readline()
        assert json.loads(json_log)  # 确保是有效的JSON
    
    # 验证普通格式日志
    with open(temp_log_dir / "text_test.log", "r", encoding="utf-8") as f:
        text_log = f.readline()
        assert "[INFO]" in text_log
        assert "Text message" in text_log

def test_add_remove_handlers(log_manager):
    """测试添加和移除处理器"""
    logger = log_manager.get_logger()
    initial_handlers = len(logger.handlers)
    
    # 添加新的文件处理器
    log_manager.add_file_handler("custom.log", "DEBUG")
    assert len(logger.handlers) == initial_handlers + 1
    
    # 移除所有处理器
    log_manager.clear_handlers()
    assert len(logger.handlers) == 0
    
    # 添加新的处理器
    log_manager.add_file_handler("test.log", "INFO")
    assert len(logger.handlers) == 1
    
    # 移除特定类型的处理器
    log_manager.remove_handler(logging.FileHandler)
    assert len(logger.handlers) == 0

def test_log_config_file(temp_log_dir):
    """测试日志配置文件"""
    # 创建配置文件
    config = {
        "version": 1,
        "formatters": {
            "simple": {
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout"
            }
        },
        "loggers": {
            "test": {
                "level": "INFO",
                "handlers": ["console"]
            }
        }
    }
    
    config_file = temp_log_dir / "logging.json"
    with open(config_file, "w", encoding="utf-8") as f:
        json.dump(config, f)
    
    # 加载配置
    LogManager.load_config(str(config_file))
    
    # 验证配置是否生效
    logger = logging.getLogger("test")
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)

def test_get_logger_function():
    """测试全局获取日志器函数"""
    # 测试默认日志器
    logger1 = get_logger()
    assert logger1.name == "crawler"
    
    # 测试带名称的日志器
    logger2 = get_logger("test")
    assert logger2.name == "crawler.test"
    
    # 验证是否是同一个日志器实例
    logger3 = get_logger("test")
    assert logger2 is logger3

def test_log_content_validation(log_manager):
    """测试日志内容验证"""
    logger = log_manager.get_logger()
    test_msg = "Test message with special chars: !@#$%^&*()"
    logger.info(test_msg)
    
    # 验证日志文件内容
    log_file = log_manager.log_dir / "test.log"
    with open(log_file, "r", encoding="utf-8") as f:
        log_entry = json.loads(f.readline())
        assert log_entry["message"] == test_msg
        assert "timestamp" in log_entry
        assert "module" in log_entry
        assert "function" in log_entry
        assert "line" in log_entry
        assert "process" in log_entry
        assert "thread" in log_entry

def test_concurrent_logging(log_manager):
    """测试并发日志记录"""
    import threading
    
    def log_messages():
        logger = log_manager.get_logger()
        for i in range(100):
            logger.info(f"Message from thread {threading.current_thread().name}: {i}")
    
    # 创建多个线程同时写日志
    threads = [
        threading.Thread(target=log_messages)
        for _ in range(5)
    ]
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
    # 验证所有日志是否都被正确记录
    log_file = log_manager.log_dir / "test.log"
    with open(log_file, "r", encoding="utf-8") as f:
        logs = [json.loads(line) for line in f]
        assert len(logs) == 500  # 5个线程 * 100条消息

def test_log_rotation(temp_log_dir):
    """测试日志轮转"""
    from logging.handlers import RotatingFileHandler
    
    # 创建带轮转的日志管理器
    manager = LogManager(
        name="rotation_test",
        log_dir=str(temp_log_dir)
    )
    
    # 添加轮转处理器
    handler = RotatingFileHandler(
        temp_log_dir / "rotation.log",
        maxBytes=1024,  # 1KB
        backupCount=3
    )
    handler.setFormatter(LogFormatter())
    manager.get_logger().addHandler(handler)
    
    # 写入足够多的日志触发轮转
    logger = manager.get_logger()
    for i in range(1000):
        logger.info("A" * 100)  # 每条日志大约100字节
    
    # 验证是否创建了轮转文件
    assert (temp_log_dir / "rotation.log").exists()
    assert (temp_log_dir / "rotation.log.1").exists()
    assert (temp_log_dir / "rotation.log.2").exists()
    assert (temp_log_dir / "rotation.log.3").exists()

def test_error_handling(log_manager):
    """测试错误处理"""
    logger = log_manager.get_logger()
    
    try:
        raise ValueError("Test error")
    except Exception:
        logger.exception("An error occurred")
    
    # 验证错误日志
    error_file = log_manager.log_dir / "test_error.log"
    with open(error_file, "r", encoding="utf-8") as f:
        log_entry = json.loads(f.readline())
        assert log_entry["level"] == "ERROR"
        assert "An error occurred" in log_entry["message"]
        assert "Traceback" in log_entry["exc_info"]
        assert "ValueError: Test error" in log_entry["exc_info"] 