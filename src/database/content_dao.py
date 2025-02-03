"""内容数据访问对象模块。"""

from typing import List, Dict, Any, Optional, Tuple, Union
from datetime import datetime
from sqlalchemy import desc, and_, func, or_
from sqlalchemy.orm import Session
from .base_dao import BaseDAO
from ..models.content import Content, ContentStatus, ContentType, Platform, Tag
from ..utils.error_handler import DatabaseError, NotFoundError

class ContentDAO(BaseDAO):
    """内容数据访问对象。"""
    
    def __init__(self, session: Session):
        """初始化内容数据访问对象。

        Args:
            session: 数据库会话
        """
        super().__init__(Content, session)
    
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

    async def get_by_url(self, url: str) -> Optional[Content]:
        """根据URL获取内容。

        Args:
            url: 内容URL

        Returns:
            内容对象，如果不存在则返回None
        """
        try:
            return self.session.query(Content).filter(Content.url == url).first()
        except Exception as e:
            raise DatabaseError(f"获取内容失败: {str(e)}")

    async def get_by_platform(
        self,
        platform_id: int,
        offset: int = 0,
        limit: int = 20,
        content_type: Optional[ContentType] = None,
        status: Optional[ContentStatus] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Tuple[List[Content], int]:
        """获取平台内容列表。

        Args:
            platform_id: 平台ID
            offset: 偏移量
            limit: 限制数量
            content_type: 内容类型
            status: 内容状态
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            内容列表和总数
        """
        try:
            query = self.session.query(Content).filter(Content.platform_id == platform_id)

            if content_type:
                query = query.filter(Content.content_type == content_type)
            if status:
                query = query.filter(Content.status == status)
            if start_time:
                query = query.filter(Content.publish_time >= start_time)
            if end_time:
                query = query.filter(Content.publish_time <= end_time)

            total = query.count()
            contents = (
                query.order_by(desc(Content.publish_time))
                .offset(offset)
                .limit(limit)
                .all()
            )

            return contents, total
        except Exception as e:
            raise DatabaseError(f"获取平台内容列表失败: {str(e)}")

    async def search(
        self,
        keyword: Optional[str] = None,
        platform_id: Optional[int] = None,
        content_type: Optional[ContentType] = None,
        status: Optional[ContentStatus] = None,
        tags: Optional[List[str]] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        is_original: Optional[bool] = None,
        is_premium: Optional[bool] = None,
        min_score: Optional[float] = None,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "publish_time",
        order_desc: bool = True,
    ) -> Tuple[List[Content], int]:
        """搜索内容。

        Args:
            keyword: 关键词
            platform_id: 平台ID
            content_type: 内容类型
            status: 内容状态
            tags: 标签列表
            start_time: 开始时间
            end_time: 结束时间
            is_original: 是否原创
            is_premium: 是否优质内容
            min_score: 最低评分
            offset: 偏移量
            limit: 限制数量
            order_by: 排序字段
            order_desc: 是否降序

        Returns:
            内容列表和总数
        """
        try:
            query = self.session.query(Content)

            # 构建过滤条件
            filters = []
            if keyword:
                filters.append(
                    or_(
                        Content.title.ilike(f"%{keyword}%"),
                        Content.content.ilike(f"%{keyword}%"),
                        Content.summary.ilike(f"%{keyword}%"),
                    )
                )
            if platform_id:
                filters.append(Content.platform_id == platform_id)
            if content_type:
                filters.append(Content.content_type == content_type)
            if status:
                filters.append(Content.status == status)
            if start_time:
                filters.append(Content.publish_time >= start_time)
            if end_time:
                filters.append(Content.publish_time <= end_time)
            if is_original is not None:
                filters.append(Content.is_original == is_original)
            if is_premium is not None:
                filters.append(Content.is_premium == is_premium)
            if min_score is not None:
                filters.append(Content.score >= min_score)

            # 标签过滤
            if tags:
                tag_subquery = (
                    self.session.query(Tag.id).filter(Tag.name.in_(tags)).subquery()
                )
                query = query.join(Content.tags).filter(Tag.id.in_(tag_subquery))

            if filters:
                query = query.filter(and_(*filters))

            # 获取总数
            total = query.count()

            # 排序
            if hasattr(Content, order_by):
                order_column = getattr(Content, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(order_column)

            # 分页
            contents = query.offset(offset).limit(limit).all()

            return contents, total
        except Exception as e:
            raise DatabaseError(f"搜索内容失败: {str(e)}")

    async def get_stats(
        self,
        platform_id: Optional[int] = None,
        content_type: Optional[ContentType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """获取内容统计信息。

        Args:
            platform_id: 平台ID
            content_type: 内容类型
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        try:
            query = self.session.query(Content)

            # 构建过滤条件
            if platform_id:
                query = query.filter(Content.platform_id == platform_id)
            if content_type:
                query = query.filter(Content.content_type == content_type)
            if start_time:
                query = query.filter(Content.publish_time >= start_time)
            if end_time:
                query = query.filter(Content.publish_time <= end_time)

            # 统计数据
            total = query.count()
            original_count = query.filter(Content.is_original == True).count()  # noqa
            premium_count = query.filter(Content.is_premium == True).count()  # noqa
            avg_score = (
                query.with_entities(func.avg(Content.score)).scalar() or 0
            )
            avg_word_count = (
                query.with_entities(func.avg(Content.word_count)).scalar() or 0
            )

            # 按内容类型统计
            type_stats = (
                query.with_entities(
                    Content.content_type, func.count(Content.id)
                )
                .group_by(Content.content_type)
                .all()
            )
            type_distribution = {
                content_type: count for content_type, count in type_stats
            }

            # 按状态统计
            status_stats = (
                query.with_entities(Content.status, func.count(Content.id))
                .group_by(Content.status)
                .all()
            )
            status_distribution = {
                status: count for status, count in status_stats
            }

            return {
                "total": total,
                "original_count": original_count,
                "premium_count": premium_count,
                "avg_score": float(avg_score),
                "avg_word_count": int(avg_word_count),
                "type_distribution": type_distribution,
                "status_distribution": status_distribution,
            }
        except Exception as e:
            raise DatabaseError(f"获取内容统计信息失败: {str(e)}")

    async def update_stats(self, content_id: int, stats: Dict[str, Any]) -> Content:
        """更新内容统计信息。

        Args:
            content_id: 内容ID
            stats: 统计信息

        Returns:
            更新后的内容对象

        Raises:
            NotFoundError: 内容不存在
            DatabaseError: 数据库操作失败
        """
        try:
            content = self.session.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise NotFoundError(f"内容不存在: {content_id}")

            content.stats = stats
            self.session.commit()
            return content
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"更新内容统计信息失败: {str(e)}")

    async def update_quality(
        self, content_id: int, score: float, quality_check: Dict[str, Any]
    ) -> Content:
        """更新内容质量信息。

        Args:
            content_id: 内容ID
            score: 评分
            quality_check: 质量检查结果

        Returns:
            更新后的内容对象

        Raises:
            NotFoundError: 内容不存在
            DatabaseError: 数据库操作失败
        """
        try:
            content = self.session.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise NotFoundError(f"内容不存在: {content_id}")

            content.score = score
            content.quality_check = quality_check
            self.session.commit()
            return content
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"更新内容质量信息失败: {str(e)}")

    async def add_tags(self, content_id: int, tag_names: List[str]) -> Content:
        """添加内容标签。

        Args:
            content_id: 内容ID
            tag_names: 标签名称列表

        Returns:
            更新后的内容对象

        Raises:
            NotFoundError: 内容不存在
            DatabaseError: 数据库操作失败
        """
        try:
            content = self.session.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise NotFoundError(f"内容不存在: {content_id}")

            # 获取或创建标签
            tags = []
            for name in tag_names:
                tag = self.session.query(Tag).filter(Tag.name == name).first()
                if not tag:
                    tag = Tag(name=name)
                    self.session.add(tag)
                tags.append(tag)

            # 添加标签
            content.tags.extend(tags)
            self.session.commit()
            return content
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"添加内容标签失败: {str(e)}")

    async def remove_tags(self, content_id: int, tag_names: List[str]) -> Content:
        """移除内容标签。

        Args:
            content_id: 内容ID
            tag_names: 标签名称列表

        Returns:
            更新后的内容对象

        Raises:
            NotFoundError: 内容不存在
            DatabaseError: 数据库操作失败
        """
        try:
            content = self.session.query(Content).filter(Content.id == content_id).first()
            if not content:
                raise NotFoundError(f"内容不存在: {content_id}")

            # 获取要移除的标签
            tags = self.session.query(Tag).filter(Tag.name.in_(tag_names)).all()
            for tag in tags:
                content.tags.remove(tag)

            self.session.commit()
            return content
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"移除内容标签失败: {str(e)}") 