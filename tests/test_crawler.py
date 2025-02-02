"""爬虫测试"""

import pytest
import asyncio
from src.crawlers.base import BaseCrawler
from src.models.content import Content
from src.models.platform import Platform
from typing import Dict, Any, List

class TestCrawler(BaseCrawler):
    """测试爬虫"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化
        
        Args:
            config: 配置
        """
        if 'platform_name' not in config:
            config['platform_name'] = 'test'
        super().__init__(config)
        
    async def search(self, keyword: str) -> List[Content]:
        """搜索
        
        Args:
            keyword: 关键词
            
        Returns:
            List[Content]: 内容列表
        """
        return [
            Content(
                title=f"测试内容 {i}",
                content=f"这是测试内容 {i}",
                url=f"https://example.com/{i}",
                platform=self.platform
            )
            for i in range(3)
        ]
        
    async def get_detail(self, content: Content) -> Content:
        """获取详情
        
        Args:
            content: 内容
            
        Returns:
            Content: 内容
        """
        content.content = f"这是详细内容: {content.title}"
        return content
        
    async def crawl(self, keywords: List[str], time_range: str = '24h',
                   limit: int = 100) -> List[Dict]:
        """爬取内容"""
        results = []
        for keyword in keywords:
            contents = await self.search(keyword)
            for content in contents:
                content = await self.get_detail(content)
                results.append(content.to_dict())
        return results[:limit]
        
    async def parse(self, data: Dict) -> Dict:
        """解析数据"""
        return {
            'title': data.get('title', ''),
            'content': data.get('content', ''),
            'url': data.get('url', ''),
            'author': data.get('author', {}),
            'publish_time': data.get('publish_time')
        }
        
    def extract_tags(self, data: Dict[str, Any]) -> List[str]:
        """提取标签"""
        content = data.get('content', '')
        # 简单的标签提取逻辑
        return [word for word in content.split() if word.startswith('#')]

@pytest.fixture
async def crawler(test_crawler_config, db_session):
    """创建测试爬虫"""
    crawler = TestCrawler(test_crawler_config)
    await crawler.initialize()
    return crawler

@pytest.mark.asyncio
async def test_search(crawler, db_session):
    """测试搜索"""
    _crawler = await crawler
    contents = await _crawler.search("测试")
    assert len(contents) == 3
    for i, content in enumerate(contents):
        assert content.title == f"测试内容 {i}"
        assert content.content == f"这是测试内容 {i}"
        assert content.url == f"https://example.com/{i}"
        assert content.platform.name == "test"
        db_session.add(content)
    db_session.commit()
        
@pytest.mark.asyncio
async def test_get_detail(crawler, db_session):
    """测试获取详情"""
    _crawler = await crawler
    content = Content(
        title="测试内容",
        content="这是测试内容",
        url="https://example.com/test",
        platform=_crawler.platform
    )
    db_session.add(content)
    db_session.commit()
    
    content = await _crawler.get_detail(content)
    assert content.content == "这是详细内容: 测试内容"
    db_session.commit()
    
@pytest.mark.asyncio
async def test_concurrent_search(crawler, db_session):
    """测试并发搜索"""
    _crawler = await crawler
    keywords = ["测试1", "测试2", "测试3"]
    tasks = [_crawler.search(keyword) for keyword in keywords]
    results = await asyncio.gather(*tasks)
    assert len(results) == 3
    for contents in results:
        assert len(contents) == 3
        for content in contents:
            db_session.add(content)
    db_session.commit()
    
@pytest.mark.asyncio
async def test_crawl(crawler, db_session):
    """测试爬取内容"""
    _crawler = await crawler
    keywords = ["测试1", "测试2"]
    results = await _crawler.crawl(keywords, time_range='24h', limit=5)
    assert len(results) == 5
    for result in results:
        assert 'title' in result
        assert 'content' in result
        assert 'url' in result
        
@pytest.mark.asyncio
async def test_parse(crawler):
    """测试解析数据"""
    _crawler = await crawler
    data = {
        'title': '测试标题',
        'content': '测试内容',
        'url': 'https://example.com',
        'author': {'name': '测试作者'},
        'publish_time': '2024-01-01 12:00:00'
    }
    result = await _crawler.parse(data)
    assert result['title'] == '测试标题'
    assert result['content'] == '测试内容'
    assert result['url'] == 'https://example.com'
    assert result['author'] == {'name': '测试作者'}
    assert result['publish_time'] == '2024-01-01 12:00:00'
    
@pytest.mark.asyncio
async def test_extract_tags(crawler):
    """测试提取标签"""
    _crawler = await crawler
    data = {
        'content': '这是一个 #测试 内容 #标签'
    }
    tags = _crawler.extract_tags(data)
    assert len(tags) == 2
    assert '#测试' in tags
    assert '#标签' in tags 