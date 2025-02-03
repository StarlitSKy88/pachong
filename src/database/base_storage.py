"""数据存储基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import hashlib
from loguru import logger

class BaseStorage(ABC):
    """数据存储基类"""
    
    def __init__(self):
        """初始化存储"""
        self.logger = logger.bind(name=self.__class__.__name__)
        
    @abstractmethod
    async def save(self, data: Dict[str, Any]) -> bool:
        """保存数据
        
        Args:
            data: 数据字典
            
        Returns:
            是否保存成功
        """
        pass
        
    @abstractmethod
    async def get(self, id: str) -> Optional[Dict[str, Any]]:
        """获取数据
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典
        """
        pass
        
    @abstractmethod
    async def update(self, id: str, data: Dict[str, Any]) -> bool:
        """更新数据
        
        Args:
            id: 数据ID
            data: 新数据
            
        Returns:
            是否更新成功
        """
        pass
        
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """删除数据
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        pass
        
    @abstractmethod
    async def list(self, filter: Dict[str, Any] = None, 
                  sort: List[tuple] = None,
                  limit: int = 100,
                  offset: int = 0) -> List[Dict[str, Any]]:
        """列出数据
        
        Args:
            filter: 过滤条件
            sort: 排序条件 [(field, order)]
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            数据列表
        """
        pass
        
    def generate_id(self, data: Dict[str, Any]) -> str:
        """生成数据ID
        
        Args:
            data: 数据字典
            
        Returns:
            数据ID
        """
        # 使用数据内容生成唯一ID
        content = json.dumps(data, sort_keys=True)
        return hashlib.md5(content.encode()).hexdigest()
        
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """验证数据
        
        Args:
            data: 数据字典
            
        Returns:
            是否验证通过
        """
        # 检查必要字段
        required_fields = ['id', 'content', 'source', 'created_at']
        for field in required_fields:
            if field not in data:
                self.logger.error(f"数据缺少必要字段: {field}")
                return False
                
        # 检查字段类型
        if not isinstance(data['created_at'], datetime):
            self.logger.error("created_at 必须是 datetime 类型")
            return False
            
        return True
        
    def prepare_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """准备数据
        
        - 添加元数据
        - 生成ID
        - 添加时间戳
        
        Args:
            data: 原始数据
            
        Returns:
            处理后的数据
        """
        # 复制数据避免修改原始数据
        new_data = data.copy()
        
        # 添加元数据
        new_data.update({
            'id': self.generate_id(data),
            'created_at': datetime.now(),
            'updated_at': datetime.now(),
            'version': 1
        })
        
        return new_data
        
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> bool:
        """批量保存数据
        
        Args:
            data_list: 数据列表
            
        Returns:
            是否全部保存成功
        """
        success = True
        for data in data_list:
            if not await self.save(data):
                success = False
                
        return success
        
    async def exists(self, id: str) -> bool:
        """检查数据是否存在
        
        Args:
            id: 数据ID
            
        Returns:
            是否存在
        """
        return await self.get(id) is not None
        
    async def count(self, filter: Dict[str, Any] = None) -> int:
        """统计数据数量
        
        Args:
            filter: 过滤条件
            
        Returns:
            数据数量
        """
        data = await self.list(filter=filter)
        return len(data)
        
    async def clear(self) -> bool:
        """清空所有数据
        
        Returns:
            是否清空成功
        """
        try:
            data = await self.list()
            for item in data:
                await self.delete(item['id'])
            return True
        except Exception as e:
            self.logger.error(f"清空数据失败: {str(e)}")
            return False 