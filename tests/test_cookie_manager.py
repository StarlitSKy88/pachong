import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from src.crawlers.cookie_manager import CookieManager

@pytest.fixture
async def cookie_manager():
    """创建CookieManager实例"""
    manager = CookieManager()
    await manager.init()
    yield manager
    await manager.close()

@pytest.fixture
def mock_cookie():
    """创建测试用Cookie"""
    return {
        'user_id': '12345',
        'session': 'test_session',
        'token': 'test_token'
    }

@pytest.mark.asyncio
async def test_cookie_lifecycle(cookie_manager, mock_cookie):
    """测试Cookie生命周期管理"""
    # 添加Cookie
    cookie_manager.add_cookie('xhs', mock_cookie.copy())
    assert len(cookie_manager.cookies['xhs']) == 1
    
    # 验证Cookie状态
    cookie = cookie_manager.cookies['xhs'][0]
    assert cookie['is_valid'] is True
    assert cookie['fail_count'] == 0
    assert cookie['success_count'] == 0
    assert cookie['total_count'] == 0
    
    # 测试成功状态标记
    cookie_manager.mark_cookie_status('xhs', cookie, True)
    assert cookie['success_count'] == 1
    assert cookie['fail_count'] == 0
    
    # 测试失败状态标记
    for _ in range(cookie_manager.max_fail_count):
        cookie_manager.mark_cookie_status('xhs', cookie, False)
    
    assert cookie['is_valid'] is False
    assert cookie['fail_count'] == cookie_manager.max_fail_count

@pytest.mark.asyncio
async def test_cookie_selection(cookie_manager):
    """测试Cookie选择策略"""
    # 添加多个Cookie
    cookies = [
        {'id': '1', 'success_count': 80, 'total_count': 100},
        {'id': '2', 'success_count': 60, 'total_count': 100},
        {'id': '3', 'success_count': 40, 'total_count': 100},
    ]
    
    for cookie in cookies:
        cookie_manager.add_cookie('xhs', cookie)
    
    # 获取Cookie多次，验证选择偏好
    selected_counts = {'1': 0, '2': 0, '3': 0}
    for _ in range(1000):
        cookie = cookie_manager.get_cookie('xhs')
        selected_counts[cookie['id']] += 1
    
    # 验证成功率高的Cookie被选中的概率更高
    assert selected_counts['1'] > selected_counts['2'] > selected_counts['3']

@pytest.mark.asyncio
async def test_cookie_validation(cookie_manager, mock_cookie):
    """测试Cookie有效性检测"""
    with patch('aiohttp.ClientSession') as mock_session:
        # 模拟小红书Cookie检测
        mock_response = Mock()
        mock_response.status = 200
        mock_response.text = asyncio.Future()
        mock_response.text.set_result('用户主页内容')
        
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response
        
        # 添加Cookie并检测
        cookie_manager.add_cookie('xhs', mock_cookie)
        is_valid = await cookie_manager.check_cookie('xhs', mock_cookie)
        assert is_valid is True
        
        # 模拟失效的Cookie
        mock_response.status = 403
        is_valid = await cookie_manager.check_cookie('xhs', mock_cookie)
        assert is_valid is False

@pytest.mark.asyncio
async def test_cookie_auto_update(cookie_manager):
    """测试Cookie自动更新"""
    # 模拟Cookie生成器
    async def mock_generate_cookie(platform):
        return {'id': f'new_{platform}', 'token': 'new_token'}
    
    cookie_manager.generator_manager.generate_cookie = mock_generate_cookie
    
    # 触发自动更新
    await cookie_manager.update_cookies()
    
    # 验证是否生成了新的Cookie
    assert len(cookie_manager.cookies['xhs']) > 0
    assert len(cookie_manager.cookies['bilibili']) > 0

@pytest.mark.asyncio
async def test_cookie_cleanup(cookie_manager):
    """测试Cookie清理机制"""
    # 添加有效和无效的Cookie
    valid_cookie = {'id': 'valid', 'token': 'valid_token'}
    invalid_cookie = {'id': 'invalid', 'token': 'invalid_token'}
    
    cookie_manager.add_cookie('xhs', valid_cookie)
    cookie_manager.add_cookie('xhs', invalid_cookie)
    
    # 标记无效Cookie
    cookie = cookie_manager.cookies['xhs'][1]
    for _ in range(cookie_manager.max_fail_count):
        cookie_manager.mark_cookie_status('xhs', cookie, False)
    
    # 清理无效Cookie
    cookie_manager.remove_invalid_cookies()
    
    # 验证结果
    assert len(cookie_manager.cookies['xhs']) == 1
    assert cookie_manager.cookies['xhs'][0]['id'] == 'valid'

@pytest.mark.asyncio
async def test_cookie_stats(cookie_manager):
    """测试Cookie统计信息"""
    # 添加测试数据
    cookies = [
        {'id': '1', 'success_count': 80, 'total_count': 100},
        {'id': '2', 'success_count': 60, 'total_count': 100},
        {'id': '3', 'success_count': 0, 'total_count': 0},
    ]
    
    for cookie in cookies:
        cookie_manager.add_cookie('xhs', cookie)
    
    # 获取统计信息
    stats = cookie_manager.get_stats()
    
    # 验证统计结果
    assert 'xhs' in stats
    assert stats['xhs']['total'] == 3
    assert stats['xhs']['valid'] == 3
    assert stats['xhs']['active'] == 3
    assert 0.6 < stats['xhs']['success_rate'] < 0.8  # (80+60)/(100+100) = 0.7

@pytest.mark.asyncio
async def test_error_handling(cookie_manager):
    """测试错误处理机制"""
    # 测试不支持的平台
    with pytest.raises(ValueError):
        cookie_manager.add_cookie('unsupported', {})
    
    # 测试Cookie检查异常
    with patch('aiohttp.ClientSession') as mock_session:
        mock_session.return_value.__aenter__.return_value.get.side_effect = Exception('Network error')
        
        is_valid = await cookie_manager.check_cookie('xhs', {'token': 'test'})
        assert is_valid is False

@pytest.mark.asyncio
async def test_cookie_check_loop(cookie_manager):
    """测试Cookie检查循环"""
    # 添加测试Cookie
    cookie_manager.add_cookie('xhs', {'id': 'test', 'token': 'test'})
    
    # 修改检查间隔为测试用
    cookie_manager.check_interval = 1
    
    # 启动检查循环
    check_task = asyncio.create_task(cookie_manager._cookie_check_loop())
    
    # 等待一段时间让循环执行
    await asyncio.sleep(2)
    
    # 取消任务
    check_task.cancel()
    try:
        await check_task
    except asyncio.CancelledError:
        pass
    
    # 验证Cookie已被检查
    cookie = cookie_manager.cookies['xhs'][0]
    assert 'last_check_time' in cookie 