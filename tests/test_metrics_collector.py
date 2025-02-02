import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from src.monitor.metrics_collector import MetricsCollector, Metric

@pytest.fixture
async def metrics_collector():
    """创建MetricsCollector实例"""
    collector = MetricsCollector()
    yield collector

@pytest.mark.asyncio
async def test_system_metrics(metrics_collector):
    """测试系统指标收集"""
    await metrics_collector.collect_system_metrics()
    
    # 验证基本指标存在
    assert 'system.cpu.usage' in metrics_collector.metrics
    assert 'system.memory.percent' in metrics_collector.metrics
    assert 'system.disk.percent' in metrics_collector.metrics
    
    # 验证指标格式
    cpu_metric = metrics_collector.metrics['system.cpu.usage']
    assert isinstance(cpu_metric, Metric)
    assert isinstance(cpu_metric.value, (int, float))
    assert cpu_metric.unit == '%'
    assert isinstance(cpu_metric.timestamp, datetime)

@pytest.mark.asyncio
async def test_crawler_metrics(metrics_collector):
    """测试爬虫指标收集"""
    # 模拟数据访问对象
    with patch('src.database.content_dao') as mock_content_dao, \
         patch('src.database.task_log_dao') as mock_task_log_dao, \
         patch('src.database.error_log_dao') as mock_error_log_dao:
        
        # 设置模拟返回值
        mock_content_dao.count_by_platform = AsyncMock(return_value=100)
        mock_content_dao.count_by_platform_and_time_range = AsyncMock(return_value=24)
        mock_task_log_dao.get_task_logs = AsyncMock(return_value=[
            Mock(status='success'),
            Mock(status='success'),
            Mock(status='failed')
        ])
        mock_error_log_dao.get_error_logs = AsyncMock(return_value=[
            Mock(error_type='network'),
            Mock(error_type='parse')
        ])
        
        # 收集指标
        await metrics_collector.collect_crawler_metrics()
        
        # 验证指标
        for platform in ['xhs', 'bilibili']:
            assert f'crawler.{platform}.content.total' in metrics_collector.metrics
            assert f'crawler.{platform}.content.recent' in metrics_collector.metrics
            assert f'crawler.{platform}.content.rate' in metrics_collector.metrics
            assert f'crawler.{platform}.error.count' in metrics_collector.metrics
            
            # 验证内容统计
            total_metric = metrics_collector.metrics[f'crawler.{platform}.content.total']
            assert total_metric.value == 100
            assert total_metric.unit == '条'
            
            # 验证错误统计
            error_metric = metrics_collector.metrics[f'crawler.{platform}.error.count']
            assert error_metric.value == 2
            assert error_metric.unit == '次'

@pytest.mark.asyncio
async def test_proxy_metrics(metrics_collector):
    """测试代理池指标收集"""
    # 模拟代理管理器
    mock_proxy = Mock(
        is_valid=True,
        fail_count=0,
        total_count=100,
        success_count=80,
        avg_latency=200
    )
    metrics_collector.proxy_manager.proxies = [mock_proxy]
    metrics_collector.proxy_manager.update_count = 10
    metrics_collector.proxy_manager.last_update_time = datetime.now()
    
    # 收集指标
    await metrics_collector.collect_proxy_metrics()
    
    # 验证指标
    assert metrics_collector.metrics['proxy.total_count'].value == 1
    assert metrics_collector.metrics['proxy.available_count'].value == 1
    assert metrics_collector.metrics['proxy.success_rate'].value == 80
    assert metrics_collector.metrics['proxy.avg_latency'].value == 200
    assert metrics_collector.metrics['proxy.update_count'].value == 10

@pytest.mark.asyncio
async def test_cookie_metrics(metrics_collector):
    """测试Cookie池指标收集"""
    # 模拟Cookie管理器
    mock_cookie = {
        'is_valid': True,
        'fail_count': 0,
        'total_count': 100,
        'success_count': 90,
        'add_time': datetime.now() - timedelta(hours=12)
    }
    metrics_collector.cookie_manager.cookies = {
        'xhs': [mock_cookie],
        'bilibili': [mock_cookie]
    }
    metrics_collector.cookie_manager.update_count = {'xhs': 5, 'bilibili': 5}
    metrics_collector.cookie_manager.last_update_time = {
        'xhs': datetime.now(),
        'bilibili': datetime.now()
    }
    
    # 收集指标
    await metrics_collector.collect_cookie_metrics()
    
    # 验证指标
    for platform in ['xhs', 'bilibili']:
        assert metrics_collector.metrics[f'cookie.{platform}.total_count'].value == 1
        assert metrics_collector.metrics[f'cookie.{platform}.valid_count'].value == 1
        assert metrics_collector.metrics[f'cookie.{platform}.success_rate'].value == 90
        assert metrics_collector.metrics[f'cookie.{platform}.update_count'].value == 5

@pytest.mark.asyncio
async def test_request_metrics(metrics_collector):
    """测试请求统计指标收集"""
    # 模拟请求日志
    mock_requests = [
        Mock(status_code=200, latency=100, is_throttled=False, retry_count=0),
        Mock(status_code=200, latency=150, is_throttled=False, retry_count=0),
        Mock(status_code=403, latency=200, is_throttled=True, retry_count=2),
        Mock(status_code=500, latency=300, is_throttled=False, retry_count=1)
    ]
    
    with patch('src.database.request_log_dao') as mock_request_log_dao:
        mock_request_log_dao.get_request_logs = AsyncMock(return_value=mock_requests)
        
        # 收集指标
        await metrics_collector.collect_request_metrics()
        
        # 验证指标
        for platform in ['xhs', 'bilibili']:
            assert metrics_collector.metrics[f'request.{platform}.total'].value == 4
            assert metrics_collector.metrics[f'request.{platform}.success'].value == 2
            assert metrics_collector.metrics[f'request.{platform}.failed'].value == 2
            assert metrics_collector.metrics[f'request.{platform}.success_rate'].value == 50
            assert metrics_collector.metrics[f'request.{platform}.throttled'].value == 1
            assert metrics_collector.metrics[f'request.{platform}.retry'].value == 2

@pytest.mark.asyncio
async def test_history_metrics(metrics_collector):
    """测试历史数据管理"""
    # 添加测试指标
    metrics_collector.metrics['test.metric'] = Metric(
        value=100,
        timestamp=datetime.now(),
        unit='count',
        description='Test metric'
    )
    
    # 更新历史数据
    metrics_collector._update_history()
    
    # 验证历史数据
    history = metrics_collector.get_history('test.metric', hours=1)
    assert len(history) == 1
    assert history[0][1] == 100

@pytest.mark.asyncio
async def test_metrics_by_prefix(metrics_collector):
    """测试指标前缀过滤"""
    # 添加测试指标
    metrics_collector.metrics.update({
        'test.a': Metric(value=1),
        'test.b': Metric(value=2),
        'other.c': Metric(value=3)
    })
    
    # 获取指定前缀的指标
    test_metrics = metrics_collector.get_metrics_by_prefix('test.')
    assert len(test_metrics) == 2
    assert 'test.a' in test_metrics
    assert 'test.b' in test_metrics
    assert 'other.c' not in test_metrics

@pytest.mark.asyncio
async def test_error_handling(metrics_collector):
    """测试错误处理"""
    # 模拟异常情况
    with patch('psutil.cpu_percent', side_effect=Exception('Test error')):
        # 收集系统指标
        await metrics_collector.collect_system_metrics()
        
        # 验证错误不会导致程序崩溃
        assert 'system.cpu.usage' not in metrics_collector.metrics
        
    # 模拟数据库异常
    with patch('src.database.content_dao.count_by_platform', 
              side_effect=Exception('Database error')):
        # 收集爬虫指标
        await metrics_collector.collect_crawler_metrics()
        
        # 验证错误不会导致程序崩溃
        for platform in ['xhs', 'bilibili']:
            metric = metrics_collector.metrics.get(f'crawler.{platform}.content.total')
            if metric:
                assert metric.value == 0

@pytest.mark.asyncio
async def test_concurrent_collection(metrics_collector):
    """测试并发指标收集"""
    # 模拟耗时操作
    async def slow_operation():
        await asyncio.sleep(0.1)
        return 100
    
    # 替换实际的数据访问方法
    with patch('src.database.content_dao.count_by_platform', 
              new_callable=lambda: AsyncMock(side_effect=slow_operation)):
        # 并发收集所有指标
        start_time = datetime.now()
        await metrics_collector.collect_all_metrics()
        end_time = datetime.now()
        
        # 验证总耗时小于所有操作的累加时间
        assert (end_time - start_time).total_seconds() < 0.5  # 假设有5个0.1秒的操作 