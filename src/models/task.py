from sqlalchemy import Column, String, Integer, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Task(Base):
    """任务模型"""
    __tablename__ = 'tasks'
    
    id = Column(String, primary_key=True)
    platform = Column(String, nullable=False)
    keywords = Column(JSON, nullable=False)
    status = Column(String, nullable=False)
    progress = Column(Integer, default=0)
    filters = Column(JSON)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'platform': self.platform,
            'keywords': self.keywords,
            'status': self.status,
            'progress': self.progress,
            'filters': self.filters,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        } 