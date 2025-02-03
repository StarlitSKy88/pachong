import pytest
import asyncio
from src.utils.proxy_manager import ProxyManager, ProxyAnonymity, ProxyInfo
from src.utils.proxy_providers import ProxyProviderManager
from datetime import datetime, timedelta

@pytest.fixture
def proxy_manager():
    """代理管理器fixture"""
    manager = ProxyManager()
    # 添加一些测试用代理
    manager.proxies = {
        "http://127.0.0.1:8080": ProxyInfo(
            url="http://127.0.0.1:8080",
            score=80,
            is_valid=True,
            response_time=0.1,
            anonymity=ProxyAnonymity.HIGH_ANONYMOUS
        ),
        "http://127.0.0.1:1080": ProxyInfo(
            url="http://127.0.0.1:1080",
            score=70,
            is_valid=True,
            response_time=0.2,
            anonymity=ProxyAnonymity.ANONYMOUS
        ),
        "http://127.0.0.1:7890": ProxyInfo(
            url="http://127.0.0.1:7890",
            score=60,
            is_valid=True,
            response_time=0.3,
            anonymity=ProxyAnonymity.TRANSPARENT
        ),
    }
    # 禁用代理检查
    manager.check_interval = float('inf')
    return manager

@pytest.mark.asyncio
async def test_proxy_provider_manager():
    """测试代理源管理器"""
    manager = ProxyProviderManager()
    proxies = await manager.get_all_proxies()
    
    # 验证获取到代理
    assert len(proxies) > 0
    
    # 验证代理格式
    for proxy in proxies:
        assert proxy.startswith('http://')
        assert ':' in proxy
        
    # 打印统计信息
    print(f"\nTotal proxies: {len(proxies)}")
    print("Sample proxies:")
    for proxy in proxies[:5]:
        print(f"  {proxy}")

@pytest.mark.asyncio
async def test_proxy_manager_get_proxy(proxy_manager):
    """测试获取代理"""
    # 获取代理
    proxy = await proxy_manager.get_proxy()
    
    # 验证代理格式
    assert proxy is not None
    assert proxy.startswith('http://')
    
    print(f"\nGot proxy: {proxy}")
    
    # 获取代理信息
    info = proxy_manager.proxies[proxy]
    assert info is not None
    
    # 打印代理信息
    print(f"Proxy info: {info.to_dict()}")

@pytest.mark.asyncio
async def test_proxy_manager_update_pool(proxy_manager):
    """测试更新代理池"""
    # 验证代理池状态
    stats = proxy_manager.get_stats()
    assert stats['total'] > 0
    assert stats['valid'] > 0
    
    # 打印统计信息
    print("\nProxy pool stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")

@pytest.mark.asyncio
async def test_proxy_manager_report_result(proxy_manager):
    """测试报告代理使用结果"""
    # 获取代理
    proxy = await proxy_manager.get_proxy()
    assert proxy is not None
    
    # 获取初始信息
    info = proxy_manager.proxies[proxy]
    initial_score = info.score
    initial_success_count = info.success_count
    initial_fail_count = info.fail_count
    
    # 报告成功
    await proxy_manager.report_result(proxy, True)
    assert info.success_count == initial_success_count + 1
    assert info.score > initial_score
    
    # 报告失败
    await proxy_manager.report_result(proxy, False)
    assert info.fail_count == initial_fail_count + 1
    assert info.score < initial_score

@pytest.mark.asyncio
async def test_proxy_manager_check_anonymity(proxy_manager):
    """测试检查代理匿名度"""
    # 获取代理
    proxy = await proxy_manager.get_proxy()
    assert proxy is not None
    
    # 获取初始匿名度
    info = proxy_manager.proxies[proxy]
    initial_anonymity = info.anonymity
    
    print(f"\nProxy {proxy} initial anonymity: {initial_anonymity}")
    
    # 检查匿名度
    anonymity = await proxy_manager.check_anonymity(proxy)
    assert anonymity is not None
    
    print(f"Proxy {proxy} checked anonymity: {anonymity}")

@pytest.mark.asyncio
async def test_proxy_manager_concurrent_usage(proxy_manager):
    """测试并发使用代理"""
    # 并发获取多个代理
    tasks = [proxy_manager.get_proxy() for _ in range(10)]
    proxies = await asyncio.gather(*tasks)
    
    # 验证获取到的代理
    valid_proxies = [p for p in proxies if p is not None]
    assert len(valid_proxies) > 0
    
    # 打印统计信息
    print(f"\nGot {len(valid_proxies)} valid proxies out of {len(proxies)} requests")
    
    # 获取代理信息
    for proxy in valid_proxies[:3]:  # 只显示前3个代理
        info = proxy_manager.proxies[proxy]
        print(f"Proxy {proxy}: score={info.score:.1f}, response_time={info.response_time:.3f}s")

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 