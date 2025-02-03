"""内容分析器测试"""

import json
import pytest
from unittest.mock import patch
from datetime import datetime
from src.processors.analyzer import ContentAnalyzer, content_analyzer

@pytest.fixture
def analyzer():
    """分析器fixture"""
    return ContentAnalyzer()

@pytest.fixture
def sample_content():
    """示例内容fixture"""
    return {
        "id": "test_note_1",
        "title": "Cursor开发教程：如何使用AI助手提升编程效率 #编程 #AI",
        "content": """
        在本教程中，我将分享如何使用Cursor IDE的AI助手功能来提升编程效率。
        
        1. 代码补全
        - 智能提示
        - 上下文感知
        - 多语言支持
        
        2. 代码重构
        - 自动优化
        - 错误修复
        - 性能建议
        
        3. 文档生成
        - 注释补全
        - API文档
        - 使用示例
        
        #Cursor #AI助手 #效率工具
        """,
        "images": [
            "https://example.com/cursor-ide.jpg",
            "https://example.com/ai-assistant.jpg"
        ],
        "created_at": datetime.now(),
        "stats": {
            "likes": "120",
            "comments": "25",
            "shares": "30",
            "collects": "15"
        },
        "tags": ["编程", "AI", "Cursor", "AI助手", "效率工具"]
    }

@pytest.fixture
def mock_llm_response():
    """模拟LLM响应fixture"""
    return {
        "quality_assessment": {
            "score": 8.5,
            "dimensions": {
                "完整性": 9,
                "清晰度": 8,
                "匹配度": 9,
                "吸引力": 8,
                "互动性": 8
            },
            "comments": {
                "pros": [
                    "内容结构清晰",
                    "主题聚焦",
                    "实用性强"
                ],
                "cons": [
                    "示例可以更具体",
                    "缺少实际效果展示"
                ]
            },
            "suggestions": [
                "添加具体的代码示例",
                "增加效果对比图",
                "补充用户反馈"
            ]
        },
        "topic_analysis": {
            "topics": {
                "main": "Cursor IDE的AI助手功能应用",
                "sub": [
                    "代码补全",
                    "代码重构",
                    "文档生成"
                ]
            },
            "keywords": [
                "Cursor",
                "AI助手",
                "编程效率",
                "代码补全",
                "代码重构",
                "文档生成"
            ],
            "entities": {
                "person": [],
                "location": [],
                "brand": ["Cursor"],
                "other": ["IDE", "AI助手"]
            },
            "summary": "本文介绍了如何使用Cursor IDE的AI助手功能提升编程效率，主要包括代码补全、代码重构和文档生成三个方面的应用。"
        },
        "relevance_assessment": {
            "score": {
                "title_relevance": 9,
                "tag_relevance": 8,
                "content_consistency": 9,
                "overall": 8.7
            },
            "explanation": "标题、内容和标签高度相关，主题聚焦明确",
            "key_matches": [
                "标题与内容主题一致",
                "标签覆盖核心概念",
                "内容结构完整"
            ],
            "mismatches": [
                "部分标签可以更专业化"
            ]
        }
    }

@pytest.mark.asyncio
async def test_process_content(analyzer, sample_content, mock_llm_response):
    """测试内容处理"""
    with patch('src.processors.analyzer.query_llm') as mock_query:
        mock_query.side_effect = [
            json.dumps(mock_llm_response['quality_assessment']),
            json.dumps(mock_llm_response['topic_analysis']),
            json.dumps(mock_llm_response['relevance_assessment'])
        ]
        
        result = await analyzer.process(sample_content)
        
        # 验证基本字段
        assert result["id"] == sample_content["id"]
        assert "analysis" in result
        assert "processed_at" in result
        
        # 验证分析结果
        analysis = result["analysis"]
        assert "quality" in analysis
        assert "topic" in analysis
        assert "relevance" in analysis
        assert "analyzed_at" in analysis
        
        # 验证调用次数
        assert mock_query.call_count == 3

@pytest.mark.asyncio
async def test_quality_assessment(analyzer, sample_content, mock_llm_response):
    """测试质量评估"""
    with patch('src.processors.analyzer.query_llm') as mock_query:
        mock_query.return_value = json.dumps(mock_llm_response['quality_assessment'])
        
        result = await analyzer._assess_quality(sample_content)
        
        assert result["score"] == 8.5
        assert len(result["dimensions"]) == 5
        assert len(result["comments"]["pros"]) == 3
        assert len(result["comments"]["cons"]) == 2
        assert len(result["suggestions"]) == 3

@pytest.mark.asyncio
async def test_topic_analysis(analyzer, sample_content, mock_llm_response):
    """测试主题分析"""
    with patch('src.processors.analyzer.query_llm') as mock_query:
        mock_query.return_value = json.dumps(mock_llm_response['topic_analysis'])
        
        result = await analyzer._analyze_topic(sample_content)
        
        assert result["topics"]["main"] == "Cursor IDE的AI助手功能应用"
        assert len(result["topics"]["sub"]) == 3
        assert len(result["keywords"]) == 6
        assert len(result["entities"]["brand"]) == 1
        assert len(result["summary"]) > 0

@pytest.mark.asyncio
async def test_relevance_assessment(analyzer, sample_content, mock_llm_response):
    """测试相关性评估"""
    # 添加测试主题
    analyzer.add_topic("AI开发")
    analyzer.add_topic("编程效率")
    
    with patch('src.processors.analyzer.query_llm') as mock_query:
        mock_query.return_value = json.dumps({
            "score": {
                "topic_relevance": 9,
                "tag_relevance": 8,
                "content_consistency": 9,
                "overall": 8.7
            },
            "explanation": "内容与AI开发和编程效率主题高度相关",
            "key_matches": [
                "涉及AI助手应用",
                "关注开发效率提升",
                "工具应用场景明确"
            ],
            "mismatches": [
                "部分技术细节可以补充"
            ]
        })
        
        result = await analyzer._assess_relevance(sample_content)
        
        assert result["score"]["overall"] == 8.7
        assert result["score"]["topic_relevance"] == 9
        assert result["score"]["tag_relevance"] == 8
        assert result["score"]["content_consistency"] == 9
        assert len(result["key_matches"]) == 3
        assert len(result["mismatches"]) == 1
        
        # 验证提示词中包含主题（小写形式）
        prompt = mock_query.call_args[0][0]
        assert "ai开发" in prompt.lower()
        assert "编程效率" in prompt.lower()

@pytest.mark.asyncio
async def test_batch_process(analyzer, sample_content, mock_llm_response):
    """测试批量处理"""
    with patch('src.processors.analyzer.query_llm') as mock_query:
        mock_query.side_effect = [
            json.dumps(mock_llm_response['quality_assessment']),
            json.dumps(mock_llm_response['topic_analysis']),
            json.dumps(mock_llm_response['relevance_assessment'])
        ] * 3  # 处理3个内容
        
        contents = [sample_content] * 3
        results = await analyzer.batch_process(contents)
        
        # 验证结果数量
        assert len(results) == 3
        
        # 验证每个结果
        for result in results:
            assert "analysis" in result
            assert "processed_at" in result
            
        # 验证调用次数
        assert mock_query.call_count == 9  # 每个内容调用3次

@pytest.mark.asyncio
async def test_error_handling(analyzer, sample_content):
    """测试错误处理"""
    with patch('src.processors.analyzer.query_llm') as mock_query:
        # 模拟API调用失败
        mock_query.side_effect = Exception("API error")
        
        result = await analyzer.process(sample_content)
        
        # 验证返回原始内容
        assert result["id"] == sample_content["id"]
        assert "analysis" not in result

@pytest.mark.asyncio
async def test_invalid_response(analyzer, sample_content):
    """测试无效响应处理"""
    with patch('src.processors.analyzer.query_llm') as mock_query:
        # 返回无效的JSON
        mock_query.return_value = "invalid json"
        
        # 验证抛出JSONDecodeError异常
        with pytest.raises(json.JSONDecodeError):
            await analyzer._assess_quality(sample_content)

@pytest.mark.asyncio
async def test_topic_management(analyzer):
    """测试主题管理功能"""
    # 初始状态
    assert len(analyzer.get_topics()) == 0
    
    # 添加主题
    analyzer.add_topic("AI开发")
    analyzer.add_topic("机器学习")
    assert len(analyzer.get_topics()) == 2
    assert "ai开发" in analyzer.topics  # 测试小写转换
    
    # 添加重复主题
    analyzer.add_topic("AI开发")
    assert len(analyzer.get_topics()) == 2
    
    # 移除主题
    analyzer.remove_topic("AI开发")
    assert len(analyzer.get_topics()) == 1
    assert "ai开发" not in analyzer.topics
    
    # 移除不存在的主题
    analyzer.remove_topic("不存在的主题")
    assert len(analyzer.get_topics()) == 1
    
    # 清空主题
    analyzer.clear_topics()
    assert len(analyzer.get_topics()) == 0

if __name__ == "__main__":
    pytest.main(["-v", __file__]) 