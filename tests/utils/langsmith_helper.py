import os
from datetime import datetime
from langsmith import Client
from langsmith.run_trees import RunTree
from langsmith.schemas import Run, Field
from dotenv import load_dotenv
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class LangSmithHelper:
    def __init__(self):
        """初始化LangSmith客户端"""
        # 加载环境变量
        load_dotenv()
        
        # 检查必要的环境变量
        required_vars = [
            "LANGCHAIN_API_KEY",
            "LANGCHAIN_ENDPOINT",
            "LANGCHAIN_PROJECT"
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"缺少必要的环境变量: {', '.join(missing_vars)}")
        
        # 初始化客户端
        self.client = Client(
            api_url=os.getenv("LANGCHAIN_ENDPOINT"),
            api_key=os.getenv("LANGCHAIN_API_KEY")
        )
        
        self.project_name = os.getenv("LANGCHAIN_PROJECT", "crawler_test")
    
    def start_trace(self, name: str):
        """开始追踪

        Args:
            name: 追踪名称

        Returns:
            追踪对象
        """
        return {"name": name, "start_time": datetime.now()}

    async def end_trace(self, trace):
        """结束追踪

        Args:
            trace: 追踪对象
        """
        if trace is None:
            return
        
        trace["end_time"] = datetime.now()
        duration = trace["end_time"] - trace["start_time"]
        logger.info(f"Trace {trace['name']} completed in {duration.total_seconds():.2f}s")

    def log_request(self, trace, name: str, data: Any):
        """记录请求

        Args:
            trace: 追踪对象
            name: 请求名称
            data: 请求数据
        """
        if trace is None:
            return
        
        logger.info(f"Request {name}: {data}")

    def log_parse(self, trace: Dict[str, Any], input_data: Dict[str, Any], output_data: Dict[str, Any]) -> None:
        """记录解析"""
        trace["events"].append({
            "type": "parse",
            "time": datetime.now(),
            "input": input_data,
            "output": output_data
        })
    
    def log_error(self, trace, error: Exception):
        """记录错误

        Args:
            trace: 追踪对象
            error: 错误对象
        """
        if trace is None:
            return
        
        logger.error(f"Error in trace {trace['name']}: {error}")
    
    def get_test_stats(self) -> dict:
        """获取测试统计信息
        
        Returns:
            统计数据字典
        """
        try:
            runs = self.client.list_runs(
                project_name=self.project_name,
                execution_order=1
            )
            
            stats = {
                "total": 0,
                "success": 0,
                "failure": 0,
                "avg_latency": 0.0
            }
            
            total_latency = 0.0
            for run in runs:
                stats["total"] += 1
                if run.error is None:
                    stats["success"] += 1
                else:
                    stats["failure"] += 1
                if run.end_time and run.start_time:
                    total_latency += (run.end_time - run.start_time).total_seconds()
            
            if stats["total"] > 0:
                stats["avg_latency"] = total_latency / stats["total"]
            
            return stats
        except Exception as e:
            print(f"获取测试统计信息失败: {str(e)}")
            return {
                "total": 0,
                "success": 0,
                "failure": 0,
                "avg_latency": 0.0
            }
    
    def export_report(self, output_path: str):
        """导出测试报告
        
        Args:
            output_path: 输出文件路径
        """
        try:
            stats = self.get_test_stats()
            runs = self.client.list_runs(
                project_name=self.project_name,
                execution_order=1
            )
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# LangSmith测试报告\n\n")
                f.write(f"## 测试统计\n")
                f.write(f"- 总测试数: {stats['total']}\n")
                f.write(f"- 成功数: {stats['success']}\n")
                f.write(f"- 失败数: {stats['failure']}\n")
                f.write(f"- 平均延迟: {stats['avg_latency']:.2f}秒\n\n")
                
                f.write("## 测试详情\n")
                for run in runs:
                    f.write(f"\n### {run.name}\n")
                    f.write(f"- 状态: {'成功' if run.error is None else '失败'}\n")
                    f.write(f"- 开始时间: {run.start_time}\n")
                    f.write(f"- 结束时间: {run.end_time}\n")
                    if run.error:
                        f.write(f"- 错误信息: {run.error}\n")
        except Exception as e:
            print(f"导出测试报告失败: {str(e)}")
    
    def create_dataset(self, examples: list, dataset_name: str = "测试数据集") -> str:
        """创建评估数据集
        
        Args:
            examples: 示例列表，每个示例是一个(问题, 答案)元组
            dataset_name: 数据集名称
            
        Returns:
            数据集ID
        """
        try:
            # 准备输入输出数据
            inputs = [{"question": input_prompt} for input_prompt, _ in examples]
            outputs = [{"answer": output_answer} for _, output_answer in examples]
            
            # 创建数据集
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description="用于评估DeepSeek API响应质量的数据集"
            )
            
            # 添加示例
            self.client.create_examples(
                inputs=inputs,
                outputs=outputs,
                dataset_id=dataset.id
            )
            
            return dataset.id
        except Exception as e:
            print(f"创建数据集失败: {str(e)}")
            return None
    
    def create_evaluator(self, instructions: str) -> callable:
        """创建评估器
        
        Args:
            instructions: 评估指令
            
        Returns:
            评估函数
        """
        def accuracy(outputs: dict, reference_outputs: dict) -> bool:
            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": instructions},
                    {"role": "user", "content": f"""Ground Truth: {reference_outputs["answer"]};
                    Student's Answer: {outputs["response"]}"""}
                ],
                response_format=Grade
            )
            return response.choices[0].message.parsed.score
            
        return accuracy
    
    def run_evaluation(self, dataset_id: str, target_func: callable, evaluator: callable) -> dict:
        """运行评估
        
        Args:
            dataset_id: 数据集ID
            target_func: 目标函数
            evaluator: 评估函数
            
        Returns:
            评估结果
        """
        try:
            results = self.client.evaluate(
                target=target_func,
                data=dataset_id,
                evaluators=[evaluator],
                experiment_prefix="deepseek-eval",
                max_concurrency=2
            )
            return results
        except Exception as e:
            print(f"运行评估失败: {str(e)}")
            return None 