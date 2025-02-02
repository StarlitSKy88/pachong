from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from . import Base
import datetime

# 报告-内容关联表
report_contents = Table('report_contents', Base.metadata,
    Column('report_id', Integer, ForeignKey('reports.id'), primary_key=True),
    Column('content_id', Integer, ForeignKey('contents.id'), primary_key=True),
    extend_existing=True
)

class Report(Base):
    """报告模型"""
    __tablename__ = 'reports'

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text)
    report_type = Column(String(50))  # daily, weekly, monthly
    report_date = Column(DateTime, nullable=False)
    create_time = Column(DateTime, default=datetime.datetime.now)
    update_time = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    status = Column(Integer, default=0)  # 0: 草稿, 1: 已发布

    # 关联关系
    contents = relationship("Content", secondary=report_contents, back_populates="reports")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'summary': self.summary,
            'report_type': self.report_type,
            'report_date': self.report_date.strftime('%Y-%m-%d'),
            'create_time': self.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'update_time': self.update_time.strftime('%Y-%m-%d %H:%M:%S'),
            'status': self.status,
            'contents': [content.to_dict() for content in self.contents]
        }

    def __repr__(self):
        return f'<Report {self.title}>' 