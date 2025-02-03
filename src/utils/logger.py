"""日志配置模块。"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from loguru import logger

from src.config.settings import settings


class InterceptHandler(logging.Handler):
    """将标准库日志重定向到loguru的处理器。"""

    def emit(self, record: logging.LogRecord) -> None:
        """发送日志记录。"""
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


class JsonFormatter:
    """JSON格式化器。"""

    def __call__(self, record: Dict[str, Any]) -> str:
        """格式化日志记录。"""
        subset = {
            "timestamp": record["time"].isoformat(),
            "level": record["level"].name,
            "message": record["message"],
            "module": record["name"],
        }
        if "exception" in record["extra"]:
            subset["exception"] = record["extra"]["exception"]
        return json.dumps(subset)


def setup_logging(
    *,
    level: Union[str, int] = "INFO",
    format_type: str = "json",
    log_file: Optional[Union[str, Path]] = None,
    rotation: str = "500 MB",
    retention: str = "7 days",
    serialize: bool = True,
) -> None:
    """配置日志系统。

    Args:
        level: 日志级别
        format_type: 日志格式类型（json或text）
        log_file: 日志文件路径
        rotation: 日志轮转大小
        retention: 日志保留时间
        serialize: 是否序列化为JSON
    """
    # 移除所有默认处理器
    logger.remove()

    # 配置日志格式
    if format_type == "json":
        log_format = JsonFormatter()
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        )

    # 添加控制台处理器
    logger.add(
        sys.stderr,
        format=log_format,
        level=level,
        serialize=serialize and format_type == "json",
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )

    # 添加文件处理器
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            str(log_path),
            format=log_format,
            level=level,
            rotation=rotation,
            retention=retention,
            serialize=serialize and format_type == "json",
            backtrace=True,
            diagnose=True,
            enqueue=True,
        )

    # 拦截标准库日志
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # 设置第三方库的日志级别
    for name in logging.root.manager.loggerDict:
        logging.getLogger(name).handlers = []
        logging.getLogger(name).propagate = True

    logger.configure(
        handlers=[{"sink": sys.stderr, "format": log_format}],
        extra={"common_to_all": "default"},
    )


def get_logger(name: str) -> "logger":  # type: ignore
    """获取logger实例。

    Args:
        name: 日志记录器名称

    Returns:
        logger实例
    """
    return logger.bind(name=name)


# 初始化日志系统
setup_logging(
    level=settings.LOG_LEVEL,
    format_type=settings.LOG_FORMAT,
    log_file=settings.LOG_FILE,
) 