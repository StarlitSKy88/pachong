import pytest
from src.summarizer.deepseek_client import DeepseekClient

def test_content_summary():
    client = DeepseekClient()
    test_content = """
    Cursor IDE发布重大更新：集成Claude 3 Opus模型
    
    今日，Cursor IDE发布了最新版本，集成了Anthropic公司的Claude 3 Opus模型。
    这次更新带来了以下重要特性：
    1. 更强大的代码补全能力
    2. 更准确的代码解释和文档生成
    3. 支持多语言上下文理解
    4. 优化了项目依赖分析
    
    用户反馈表示，新版本的响应速度提升明显，代码建议的准确性也有很大提高。
    """
    
    result = client.summarize_content(test_content)
    assert result is not None
    assert "category" in result
    assert "summary" in result
    assert "key_points" in result
    assert "value_score" in result
    
    print("\n测试结果：")
    print(f"分类：{result['category']}")
    print(f"摘要：{result['summary']}")
    print("关键点：")
    for point in result['key_points']:
        print(f"- {point}")
    print(f"价值评分：{'★' * result['value_score']}")
    print(f"评分说明：{result['value_explanation']}")

if __name__ == "__main__":
    test_content_summary() 