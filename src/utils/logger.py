"""日志配置模块。"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger

LOG_LEVEL = "INFO"
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
    "<level>{message}</level>"
)

class LogFormatter:
    """日志格式化器"""

    def __init__(self, fmt: Optional[str] = None):
        """初始化。

        Args:
            fmt: 格式字符串
        """
        self.fmt = fmt or LOG_FORMAT

    def format(self, record: Dict[str, Any]) -> str:
        """格式化日志记录。

        Args:
            record: 日志记录

        Returns:
            格式化后的字符串
        """
        return self.fmt.format(**record)

class LogManager:
    """日志管理器"""

    def __init__(
        self,
        name: str,
        level: Optional[Union[str, int]] = None,
        fmt: Optional[str] = None,
        log_path: Optional[Union[str, Path]] = None,
        rotation: str = "500 MB",
        retention: str = "7 days",
    ):
        """初始化。

        Args:
            name: 日志名称
            level: 日志级别
            fmt: 格式字符串
            log_path: 日志文件路径
            rotation: 日志轮转大小
            retention: 日志保留时间
        """
        self.name = name
        self.level = level or LOG_LEVEL
        self.formatter = LogFormatter(fmt)
        self.log_path = Path(log_path) if log_path else None
        self.rotation = rotation
        self.retention = retention

        self._setup_logger()

    def _setup_logger(self) -> None:
        """设置日志记录器。"""
        # 移除默认的处理器
        logger.remove()

        # 添加控制台处理器
        logger.add(
            sys.stderr,
            format=self.formatter.fmt,
            level=self.level,
            backtrace=True,
            diagnose=True,
        )

        # 如果指定了日志文件路径，添加文件处理器
        if self.log_path:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            logger.add(
                str(self.log_path),
                format=self.formatter.fmt,
                level=self.level,
                rotation=self.rotation,
                retention=self.retention,
                backtrace=True,
                diagnose=True,
            )

        # 设置日志上下文
        logger.configure(
            extra={
                "name": self.name,
            }
        )

    def get_logger(self) -> "logger":
        """获取日志记录器。

        Returns:
            日志记录器
        """
        return logger.bind(name=self.name)

def setup_logger(
    name: str,
    level: Optional[Union[str, int]] = None,
    rotation: str = "500 MB",
    retention: str = "7 days",
    log_path: Optional[Union[str, Path]] = None,
) -> None:
    """设置日志配置。

    Args:
        name: 日志名称
        level: 日志级别
        rotation: 日志轮转大小
        retention: 日志保留时间
        log_path: 日志文件路径
    """
    # 移除默认的处理器
    logger.remove()

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format=LOG_FORMAT,
        level=level or LOG_LEVEL,
        backtrace=True,
        diagnose=True,
    )

    # 如果指定了日志文件路径，添加文件处理器
    if log_path:
        log_path = Path(log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            format=LOG_FORMAT,
            level=level or LOG_LEVEL,
            rotation=rotation,
            retention=retention,
            backtrace=True,
            diagnose=True,
        )

    # 设置日志上下文
    logger.configure(
        extra={
            "name": name,
        }
    )

def get_logger(name: str) -> "logger":
    """获取日志记录器。

    Args:
        name: 日志名称

    Returns:
        日志记录器
    """
    return logger.bind(name=name) 