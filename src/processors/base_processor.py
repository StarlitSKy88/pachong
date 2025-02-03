"""内容处理器基类"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from datetime import datetime
from loguru import logger

class BaseProcessor(ABC):
    """内容处理器基类"""
    
    def __init__(self):
        """初始化处理器"""
        self.logger = logger.bind(name=self.__class__.__name__)
        
    @abstractmethod
    async def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """处理内容
        
        Args:
            content: 原始内容
            
        Returns:
            处理后的内容
        """
        pass
        
    @abstractmethod
    async def batch_process(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理内容
        
        Args:
            contents: 原始内容列表
            
        Returns:
            处理后的内容列表
        """
        pass
        
    async def validate(self, content: Dict[str, Any]) -> bool:
        """验证内容
        
        Args:
            content: 待验证的内容
            
        Returns:
            是否有效
        """
        return True
        
    async def clean(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """清洗内容
        
        Args:
            content: 待清洗的内容
            
        Returns:
            清洗后的内容
        """
        return content
        
    async def transform(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """转换内容格式
        
        Args:
            content: 待转换的内容
            
        Returns:
            转换后的内容
        """
        return content
        
    async def enrich(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """丰富内容
        
        Args:
            content: 待丰富的内容
            
        Returns:
            丰富后的内容
        """
        return content
        
    def get_stats(self) -> Dict[str, Any]:
        """获取处理器统计信息
        
        Returns:
            统计信息
        """
        return {
            "processed_count": 0,
            "success_count": 0,
            "fail_count": 0,
            "avg_process_time": 0
        } 