"""爬虫管理器模块。"""

from typing import Dict, List, Optional, Type

from loguru import logger

from src.config.settings import Settings
from src.crawlers.base import BaseCrawler
from src.crawlers.bilibili import BiliBiliCrawler
from src.crawlers.xiaohongshu import XiaoHongShuCrawler
from src.database.content_dao import ContentDAO
from src.database.platform_dao import PlatformDAO
from src.models.content import Content, Platform
from src.utils.error_handler import CrawlerError


class CrawlerManager:
    """爬虫管理器。"""

    def __init__(self, settings: Settings):
        """初始化爬虫管理器。

        Args:
            settings: 配置对象
        """
        self.settings = settings
        self.crawlers: Dict[str, Type[BaseCrawler]] = {
            "bilibili": BiliBiliCrawler,
            "xiaohongshu": XiaoHongShuCrawler,
        }
        self.platform_dao = PlatformDAO(settings.get_db())
        self.content_dao = ContentDAO(settings.get_db())

    async def get_crawler(self, platform_name: str) -> Optional[BaseCrawler]:
        """获取爬虫实例。

        Args:
            platform_name: 平台名称

        Returns:
            爬虫实例
        """
        try:
            # 获取平台信息
            platform = await self.platform_dao.get_by_name(platform_name)
            if not platform:
                logger.warning(f"平台不存在: {platform_name}")
                return None

            if not platform.enabled:
                logger.warning(f"平台已禁用: {platform_name}")
                return None

            # 获取爬虫类
            crawler_cls = self.crawlers.get(platform_name.lower())
            if not crawler_cls:
                logger.warning(f"爬虫不存在: {platform_name}")
                return None

            # 创建爬虫实例
            return crawler_cls(self.settings)
        except Exception as e:
            logger.error(f"获取爬虫实例失败: {str(e)}")
            return None

    async def crawl_content(
        self,
        platform_name: str,
        keywords: List[str],
        time_range: str = "24h",
        limit: int = 100,
    ) -> List[Content]:
        """爬取内容。

        Args:
            platform_name: 平台名称
            keywords: 关键词列表
            time_range: 时间范围
            limit: 限制数量

        Returns:
            内容列表
        """
        try:
            # 获取爬虫实例
            crawler = await self.get_crawler(platform_name)
            if not crawler:
                raise CrawlerError(f"获取爬虫实例失败: {platform_name}")

            contents = []
            for keyword in keywords:
                try:
                    # 搜索内容
                    if platform_name.lower() == "bilibili":
                        videos, total = await crawler.search_videos(
                            keyword=keyword,
                            page=1,
                            page_size=min(limit, 20),
                        )
                        for video in videos:
                            try:
                                # 获取视频详情
                                detail = await crawler.get_video_detail(video["bvid"])
                                content = crawler._parse_video(detail)
                                contents.append(content)
                            except Exception as e:
                                logger.error(f"处理视频失败: {str(e)}")
                                continue

                    elif platform_name.lower() == "xiaohongshu":
                        notes, total = await crawler.search_notes(
                            keyword=keyword,
                            page=1,
                            page_size=min(limit, 20),
                        )
                        for note in notes:
                            try:
                                # 获取笔记详情
                                detail = await crawler.get_note_detail(note["id"])
                                content = crawler._parse_note(detail)
                                contents.append(content)
                            except Exception as e:
                                logger.error(f"处理笔记失败: {str(e)}")
                                continue

                except Exception as e:
                    logger.error(f"搜索关键词失败: {keyword}, 错误: {str(e)}")
                    continue

            return contents
        except Exception as e:
            raise CrawlerError(f"爬取内容失败: {str(e)}")

    async def save_contents(self, contents: List[Content]) -> None:
        """保存内容。

        Args:
            contents: 内容列表
        """
        try:
            for content in contents:
                try:
                    # 检查内容是否已存在
                    existing = await self.content_dao.get_by_url(content.url)
                    if existing:
                        logger.info(f"内容已存在: {content.url}")
                        continue

                    # 保存内容
                    await self.content_dao.create(content)
                    logger.info(f"保存内容成功: {content.url}")
                except Exception as e:
                    logger.error(f"保存内容失败: {content.url}, 错误: {str(e)}")
                    continue
        except Exception as e:
            raise CrawlerError(f"保存内容失败: {str(e)}")

    async def crawl_and_save(
        self,
        platform_name: str,
        keywords: List[str],
        time_range: str = "24h",
        limit: int = 100,
    ) -> None:
        """爬取并保存内容。

        Args:
            platform_name: 平台名称
            keywords: 关键词列表
            time_range: 时间范围
            limit: 限制数量
        """
        try:
            # 爬取内容
            contents = await self.crawl_content(
                platform_name=platform_name,
                keywords=keywords,
                time_range=time_range,
                limit=limit,
            )

            # 保存内容
            await self.save_contents(contents)
        except Exception as e:
            raise CrawlerError(f"爬取并保存内容失败: {str(e)}")

    async def get_enabled_platforms(self) -> List[Platform]:
        """获取已启用的平台列表。

        Returns:
            平台列表
        """
        try:
            return await self.platform_dao.get_enabled()
        except Exception as e:
            raise CrawlerError(f"获取已启用平台列表失败: {str(e)}")

    async def crawl_all_platforms(
        self,
        keywords: List[str],
        time_range: str = "24h",
        limit: int = 100,
    ) -> None:
        """爬取所有平台的内容。

        Args:
            keywords: 关键词列表
            time_range: 时间范围
            limit: 限制数量
        """
        try:
            # 获取已启用的平台
            platforms = await self.get_enabled_platforms()
            if not platforms:
                logger.warning("没有已启用的平台")
                return

            # 爬取每个平台的内容
            for platform in platforms:
                try:
                    await self.crawl_and_save(
                        platform_name=platform.name,
                        keywords=keywords,
                        time_range=time_range,
                        limit=limit,
                    )
                except Exception as e:
                    logger.error(f"爬取平台失败: {platform.name}, 错误: {str(e)}")
                    continue
        except Exception as e:
            raise CrawlerError(f"爬取所有平台内容失败: {str(e)}")

    async def update_platform_stats(self) -> None:
        """更新平台统计信息。"""
        try:
            # 获取所有平台
            platforms = await self.platform_dao.get_all()
            if not platforms:
                logger.warning("没有平台")
                return

            # 更新每个平台的统计信息
            for platform in platforms:
                try:
                    stats = await self.platform_dao.get_stats(platform.id)
                    await self.platform_dao.update(
                        platform.id,
                        {"stats": stats},
                    )
                    logger.info(f"更新平台统计信息成功: {platform.name}")
                except Exception as e:
                    logger.error(f"更新平台统计信息失败: {platform.name}, 错误: {str(e)}")
                    continue
        except Exception as e:
            raise CrawlerError(f"更新平台统计信息失败: {str(e)}")

    async def update_content_stats(self) -> None:
        """更新内容统计信息。"""
        try:
            # 获取所有平台
            platforms = await self.platform_dao.get_all()
            if not platforms:
                logger.warning("没有平台")
                return

            # 更新每个平台的内容统计信息
            for platform in platforms:
                try:
                    # 获取爬虫实例
                    crawler = await self.get_crawler(platform.name)
                    if not crawler:
                        logger.warning(f"获取爬虫实例失败: {platform.name}")
                        continue

                    # 获取平台内容
                    contents = await self.content_dao.get_by_platform(platform.id)
                    for content in contents:
                        try:
                            if platform.name.lower() == "bilibili":
                                # 获取视频详情
                                detail = await crawler.get_video_detail(
                                    content.metadata["bvid"]
                                )
                                # 更新统计信息
                                await self.content_dao.update_stats(
                                    content.id,
                                    detail.get("stat", {}),
                                )
                            elif platform.name.lower() == "xiaohongshu":
                                # 获取笔记详情
                                detail = await crawler.get_note_detail(
                                    content.metadata["note_id"]
                                )
                                # 更新统计信息
                                await self.content_dao.update_stats(
                                    content.id,
                                    {
                                        "likes": detail.get("likes", 0),
                                        "comments": detail.get("comments", 0),
                                        "collects": detail.get("collects", 0),
                                        "shares": detail.get("shares", 0),
                                    },
                                )
                        except Exception as e:
                            logger.error(f"更新内容统计信息失败: {content.url}, 错误: {str(e)}")
                            continue
                except Exception as e:
                    logger.error(f"更新平台内容统计信息失败: {platform.name}, 错误: {str(e)}")
                    continue
        except Exception as e:
            raise CrawlerError(f"更新内容统计信息失败: {str(e)}")

    async def cleanup(self) -> None:
        """清理资源。"""
        try:
            # 关闭数据库连接
            await self.platform_dao.close()
            await self.content_dao.close()
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

    async def __aenter__(self) -> "CrawlerManager":
        """异步上下文管理器入口。

        Returns:
            爬虫管理器实例
        """
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """异步上下文管理器出口。

        Args:
            exc_type: 异常类型
            exc_val: 异常值
            exc_tb: 异常回溯
        """
        await self.cleanup() 