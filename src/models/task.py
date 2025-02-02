from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Task(Base):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # 任务类型
    status = Column(String(20), default='pending')  # 任务状态
    priority = Column(Integer, default=0)  # 优先级
    params = Column(Text)  # 任务参数
    result = Column(Text)  # 任务结果
    error = Column(Text)  # 错误信息
    retry_count = Column(Integer, default=0)  # 重试次数
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'status': self.status,
            'priority': self.priority,
            'params': self.params,
            'result': self.result,
            'error': self.error,
            'retry_count': self.retry_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 