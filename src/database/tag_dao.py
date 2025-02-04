"""标签数据访问对象模块。"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime

from sqlalchemy import and_, or_, desc
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from pydantic import BaseModel

from ..models import Content, Tag, content_tags
from .base_dao import BaseDAO
from src.utils.error_handler import DatabaseError, NotFoundError


class TagCreate(BaseModel):
    """标签创建模型"""
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: int = 0
    weight: float = 1.0

class TagUpdate(BaseModel):
    """标签更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    level: Optional[int] = None
    weight: Optional[float] = None

class TagDAO(BaseDAO[Tag, TagCreate, TagUpdate]):
    """标签数据访问对象"""

    def __init__(self):
        """初始化标签数据访问对象。"""
        super().__init__(Tag)

    async def get_by_name(self, name: str) -> Optional[Tag]:
        """根据名称获取标签。

        Args:
            name: 标签名称

        Returns:
            标签对象，如果不存在则返回None
        """
        try:
            return self.session.query(Tag).filter(Tag.name == name).first()
        except Exception as e:
            raise DatabaseError(f"获取标签失败: {str(e)}")

    async def get_by_names(self, names: List[str]) -> List[Tag]:
        """根据名称列表获取标签列表。

        Args:
            names: 标签名称列表

        Returns:
            标签列表
        """
        try:
            return self.session.query(Tag).filter(Tag.name.in_(names)).all()
        except Exception as e:
            raise DatabaseError(f"获取标签列表失败: {str(e)}")

    async def get_children(self, parent_id: int) -> List[Tag]:
        """获取子标签列表。

        Args:
            parent_id: 父标签ID

        Returns:
            子标签列表
        """
        try:
            return self.session.query(Tag).filter(Tag.parent_id == parent_id).all()
        except Exception as e:
            raise DatabaseError(f"获取子标签列表失败: {str(e)}")

    async def get_ancestors(self, tag_id: int) -> List[Tag]:
        """获取标签的所有祖先标签。

        Args:
            tag_id: 标签ID

        Returns:
            祖先标签列表
        """
        try:
            ancestors = []
            current_tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
            while current_tag and current_tag.parent_id:
                parent = self.session.query(Tag).filter(Tag.id == current_tag.parent_id).first()
                if parent:
                    ancestors.append(parent)
                    current_tag = parent
                else:
                    break
            return ancestors
        except Exception as e:
            raise DatabaseError(f"获取祖先标签列表失败: {str(e)}")

    async def get_descendants(self, tag_id: int) -> List[Tag]:
        """获取标签的所有后代标签。

        Args:
            tag_id: 标签ID

        Returns:
            后代标签列表
        """
        try:
            descendants = []
            children = await self.get_children(tag_id)
            for child in children:
                descendants.append(child)
                child_descendants = await self.get_descendants(child.id)
                descendants.extend(child_descendants)
            return descendants
        except Exception as e:
            raise DatabaseError(f"获取后代标签列表失败: {str(e)}")

    async def get_related_tags(
        self, tag_id: int, min_correlation: float = 0.1, limit: int = 10
    ) -> List[Tuple[Tag, float]]:
        """获取相关标签。

        Args:
            tag_id: 标签ID
            min_correlation: 最小相关度
            limit: 返回数量限制

        Returns:
            相关标签列表，每个元素为(标签, 相关度)元组
        """
        try:
            # 获取当前标签的内容数量
            tag_content_count = (
                self.session.query(func.count(content_tags.c.content_id))
                .filter(content_tags.c.tag_id == tag_id)
                .scalar()
            )

            if not tag_content_count:
                return []

            # 创建子查询，获取与当前标签共现的标签
            other_tags = aliased(content_tags)
            cooccurrence = (
                self.session.query(
                    other_tags.c.tag_id,
                    func.count(other_tags.c.content_id).label("common_count"),
                )
                .join(
                    content_tags,
                    content_tags.c.content_id == other_tags.c.content_id,
                )
                .filter(content_tags.c.tag_id == tag_id)
                .filter(other_tags.c.tag_id != tag_id)
                .group_by(other_tags.c.tag_id)
                .having(func.count(other_tags.c.content_id) > 0)
                .subquery()
            )

            # 计算相关度并获取标签信息
            related = (
                self.session.query(
                    Tag,
                    (cooccurrence.c.common_count / tag_content_count).label("correlation"),
                )
                .join(cooccurrence, Tag.id == cooccurrence.c.tag_id)
                .filter(
                    (cooccurrence.c.common_count / tag_content_count) >= min_correlation
                )
                .order_by("correlation DESC")
                .limit(limit)
                .all()
            )

            return [(tag, float(correlation)) for tag, correlation in related]
        except Exception as e:
            raise DatabaseError(f"获取相关标签失败: {str(e)}")

    async def search(
        self,
        keyword: Optional[str] = None,
        parent_id: Optional[int] = None,
        level: Optional[int] = None,
        min_weight: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Tag], int]:
        """搜索标签。

        Args:
            keyword: 关键词
            parent_id: 父标签ID
            level: 标签层级
            min_weight: 最小权重
            offset: 偏移量
            limit: 限制数量

        Returns:
            标签列表和总数
        """
        try:
            query = self.session.query(Tag)

            # 构建过滤条件
            filters = []
            if keyword:
                filters.append(
                    Tag.name.ilike(f"%{keyword}%")
                    | Tag.description.ilike(f"%{keyword}%")
                )
            if parent_id is not None:
                filters.append(Tag.parent_id == parent_id)
            if level is not None:
                filters.append(Tag.level == level)
            if min_weight is not None:
                filters.append(Tag.weight >= min_weight)

            if filters:
                query = query.filter(and_(*filters))

            # 获取总数
            total = query.count()

            # 分页
            tags = query.offset(offset).limit(limit).all()

            return tags, total
        except Exception as e:
            raise DatabaseError(f"搜索标签失败: {str(e)}")

    async def get_popular_tags(
        self,
        limit: int = 10,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> List[Tuple[Tag, int]]:
        """获取热门标签。

        Args:
            limit: 返回数量限制
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            热门标签列表，每个元素为(标签, 使用次数)元组
        """
        try:
            # 构建内容过滤条件
            content_filters = []
            if start_time:
                content_filters.append(Content.publish_time >= start_time)
            if end_time:
                content_filters.append(Content.publish_time <= end_time)

            # 获取标签使用次数
            query = (
                self.session.query(
                    Tag,
                    func.count(content_tags.c.content_id).label("usage_count"),
                )
                .join(content_tags)
                .join(Content)
            )

            if content_filters:
                query = query.filter(and_(*content_filters))

            popular_tags = (
                query.group_by(Tag)
                .order_by("usage_count DESC")
                .limit(limit)
                .all()
            )

            return [(tag, int(count)) for tag, count in popular_tags]
        except Exception as e:
            raise DatabaseError(f"获取热门标签失败: {str(e)}")

    async def get_tag_stats(self, tag_id: int) -> Dict:
        """获取标签统计信息。

        Args:
            tag_id: 标签ID

        Returns:
            统计信息

        Raises:
            NotFoundError: 标签不存在
            DatabaseError: 数据库操作失败
        """
        try:
            tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                raise NotFoundError(f"标签不存在: {tag_id}")

            # 获取使用该标签的内容数量
            content_count = (
                self.session.query(func.count(content_tags.c.content_id))
                .filter(content_tags.c.tag_id == tag_id)
                .scalar()
            )

            # 获取子标签数量
            child_count = (
                self.session.query(func.count(Tag.id))
                .filter(Tag.parent_id == tag_id)
                .scalar()
            )

            # 获取平均内容评分
            avg_score = (
                self.session.query(func.avg(Content.score))
                .join(content_tags)
                .filter(content_tags.c.tag_id == tag_id)
                .scalar()
            )

            # 获取平均内容字数
            avg_word_count = (
                self.session.query(func.avg(Content.word_count))
                .join(content_tags)
                        .filter(content_tags.c.tag_id == tag_id)
                .scalar()
            )

            return {
                "content_count": content_count,
                "child_count": child_count,
                "avg_score": float(avg_score) if avg_score else 0.0,
                "avg_word_count": int(avg_word_count) if avg_word_count else 0,
                "level": tag.level,
                "weight": tag.weight,
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取标签统计信息失败: {str(e)}")

    async def update_weight(self, tag_id: int, weight: float) -> Tag:
        """更新标签权重。

        Args:
            tag_id: 标签ID
            weight: 权重值

        Returns:
            更新后的标签对象

        Raises:
            NotFoundError: 标签不存在
            DatabaseError: 数据库操作失败
        """
        try:
            tag = self.session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                raise NotFoundError(f"标签不存在: {tag_id}")

            tag.weight = weight
            self.session.commit()
            return tag
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"更新标签权重失败: {str(e)}")

    async def merge_tags(self, source_id: int, target_id: int) -> Tag:
        """合并标签。

        将source_id标签合并到target_id标签，包括关联的内容和子标签。

        Args:
            source_id: 源标签ID
            target_id: 目标标签ID

        Returns:
            目标标签对象

        Raises:
            NotFoundError: 标签不存在
            DatabaseError: 数据库操作失败
        """
        try:
            source_tag = self.session.query(Tag).filter(Tag.id == source_id).first()
            target_tag = self.session.query(Tag).filter(Tag.id == target_id).first()

            if not source_tag:
                raise NotFoundError(f"源标签不存在: {source_id}")
            if not target_tag:
                raise NotFoundError(f"目标标签不存在: {target_id}")

            # 更新内容关联
            self.session.execute(
                content_tags.update()
                .where(content_tags.c.tag_id == source_id)
                .values(tag_id=target_id)
            )

            # 更新子标签的父标签
            self.session.query(Tag).filter(Tag.parent_id == source_id).update(
                {"parent_id": target_id}
            )
                
                # 删除源标签
            self.session.delete(source_tag)
            self.session.commit()

            return target_tag
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"合并标签失败: {str(e)}")

    async def get_tag_hierarchy(self, root_id: Optional[int] = None) -> List[Dict]:
        """获取标签层级结构。

        Args:
            root_id: 根标签ID，如果为None则获取所有顶级标签

        Returns:
            标签层级结构列表
        """
        try:
            def build_hierarchy(parent_id: Optional[int]) -> List[Dict]:
                tags = (
                    self.session.query(Tag)
                    .filter(Tag.parent_id == parent_id)
                    .all()
                )
                return [
                    {
                        "id": tag.id,
                        "name": tag.name,
                        "description": tag.description,
                        "level": tag.level,
                        "weight": tag.weight,
                        "children": build_hierarchy(tag.id),
                    }
                    for tag in tags
                ]

            return build_hierarchy(root_id)
        except Exception as e:
            raise DatabaseError(f"获取标签层级结构失败: {str(e)}") 