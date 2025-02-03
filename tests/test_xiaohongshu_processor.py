"""小红书内容处理器测试"""

import pytest
from datetime import datetime
from src.processors.xiaohongshu_processor import XiaoHongShuProcessor

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