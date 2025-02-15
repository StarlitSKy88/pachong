"""枚举定义模块。"""

from enum import Enum as PyEnum

class ContentType(str, PyEnum):
    """内容类型枚举。"""
    ARTICLE = "article"  # 文章
    VIDEO = "video"  # 视频
    IMAGE = "image"  # 图片
    AUDIO = "audio"  # 音频

class ContentStatus(str, PyEnum):
    """内容状态枚举。"""
    PENDING = "pending"  # 待处理
    DRAFT = "draft"  # 草稿
    REVIEWING = "reviewing"  # 审核中
    PUBLISHED = "published"  # 已发布
    ARCHIVED = "archived"  # 已归档
    REJECTED = "rejected"  # 已拒绝
    DELETED = "deleted"  # 已删除 