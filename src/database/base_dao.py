"""基础DAO类"""

from typing import List, Dict, Any, Optional, Type, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete
from contextlib import contextmanager, asynccontextmanager

from src.models.base import Base

T = TypeVar('T', bound=Base)

class BaseDAO(Generic[T]):
    """基础DAO类"""
    
    def __init__(self, model: Type[T]):
        """初始化
        
        Args:
            model: 模型类
        """
        self.model = model
    
    @asynccontextmanager
    async def get_session(self) -> Session:
        """获取数据库会话"""
        async with get_db() as session:
            yield session
    
    @asynccontextmanager
    async def transaction(self):
        """事务上下文管理器"""
        async with self.get_session() as session:
            try:
                yield session
                await session.commit()
            except:
                await session.rollback()
                raise
        
    async def add(self, data: Dict[str, Any]) -> T:
        """添加记录
        
        Args:
            data: 记录数据
            
        Returns:
            T: 记录对象
        """
        async with self.transaction() as session:
            instance = self.model(**data)
            session.add(instance)
            await session.refresh(instance)
            return instance
        
    def get(self, session: Session, id: int) -> Optional[T]:
        """获取记录
        
        Args:
            session: 数据库会话
            id: 记录ID
            
        Returns:
            Optional[T]: 记录对象
        """
        return session.get(self.model, id)
        
    async def get_by_field(self, field: str, value: Any) -> Optional[T]:
        """根据字段获取记录
        
        Args:
            field: 字段名
            value: 字段值
            
        Returns:
            Optional[T]: 记录对象
        """
        async with self.get_session() as session:
            return await session.query(self.model).filter_by(**{field: value}).first()
        
    async def list(self, **filters) -> List[T]:
        """获取记录列表
        
        Args:
            **filters: 过滤条件
            
        Returns:
            List[T]: 记录列表
        """
        async with self.get_session() as session:
            query = session.query(self.model)
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)
            return await query.all()
        
    def update(self, session: Session, id: int, **kwargs) -> Optional[T]:
        """更新记录
        
        Args:
            session: 数据库会话
            id: 记录ID
            **kwargs: 要更新的字段值
            
        Returns:
            Optional[T]: 更新后的记录
        """
        stmt = update(self.model).where(self.model.id == id).values(**kwargs)
        session.execute(stmt)
        session.commit()
        return self.get(session, id)
        
    def delete(self, session: Session, id: int) -> bool:
        """删除记录
        
        Args:
            session: 数据库会话
            id: 记录ID
            
        Returns:
            bool: 是否删除成功
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = session.execute(stmt)
        session.commit()
        return result.rowcount > 0
    
    def get_all(self, session: Session) -> List[T]:
        """获取所有记录
        
        Args:
            session: 数据库会话
            
        Returns:
            List[T]: 记录列表
        """
        stmt = select(self.model)
        return list(session.scalars(stmt))
    
    async def count(self) -> int:
        """获取记录总数"""
        async with self.get_session() as session:
            return await session.query(self.model).count()
    
    async def exists(self, **kwargs) -> bool:
        """检查记录是否存在"""
        async with self.get_session() as session:
            return await session.query(self.model)\
                .filter_by(**kwargs)\
                .first() is not None
    
    async def get_by_fields(self, **kwargs) -> Optional[T]:
        """根据多个字段获取记录"""
        async with self.get_session() as session:
            return await session.query(self.model)\
                .filter_by(**kwargs)\
                .first()
    
    async def find_by_field(self, field: str, value: Any, page: int = 1, per_page: int = 20) -> List[T]:
        """根据字段查找记录"""
        async with self.get_session() as session:
            return await session.query(self.model)\
                .filter(getattr(self.model, field) == value)\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()
    
    async def find_by_fields(self, page: int = 1, per_page: int = 20, **kwargs) -> List[T]:
        """根据多个字段查找记录"""
        async with self.get_session() as session:
            return await session.query(self.model)\
                .filter_by(**kwargs)\
                .offset((page - 1) * per_page)\
                .limit(per_page)\
                .all()

    def create(self, session: Session, **kwargs) -> T:
        """创建记录

        Args:
            session: 数据库会话
            **kwargs: 字段值

        Returns:
            T: 创建的记录
        """
        obj = self.model(**kwargs)
        session.add(obj)
        session.commit()
        return obj

    def delete(self, session: Session, id: int) -> bool:
        """删除记录

        Args:
            session: 数据库会话
            id: 记录ID

        Returns:
            bool: 是否删除成功
        """
        stmt = delete(self.model).where(self.model.id == id)
        result = session.execute(stmt)
        session.commit()
        return result.rowcount > 0 