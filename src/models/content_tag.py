"""内容标签关联模型"""
from sqlalchemy import Table, Column, Integer, ForeignKey
from .base import Base

# 内容-标签关联表
content_tag_table = Table(
    'content_tags',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    extend_existing=True  # 允许重复定义
) 