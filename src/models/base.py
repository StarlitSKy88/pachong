from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, scoped_session
from datetime import datetime, UTC
import os
from dotenv import load_dotenv
from typing import Any, Dict
from sqlalchemy.sql import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 加载环境变量
load_dotenv()

# 创建数据库引擎
DB_PARAMS = {
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', '3306')),
    'database': os.getenv('DB_NAME', 'crawler')
}

DB_URL = "postgresql://{user}:{password}@{host}:{port}/{database}".format(**DB_PARAMS)

engine = create_engine(
    DB_URL,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    connect_args={
        'client_encoding': 'utf8',
        'options': '-c search_path=public'
    }
)

# 创建会话工厂
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)

# 创建基类
Base = declarative_base()

class BaseModel:
    """基础模型类"""
    __abstract__ = True

    id = Column(Integer, primary_key=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)
    meta_info = Column(JSON, nullable=True)  # 存储额外的元数据

    def to_dict(self):
        """将模型转换为字典"""
        result = {}
        for c in self.__table__.columns:
            value = getattr(self, c.name)
            if isinstance(value, datetime):
                value = value.isoformat()
            result[c.name] = value
        return result

def init_db():
    """初始化数据库"""
    Base.metadata.create_all(engine)

def get_session():
    """获取数据库会话"""
    return Session()

def cleanup_session():
    """清理数据库会话"""
    Session.remove()

class Base(DeclarativeBase):
    """基础模型类"""
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            字典表示
        """
        return {
            c.name: getattr(self, c.name)
            for c in self.__table__.columns
        }

# 创建基础模型类
Base = declarative_base(cls=BaseModel) 