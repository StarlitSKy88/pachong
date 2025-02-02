"""依赖注入测试模块"""

import pytest
from src.utils.dependency_injector import DependencyContainer
from src.utils.exceptions import ConfigError

class TestService:
    """测试服务类"""
    
    def __init__(self, name: str = "test"):
        self.name = name

@pytest.fixture
def container():
    """依赖注入容器实例"""
    return DependencyContainer()

def test_register_instance(container):
    """测试注册实例"""
    service = TestService()
    container.register_instance("service", service)
    
    assert "service" in container
    assert container.get("service") is service

def test_register_factory(container):
    """测试注册工厂函数"""
    def factory():
        return TestService()
        
    container.register_factory("service", factory)
    
    assert "service" in container
    instance1 = container.get("service")
    instance2 = container.get("service")
    assert isinstance(instance1, TestService)
    assert instance1 is instance2  # 默认是单例

def test_register_factory_non_singleton(container):
    """测试注册非单例工厂函数"""
    def factory():
        return TestService()
        
    container.register_factory("service", factory, singleton=False)
    
    instance1 = container.get("service")
    instance2 = container.get("service")
    assert isinstance(instance1, TestService)
    assert instance1 is not instance2  # 非单例应该返回不同实例

def test_get_not_found(container):
    """测试获取不存在的实例"""
    with pytest.raises(ConfigError) as exc_info:
        container.get("not_exists")
    assert "依赖不存在" in str(exc_info.value)

def test_get_typed(container):
    """测试获取指定类型的实例"""
    service = TestService()
    container.register_instance("service", service)
    
    # 正确的类型
    instance = container.get_typed("service", TestService)
    assert instance is service
    
    # 错误的类型
    with pytest.raises(ConfigError) as exc_info:
        container.get_typed("service", str)
    assert "类型不匹配" in str(exc_info.value)

def test_clear(container):
    """测试清除所有实例和工厂"""
    # 注册一些实例和工厂
    container.register_instance("service1", TestService())
    container.register_factory("service2", lambda: TestService())
    
    assert len(container) == 2
    
    # 清除所有
    container.clear()
    assert len(container) == 0
    assert "service1" not in container
    assert "service2" not in container

def test_contains(container):
    """测试检查实例是否存在"""
    container.register_instance("service1", TestService())
    container.register_factory("service2", lambda: TestService())
    
    assert "service1" in container
    assert "service2" in container
    assert "not_exists" not in container

def test_getitem(container):
    """测试通过下标访问实例"""
    service = TestService()
    container.register_instance("service", service)
    
    assert container["service"] is service
    
    with pytest.raises(ConfigError):
        _ = container["not_exists"]

def test_len(container):
    """测试获取实例和工厂总数"""
    assert len(container) == 0
    
    container.register_instance("service1", TestService())
    assert len(container) == 1
    
    container.register_factory("service2", lambda: TestService())
    assert len(container) == 2

def test_factory_with_dependencies(container):
    """测试带依赖的工厂函数"""
    # 创建依赖
    dep = TestService("dependency")
    container.register_instance("dependency", dep)
    
    # 创建依赖于其他服务的工厂
    def factory():
        dependency = container.get("dependency")
        return TestService(f"service_with_{dependency.name}")
        
    container.register_factory("service", factory)
    
    # 获取服务
    service = container.get("service")
    assert isinstance(service, TestService)
    assert service.name == "service_with_dependency"

def test_register_instance_override(container):
    """测试覆盖注册实例"""
    service1 = TestService("service1")
    service2 = TestService("service2")
    
    container.register_instance("service", service1)
    assert container.get("service") is service1
    
    container.register_instance("service", service2)
    assert container.get("service") is service2

def test_register_factory_with_existing_instance(container):
    """测试对已有实例注册工厂"""
    service = TestService()
    container.register_instance("service", service)
    
    # 尝试注册工厂
    container.register_factory("service", lambda: TestService())
    
    # 应该返回原有实例
    assert container.get("service") is service 