"""数据库基础模块。"""

from datetime import datetime
from typing import Any, Dict, Optional, TypeVar

from sqlalchemy import create_engine, Column, Integer, DateTime
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import func

from src.config.settings import settings
from src.utils.logger import get_logger
from src.models import Base

logger = get_logger(__name__)

# 类型变量
ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType")
UpdateSchemaType = TypeVar("UpdateSchemaType")

# 元数据对象
metadata = Base.metadata


class CustomBase:
    """自定义基类，为所有模型提供通用功能。"""

    @declared_attr
    def __tablename__(cls) -> str:
        """获取表名。

        Returns:
            str: 表名
        """
        return cls.__name__.lower()

    # 通用字段
    id: Any
    created_at: datetime
    updated_at: datetime

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典。

        Returns:
            Dict[str, Any]: 字典形式的数据
        """
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }

    def __repr__(self) -> str:
        """字符串表示"""
        values = ", ".join(
            f"{column.name}={getattr(self, column.name)!r}"
            for column in self.__table__.columns
        )
        return f"{self.__class__.__name__}({values})"


# 创建基类
Base = declarative_base(cls=CustomBase, metadata=metadata)


class Database:
    """数据库管理类。"""

    def __init__(self) -> None:
        """初始化数据库管理器。"""
        self._engine = None
        self._session_factory = None
        self._init_engine()
        self._init_session_factory()

    def _get_database_url(self) -> str:
        """获取数据库URL。

        Returns:
            str: 数据库URL
        """
        if settings.DB_TYPE == "sqlite":
            return f"sqlite:///{settings.DB_NAME}.db"
        elif settings.DB_TYPE == "mysql":
            return (
                f"mysql+pymysql://{settings.DB_USER}:{settings.DB_PASSWORD}"
                f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            )
        else:
            raise ValueError(f"Unsupported database type: {settings.DB_TYPE}")

    def _init_engine(self) -> None:
        """初始化数据库引擎。"""
        database_url = self._get_database_url()
        try:
            self._engine = create_engine(
                database_url,
                echo=settings.DEBUG,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
                pool_recycle=1800,
                poolclass=QueuePool,
            )
            logger.info(f"Database engine initialized: {settings.DB_TYPE}")
        except Exception as e:
            logger.error(f"Failed to initialize database engine: {e}")
            raise

    def _init_session_factory(self) -> None:
        """初始化会话工厂。"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        try:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine,
            )
            logger.info("Database session factory initialized")
        except Exception as e:
            logger.error(f"Failed to initialize session factory: {e}")
            raise

    def create_database(self) -> None:
        """创建数据库表。"""
        if not self._engine:
            raise RuntimeError("Database engine not initialized")
        try:
            Base.metadata.create_all(bind=self._engine)
            logger.info("Database tables created")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise

    def get_session(self) -> Session:
        """获取数据库会话。

        Returns:
            Session: 数据库会话
        """
        if not self._session_factory:
            raise RuntimeError("Session factory not initialized")
        return self._session_factory()

    def close(self) -> None:
        """关闭数据库连接。"""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connection closed")


# 全局数据库实例
db = Database()


def get_db() -> Session:
    """获取数据库会话。

    Returns:
        Session: 数据库会话

    Yields:
        Iterator[Session]: 数据库会话
    """
    session = db.get_session()
    try:
        yield session
    finally:
        session.close() 