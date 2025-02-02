"""小红书爬虫测试"""
import string
from datetime import datetime
from unittest.mock import patch, AsyncMock, MagicMock

import pytest

from src.crawlers.xiaohongshu.crawler import XiaoHongShuCrawler
from src.crawlers.xiaohongshu.sign import XHSSign
from src.models.content import Content

@pytest.mark.asyncio
async def test_sign_generator():
    """测试签名生成器"""
    print("\nTesting Sign Generator...")
    sign_generator = XHSSign()

    # 测试搜索签名
    search_params = sign_generator.generate_search_sign('Python编程')
    print("\nSearch Params:")
    print(search_params)

    # 验证签名格式
    assert 'sign' in search_params
    assert len(search_params['sign']) == 32  # MD5长度
    assert all(c in string.hexdigits for c in search_params['sign'])  # 十六进制字符

    # 验证必要参数
    required_params = ['keyword', 'page', 'page_size', 'device_id', 'timestamp', 'nonce']
    for param in required_params:
        assert param in search_params

    # 测试笔记签名
    note_params = sign_generator.generate_note_sign('64a123b5000000001f00a2e1')
    print("\nNote Params:")
    print(note_params)

    # 验证签名
    assert sign_generator.verify_sign(
        {k: v for k, v in note_params.items() if k != 'sign'},
        note_params['sign']
    )

@pytest.mark.asyncio
async def test_search(crawler):
    """测试搜索功能"""
    # 模拟搜索响应
    mock_search_response = {
        "success": True,
        "data": {
            "notes": [
                {
                    "id": "note1",
                    "title": "测试笔记1",
                    "type": "normal"
                },
                {
                    "id": "note2",
                    "title": "测试笔记2",
                    "type": "normal"
                }
            ]
        }
    }

    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value=mock_search_response)
        mock_request.return_value.__aenter__.return_value = mock_response

        results = await crawler.search("测试", page=1, page_size=2)
        assert len(results) == 2

@pytest.mark.asyncio
async def test_get_detail(crawler, mock_response):
    """测试获取详情"""
    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_request.return_value.__aenter__.return_value = mock_resp

        detail = await crawler.get_detail("note1")
        assert detail is not None
        assert detail["id"] == "note1"

@pytest.mark.asyncio
async def test_parse(crawler, mock_response):
    """测试解析数据"""
    data = {
        "id": "note1",
        "title": "测试笔记1",
        "content": "测试内容1",
        "user": {
            "nickname": "测试用户1",
            "avatar": "avatar1.jpg",
            "id": "user1"
        },
        "time": "2024-03-27T12:00:00",
        "stats": {
            "likes": 100,
            "comments": 50,
            "shares": 20,
            "collects": 30
        },
        "images": ["image1.jpg"],
        "video": "video1.mp4"
    }
    content = crawler.parse(data)
    assert isinstance(content, Content)
    assert content.title == "测试笔记1"
    assert content.author_name == "测试用户1"

@pytest.mark.asyncio
async def test_parse_error_handling(crawler):
    """测试解析错误处理"""
    # 测试解析空数据
    with pytest.raises(KeyError):
        crawler.parse({})

@pytest.mark.asyncio
async def test_crawl(crawler, mock_response):
    """测试批量爬取"""
    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(side_effect=[
            {  # 搜索响应
                "success": True,
                "data": {
                    "notes": [
                        {"id": "note1", "type": "normal"},
                        {"id": "note2", "type": "normal"}
                    ]
                }
            },
            mock_response,  # 第一个笔记详情
            mock_response   # 第二个笔记详情
        ])
        mock_request.return_value.__aenter__.return_value = mock_resp

        results = await crawler.crawl(["测试"], max_pages=1)
        assert len(results) == 2

@pytest.mark.asyncio
async def test_error_handling(crawler):
    """测试错误处理"""
    # 测试搜索错误
    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("网络错误")
        results = await crawler.search("测试")
        assert len(results) == 0

    # 测试获取详情错误
    with patch('aiohttp.ClientSession.request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("网络错误")
        detail = await crawler.get_detail("note1")
        assert detail is None

class TestXiaoHongShuCrawler:
    """小红书爬虫测试类"""

    @pytest.mark.asyncio
    async def test_search(self, crawler, mock_search_response):
        """测试搜索功能"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = mock_search_response

            notes = await crawler.search("测试")
            assert len(notes) == 2
            assert notes[0]["id"] == "note1"

    @pytest.mark.asyncio
    async def test_get_detail(self, crawler, mock_detail_response):
        """测试获取详情"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.return_value = mock_detail_response

            data = await crawler.get_detail("note1")
            assert isinstance(data, dict)
            assert data["id"] == "note1"

    @pytest.mark.asyncio
    async def test_parse(self, crawler, mock_detail_response):
        """测试解析数据"""
        data = {
            "id": "note1",
            "title": "测试笔记1",
            "content": "测试内容1",
            "user": {
                "nickname": "测试用户1",
                "avatar": "avatar1.jpg",
                "id": "user1"
            },
            "time": "2024-03-27T12:00:00",
            "stats": {
                "likes": 100,
                "comments": 50,
                "shares": 20,
                "collects": 30
            },
            "images": ["image1.jpg"],
            "video": "video1.mp4"
        }
        content = crawler.parse(data)
        assert isinstance(content, Content)
        assert content.title == "测试笔记1"
        assert content.author_name == "测试用户1"

    @pytest.mark.asyncio
    async def test_crawl(self, crawler, mock_search_response, mock_detail_response):
        """测试批量爬取"""
        with patch.object(crawler, '_make_request') as mock_request:
            mock_request.side_effect = [
                mock_search_response,
                mock_detail_response,
                mock_detail_response
            ]

            results = await crawler.crawl(["测试"], max_pages=1)
            assert len(results) == 2
            assert all(isinstance(content, Content) for content in results) 