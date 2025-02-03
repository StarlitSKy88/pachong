"""数据访问层基类模块。"""

from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.database.base import Base
from src.utils.error_handler import DatabaseError
from src.utils.logger import get_logger

logger = get_logger(__name__)

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseDAO(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """数据访问基类。"""

    def __init__(self, model: Type[ModelType]):
        """初始化。

        Args:
            model: 模型类
        """
        self.model = model

    def get(self, db: Session, id: Any) -> Optional[ModelType]:
        """获取单个对象。

        Args:
            db: 数据库会话
            id: 对象ID

        Returns:
            Optional[ModelType]: 查询结果

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get {self.model.__name__} by id {id}: {e}")
            raise DatabaseError(f"Failed to get {self.model.__name__}") from e

    def get_multi(
        self,
        db: Session,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ModelType]:
        """获取多个对象。

        Args:
            db: 数据库会话
            skip: 跳过数量
            limit: 限制数量
            filters: 过滤条件

        Returns:
            List[ModelType]: 查询结果列表

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            query = db.query(self.model)
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.filter(getattr(self.model, key) == value)
            return query.offset(skip).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Failed to get multiple {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to get {self.model.__name__} list") from e

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """创建对象。

        Args:
            db: 数据库会话
            obj_in: 创建对象数据

        Returns:
            ModelType: 创建的对象

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            obj_in_data = jsonable_encoder(obj_in)
            db_obj = self.model(**obj_in_data)
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to create {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to create {self.model.__name__}") from e

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: Union[UpdateSchemaType, Dict[str, Any]],
    ) -> ModelType:
        """更新对象。

        Args:
            db: 数据库会话
            db_obj: 数据库对象
            obj_in: 更新数据

        Returns:
            ModelType: 更新后的对象

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            obj_data = jsonable_encoder(db_obj)
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)
            for field in obj_data:
                if field in update_data:
                    setattr(db_obj, field, update_data[field])
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to update {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to update {self.model.__name__}") from e

    def delete(self, db: Session, *, id: Any) -> ModelType:
        """删除对象。

        Args:
            db: 数据库会话
            id: 对象ID

        Returns:
            ModelType: 删除的对象

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            obj = db.query(self.model).get(id)
            if obj:
                db.delete(obj)
                db.commit()
            return obj
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Failed to delete {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to delete {self.model.__name__}") from e

    def count(
        self,
        db: Session,
        *,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        """获取对象数量。

        Args:
            db: 数据库会话
            filters: 过滤条件

        Returns:
            int: 对象数量

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            query = select([self.model])
            if filters:
                for key, value in filters.items():
                    if hasattr(self.model, key):
                        query = query.where(getattr(self.model, key) == value)
            return db.execute(query).count()
        except SQLAlchemyError as e:
            logger.error(f"Failed to count {self.model.__name__}: {e}")
            raise DatabaseError(f"Failed to count {self.model.__name__}") from e

    def exists(self, db: Session, *, id: Any) -> bool:
        """检查对象是否存在。

        Args:
            db: 数据库会话
            id: 对象ID

        Returns:
            bool: 是否存在

        Raises:
            DatabaseError: 数据库错误
        """
        try:
            return db.query(self.model).filter(self.model.id == id).first() is not None
        except SQLAlchemyError as e:
            logger.error(f"Failed to check {self.model.__name__} existence: {e}")
            raise DatabaseError(
                f"Failed to check {self.model.__name__} existence"
            ) from e 