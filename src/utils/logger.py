"""日志管理模块"""

import os
import sys
import json
import logging
import logging.config
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime, UTC
from pythonjsonlogger import jsonlogger
from ..config import Config

class LogFormatter(jsonlogger.JsonFormatter):
    """JSON格式日志格式化器"""
    
    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any]
    ) -> None:
        """添加额外字段
        
        Args:
            log_record: 日志记录
            record: 日志记录对象
            message_dict: 消息字典
        """
        super().add_fields(log_record, record, message_dict)
        
        # 添加时间戳
        log_record["timestamp"] = datetime.now(UTC).isoformat()
        
        # 添加日志级别
        log_record["level"] = record.levelname
        
        # 添加模块信息
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno
        
        # 添加进程和线程信息
        log_record["process"] = record.process
        log_record["process_name"] = record.processName
        log_record["thread"] = record.thread
        log_record["thread_name"] = record.threadName

class LogManager:
    """日志管理器类"""
    
    def __init__(self):
        """初始化日志管理器"""
        self.config = Config()
        self.logs_dir = Path(self.config.get("paths.logs_dir", "data/logs"))
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置默认日志格式
        self.formatter = LogFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
        
        # 设置控制台处理器
        self.console_handler = logging.StreamHandler(sys.stdout)
        self.console_handler.setFormatter(self.formatter)
        
        # 设置默认日志级别
        self.default_level = self.config.get("logging.level", "INFO")
        
    def get_logger(
        self,
        name: str,
        level: Optional[str] = None
    ) -> logging.Logger:
        """获取日志器
        
        Args:
            name: 日志器名称
            level: 日志级别
            
        Returns:
            logging.Logger: 日志器对象
        """
        logger = logging.getLogger(name)
        logger.setLevel(level or self.default_level)
        
        # 如果没有处理器，添加默认处理器
        if not logger.handlers:
            # 添加控制台处理器
            logger.addHandler(self.console_handler)
            
            # 添加文件处理器
            file_handler = logging.FileHandler(
                self.logs_dir / f"{name}.log",
                encoding='utf-8'
            )
            file_handler.setFormatter(self.formatter)
            logger.addHandler(file_handler)
            
            # 如果是错误日志，添加错误文件处理器
            error_handler = logging.FileHandler(
                self.logs_dir / "error.log",
                encoding='utf-8'
            )
            error_handler.setFormatter(self.formatter)
            error_handler.setLevel(logging.ERROR)
            logger.addHandler(error_handler)
        
        return logger

# 创建全局日志管理器实例
_log_manager = LogManager()

def get_logger(name: str, level: Optional[str] = None) -> logging.Logger:
    """获取日志器的全局函数
    
    Args:
        name: 日志器名称
        level: 日志级别
        
    Returns:
        logging.Logger: 日志器对象
    """
    return _log_manager.get_logger(name, level) 