"""自定义指标示例"""

from typing import Dict, List, Any
from dataclasses import dataclass
import time
import json

@dataclass
class MetricDefinition:
    """指标定义"""
    name: str                # 指标名称
    type: str               # 指标类型
    help: str               # 帮助信息
    labels: List[str]       # 标签列表
    buckets: List[float]    # 直方图桶（仅用于histogram类型）

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        """初始化指标收集器"""
        self.metrics: Dict[str, Dict[str, Any]] = {}
        
    def register_metric(
        self,
        definition: MetricDefinition
    ):
        """注册指标
        
        Args:
            definition: 指标定义
        """
        if definition.name in self.metrics:
            return
            
        self.metrics[definition.name] = {
            "definition": definition,
            "values": {}
        }
        
    def _get_label_key(self, labels: Dict[str, str]) -> str:
        """获取标签键
        
        Args:
            labels: 标签字典
            
        Returns:
            str: 标签键
        """
        return json.dumps(labels, sort_keys=True)
        
    def observe(
        self,
        name: str,
        value: float,
        labels: Dict[str, str]
    ):
        """观察指标值
        
        Args:
            name: 指标名称
            value: 指标值
            labels: 标签值
        """
        if name not in self.metrics:
            raise ValueError(f"Metric {name} not registered")
            
        metric = self.metrics[name]
        definition = metric["definition"]
        
        # 验证标签
        for label in labels:
            if label not in definition.labels:
                raise ValueError(f"Invalid label {label}")
                
        label_key = self._get_label_key(labels)
        
        if definition.type == "counter":
            if label_key not in metric["values"]:
                metric["values"][label_key] = 0
            metric["values"][label_key] += value
            
        elif definition.type == "gauge":
            metric["values"][label_key] = value
            
        elif definition.type == "histogram":
            if label_key not in metric["values"]:
                metric["values"][label_key] = {
                    "count": 0,
                    "sum": 0,
                    "buckets": {str(b): 0 for b in definition.buckets}
                }
            
            data = metric["values"][label_key]
            data["count"] += 1
            data["sum"] += value
            
            for bucket in definition.buckets:
                if value <= bucket:
                    data["buckets"][str(bucket)] += 1
                    
    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标
        
        Returns:
            Dict[str, Any]: 指标数据
        """
        return self.metrics

# 使用示例
if __name__ == "__main__":
    # 创建指标收集器
    collector = MetricsCollector()
    
    # 注册内容处理指标
    collector.register_metric(
        MetricDefinition(
            name="content_processing_time",
            type="histogram",
            help="内容处理耗时分布",
            labels=["platform", "content_type"],
            buckets=[0.1, 0.5, 1, 5]
        )
    )
    
    # 注册请求计数指标
    collector.register_metric(
        MetricDefinition(
            name="request_total",
            type="counter",
            help="请求总数",
            labels=["platform", "status"],
            buckets=[]
        )
    )
    
    # 注册并发数指标
    collector.register_metric(
        MetricDefinition(
            name="concurrent_requests",
            type="gauge",
            help="当前并发请求数",
            labels=["platform"],
            buckets=[]
        )
    )
    
    # 模拟指标收集
    def process_content(platform: str, content_type: str):
        """模拟内容处理
        
        Args:
            platform: 平台
            content_type: 内容类型
        """
        start_time = time.time()
        
        # 记录并发数
        collector.observe(
            "concurrent_requests",
            1,
            {"platform": platform}
        )
        
        try:
            # 模拟处理
            time.sleep(0.3)
            
            # 记录请求成功
            collector.observe(
                "request_total",
                1,
                {
                    "platform": platform,
                    "status": "success"
                }
            )
            
        except Exception:
            # 记录请求失败
            collector.observe(
                "request_total",
                1,
                {
                    "platform": platform,
                    "status": "error"
                }
            )
            raise
            
        finally:
            # 记录处理时间
            duration = time.time() - start_time
            collector.observe(
                "content_processing_time",
                duration,
                {
                    "platform": platform,
                    "content_type": content_type
                }
            )
            
            # 更新并发数
            collector.observe(
                "concurrent_requests",
                0,
                {"platform": platform}
            )
            
    # 模拟多次处理
    for _ in range(5):
        process_content("xhs", "image")
        process_content("bilibili", "video")
        
    # 打印指标数据
    print(json.dumps(collector.get_metrics(), indent=2)) 