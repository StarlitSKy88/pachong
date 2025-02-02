import pytest
from tests.utils.langsmith_helper import LangSmithHelper

def test_langsmith_connection():
    """测试LangSmith连接配置"""
    try:
        # 初始化LangSmith助手
        helper = LangSmithHelper()
        
        # 开始一个测试追踪
        trace = helper.start_trace("DeepSeek API测试")
        
        # 记录API配置信息
        helper.log_request(
            trace,
            url="https://api.deepseek.com/v1/chat/completions",
            response={
                "model": "deepseek-chat",
                "api_key": "sk-4e8e23e071184186b1a70bd7b87cbff3",
                "status": "configured"
            }
        )
        
        # 模拟API调用
        test_prompt = "你好，这是一个测试消息"
        helper.log_request(
            trace,
            url="https://api.deepseek.com/v1/chat/completions",
            response={
                "status": "success",
                "prompt": test_prompt,
                "model": "deepseek-chat",
                "timestamp": "2024-03-27T10:00:00Z"
            }
        )
        
        # 结束追踪
        helper.end_trace(trace, success=True)
        
        # 获取测试统计
        stats = helper.get_test_stats()
        
        assert stats["total"] >= 1, "应该至少有一个测试记录"
        assert stats["success"] >= 1, "应该至少有一个成功的测试"
        
    except Exception as e:
        pytest.fail(f"LangSmith连接测试失败: {str(e)}")

def test_error_handling():
    """测试错误处理"""
    try:
        helper = LangSmithHelper()
        trace = helper.start_trace("错误处理测试")
        
        # 模拟API错误
        try:
            raise Exception("DeepSeek API调用失败：请求超时")
        except Exception as e:
            helper.log_error(trace, e)
        
        helper.end_trace(trace, success=False)
        
        # 验证错误记录
        stats = helper.get_test_stats()
        assert stats["failure"] >= 1, "应该记录失败的测试"
        
    except Exception as e:
        pytest.fail(f"错误处理测试失败: {str(e)}")

def test_evaluation():
    """测试评估功能"""
    try:
        helper = LangSmithHelper()
        
        # 创建测试数据集
        examples = [
            ("北京是哪个国家的首都？", "北京是中国的首都。"),
            ("长城是哪个朝代修建的？", "长城始建于春秋战国时期，秦朝统一后由秦始皇连接和修筑。"),
            ("熊猫的主要栖息地在哪里？", "大熊猫主要栖息地在中国的四川、陕西和甘肃等地。")
        ]
        dataset_id = helper.create_dataset(examples)
        assert dataset_id is not None, "数据集创建失败"
        
        # 创建目标函数
        def target(inputs: dict) -> dict:
            response = helper.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "请准确回答以下问题"},
                    {"role": "user", "content": inputs["question"]}
                ]
            )
            return {"response": response.choices[0].message.content.strip()}
        
        # 创建评估器
        instructions = """评估回答的准确性：
        - 判断标准：概念准确性和关键信息的完整性
        - 评分规则：
          - True：回答准确且包含关键信息
          - False：回答不准确或缺少关键信息
        """
        evaluator = helper.create_evaluator(instructions)
        
        # 运行评估
        results = helper.run_evaluation(dataset_id, target, evaluator)
        assert results is not None, "评估执行失败"
        
        # 导出评估报告
        helper.export_report("tests/evaluation_report.md")
        
    except Exception as e:
        pytest.fail(f"评估测试失败: {str(e)}") 