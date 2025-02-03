"""
Database models and operations
"""

from .session import async_session_factory as Session
from .session import engine, init_database, get_session, get_db
from .base_dao import BaseDAO
from .content_dao import ContentDAO
from .tag_dao import TagDAO
from .platform_dao import PlatformDAO
from .category_dao import CategoryDAO
from .report_dao import ReportDAO
from .task_log_dao import TaskLogDAO

__all__ = [
    'Session',
    'engine',
    'init_database',
    'get_session',
    'get_db',
    'BaseDAO',
    'ContentDAO',
    'TagDAO',
    'PlatformDAO',
    'CategoryDAO',
    'ReportDAO',
    'TaskLogDAO'
]

# 创建DAO实例
content_dao = ContentDAO()
platform_dao = PlatformDAO()
category_dao = CategoryDAO()
tag_dao = TagDAO()
report_dao = ReportDAO()
task_log_dao = TaskLogDAO()

__all__.extend([
    'content_dao', 'platform_dao', 'category_dao', 'tag_dao', 'report_dao', 'task_log_dao'
]) 