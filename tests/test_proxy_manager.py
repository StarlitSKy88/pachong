import pytest
import asyncio
from src.utils.proxy_manager import ProxyManager, ProxyAnonymity

@pytest.mark.asyncio
async def test_proxy_anonymity():
    """测试代理匿名度检测"""
    manager = ProxyManager()
    
    # 测试代理
    test_proxy = "http://127.0.0.1:8080"
    await manager.add_proxy(test_proxy)
    
    # 检查匿名度
    anonymity = await manager.check_proxy_anonymity(test_proxy)
    assert isinstance(anonymity, ProxyAnonymity)
    
    # 获取代理状态
    status = manager.get_proxy_status(test_proxy)
    assert status is not None
    assert 'anonymity' in status

@pytest.mark.asyncio
async def test_proxy_quality():
    """测试代理质量评估"""
    manager = ProxyManager()
    
    # 添加测试代理
    test_proxies = [
        "http://127.0.0.1:8080",
        "http://127.0.0.1:8081",
        "http://127.0.0.1:8082"
    ]
    
    for proxy in test_proxies:
        await manager.add_proxy(proxy)
    
    # 检查所有代理
    await manager.check_all_proxies()
    
    # 获取代理池统计信息
    stats = manager.get_stats()
    assert 'total' in stats
    assert 'valid' in stats
    assert 'invalid' in stats
    assert 'avg_response_time' in stats
    assert 'avg_success_rate' in stats
    
    # 测试自动清理
    await manager.clean_invalid_proxies()
    assert len(manager.proxies) <= len(test_proxies)

@pytest.mark.asyncio
async def test_proxy_lifecycle():
    """测试代理生命周期管理"""
    manager = ProxyManager()
    
    # 添加代理
    test_proxy = "http://127.0.0.1:8080"
    await manager.add_proxy(test_proxy)
    assert test_proxy in manager.proxies
    
    # 检查代理
    status = manager.proxies[test_proxy]
    assert status.success_count == 0
    assert status.fail_count == 0
    
    # 模拟成功和失败
    for _ in range(3):
        await manager.check_proxy(test_proxy)
    
    # 验证统计信息更新
    status = manager.proxies[test_proxy]
    assert status.success_count + status.fail_count == 3
    
    # 测试连续失败清理
    status.consecutive_failures = manager.max_consecutive_failures
    await manager.clean_invalid_proxies()
    assert test_proxy not in manager.proxies

@pytest.mark.asyncio
async def test_proxy_pool_update():
    """测试代理池更新"""
    manager = ProxyManager()
    
    # 初始状态
    assert len(manager.proxies) == 0
    
    # 更新代理池
    await manager.update_proxy_pool()
    
    # 验证代理池状态
    stats = manager.get_stats()
    print("\nProxy Pool Stats:")
    print(f"Total Proxies: {stats['total']}")
    print(f"Valid Proxies: {stats['valid']}")
    print(f"Invalid Proxies: {stats['invalid']}")
    print(f"High Anonymous: {stats['high_anonymous']}")
    print(f"Anonymous: {stats['anonymous']}")
    print(f"Transparent: {stats['transparent']}")
    print(f"Average Response Time: {stats['avg_response_time']:.2f}s")
    print(f"Average Success Rate: {stats['avg_success_rate']:.2%}")

if __name__ == '__main__':
    pytest.main(['-v', 'test_proxy_manager.py']) 