from typing import List, Optional
from .base_dao import BaseDAO
from ..models.platform import Platform

class PlatformDAO(BaseDAO):
    """平台DAO类"""
    
    def __init__(self):
        super().__init__(Platform)
    
    def get_by_name(self, name: str) -> Optional[Platform]:
        """根据名称获取平台"""
        return self.get_by_field('name', name)
    
    def get_active_platforms(self) -> List[Platform]:
        """获取所有启用的平台"""
        with self.get_session() as session:
            return session.query(Platform)\
                .filter_by(status=1)\
                .all()
    
    def enable(self, id: int) -> bool:
        """启用平台"""
        return self.update(id, {'status': 1}) is not None
    
    def disable(self, id: int) -> bool:
        """禁用平台"""
        return self.update(id, {'status': 0}) is not None 