"""平台模型"""

from sqlalchemy import Column, Integer, String, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from .base import Base

class Platform(Base):
    """平台模型"""
    __tablename__ = 'platforms'

    name = Column(String(50), nullable=False, unique=True)  # 平台名称
    description = Column(Text)  # 平台描述
    base_url = Column(String(200))  # 平台基础URL
    api_base_url = Column(String(200))  # API基础URL
    
    # 配置信息
    crawler_config = Column(JSON)  # 爬虫配置
    api_config = Column(JSON)  # API配置
    cookie_config = Column(JSON)  # Cookie配置
    
    # 状态信息
    is_active = Column(Boolean, default=True)  # 是否启用
    error_count = Column(Integer, default=0)  # 错误计数
    last_error = Column(Text)  # 最后一次错误信息
    
    # 爬虫设置
    crawl_interval = Column(Integer, default=3600)  # 爬取间隔（秒）
    rate_limit = Column(Integer, default=1)  # 请求频率限制（次/秒）
    retry_limit = Column(Integer, default=3)  # 重试次数限制
    
    # 关联关系
    contents = relationship("Content", back_populates="platform")
    
    def __repr__(self):
        return f'<Platform {self.name}>' 