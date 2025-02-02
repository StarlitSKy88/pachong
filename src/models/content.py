"""内容模型"""

from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import Table, Column, Integer, String, ForeignKey, DateTime, JSON, Text
from sqlalchemy.orm import relationship
from .base import Base
from .report import report_contents
from .content_tag import content_tag_table

# 内容-标签关联表
content_tags = Table(
    'content_tags',
    Base.metadata,
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    extend_existing=True
)

class Content(Base):
    """内容模型"""
    
    __tablename__ = 'contents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # 主键ID
    title = Column(String(255), nullable=False)  # 标题
    content = Column(Text, nullable=False)  # 内容
    author_name = Column(String(255), nullable=False)  # 作者名称
    author_id = Column(String(255), nullable=False)  # 作者ID
    platform_id = Column(Integer, ForeignKey('platforms.id'), nullable=True)  # 平台ID
    url = Column(String(1024), nullable=False)  # 内容URL
    images = Column(JSON, nullable=True)  # 图片列表
    video = Column(JSON, nullable=True)  # 视频信息
    publish_time = Column(DateTime, nullable=False)  # 发布时间
    likes = Column(Integer, default=0)  # 点赞数
    comments = Column(Integer, default=0)  # 评论数
    collects = Column(Integer, default=0)  # 收藏数
    shares = Column(Integer, default=0)  # 分享数
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间
    
    # 平台信息
    platform = relationship('Platform', back_populates='contents')
    
    # 分类信息
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship('Category', back_populates='contents')
    
    # 媒体信息
    cover = Column(String(500))  # 封面图
    
    # 统计信息
    views = Column(Integer, default=0)  # 浏览量
    coins = Column(Integer, default=0)  # 投币数
    
    # 状态信息
    status = Column(Integer, default=1)  # 状态：1-正常，0-删除
    
    # 关联标签
    tags = relationship('Tag', secondary=content_tag_table, back_populates='contents')
    
    # 关联生成内容
    generated_contents = relationship('GeneratedContent', back_populates='source_content', lazy='dynamic')
    
    # 关联报告
    reports = relationship('Report', secondary='report_contents', back_populates='contents')
    
    def __init__(
        self,
        title: str,
        content: str,
        author_name: str,
        author_id: str,
        url: str,
        images: List[str],
        video: Optional[Dict[str, str]],
        publish_time: datetime,
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        collects: int = 0
    ):
        """初始化内容模型

        Args:
            title: 标题
            content: 内容
            author_name: 作者名称
            author_id: 作者ID
            url: 内容URL
            images: 图片列表
            video: 视频信息
            publish_time: 发布时间
            likes: 点赞数
            comments: 评论数
            shares: 分享数
            collects: 收藏数
        """
        self.title = title
        self.content = content
        self.author_name = author_name
        self.author_id = author_id
        self.url = url
        self.images = images
        self.video = video
        self.publish_time = publish_time
        self.likes = likes
        self.comments = comments
        self.shares = shares
        self.collects = collects

    def __repr__(self) -> str:
        """字符串表示

        Returns:
            字符串表示
        """
        return f"<Content {self.title}>"

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典

        Returns:
            字典表示
        """
        return {
            "title": self.title,
            "content": self.content,
            "author_name": self.author_name,
            "author_id": self.author_id,
            "url": self.url,
            "images": self.images,
            "video": self.video,
            "publish_time": self.publish_time.isoformat(),
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "collects": self.collects
        } 