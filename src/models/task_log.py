from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from . import Base
import datetime

class TaskLog(Base):
    """任务执行记录模型"""
    __tablename__ = 'task_logs'

    id = Column(Integer, primary_key=True)
    task_id = Column(String(100), nullable=False)  # 任务ID
    task_type = Column(String(50), nullable=False)  # 任务类型：crawler, report
    platform = Column(String(50))  # 平台名称
    status = Column(String(20), nullable=False)  # 状态：success, failed, running
    start_time = Column(DateTime, default=datetime.datetime.now)  # 开始时间
    end_time = Column(DateTime)  # 结束时间
    error_message = Column(Text)  # 错误信息
    result = Column(Text)  # 执行结果
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'task_type': self.task_type,
            'platform': self.platform,
            'status': self.status,
            'start_time': self.start_time.strftime('%Y-%m-%d %H:%M:%S'),
            'end_time': self.end_time.strftime('%Y-%m-%d %H:%M:%S') if self.end_time else None,
            'error_message': self.error_message,
            'result': self.result
        }
    
    def __repr__(self):
        return f'<TaskLog {self.task_id} - {self.status}>' 