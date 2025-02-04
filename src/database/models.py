"""数据库模型模块。"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, func, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class BaseModel(Base):
    """基础模型"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())

class Content(BaseModel):
    """内容模型"""
    __tablename__ = "contents"

    platform = Column(String(50), nullable=False, index=True)
    content_id = Column(String(100), nullable=False, unique=True)
    title = Column(String(500))
    content = Column(Text)
    author = Column(String(100))
    publish_time = Column(DateTime)
    url = Column(String(500))
    meta_data = Column(JSON)

class Tag(BaseModel):
    """标签模型"""
    __tablename__ = "tags"

    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500))

class ContentTag(BaseModel):
    """内容标签关联模型"""
    __tablename__ = "content_tags"

    content_id = Column(Integer, ForeignKey("contents.id"), nullable=False)
    tag_id = Column(Integer, ForeignKey("tags.id"), nullable=False)

class TaskLog(BaseModel):
    """任务日志模型"""
    __tablename__ = "task_logs"

    task_id = Column(String(100), nullable=False, index=True)
    task_type = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)
    message = Column(Text)
    meta_data = Column(JSON)

class BackupRecord(BaseModel):
    """备份记录模型"""
    __tablename__ = "backup_records"

    backup_type = Column(String(50), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    status = Column(String(20), nullable=False)
    message = Column(Text)
    meta_data = Column(JSON)

class MetricRecord(BaseModel):
    """指标记录模型"""
    __tablename__ = "metric_records"

    name = Column(String(100), nullable=False, index=True)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False, default=func.now(), index=True)

class ErrorLog(BaseModel):
    """错误日志模型"""
    __tablename__ = "error_logs"

    error_type = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    traceback = Column(Text)
    meta_data = Column(JSON)

class Config(BaseModel):
    """配置模型"""
    __tablename__ = "configs"

    key = Column(String(100), nullable=False, unique=True)
    value = Column(JSON, nullable=False)
    description = Column(String(500))

class User(BaseModel):
    """用户模型"""
    __tablename__ = "users"

    username = Column(String(100), nullable=False, unique=True)
    password = Column(String(100), nullable=False)
    email = Column(String(100))
    is_active = Column(Integer, default=1)
    last_login = Column(DateTime)

class UserLog(BaseModel):
    """用户日志模型"""
    __tablename__ = "user_logs"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    ip = Column(String(50))
    meta_data = Column(JSON) 