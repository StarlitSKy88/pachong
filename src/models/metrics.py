"""指标模型模块。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

from src.database.session import engine, async_session_factory

Base = declarative_base()

class MetricRecord(Base):
    """指标记录模型"""
    __tablename__ = "metric_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

    def __repr__(self) -> str:
        """字符串表示。

        Returns:
            字符串表示
        """
        return f"<MetricRecord(name={self.name}, value={self.value}, timestamp={self.timestamp})>"

def get_session():
    """获取数据库会话。

    Returns:
        数据库会话
    """
    return async_session_factory() 