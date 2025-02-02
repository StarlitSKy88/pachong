from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from datetime import datetime
from . import Base

class Proxy(Base):
    """代理模型"""
    __tablename__ = 'proxies'
    
    id = Column(Integer, primary_key=True)
    host = Column(String(100), nullable=False)  # 代理主机
    port = Column(Integer, nullable=False)  # 代理端口
    protocol = Column(String(10), default='http')  # 代理协议
    username = Column(String(50))  # 用户名
    password = Column(String(50))  # 密码
    is_valid = Column(Boolean, default=True)  # 是否有效
    fail_count = Column(Integer, default=0)  # 失败次数
    success_count = Column(Integer, default=0)  # 成功次数
    total_count = Column(Integer, default=0)  # 总使用次数
    avg_latency = Column(Float, default=0)  # 平均延迟(ms)
    last_check = Column(DateTime)  # 最后检查时间
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'host': self.host,
            'port': self.port,
            'protocol': self.protocol,
            'username': self.username,
            'password': self.password,
            'is_valid': self.is_valid,
            'fail_count': self.fail_count,
            'success_count': self.success_count,
            'total_count': self.total_count,
            'avg_latency': self.avg_latency,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        } 