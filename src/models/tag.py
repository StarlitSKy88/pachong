"""标签模型"""

from sqlalchemy import Column, Integer, String, Text, Float
from sqlalchemy.orm import relationship
from .base import Base
from .content import content_tags

class Tag(Base):
    """标签模型"""
    __tablename__ = 'tags'

    name = Column(String(50), unique=True)  # 标签名称
    description = Column(Text)  # 标签描述
    category = Column(String(50))  # 标签分类
    weight = Column(Float, default=1.0)  # 标签权重
    usage_count = Column(Integer, default=0)  # 使用次数
    
    # 关联关系
    contents = relationship('Content', secondary=content_tags, back_populates='tags')
    
    def __repr__(self):
        return f'<Tag {self.name}>' 