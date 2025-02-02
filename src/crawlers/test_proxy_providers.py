import asyncio
import logging
from datetime import datetime
from .proxy_providers import ProxyProviderManager, ZhimaProxyProvider, KuaidailiProxyProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_zhima_provider():
    """测试芝麻代理"""
    print("\nTesting Zhima Provider...")
    provider = ZhimaProxyProvider(
        api_url='http://webapi.zhimaproxy.com/api/getip',
        api_key='your_zhima_api_key'
    )
    
    # 获取代理
    print("\nFetching proxies...")
    proxies = await provider.fetch_proxies()
    print(f"Fetched {len(proxies)} proxies:")
    for proxy in proxies[:5]:  # 只显示前5个
        print(proxy)
    
    # 获取余额
    print("\nChecking balance...")
    balance = await provider.get_balance()
    print(f"Balance: {balance}")

async def test_kuaidaili_provider():
    """测试快代理"""
    print("\nTesting Kuaidaili Provider...")
    provider = KuaidailiProxyProvider(
        api_url='http://dev.kdlapi.com/api/getproxy',
        api_key='your_kuaidaili_api_key'
    )
    
    # 获取代理
    print("\nFetching proxies...")
    proxies = await provider.fetch_proxies()
    print(f"Fetched {len(proxies)} proxies:")
    for proxy in proxies[:5]:  # 只显示前5个
        print(proxy)
    
    # 获取余额
    print("\nChecking balance...")
    balance = await provider.get_balance()
    print(f"Balance: {balance}")

async def test_provider_manager():
    """测试代理服务商管理器"""
    print("\nTesting Provider Manager...")
    manager = ProxyProviderManager()
    
    # 添加服务商
    zhima = ZhimaProxyProvider(
        api_url='http://webapi.zhimaproxy.com/api/getip',
        api_key='your_zhima_api_key'
    )
    manager.add_provider('zhima', zhima)
    
    kuaidaili = KuaidailiProxyProvider(
        api_url='http://dev.kdlapi.com/api/getproxy',
        api_key='your_kuaidaili_api_key'
    )
    manager.add_provider('kuaidaili', kuaidaili)
    
    # 获取所有代理
    print("\nFetching all proxies...")
    proxies = await manager.fetch_all_proxies()
    print(f"Fetched {len(proxies)} proxies in total")
    
    # 检查所有余额
    print("\nChecking all balances...")
    balances = await manager.check_balances()
    for provider, balance in balances.items():
        print(f"{provider}: {balance}")

async def main():
    """主函数"""
    try:
        # 测试芝麻代理
        await test_zhima_provider()
        
        # 测试快代理
        await test_kuaidaili_provider()
        
        # 测试代理管理器
        await test_provider_manager()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 