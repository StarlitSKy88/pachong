"""数据库包初始化文件。"""

from .base import Database
from .session import engine, init_db, get_session
from .tag_dao import TagDAO
from .content_dao import ContentDAO
from .platform_dao import PlatformDAO
from .report_dao import ReportDAO

__all__ = [
    'Database',
    'engine',
    'init_db',
    'get_session',
    'TagDAO',
    'ContentDAO',
    'PlatformDAO',
    'ReportDAO'
]

# 创建DAO实例
content_dao = ContentDAO()
platform_dao = PlatformDAO()
tag_dao = TagDAO()
report_dao = ReportDAO()

__all__.extend([
    'content_dao', 'platform_dao', 'tag_dao', 'report_dao'
]) 