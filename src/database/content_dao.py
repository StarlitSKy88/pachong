from typing import List, Dict, Any, Optional
from datetime import datetime
from sqlalchemy import desc
from .base_dao import BaseDAO
from ..models.content import Content
from ..models.tag import Tag

class ContentDAO(BaseDAO):
    """内容DAO类"""
    
    def __init__(self):
        super().__init__(Content)
    
    def add_with_tags(self, data: Dict[str, Any], tag_names: List[str]) -> Content:
        """添加内容及其标签"""
        with self.get_session() as session:
            # 创建内容
            content = Content(**data)
            session.add(content)
            
            # 处理标签
            for tag_name in tag_names:
                # 获取或创建标签
                tag = session.query(Tag).filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                content.tags.append(tag)
            
            session.commit()
            session.refresh(content)
            return content
    
    def get_latest(self, limit: int = 10) -> List[Content]:
        """获取最新内容"""
        with self.get_session() as session:
            return session.query(Content)\
                .filter_by(status=1)\
                .order_by(desc(Content.publish_time))\
                .limit(limit)\
                .all()
    
    def get_by_platform(self, platform_id: int, page: int = 1, per_page: int = 20) -> List[Content]:
        """获取平台内容"""
        with self.get_session() as session:
            return session.query(Content)\
                .filter_by(platform_id=platform_id, status=1)\
                .order_by(desc(Content.publish_time))\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
    
    def get_by_category(self, category_id: int, page: int = 1, per_page: int = 20) -> List[Content]:
        """获取分类内容"""
        with self.get_session() as session:
            return session.query(Content)\
                .filter_by(category_id=category_id, status=1)\
                .order_by(desc(Content.publish_time))\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
    
    def get_by_tag(self, tag_name: str, page: int = 1, per_page: int = 20) -> List[Content]:
        """获取标签内容"""
        with self.get_session() as session:
            return session.query(Content)\
                .join(Content.tags)\
                .filter(Tag.name == tag_name)\
                .filter(Content.status == 1)\
                .order_by(desc(Content.publish_time))\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
    
    def get_by_date_range(self, start_date: datetime, end_date: datetime, 
                         platform_id: Optional[int] = None,
                         category_id: Optional[int] = None) -> List[Content]:
        """获取日期范围内的内容"""
        with self.get_session() as session:
            query = session.query(Content)\
                .filter(Content.publish_time >= start_date)\
                .filter(Content.publish_time <= end_date)\
                .filter(Content.status == 1)
            
            if platform_id:
                query = query.filter(Content.platform_id == platform_id)
            if category_id:
                query = query.filter(Content.category_id == category_id)
            
            return query.order_by(desc(Content.publish_time)).all()
    
    def search(self, keyword: str, page: int = 1, per_page: int = 20) -> List[Content]:
        """搜索内容"""
        with self.get_session() as session:
            return session.query(Content)\
                .filter(
                    (Content.title.ilike(f'%{keyword}%')) |
                    (Content.content.ilike(f'%{keyword}%')) |
                    (Content.summary.ilike(f'%{keyword}%'))
                )\
                .filter(Content.status == 1)\
                .order_by(desc(Content.publish_time))\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
    
    def get_hot_contents(self, days: int = 7, limit: int = 10) -> List[Content]:
        """获取热门内容"""
        with self.get_session() as session:
            cutoff_date = datetime.now() - datetime.timedelta(days=days)
            return session.query(Content)\
                .filter(Content.publish_time >= cutoff_date)\
                .filter(Content.status == 1)\
                .order_by(desc(Content.likes + Content.comments + Content.shares))\
                .limit(limit)\
                .all() 