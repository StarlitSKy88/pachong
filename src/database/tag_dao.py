from typing import List, Optional, Tuple
from sqlalchemy import func, desc
from .base_dao import BaseDAO
from ..models.tag import Tag
from ..models.content import Content, content_tags

class TagDAO(BaseDAO):
    """标签DAO类"""
    
    def __init__(self):
        super().__init__(Tag)
    
    def get_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签"""
        return self.get_by_field('name', name)
    
    def get_active_tags(self) -> List[Tag]:
        """获取所有启用的标签"""
        with self.get_session() as session:
            return session.query(Tag)\
                .filter_by(status=1)\
                .all()
    
    def enable(self, id: int) -> bool:
        """启用标签"""
        return self.update(id, {'status': 1}) is not None
    
    def disable(self, id: int) -> bool:
        """禁用标签"""
        return self.update(id, {'status': 0}) is not None
    
    def get_hot_tags(self, limit: int = 20) -> List[Tuple[Tag, int]]:
        """获取热门标签及其使用次数"""
        with self.get_session() as session:
            return session.query(Tag, func.count(content_tags.c.content_id).label('count'))\
                .join(content_tags)\
                .join(Content)\
                .filter(Tag.status == 1)\
                .filter(Content.status == 1)\
                .group_by(Tag)\
                .order_by(desc('count'))\
                .limit(limit)\
                .all()
    
    def get_related_tags(self, tag_id: int, limit: int = 10) -> List[Tuple[Tag, int]]:
        """获取相关标签及其关联次数"""
        with self.get_session() as session:
            # 获取与指定标签共同出现的其他标签
            return session.query(Tag, func.count(content_tags.c.content_id).label('count'))\
                .join(content_tags)\
                .join(Content)\
                .filter(Content.id.in_(
                    session.query(content_tags.c.content_id)\
                        .filter(content_tags.c.tag_id == tag_id)
                ))\
                .filter(Tag.id != tag_id)\
                .filter(Tag.status == 1)\
                .filter(Content.status == 1)\
                .group_by(Tag)\
                .order_by(desc('count'))\
                .limit(limit)\
                .all()
    
    def merge_tags(self, source_id: int, target_id: int) -> bool:
        """合并标签"""
        try:
            with self.get_session() as session:
                source_tag = session.query(Tag).get(source_id)
                target_tag = session.query(Tag).get(target_id)
                
                if not source_tag or not target_tag:
                    return False
                
                # 将源标签的内容关联转移到目标标签
                for content in source_tag.contents:
                    if content not in target_tag.contents:
                        target_tag.contents.append(content)
                
                # 删除源标签
                session.delete(source_tag)
                session.commit()
                return True
        except:
            return False 