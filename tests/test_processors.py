import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.processors.analyzer import ContentAnalyzer, content_analyzer
from src.processors.generator import ContentGenerator, content_generator
from src.processors.xiaohongshu_processor import XiaoHongShuProcessor

class TestContentAnalyzer:
    """内容分析器测试"""
    
    @pytest.mark.asyncio
    async def test_analyze_content(self, sample_content, mock_llm_response):
        """测试内容分析"""
        with patch('src.processors.analyzer.query_llm') as mock_query:
            mock_query.side_effect = [
                str(mock_llm_response['quality_assessment']),
                str(mock_llm_response['topic_analysis']),
                str(mock_llm_response['relevance_assessment'])
            ]
            
            analyzer = content_analyzer
            result = await analyzer.analyze_content(sample_content)
            
            assert result is not None
            assert 'quality' in result
            assert 'topic' in result
            assert 'relevance' in result
            assert mock_query.call_count == 3
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, sample_content, mock_llm_response):
        """测试质量评估"""
        with patch('src.processors.analyzer.query_llm') as mock_query:
            mock_query.return_value = str(mock_llm_response['quality_assessment'])
            
            analyzer = content_analyzer
            result = await analyzer._assess_quality(sample_content)
            
            assert result is not None
            assert result['score'] == mock_llm_response['quality_assessment']['score']
            assert 'dimensions' in result
            assert 'comments' in result
            assert 'suggestions' in result
    
    @pytest.mark.asyncio
    async def test_topic_analysis(self, sample_content, mock_llm_response):
        """测试主题分析"""
        with patch('src.processors.analyzer.query_llm') as mock_query:
            mock_query.return_value = str(mock_llm_response['topic_analysis'])
            
            analyzer = content_analyzer
            result = await analyzer._analyze_topic(sample_content)
            
            assert result is not None
            assert 'topics' in result
            assert 'keywords' in result
            assert 'entities' in result
            assert 'summary' in result
    
    @pytest.mark.asyncio
    async def test_relevance_assessment(self, sample_content, mock_llm_response):
        """测试相关性评估"""
        with patch('src.processors.analyzer.query_llm') as mock_query:
            mock_query.return_value = str(mock_llm_response['relevance_assessment'])
            
            analyzer = content_analyzer
            result = await analyzer._assess_relevance(sample_content)
            
            assert result is not None
            assert 'score' in result
            assert 'explanation' in result
            assert 'key_matches' in result

class TestContentGenerator:
    """内容生成器测试"""
    
    @pytest.mark.asyncio
    async def test_generate_xiaohongshu(self, sample_content, mock_llm_response):
        """测试生成小红书内容"""
        with patch('src.processors.generator.query_llm') as mock_query:
            mock_query.return_value = str(mock_llm_response['xiaohongshu_generation'])
            
            generator = content_generator
            result = await generator.generate_content(
                content=sample_content,
                content_type='xiaohongshu'
            )
            
            assert result is not None
            assert result.title == mock_llm_response['xiaohongshu_generation']['title']
            assert result.content == mock_llm_response['xiaohongshu_generation']['content']
            assert 'image_suggestions' in result.format_config
            assert 'tags' in result.format_config
    
    @pytest.mark.asyncio
    async def test_generate_podcast(self, sample_content, mock_llm_response):
        """测试生成播客内容"""
        with patch('src.processors.generator.query_llm') as mock_query:
            mock_query.return_value = str({
                'title': 'Test Podcast',
                'script': 'Hello everyone...',
                'duration': '180',
                'segments': [
                    {
                        'type': 'speech',
                        'content': 'Introduction...',
                        'duration': '30'
                    }
                ],
                'background_music': 'Soft piano'
            })
            
            generator = content_generator
            result = await generator.generate_content(
                content=sample_content,
                content_type='podcast'
            )
            
            assert result is not None
            assert result.title == 'Test Podcast'
            assert result.content == 'Hello everyone...'
            assert 'segments' in result.format_config
            assert 'background_music' in result.format_config
            assert result.format_config['duration'] == '180'
    
    @pytest.mark.asyncio
    async def test_generate_html(self, sample_content, mock_llm_response):
        """测试生成HTML内容"""
        with patch('src.processors.generator.query_llm') as mock_query:
            mock_query.return_value = str({
                'title': 'Test Article',
                'meta_description': 'This is a test article',
                'html_content': '<html>...</html>',
                'css_styles': 'body { ... }',
                'image_layout': [
                    {
                        'position': 'header',
                        'size': 'full-width',
                        'style': 'cover'
                    }
                ]
            })
            
            with patch('src.processors.generator.take_screenshot_sync') as mock_screenshot:
                mock_screenshot.return_value = 'preview.png'
                
                generator = content_generator
                result = await generator.generate_content(
                    content=sample_content,
                    content_type='html'
                )
                
                assert result is not None
                assert result.title == 'Test Article'
                assert result.content.startswith('<html>')
                assert 'meta_description' in result.format_config
                assert 'css_styles' in result.format_config
                assert 'image_layout' in result.format_config
                assert result.images == ['preview.png']
    
    @pytest.mark.asyncio
    async def test_generation_retry(self, sample_content):
        """测试生成重试"""
        with patch('src.processors.generator.query_llm') as mock_query:
            # 前两次失败，第三次成功
            mock_query.side_effect = [
                Exception("Generation failed"),
                Exception("Generation failed"),
                str({
                    'title': 'Test Content',
                    'content': 'Hello...',
                    'image_suggestions': [],
                    'tags': []
                })
            ]
            
            generator = content_generator
            generator.max_retries = 3
            
            result = await generator.generate_content(
                content=sample_content,
                content_type='xiaohongshu'
            )
            
            assert result is not None
            assert result.title == 'Test Content'
            assert mock_query.call_count == 3 

@pytest.fixture
def processor():
    """处理器fixture"""
    return XiaoHongShuProcessor()

@pytest.fixture
def sample_content():
    """示例内容fixture"""
    return {
        "id": "test_note_1",
        "title": "测试笔记 #美食 #旅行",
        "content": "<p>这是一篇测试笔记的内容 #美食 #生活 #分享</p>",
        "images": [
            "  https://example.com/image1.jpg  ",
            "https://example.com/image2.jpg",
            "",
            "  https://example.com/image3.jpg  "
        ],
        "created_at": datetime.now(),
        "stats": {
            "likes": "100",
            "comments": "20",
            "shares": "5",
            "collects": "10"
        }
    }

@pytest.mark.asyncio
async def test_process_content(processor, sample_content):
    """测试内容处理"""
    # 处理内容
    result = await processor.process(sample_content)
    
    # 验证基本字段
    assert result["id"] == sample_content["id"]
    assert "#美食" not in result["title"]
    assert "<p>" not in result["content"]
    assert len(result["images"]) == 3
    assert all(url.strip() == url for url in result["images"])
    
    # 验证统计数据
    assert isinstance(result["stats"]["likes"], int)
    assert isinstance(result["stats"]["comments"], int)
    assert isinstance(result["stats"]["shares"], int)
    assert isinstance(result["stats"]["collects"], int)
    
    # 验证标签
    assert "美食" in result["tags"]
    assert "旅行" in result["tags"]
    assert "生活" in result["tags"]
    assert "分享" in result["tags"]
    
    # 验证类型
    assert result["type"] == "gallery"
    
    # 验证处理时间
    assert "processed_at" in result

@pytest.mark.asyncio
async def test_validate_content(processor, sample_content):
    """测试内容验证"""
    # 验证完整内容
    assert await processor.validate(sample_content)
    
    # 验证缺失字段
    invalid_content = sample_content.copy()
    del invalid_content["title"]
    assert not await processor.validate(invalid_content)

@pytest.mark.asyncio
async def test_clean_content(processor, sample_content):
    """测试内容清洗"""
    result = await processor.clean(sample_content)
    
    # 验证HTML清洗
    assert "<p>" not in result["content"]
    assert "这是一篇测试笔记的内容" in result["content"]
    
    # 验证标题清洗
    assert result["title"].strip() == result["title"]
    
    # 验证图片URL清洗
    assert len(result["images"]) == 3
    assert all(url.strip() == url for url in result["images"])

@pytest.mark.asyncio
async def test_transform_content(processor, sample_content):
    """测试内容转换"""
    result = await processor.transform(sample_content)
    
    # 验证时间格式
    assert isinstance(result["created_at"], str)
    
    # 验证统计数据
    assert isinstance(result["stats"]["likes"], int)
    assert result["stats"]["likes"] == 100
    assert isinstance(result["stats"]["comments"], int)
    assert result["stats"]["comments"] == 20
    assert isinstance(result["stats"]["shares"], int)
    assert result["stats"]["shares"] == 5
    assert isinstance(result["stats"]["collects"], int)
    assert result["stats"]["collects"] == 10

@pytest.mark.asyncio
async def test_enrich_content(processor, sample_content):
    """测试内容丰富"""
    result = await processor.enrich(sample_content)
    
    # 验证内容类型
    assert "type" in result
    assert result["type"] in ["text", "image", "gallery"]
    
    # 验证标签
    assert "tags" in result
    assert isinstance(result["tags"], list)
    assert "美食" in result["tags"]
    assert "旅行" in result["tags"]
    
    # 验证处理时间
    assert "processed_at" in result
    assert isinstance(result["processed_at"], str)

@pytest.mark.asyncio
async def test_batch_process(processor, sample_content):
    """测试批量处理"""
    contents = [sample_content] * 3
    results = await processor.batch_process(contents)
    
    # 验证结果数量
    assert len(results) == 3
    
    # 验证每个结果
    for result in results:
        assert result["id"] == sample_content["id"]
        assert "<p>" not in result["content"]
        assert len(result["images"]) == 3
        assert "type" in result
        assert "tags" in result
        assert "processed_at" in result

@pytest.mark.asyncio
async def test_processor_stats(processor, sample_content):
    """测试处理器统计"""
    # 处理一些内容
    await processor.process(sample_content)
    await processor.process(sample_content)
    
    # 处理一个无效内容
    invalid_content = {"id": "test"}
    await processor.process(invalid_content)
    
    # 获取统计信息
    stats = processor.get_stats()
    
    # 验证统计数据
    assert stats["processed_count"] == 3
    assert stats["success_count"] == 2
    assert stats["fail_count"] == 1
    assert stats["avg_process_time"] > 0

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 