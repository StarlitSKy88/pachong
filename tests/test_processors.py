import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.processors.analyzer import ContentAnalyzer, content_analyzer
from src.processors.generator import ContentGenerator, content_generator

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