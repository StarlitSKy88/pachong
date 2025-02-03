"""MongoDB存储实现"""
from typing import List, Dict, Any, Optional
from datetime import datetime
import motor.motor_asyncio
from bson import ObjectId
from loguru import logger

from .base_storage import BaseStorage

class MongoStorage(BaseStorage):
    """MongoDB存储实现"""
    
    def __init__(self, mongo_url: str, database: str, collection: str):
        """初始化
        
        Args:
            mongo_url: MongoDB连接URL
            database: 数据库名
            collection: 集合名
        """
        super().__init__()
        self.client = motor.motor_asyncio.AsyncIOMotorClient(mongo_url)
        self.db = self.client[database]
        self.collection = self.db[collection]
        
    async def init(self):
        """初始化数据库
        
        - 创建索引
        - 设置验证规则
        """
        # 创建索引
        await self.collection.create_index('id', unique=True)
        await self.collection.create_index('source')
        await self.collection.create_index('created_at')
        
        # 创建复合索引
        await self.collection.create_index([
            ('source', 1),
            ('created_at', -1)
        ])
        
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据"""
        try:
            # 验证数据
            if not self.validate_data(data):
                return False
                
            # 准备数据
            data = self.prepare_data(data)
            
            # 转换数据类型
            doc = self._convert_to_mongo(data)
            
            # 保存数据
            result = await self.collection.insert_one(doc)
            return bool(result.inserted_id)
            
        except Exception as e:
            self.logger.error(f"保存数据失败: {str(e)}")
            return False
            
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """获取数据"""
        try:
            doc = await self.collection.find_one({'id': id})
            if doc:
                return self._convert_from_mongo(doc)
            return None
            
        except Exception as e:
            self.logger.error(f"获取数据失败: {str(e)}")
            return None
            
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新数据"""
        try:
            # 获取原数据
            old_data = await self.get(id)
            if not old_data:
                return False
                
            # 合并数据
            new_data = old_data.copy()
            new_data.update(data)
            new_data['updated_at'] = datetime.now()
            new_data['version'] += 1
            
            # 转换数据类型
            doc = self._convert_to_mongo(new_data)
            
            # 更新数据
            result = await self.collection.replace_one(
                {'id': id},
                doc
            )
            return result.modified_count > 0
            
        except Exception as e:
            self.logger.error(f"更新数据失败: {str(e)}")
            return False
            
    async def delete(self, id: str) -> bool:
        """删除数据"""
        try:
            result = await self.collection.delete_one({'id': id})
            return result.deleted_count > 0
            
        except Exception as e:
            self.logger.error(f"删除数据失败: {str(e)}")
            return False
            
    async def list(self, filter: Dict[str, Any] = None,
                  sort: List[tuple] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """列出数据"""
        try:
            # 构建查询
            query = filter or {}
            
            # 构建排序
            sort_list = []
            if sort:
                for field, order in sort:
                    sort_list.append((field, 1 if order == 'ASC' else -1))
                    
            # 执行查询
            cursor = self.collection.find(query)
            
            # 添加排序
            if sort_list:
                cursor = cursor.sort(sort_list)
                
            # 添加分页
            cursor = cursor.skip(offset).limit(limit)
            
            # 获取结果
            docs = await cursor.to_list(length=limit)
            
            # 转换数据
            return [self._convert_from_mongo(doc) for doc in docs]
            
        except Exception as e:
            self.logger.error(f"列出数据失败: {str(e)}")
            return []
            
    def _convert_to_mongo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """转换数据为MongoDB格式
        
        - 处理ObjectId
        - 处理日期时间
        - 处理特殊类型
        """
        doc = data.copy()
        
        # 转换日期时间
        for key in ['created_at', 'updated_at']:
            if key in doc and isinstance(doc[key], datetime):
                doc[key] = doc[key]
                
        return doc
        
    def _convert_from_mongo(self, doc: Dict[str, Any]) -> Dict[str, Any]:
        """转换MongoDB数据为Python格式
        
        - 处理ObjectId
        - 处理日期时间
        - 处理特殊类型
        """
        data = doc.copy()
        
        # 删除MongoDB ID
        if '_id' in data:
            del data['_id']
            
        return data
        
    async def count(self, filter: Dict[str, Any] = None) -> int:
        """统计数据数量"""
        try:
            return await self.collection.count_documents(filter or {})
        except Exception as e:
            self.logger.error(f"统计数据失败: {str(e)}")
            return 0
            
    async def aggregate(self, pipeline: List[Dict]) -> List[Dict[str, Any]]:
        """聚合查询
        
        Args:
            pipeline: 聚合管道
            
        Returns:
            聚合结果
        """
        try:
            cursor = self.collection.aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            self.logger.error(f"聚合查询失败: {str(e)}")
            return []
            
    async def distinct(self, field: str, filter: Dict[str, Any] = None) -> List:
        """获取不同值
        
        Args:
            field: 字段名
            filter: 过滤条件
            
        Returns:
            不同值列表
        """
        try:
            return await self.collection.distinct(field, filter or {})
        except Exception as e:
            self.logger.error(f"获取不同值失败: {str(e)}")
            return [] 