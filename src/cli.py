"""命令行工具模块。"""

import asyncio
import json
from datetime import datetime
from typing import List, Optional

import click
from loguru import logger

from src.config.settings import Settings
from src.crawlers.manager import CrawlerManager
from src.database.content_dao import ContentDAO
from src.database.platform_dao import PlatformDAO
from src.models.content import Content, Platform
from src.utils.error_handler import CrawlerError


@click.group()
def cli():
    """内容采集和管理工具。"""
    pass


@cli.group()
def platform():
    """平台管理命令组。"""
    pass


@platform.command("list")
def list_platforms():
    """列出所有平台。"""
    async def _list_platforms():
        try:
            settings = Settings()
            platform_dao = PlatformDAO(settings.get_db())

            platforms = await platform_dao.get_all()
            if not platforms:
                click.echo("没有平台")
                return

            for p in platforms:
                status = "启用" if p.enabled else "禁用"
                click.echo(f"ID: {p.id}")
                click.echo(f"名称: {p.name}")
                click.echo(f"描述: {p.description}")
                click.echo(f"状态: {status}")
                click.echo(f"基础URL: {p.base_url}")
                click.echo(f"配置: {json.dumps(p.config, ensure_ascii=False)}")
                click.echo("-" * 50)
        except Exception as e:
            click.echo(f"列出平台失败: {str(e)}", err=True)

    asyncio.run(_list_platforms())


@platform.command("add")
@click.argument("name")
@click.argument("base_url")
@click.option("--description", "-d", help="平台描述")
@click.option("--config", "-c", type=click.Path(exists=True), help="配置文件路径")
def add_platform(name: str, base_url: str, description: Optional[str], config: Optional[str]):
    """添加平台。"""
    async def _add_platform():
        try:
            settings = Settings()
            platform_dao = PlatformDAO(settings.get_db())

            # 检查平台是否已存在
            existing = await platform_dao.get_by_name(name)
            if existing:
                click.echo(f"平台已存在: {name}", err=True)
                return

            # 读取配置文件
            platform_config = {}
            if config:
                with open(config, "r", encoding="utf-8") as f:
                    platform_config = json.load(f)

            # 创建平台
            platform = Platform(
                name=name,
                description=description,
                base_url=base_url,
                enabled=True,
                config=platform_config,
            )
            await platform_dao.create(platform)
            click.echo(f"添加平台成功: {name}")
        except Exception as e:
            click.echo(f"添加平台失败: {str(e)}", err=True)

    asyncio.run(_add_platform())


@platform.command("enable")
@click.argument("name")
def enable_platform(name: str):
    """启用平台。"""
    async def _enable_platform():
        try:
            settings = Settings()
            platform_dao = PlatformDAO(settings.get_db())

            # 获取平台
            platform = await platform_dao.get_by_name(name)
            if not platform:
                click.echo(f"平台不存在: {name}", err=True)
                return

            # 启用平台
            await platform_dao.enable(platform.id)
            click.echo(f"启用平台成功: {name}")
        except Exception as e:
            click.echo(f"启用平台失败: {str(e)}", err=True)

    asyncio.run(_enable_platform())


@platform.command("disable")
@click.argument("name")
def disable_platform(name: str):
    """禁用平台。"""
    async def _disable_platform():
        try:
            settings = Settings()
            platform_dao = PlatformDAO(settings.get_db())

            # 获取平台
            platform = await platform_dao.get_by_name(name)
            if not platform:
                click.echo(f"平台不存在: {name}", err=True)
                return

            # 禁用平台
            await platform_dao.disable(platform.id)
            click.echo(f"禁用平台成功: {name}")
        except Exception as e:
            click.echo(f"禁用平台失败: {str(e)}", err=True)

    asyncio.run(_disable_platform())


@cli.group()
def content():
    """内容管理命令组。"""
    pass


@content.command("crawl")
@click.argument("platform_name")
@click.argument("keywords", nargs=-1)
@click.option("--time-range", "-t", default="24h", help="时间范围")
@click.option("--limit", "-l", default=100, help="限制数量")
def crawl_content(platform_name: str, keywords: List[str], time_range: str, limit: int):
    """爬取内容。"""
    async def _crawl_content():
        try:
            settings = Settings()
            manager = CrawlerManager(settings)

            # 爬取内容
            await manager.crawl_and_save(
                platform_name=platform_name,
                keywords=list(keywords),
                time_range=time_range,
                limit=limit,
            )
            click.echo("爬取内容成功")
    except Exception as e:
            click.echo(f"爬取内容失败: {str(e)}", err=True)

    asyncio.run(_crawl_content())


@content.command("crawl-all")
@click.argument("keywords", nargs=-1)
@click.option("--time-range", "-t", default="24h", help="时间范围")
@click.option("--limit", "-l", default=100, help="限制数量")
def crawl_all_content(keywords: List[str], time_range: str, limit: int):
    """爬取所有平台的内容。"""
    async def _crawl_all_content():
        try:
            settings = Settings()
            manager = CrawlerManager(settings)

            # 爬取所有平台的内容
            await manager.crawl_all_platforms(
                keywords=list(keywords),
                time_range=time_range,
                limit=limit,
            )
            click.echo("爬取所有平台内容成功")
        except Exception as e:
            click.echo(f"爬取所有平台内容失败: {str(e)}", err=True)

    asyncio.run(_crawl_all_content())


@content.command("list")
@click.option("--platform", "-p", help="平台名称")
@click.option("--keyword", "-k", help="关键词")
@click.option("--start-time", "-s", help="开始时间")
@click.option("--end-time", "-e", help="结束时间")
@click.option("--offset", "-o", default=0, help="偏移量")
@click.option("--limit", "-l", default=20, help="限制数量")
def list_content(
    platform: Optional[str],
    keyword: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
    offset: int,
    limit: int,
):
    """列出内容。"""
    async def _list_content():
        try:
            settings = Settings()
            content_dao = ContentDAO(settings.get_db())
            platform_dao = PlatformDAO(settings.get_db())

            # 获取平台ID
            platform_id = None
            if platform:
                p = await platform_dao.get_by_name(platform)
                if not p:
                    click.echo(f"平台不存在: {platform}", err=True)
                    return
                platform_id = p.id

            # 搜索内容
            contents, total = await content_dao.search(
                keyword=keyword,
                platform_id=platform_id,
                start_time=start_time,
                end_time=end_time,
                offset=offset,
                limit=limit,
            )

            if not contents:
                click.echo("没有内容")
                return

            click.echo(f"总数: {total}")
            click.echo("-" * 50)

            for content in contents:
                click.echo(f"ID: {content.id}")
                click.echo(f"标题: {content.title}")
                click.echo(f"作者: {content.author}")
                click.echo(f"发布时间: {content.publish_time}")
                click.echo(f"URL: {content.url}")
                click.echo(f"统计: {json.dumps(content.stats, ensure_ascii=False)}")
                click.echo("-" * 50)
        except Exception as e:
            click.echo(f"列出内容失败: {str(e)}", err=True)

    asyncio.run(_list_content())


@content.command("stats")
@click.option("--platform", "-p", help="平台名称")
@click.option("--start-time", "-s", help="开始时间")
@click.option("--end-time", "-e", help="结束时间")
def content_stats(
    platform: Optional[str],
    start_time: Optional[str],
    end_time: Optional[str],
):
    """获取内容统计信息。"""
    async def _content_stats():
        try:
            settings = Settings()
            content_dao = ContentDAO(settings.get_db())
            platform_dao = PlatformDAO(settings.get_db())

            # 获取平台ID
            platform_id = None
            if platform:
                p = await platform_dao.get_by_name(platform)
                if not p:
                    click.echo(f"平台不存在: {platform}", err=True)
                    return
                platform_id = p.id

            # 获取统计信息
            stats = await content_dao.get_stats(
                platform_id=platform_id,
                start_time=start_time,
                end_time=end_time,
            )

            click.echo(json.dumps(stats, ensure_ascii=False, indent=2))
        except Exception as e:
            click.echo(f"获取内容统计信息失败: {str(e)}", err=True)

    asyncio.run(_content_stats())


@cli.group()
def task():
    """任务管理命令组。"""
    pass


@task.command("update-stats")
def update_stats():
    """更新统计信息。"""
    async def _update_stats():
        try:
            settings = Settings()
            manager = CrawlerManager(settings)

            # 更新统计信息
            await manager.update_platform_stats()
            await manager.update_content_stats()
            click.echo("更新统计信息成功")
    except Exception as e:
            click.echo(f"更新统计信息失败: {str(e)}", err=True)

    asyncio.run(_update_stats())


if __name__ == "__main__":
    cli() 