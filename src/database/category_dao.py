from typing import List, Optional
from sqlalchemy import asc
from .base_dao import BaseDAO
from ..models.category import Category

class CategoryDAO(BaseDAO):
    """分类DAO类"""
    
    def __init__(self):
        super().__init__(Category)
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """根据名称获取分类"""
        return self.get_by_field('name', name)
    
    def get_active_categories(self) -> List[Category]:
        """获取所有启用的分类"""
        with self.get_session() as session:
            return session.query(Category)\
                .filter_by(status=1)\
                .order_by(asc(Category.sort_order))\
                .all()
    
    def enable(self, id: int) -> bool:
        """启用分类"""
        return self.update(id, {'status': 1}) is not None
    
    def disable(self, id: int) -> bool:
        """禁用分类"""
        return self.update(id, {'status': 0}) is not None
    
    def update_sort_order(self, id: int, sort_order: int) -> bool:
        """更新排序顺序"""
        return self.update(id, {'sort_order': sort_order}) is not None
    
    def batch_update_sort_order(self, sort_data: List[dict]) -> bool:
        """批量更新排序顺序"""
        try:
            with self.get_session() as session:
                for data in sort_data:
                    category = session.query(Category).get(data['id'])
                    if category:
                        category.sort_order = data['sort_order']
                session.commit()
                return True
        except:
            return False 