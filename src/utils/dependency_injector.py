"""依赖注入模块"""

from typing import Dict, Any, Type, TypeVar, Optional, Callable
from .exceptions import ConfigError

T = TypeVar("T")

class DependencyContainer:
    """依赖注入容器类"""
    
    def __init__(self):
        """初始化依赖注入容器"""
        self._instances: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[..., Any]] = {}
        
    def register_instance(self, name: str, instance: Any) -> None:
        """注册实例
        
        Args:
            name: 实例名称
            instance: 实例对象
        """
        self._instances[name] = instance
        
    def register_factory(
        self,
        name: str,
        factory: Callable[..., Any],
        singleton: bool = True
    ) -> None:
        """注册工厂函数
        
        Args:
            name: 工厂名称
            factory: 工厂函数
            singleton: 是否单例
        """
        if singleton and name in self._instances:
            return
            
        self._factories[name] = (factory, singleton)
        
    def get(self, name: str) -> Any:
        """获取实例
        
        Args:
            name: 实例名称
            
        Returns:
            Any: 实例对象
            
        Raises:
            ConfigError: 当实例不存在时
        """
        # 检查是否已有实例
        if name in self._instances:
            return self._instances[name]
            
        # 检查是否有工厂函数
        if name in self._factories:
            factory, singleton = self._factories[name]
            instance = factory()
            
            # 如果是单例，缓存实例
            if singleton:
                self._instances[name] = instance
                
            return instance
            
        raise ConfigError(
            message=f"依赖不存在: {name}",
            config_key=name
        )
        
    def get_typed(self, name: str, expected_type: Type[T]) -> T:
        """获取指定类型的实例
        
        Args:
            name: 实例名称
            expected_type: 期望的类型
            
        Returns:
            T: 实例对象
            
        Raises:
            ConfigError: 当实例不存在或类型不匹配时
        """
        instance = self.get(name)
        
        if not isinstance(instance, expected_type):
            raise ConfigError(
                message=f"类型不匹配: 期望 {expected_type.__name__}，"
                f"实际 {type(instance).__name__}",
                config_key=name
            )
            
        return instance
        
    def clear(self) -> None:
        """清除所有实例和工厂"""
        self._instances.clear()
        self._factories.clear()
        
    def __contains__(self, name: str) -> bool:
        """检查是否包含指定名称的实例或工厂
        
        Args:
            name: 实例名称
            
        Returns:
            bool: 是否存在
        """
        return name in self._instances or name in self._factories
        
    def __getitem__(self, name: str) -> Any:
        """通过下标访问实例
        
        Args:
            name: 实例名称
            
        Returns:
            Any: 实例对象
        """
        return self.get(name)
        
    def __len__(self) -> int:
        """获取实例和工厂总数
        
        Returns:
            int: 总数
        """
        return len(self._instances) + len(self._factories) 