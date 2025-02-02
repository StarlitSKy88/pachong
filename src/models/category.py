from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from . import Base

class Category(Base):
    """分类模型"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    icon = Column(String(50))  # emoji图标
    sort_order = Column(Integer, default=0)  # 排序顺序
    status = Column(Integer, default=1)  # 1: 正常, 0: 禁用

    # 关联关系
    contents = relationship("Content", back_populates="category")

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'status': self.status
        }

    def __repr__(self):
        return f'<Category {self.name}>' 