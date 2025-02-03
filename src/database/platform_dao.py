"""平台数据访问对象模块。"""

from typing import Dict, List, Optional, Tuple

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.database.base_dao import BaseDAO
from src.models.content import Content, Platform
from src.utils.error_handler import DatabaseError, NotFoundError


class PlatformDAO(BaseDAO[Platform]):
    """平台数据访问对象。"""

    def __init__(self, session: Session):
        """初始化平台数据访问对象。

        Args:
            session: 数据库会话
        """
        super().__init__(Platform, session)

    async def get_by_name(self, name: str) -> Optional[Platform]:
        """根据名称获取平台。

        Args:
            name: 平台名称

        Returns:
            平台对象，如果不存在则返回None
        """
        try:
            return self.session.query(Platform).filter(Platform.name == name).first()
        except Exception as e:
            raise DatabaseError(f"获取平台失败: {str(e)}")

    async def get_enabled(self) -> List[Platform]:
        """获取所有启用的平台。

        Returns:
            平台列表
        """
        try:
            return self.session.query(Platform).filter(Platform.enabled == True).all()  # noqa
        except Exception as e:
            raise DatabaseError(f"获取启用平台列表失败: {str(e)}")

    async def enable(self, platform_id: int) -> Platform:
        """启用平台。

        Args:
            platform_id: 平台ID

        Returns:
            更新后的平台对象

        Raises:
            NotFoundError: 平台不存在
            DatabaseError: 数据库操作失败
        """
        try:
            platform = self.session.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise NotFoundError(f"平台不存在: {platform_id}")

            platform.enabled = True
            self.session.commit()
            return platform
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"启用平台失败: {str(e)}")

    async def disable(self, platform_id: int) -> Platform:
        """禁用平台。

        Args:
            platform_id: 平台ID

        Returns:
            更新后的平台对象

        Raises:
            NotFoundError: 平台不存在
            DatabaseError: 数据库操作失败
        """
        try:
            platform = self.session.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise NotFoundError(f"平台不存在: {platform_id}")

            platform.enabled = False
            self.session.commit()
            return platform
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"禁用平台失败: {str(e)}")

    async def update_config(self, platform_id: int, config: Dict) -> Platform:
        """更新平台配置。

        Args:
            platform_id: 平台ID
            config: 配置信息

        Returns:
            更新后的平台对象

        Raises:
            NotFoundError: 平台不存在
            DatabaseError: 数据库操作失败
        """
        try:
            platform = self.session.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise NotFoundError(f"平台不存在: {platform_id}")

            platform.config = config
            self.session.commit()
            return platform
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"更新平台配置失败: {str(e)}")

    async def get_stats(self, platform_id: int) -> Dict:
        """获取平台统计信息。

        Args:
            platform_id: 平台ID

        Returns:
            统计信息

        Raises:
            NotFoundError: 平台不存在
            DatabaseError: 数据库操作失败
        """
        try:
            platform = self.session.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise NotFoundError(f"平台不存在: {platform_id}")

            # 获取内容总数
            total_content = (
                self.session.query(func.count(Content.id))
                .filter(Content.platform_id == platform_id)
                .scalar()
            )

            # 获取原创内容数
            original_content = (
                self.session.query(func.count(Content.id))
                .filter(Content.platform_id == platform_id)
                .filter(Content.is_original == True)  # noqa
                .scalar()
            )

            # 获取优质内容数
            premium_content = (
                self.session.query(func.count(Content.id))
                .filter(Content.platform_id == platform_id)
                .filter(Content.is_premium == True)  # noqa
                .scalar()
            )

            # 获取平均评分
            avg_score = (
                self.session.query(func.avg(Content.score))
                .filter(Content.platform_id == platform_id)
                .scalar()
            )

            # 获取平均字数
            avg_word_count = (
                self.session.query(func.avg(Content.word_count))
                .filter(Content.platform_id == platform_id)
                .scalar()
            )

            return {
                "total_content": total_content,
                "original_content": original_content,
                "premium_content": premium_content,
                "avg_score": float(avg_score) if avg_score else 0.0,
                "avg_word_count": int(avg_word_count) if avg_word_count else 0,
            }
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取平台统计信息失败: {str(e)}")

    async def search(
        self,
        keyword: Optional[str] = None,
        enabled: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Platform], int]:
        """搜索平台。

        Args:
            keyword: 关键词
            enabled: 是否启用
            offset: 偏移量
            limit: 限制数量

        Returns:
            平台列表和总数
        """
        try:
            query = self.session.query(Platform)

            if keyword:
                query = query.filter(
                    Platform.name.ilike(f"%{keyword}%")
                    | Platform.description.ilike(f"%{keyword}%")
                )
            if enabled is not None:
                query = query.filter(Platform.enabled == enabled)

            total = query.count()
            platforms = query.offset(offset).limit(limit).all()

            return platforms, total
        except Exception as e:
            raise DatabaseError(f"搜索平台失败: {str(e)}")

    async def get_content_stats_by_time(
        self,
        platform_id: int,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        group_by: str = "day",
    ) -> List[Dict]:
        """获取平台内容时间统计信息。

        Args:
            platform_id: 平台ID
            start_time: 开始时间
            end_time: 结束时间
            group_by: 分组方式（day/week/month）

        Returns:
            统计信息列表

        Raises:
            NotFoundError: 平台不存在
            DatabaseError: 数据库操作失败
        """
        try:
            platform = self.session.query(Platform).filter(Platform.id == platform_id).first()
            if not platform:
                raise NotFoundError(f"平台不存在: {platform_id}")

            # 构建查询
            query = self.session.query(
                func.date_trunc(group_by, Content.publish_time).label("time_bucket"),
                func.count(Content.id).label("count"),
            ).filter(Content.platform_id == platform_id)

            if start_time:
                query = query.filter(Content.publish_time >= start_time)
            if end_time:
                query = query.filter(Content.publish_time <= end_time)

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
        except NotFoundError:
            raise
        except Exception as e:
            raise DatabaseError(f"获取平台内容时间统计信息失败: {str(e)}") 