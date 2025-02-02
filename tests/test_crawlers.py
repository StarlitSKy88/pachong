import json
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

from src.crawlers.base import BaseCrawler
from src.crawlers.xiaohongshu.base import XiaohongshuBaseCrawler
from src.crawlers.xiaohongshu.search import XiaohongshuSearchCrawler
from src.crawlers.bilibili.base import BilibiliBaseCrawler
from src.crawlers.bilibili.video import BilibiliVideoCrawler
from src.crawlers.bilibili.article import BilibiliArticleCrawler
from src.crawlers.bilibili.dynamic import BilibiliDynamicCrawler
from src.crawlers.bilibili.search import BilibiliSearchCrawler
from src.models.content import Content
from src.models.platform import Platform
from src.crawlers.xiaohongshu.user import XiaohongshuUserCrawler
from src.crawlers.xiaohongshu.detail import XiaohongshuDetailCrawler
from src.crawlers.xiaohongshu.tag import XiaohongshuTagCrawler

class TestBaseCrawler:
    """测试基础爬虫类"""

    @pytest.mark.asyncio
    async def test_crawler_initialization(self):
        """测试爬虫初始化"""
        crawler = BaseCrawler('test_platform')
        assert crawler.platform == 'test_platform'
        assert crawler.headers is not None
        assert crawler.proxy_manager is not None
        assert crawler.cookie_manager is not None
        assert crawler.rate_limiter is not None

    @pytest.mark.asyncio
    async def test_rate_limit(self):
        """测试请求频率限制"""
        crawler = BaseCrawler('test_platform')
        start_time = time.time()
        
        # 模拟请求成功
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.json.return_value = {'data': 'test'}
            mock_request.return_value.__aenter__.return_value = mock_response
            
            # 连续发送3个请求
            for _ in range(3):
                await crawler.request('https://test.com')
                
            duration = time.time() - start_time
            assert duration >= 2  # 应该至少花费2秒（1秒/请求）

    @pytest.mark.asyncio
    async def test_request_retry(self):
        """测试请求重试"""
        crawler = BaseCrawler('test_platform')
        
        # 模拟请求失败
        with patch('aiohttp.ClientSession.request') as mock_request:
            mock_response = AsyncMock()
            mock_response.status = 500
            mock_request.return_value.__aenter__.return_value = mock_response
            
            result = await crawler.request('https://test.com')
            assert result is None
            assert mock_request.call_count == 3  # 应该重试3次

class TestXiaohongshuCrawler:
    """测试小红书爬虫"""

    @pytest.fixture
    def mock_note_response(self):
        """模拟笔记响应数据"""
        return {
            'code': 0,
            'success': True,
            'data': {
                'note': {
                    'id': '123456',
                    'title': '测试笔记',
                    'desc': '笔记内容',
                    'type': 'normal',
                    'user': {
                        'id': '10086',
                        'nickname': '测试用户',
                        'avatar': 'http://sns-avatar.xhscdn.com/xxx.jpg'
                    },
                    'imageList': [
                        {
                            'url': 'http://sns-img.xhscdn.com/1.jpg',
                            'width': 1080,
                            'height': 1440
                        }
                    ],
                    'video': None,
                    'likes': 500,
                    'collects': 200,
                    'comments': 50,
                    'shares': 30,
                    'time': '2024-01-01T00:00:00.000Z'
                }
            }
        }
    
    @pytest.fixture
    def mock_user_response(self):
        """模拟用户响应数据"""
        return {
            'code': 0,
            'success': True,
            'data': {
                'user': {
                    'id': '10086',
                    'nickname': '测试用户',
                    'avatar': 'http://sns-avatar.xhscdn.com/xxx.jpg',
                    'desc': '用户简介',
                    'gender': 1,
                    'location': '上海',
                    'follows': 100,
                    'fans': 1000,
                    'notes': 50,
                    'collected': 200,
                    'liked': 500
                }
            }
        }
    
    @pytest.fixture
    def mock_search_response(self):
        """模拟搜索响应数据"""
        return {
            'code': 0,
            'success': True,
            'data': {
                'notes': [{
                    'id': '123456',
                    'title': '测试笔记',
                    'desc': '笔记内容',
                    'type': 'normal',
                    'user': {
                        'id': '10086',
                        'nickname': '测试用户',
                        'avatar': 'http://sns-avatar.xhscdn.com/xxx.jpg'
                    },
                    'cover': {
                        'url': 'http://sns-img.xhscdn.com/1.jpg',
                        'width': 1080,
                        'height': 1440
                    },
                    'likes': 500,
                    'collects': 200,
                    'comments': 50,
                    'time': '2024-01-01T00:00:00.000Z'
                }],
                'has_more': False,
                'cursor': ''
            }
        }
    
    @pytest.mark.asyncio
    async def test_note_crawler(self, db_session, sample_platform, mock_note_response):
        """测试笔记爬虫"""
        with patch('src.crawlers.xiaohongshu.detail.XiaohongshuDetailCrawler.request') as mock_request:
            mock_request.return_value = mock_note_response
            
            crawler = XiaohongshuDetailCrawler()
            content = await crawler.crawl_note('123456', platform=sample_platform)
            
            assert isinstance(content, Content)
            assert content.title == '测试笔记'
            assert content.content == '笔记内容'
            assert content.platform_id == sample_platform.id
            assert content.url == 'https://www.xiaohongshu.com/explore/123456'
            assert content.author['name'] == '测试用户'
            assert content.author['id'] == '10086'
            assert len(content.images) == 1
            assert content.images[0] == 'http://sns-img.xhscdn.com/1.jpg'
            assert content.likes == 500
            assert content.collects == 200
            assert content.comments == 50
            assert content.shares == 30
    
    @pytest.mark.asyncio
    async def test_user_crawler(self, db_session, sample_platform, mock_user_response):
        """测试用户爬虫"""
        with patch('src.crawlers.xiaohongshu.user.XiaohongshuUserCrawler.request') as mock_request:
            mock_request.return_value = mock_user_response
            
            crawler = XiaohongshuUserCrawler()
            user_info = await crawler.crawl_user('10086')
            
            assert user_info['id'] == '10086'
            assert user_info['nickname'] == '测试用户'
            assert user_info['avatar'] == 'http://sns-avatar.xhscdn.com/xxx.jpg'
            assert user_info['desc'] == '用户简介'
            assert user_info['gender'] == 1
            assert user_info['location'] == '上海'
            assert user_info['follows'] == 100
            assert user_info['fans'] == 1000
            assert user_info['notes'] == 50
    
    @pytest.mark.asyncio
    async def test_search_crawler(self, db_session, sample_platform, mock_search_response):
        """测试搜索爬虫"""
        with patch('src.crawlers.xiaohongshu.search.XiaohongshuSearchCrawler.request') as mock_request:
            mock_request.return_value = mock_search_response
            
            crawler = XiaohongshuSearchCrawler()
            results = await crawler.search('测试', platform=sample_platform)
            
            assert len(results) == 1
            content = results[0]
            assert isinstance(content, Content)
            assert content.title == '测试笔记'
            assert content.content == '笔记内容'
            assert content.platform_id == sample_platform.id
            assert content.url == 'https://www.xiaohongshu.com/explore/123456'
            assert content.author['name'] == '测试用户'
            assert content.likes == 500
            assert content.collects == 200
            assert content.comments == 50
    
    @pytest.mark.asyncio
    async def test_tag_crawler(self, db_session, sample_platform):
        """测试标签爬虫"""
        mock_data = {
            'code': 0,
            'success': True,
            'data': {
                'topics': [{
                    'id': '123456',
                    'name': '测试标签',
                    'desc': '标签描述',
                    'type': 'normal',
                    'icon': 'http://sns-img.xhscdn.com/tag.jpg',
                    'notes': 1000,
                    'follows': 500
                }],
                'has_more': False,
                'cursor': ''
            }
        }
        
        with patch('src.crawlers.xiaohongshu.tag.XiaohongshuTagCrawler.request') as mock_request:
            mock_request.return_value = mock_data
            
            crawler = XiaohongshuTagCrawler()
            tags = await crawler.crawl_tags('测试')
            
            assert len(tags) == 1
            tag = tags[0]
            assert tag['id'] == '123456'
            assert tag['name'] == '测试标签'
            assert tag['desc'] == '标签描述'
            assert tag['notes'] == 1000
            assert tag['follows'] == 500

class TestBilibiliCrawler:
    """测试B站爬虫"""

    @pytest.fixture
    def mock_response(self):
        """模拟响应数据"""
        return {
            'code': 0,
            'message': '0',
            'ttl': 1,
            'data': {
                'bvid': 'BV1xx411c7mD',
                'aid': 170001,
                'videos': 1,
                'tid': 17,
                'tname': '单机游戏',
                'copyright': 1,
                'pic': 'http://i2.hdslb.com/bfs/archive/xxx.jpg',
                'title': '测试视频',
                'pubdate': 1577808000,
                'ctime': 1577808000,
                'desc': '视频简介',
                'state': 0,
                'duration': 360,
                'rights': {'bp': 0, 'elec': 0, 'download': 0, 'movie': 0, 'pay': 0},
                'owner': {'mid': 10086, 'name': '测试用户', 'face': 'http://i2.hdslb.com/bfs/face/xxx.jpg'},
                'stat': {
                    'aid': 170001,
                    'view': 1000,
                    'danmaku': 100,
                    'reply': 50,
                    'favorite': 200,
                    'coin': 150,
                    'share': 30,
                    'now_rank': 0,
                    'his_rank': 0,
                    'like': 500,
                    'dislike': 0
                },
                'dynamic': '视频动态信息',
                'cid': 170001,
                'dimension': {'width': 1920, 'height': 1080, 'rotate': 0}
            }
        }
    
    @pytest.mark.asyncio
    async def test_video_crawler(self, db_session, sample_platform, mock_response):
        """测试视频爬虫"""
        with patch('src.crawlers.bilibili.video.BilibiliVideoCrawler.request') as mock_request:
            mock_request.return_value = mock_response
            
            crawler = BilibiliVideoCrawler()
            content = await crawler.crawl_video('BV1xx411c7mD', platform=sample_platform)
            
            assert isinstance(content, Content)
            assert content.title == '测试视频'
            assert content.platform_id == sample_platform.id
            assert content.url == 'https://www.bilibili.com/video/BV1xx411c7mD'
            assert content.author['name'] == '测试用户'
            assert content.views == 1000
            assert content.likes == 500
            assert content.comments == 50
            assert content.shares == 30
            assert content.collects == 200
    
    @pytest.mark.asyncio
    async def test_article_crawler(self, db_session, sample_platform):
        """测试专栏爬虫"""
        mock_data = {
            'code': 0,
            'message': '0',
            'ttl': 1,
            'data': {
                'id': 12345,
                'category': {'id': 17, 'name': '知识'},
                'categories': [{'id': 17, 'name': '知识'}],
                'title': '测试专栏',
                'summary': '专栏简介',
                'banner_url': 'http://i0.hdslb.com/bfs/article/xxx.jpg',
                'template_id': 4,
                'state': 0,
                'author': {'mid': 10086, 'name': '测试用户', 'face': 'http://i2.hdslb.com/bfs/face/xxx.jpg'},
                'stats': {'view': 1000, 'favorite': 200, 'like': 500, 'reply': 50, 'share': 30, 'coin': 150},
                'publish_time': 1577808000,
                'ctime': 1577808000,
                'content': '<p>专栏内容</p>'
            }
        }
        
        with patch('src.crawlers.bilibili.article.BilibiliArticleCrawler.request') as mock_request:
            mock_request.return_value = mock_data
            
            crawler = BilibiliArticleCrawler()
            content = await crawler.crawl_article(12345, platform=sample_platform)
            
            assert isinstance(content, Content)
            assert content.title == '测试专栏'
            assert content.platform_id == sample_platform.id
            assert content.url == 'https://www.bilibili.com/read/cv12345'
            assert content.author['name'] == '测试用户'
            assert content.views == 1000
            assert content.likes == 500
            assert content.comments == 50
            assert content.shares == 30
            assert content.collects == 200
    
    @pytest.mark.asyncio
    async def test_dynamic_crawler(self, db_session, sample_platform):
        """测试动态爬虫"""
        mock_data = {
            'code': 0,
            'message': '0',
            'ttl': 1,
            'data': {
                'card': {
                    'desc': {
                        'uid': 10086,
                        'type': 2,
                        'rid': 170001,
                        'acl': 0,
                        'view': 1000,
                        'repost': 30,
                        'comment': 50,
                        'like': 500,
                        'is_liked': 0,
                        'dynamic_id': 123456,
                        'timestamp': 1577808000,
                        'pre_dy_id': 0,
                        'orig_dy_id': 0,
                        'orig_type': 0,
                        'user_profile': {
                            'info': {
                                'uid': 10086,
                                'uname': '测试用户',
                                'face': 'http://i2.hdslb.com/bfs/face/xxx.jpg'
                            }
                        }
                    },
                    'card': json.dumps({
                        'item': {
                            'content': '动态内容',
                            'pictures': [{'img_src': 'http://i0.hdslb.com/bfs/album/xxx.jpg'}]
                        }
                    })
                }
            }
        }
        
        with patch('src.crawlers.bilibili.dynamic.BilibiliDynamicCrawler.request') as mock_request:
            mock_request.return_value = mock_data
            
            crawler = BilibiliDynamicCrawler()
            content = await crawler.crawl_dynamic(123456, platform=sample_platform)
            
            assert isinstance(content, Content)
            assert content.platform_id == sample_platform.id
            assert content.url == 'https://t.bilibili.com/123456'
            assert content.author['name'] == '测试用户'
            assert content.views == 1000
            assert content.likes == 500
            assert content.comments == 50
            assert content.shares == 30
    
    @pytest.mark.asyncio
    async def test_search_crawler(self, db_session, sample_platform):
        """测试搜索爬虫"""
        mock_data = {
            'code': 0,
            'message': '0',
            'ttl': 1,
            'data': {
                'result': [{
                    'type': 'video',
                    'id': 170001,
                    'author': '测试用户',
                    'mid': 10086,
                    'title': '测试视频',
                    'description': '视频简介',
                    'pic': 'http://i2.hdslb.com/bfs/archive/xxx.jpg',
                    'play': 1000,
                    'video_review': 100,
                    'favorites': 200,
                    'review': 50,
                    'pubdate': 1577808000,
                    'duration': '06:00',
                    'bvid': 'BV1xx411c7mD'
                }],
                'page': {
                    'num': 1,
                    'size': 20,
                    'count': 100
                }
            }
        }
        
        with patch('src.crawlers.bilibili.search.BilibiliSearchCrawler.request') as mock_request:
            mock_request.return_value = mock_data
            
            crawler = BilibiliSearchCrawler()
            results = await crawler.search('测试', platform=sample_platform)
            
            assert len(results) == 1
            content = results[0]
            assert isinstance(content, Content)
            assert content.title == '测试视频'
            assert content.platform_id == sample_platform.id
            assert content.url == 'https://www.bilibili.com/video/BV1xx411c7mD'
            assert content.author['name'] == '测试用户'
            assert content.views == 1000
            assert content.collects == 200
            assert content.comments == 50 