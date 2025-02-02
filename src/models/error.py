from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Error(Base):
    """错误日志模型"""
    __tablename__ = 'errors'
    
    id = Column(Integer, primary_key=True)
    type = Column(String(50), nullable=False)  # 错误类型
    message = Column(Text)  # 错误信息
    traceback = Column(Text)  # 堆栈跟踪
    url = Column(String(500))  # 相关URL
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'))  # 关联任务
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    task = relationship('Task', backref='errors')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'type': self.type,
            'message': self.message,
            'traceback': self.traceback,
            'url': self.url,
            'task_id': self.task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 