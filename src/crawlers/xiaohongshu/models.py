from datetime import datetime, UTC
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

class Content:
    """内容模型"""

    def __init__(
        self,
        id: str,  # 内容ID
        title: str,  # 标题
        desc: str,  # 描述
        content: str,  # 内容
        images: List[str],  # 图片列表
        user: Dict[str, Any],  # 用户信息
        stats: Dict[str, Any],  # 统计信息
        type: str = "normal",  # 内容类型
        created_at: datetime = None  # 创建时间
    ):
        self.id = id
        self.title = title
        self.desc = desc
        self.content = content
        self.images = images
        self.user = user
        self.stats = stats
        self.type = type
        self.created_at = created_at or datetime.now() 