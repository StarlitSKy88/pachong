from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from datetime import datetime
from . import Base

class Cookie(Base):
    """Cookie模型"""
    __tablename__ = 'cookies'
    
    id = Column(Integer, primary_key=True)
    platform = Column(String(50), nullable=False)  # 平台
    user_id = Column(String(100))  # 用户ID
    value = Column(Text, nullable=False)  # Cookie值
    is_valid = Column(Boolean, default=True)  # 是否有效
    fail_count = Column(Integer, default=0)  # 失败次数
    success_count = Column(Integer, default=0)  # 成功次数
    total_count = Column(Integer, default=0)  # 总使用次数
    last_check = Column(DateTime)  # 最后检查时间
    expire_time = Column(DateTime)  # 过期时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform,
            'user_id': self.user_id,
            'value': self.value,
            'is_valid': self.is_valid,
            'fail_count': self.fail_count,
            'success_count': self.success_count,
            'total_count': self.total_count,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'expire_time': self.expire_time.isoformat() if self.expire_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 