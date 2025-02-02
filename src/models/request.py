from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class Request(Base):
    """请求日志模型"""
    __tablename__ = 'requests'
    
    id = Column(Integer, primary_key=True)
    url = Column(String(500), nullable=False)  # 请求URL
    method = Column(String(10), default='GET')  # 请求方法
    headers = Column(Text)  # 请求头
    body = Column(Text)  # 请求体
    status_code = Column(Integer)  # 响应状态码
    response = Column(Text)  # 响应内容
    latency = Column(Float)  # 响应延迟(ms)
    is_success = Column(Boolean, default=False)  # 是否成功
    is_throttled = Column(Boolean, default=False)  # 是否被限流
    error = Column(Text)  # 错误信息
    proxy = Column(String(100))  # 使用的代理
    retry_count = Column(Integer, default=0)  # 重试次数
    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='SET NULL'))  # 关联任务
    created_at = Column(DateTime, default=datetime.now)
    
    # 关联关系
    task = relationship('Task', backref='requests')
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'url': self.url,
            'method': self.method,
            'headers': self.headers,
            'body': self.body,
            'status_code': self.status_code,
            'response': self.response,
            'latency': self.latency,
            'is_success': self.is_success,
            'is_throttled': self.is_throttled,
            'error': self.error,
            'proxy': self.proxy,
            'retry_count': self.retry_count,
            'task_id': self.task_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        } 