"""评论数据访问对象模块。"""

from typing import Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from src.database.base_dao import BaseDAO
from src.models.content import Comment, Content
from src.utils.error_handler import DatabaseError, NotFoundError


class CommentDAO(BaseDAO[Comment]):
    """评论数据访问对象。"""

    def __init__(self, session: Session):
        """初始化评论数据访问对象。

        Args:
            session: 数据库会话
        """
        super().__init__(Comment, session)

    async def get_by_content(
        self,
        content_id: int,
        parent_id: Optional[int] = None,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Comment], int]:
        """获取内容的评论列表。

        Args:
            content_id: 内容ID
            parent_id: 父评论ID，如果为None则获取顶级评论
            offset: 偏移量
            limit: 限制数量
            order_by: 排序字段
            order_desc: 是否降序

        Returns:
            评论列表和总数
        """
        try:
            query = self.session.query(Comment).filter(Comment.content_id == content_id)

            if parent_id is None:
                query = query.filter(Comment.parent_id.is_(None))
            else:
                query = query.filter(Comment.parent_id == parent_id)

            # 获取总数
            total = query.count()

            # 排序
            if hasattr(Comment, order_by):
                order_column = getattr(Comment, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(order_column)

            # 分页
            comments = query.offset(offset).limit(limit).all()

            return comments, total
        except Exception as e:
            raise DatabaseError(f"获取评论列表失败: {str(e)}")

    async def get_by_user(
        self,
        user_id: str,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Comment], int]:
        """获取用户的评论列表。

        Args:
            user_id: 用户ID
            offset: 偏移量
            limit: 限制数量
            order_by: 排序字段
            order_desc: 是否降序

        Returns:
            评论列表和总数
        """
        try:
            query = self.session.query(Comment).filter(Comment.user_id == user_id)

            # 获取总数
            total = query.count()

            # 排序
            if hasattr(Comment, order_by):
                order_column = getattr(Comment, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(order_column)

            # 分页
            comments = query.offset(offset).limit(limit).all()

            return comments, total
        except Exception as e:
            raise DatabaseError(f"获取用户评论列表失败: {str(e)}")

    async def get_replies(
        self,
        comment_id: int,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Comment], int]:
        """获取评论的回复列表。

        Args:
            comment_id: 评论ID
            offset: 偏移量
            limit: 限制数量
            order_by: 排序字段
            order_desc: 是否降序

        Returns:
            回复列表和总数
        """
        try:
            query = self.session.query(Comment).filter(Comment.parent_id == comment_id)

            # 获取总数
            total = query.count()

            # 排序
            if hasattr(Comment, order_by):
                order_column = getattr(Comment, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(order_column)

            # 分页
            replies = query.offset(offset).limit(limit).all()

            return replies, total
        except Exception as e:
            raise DatabaseError(f"获取回复列表失败: {str(e)}")

    async def search(
        self,
        keyword: Optional[str] = None,
        content_id: Optional[int] = None,
        user_id: Optional[str] = None,
        parent_id: Optional[int] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        min_likes: Optional[int] = None,
        is_top: Optional[bool] = None,
        status: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> Tuple[List[Comment], int]:
        """搜索评论。

        Args:
            keyword: 关键词
            content_id: 内容ID
            user_id: 用户ID
            parent_id: 父评论ID
            start_time: 开始时间
            end_time: 结束时间
            min_likes: 最小点赞数
            is_top: 是否置顶
            status: 状态
            offset: 偏移量
            limit: 限制数量
            order_by: 排序字段
            order_desc: 是否降序

        Returns:
            评论列表和总数
        """
        try:
            query = self.session.query(Comment)

            # 构建过滤条件
            filters = []
            if keyword:
                filters.append(Comment.content.ilike(f"%{keyword}%"))
            if content_id:
                filters.append(Comment.content_id == content_id)
            if user_id:
                filters.append(Comment.user_id == user_id)
            if parent_id is not None:
                filters.append(Comment.parent_id == parent_id)
            if start_time:
                filters.append(Comment.created_at >= start_time)
            if end_time:
                filters.append(Comment.created_at <= end_time)
            if min_likes is not None:
                filters.append(Comment.likes >= min_likes)
            if is_top is not None:
                filters.append(Comment.is_top == is_top)
            if status:
                filters.append(Comment.status == status)

            if filters:
                query = query.filter(and_(*filters))

            # 获取总数
            total = query.count()

            # 排序
            if hasattr(Comment, order_by):
                order_column = getattr(Comment, order_by)
                if order_desc:
                    query = query.order_by(desc(order_column))
                else:
                    query = query.order_by(order_column)

            # 分页
            comments = query.offset(offset).limit(limit).all()

            return comments, total
        except Exception as e:
            raise DatabaseError(f"搜索评论失败: {str(e)}")

    async def get_stats(
        self,
        content_id: Optional[int] = None,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
    ) -> Dict:
        """获取评论统计信息。

        Args:
            content_id: 内容ID
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            统计信息
        """
        try:
            query = self.session.query(Comment)

            # 构建过滤条件
            if content_id:
                query = query.filter(Comment.content_id == content_id)
            if user_id:
                query = query.filter(Comment.user_id == user_id)
            if start_time:
                query = query.filter(Comment.created_at >= start_time)
            if end_time:
                query = query.filter(Comment.created_at <= end_time)

            # 统计数据
            total = query.count()
            top_count = query.filter(Comment.is_top == True).count()  # noqa
            reply_count = query.filter(Comment.parent_id.isnot(None)).count()
            avg_likes = query.with_entities(func.avg(Comment.likes)).scalar() or 0

            # 状态分布
            status_stats = (
                query.with_entities(Comment.status, func.count(Comment.id))
                .group_by(Comment.status)
                .all()
            )
            status_distribution = {
                status: count for status, count in status_stats
            }

            return {
                "total": total,
                "top_count": top_count,
                "reply_count": reply_count,
                "avg_likes": float(avg_likes),
                "status_distribution": status_distribution,
            }
        except Exception as e:
            raise DatabaseError(f"获取评论统计信息失败: {str(e)}")

    async def update_likes(self, comment_id: int, likes: int) -> Comment:
        """更新评论点赞数。

        Args:
            comment_id: 评论ID
            likes: 点赞数

        Returns:
            更新后的评论对象

        Raises:
            NotFoundError: 评论不存在
            DatabaseError: 数据库操作失败
        """
        try:
            comment = self.session.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise NotFoundError(f"评论不存在: {comment_id}")

            comment.likes = likes
            self.session.commit()
            return comment
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"更新评论点赞数失败: {str(e)}")

    async def update_status(self, comment_id: int, status: str) -> Comment:
        """更新评论状态。

        Args:
            comment_id: 评论ID
            status: 状态

        Returns:
            更新后的评论对象

        Raises:
            NotFoundError: 评论不存在
            DatabaseError: 数据库操作失败
        """
        try:
            comment = self.session.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise NotFoundError(f"评论不存在: {comment_id}")

            comment.status = status
            self.session.commit()
            return comment
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"更新评论状态失败: {str(e)}")

    async def set_top(self, comment_id: int, is_top: bool = True) -> Comment:
        """设置评论置顶状态。

        Args:
            comment_id: 评论ID
            is_top: 是否置顶

        Returns:
            更新后的评论对象

        Raises:
            NotFoundError: 评论不存在
            DatabaseError: 数据库操作失败
        """
        try:
            comment = self.session.query(Comment).filter(Comment.id == comment_id).first()
            if not comment:
                raise NotFoundError(f"评论不存在: {comment_id}")

            comment.is_top = is_top
            self.session.commit()
            return comment
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"设置评论置顶状态失败: {str(e)}")

    async def get_hot_comments(
        self,
        content_id: int,
        limit: int = 10,
        min_likes: Optional[int] = None,
    ) -> List[Comment]:
        """获取热门评论。

        Args:
            content_id: 内容ID
            limit: 返回数量限制
            min_likes: 最小点赞数

        Returns:
            热门评论列表
        """
        try:
            query = (
                self.session.query(Comment)
                .filter(Comment.content_id == content_id)
                .filter(Comment.status == "normal")
            )

            if min_likes is not None:
                query = query.filter(Comment.likes >= min_likes)

            return (
                query.order_by(desc(Comment.likes), desc(Comment.created_at))
                .limit(limit)
                .all()
            )
        except Exception as e:
            raise DatabaseError(f"获取热门评论失败: {str(e)}")

    async def get_comment_stats_by_time(
        self,
        content_id: Optional[int] = None,
        user_id: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        group_by: str = "day",
    ) -> List[Dict]:
        """获取评论时间统计信息。

        Args:
            content_id: 内容ID
            user_id: 用户ID
            start_time: 开始时间
            end_time: 结束时间
            group_by: 分组方式（day/week/month）

        Returns:
            统计信息列表
        """
        try:
            # 构建查询
            query = self.session.query(
                func.date_trunc(group_by, Comment.created_at).label("time_bucket"),
                func.count(Comment.id).label("count"),
            )

            # 添加过滤条件
            if content_id:
                query = query.filter(Comment.content_id == content_id)
            if user_id:
                query = query.filter(Comment.user_id == user_id)
            if start_time:
                query = query.filter(Comment.created_at >= start_time)
            if end_time:
                query = query.filter(Comment.created_at <= end_time)

            # 按时间分组
            stats = (
                query.group_by("time_bucket")
                .order_by("time_bucket")
                .all()
            )

            return [
                {
                    "time": stat.time_bucket.isoformat(),
                    "count": stat.count,
                }
                for stat in stats
            ]
        except Exception as e:
            raise DatabaseError(f"获取评论时间统计信息失败: {str(e)}") 