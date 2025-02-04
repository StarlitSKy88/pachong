"""性能测试运行器

该模块负责执行性能测试，包括：
1. 测试用例管理
2. 测试执行控制
3. 结果收集和汇总
4. 报告生成
"""

import logging
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from .base import PerformanceTest
from .crawler_test import CrawlerPerformanceTest
from .config import TEST_SCENARIOS

logger = logging.getLogger(__name__)

class TestRunner:
    """测试运行器"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.logger = logging.getLogger('TestRunner')
        
        # 设置输出目录
        self.output_dir = Path(output_dir or 'test_results')
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 测试用例
        self.test_cases: List[PerformanceTest] = []
        
        # 测试结果
        self.results: List[Dict] = []
    
    def add_test(self, test: PerformanceTest):
        """添加测试用例"""
        self.test_cases.append(test)
    
    async def run_all(self):
        """运行所有测试"""
        self.logger.info("Starting performance tests")
        start_time = datetime.now()
        
        try:
            # 运行测试用例
            for test in self.test_cases:
                # 准备测试
                await test.setup()
                
                # 运行测试
                await test.run()
                
                # 收集结果
                result = await test.generate_report()
                self.results.append(result)
            
            # 生成汇总报告
            await self.generate_summary_report()
            
        finally:
            end_time = datetime.now()
            duration = end_time - start_time
            self.logger.info(f"All tests completed in {duration}")
    
    async def generate_summary_report(self):
        """生成汇总报告"""
        self.logger.info("Generating summary report")
        
        # 准备报告数据
        summary = {
            'test_info': {
                'total_tests': len(self.test_cases),
                'start_time': self.results[0]['test_info']['start_time'],
                'end_time': self.results[-1]['test_info']['end_time']
            },
            'test_results': self.results
        }
        
        # 保存报告
        report_file = self.output_dir / f'summary_report_{datetime.now():%Y%m%d_%H%M%S}.json'
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        # 生成图表
        await self.generate_charts()
        
        self.logger.info(f"Summary report generated: {report_file}")
    
    async def generate_charts(self):
        """生成图表"""
        self.logger.info("Generating charts")
        
        # 设置图表样式
        plt.style.use('seaborn')
        
        # 创建图表目录
        charts_dir = self.output_dir / 'charts'
        charts_dir.mkdir(exist_ok=True)
        
        # 生成响应时间图表
        self._plot_response_time(charts_dir)
        
        # 生成错误率图表
        self._plot_error_rate(charts_dir)
        
        # 生成吞吐量图表
        self._plot_throughput(charts_dir)
        
        # 生成资源使用图表
        self._plot_resource_usage(charts_dir)
        
        # 生成基准比较图表
        self._plot_baseline_comparison(charts_dir)
    
    def _plot_response_time(self, charts_dir: Path):
        """生成响应时间图表"""
        # 准备数据
        data = []
        for result in self.results:
            metrics = result['performance_metrics']['response_time']
            test_info = result['test_info']
            
            data.append({
                'name': test_info['name'],
                'p50': metrics.get('p50', 0),
                'p90': metrics.get('p90', 0),
                'p95': metrics.get('p95', 0),
                'p99': metrics.get('p99', 0)
            })
        
        df = pd.DataFrame(data)
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        df.plot(
            x='name',
            y=['p50', 'p90', 'p95', 'p99'],
            kind='bar',
            width=0.8
        )
        plt.title('Response Time Percentiles')
        plt.xlabel('Test Case')
        plt.ylabel('Response Time (ms)')
        plt.xticks(rotation=45)
        plt.legend(title='Percentile')
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(charts_dir / 'response_time.png')
        plt.close()
    
    def _plot_error_rate(self, charts_dir: Path):
        """生成错误率图表"""
        # 准备数据
        data = []
        for result in self.results:
            metrics = result['performance_metrics']['error_rate']
            test_info = result['test_info']
            
            data.append({
                'name': test_info['name'],
                'error_rate': metrics.get('mean', 0) * 100
            })
        
        df = pd.DataFrame(data)
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x='name', y='error_rate')
        plt.title('Error Rate')
        plt.xlabel('Test Case')
        plt.ylabel('Error Rate (%)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(charts_dir / 'error_rate.png')
        plt.close()
    
    def _plot_throughput(self, charts_dir: Path):
        """生成吞吐量图表"""
        # 准备数据
        data = []
        for result in self.results:
            metrics = result['performance_metrics']['throughput']
            test_info = result['test_info']
            
            data.append({
                'name': test_info['name'],
                'throughput': metrics.get('mean', 0)
            })
        
        df = pd.DataFrame(data)
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        sns.barplot(data=df, x='name', y='throughput')
        plt.title('Throughput')
        plt.xlabel('Test Case')
        plt.ylabel('Requests/Second')
        plt.xticks(rotation=45)
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(charts_dir / 'throughput.png')
        plt.close()
    
    def _plot_resource_usage(self, charts_dir: Path):
        """生成资源使用图表"""
        # 准备数据
        data = []
        for result in self.results:
            metrics = result['resource_usage']
            test_info = result['test_info']
            
            data.append({
                'name': test_info['name'],
                'cpu': metrics['cpu_usage']['mean'],
                'memory': metrics['memory_usage']['mean'],
                'disk': metrics['disk_usage']['mean']
            })
        
        df = pd.DataFrame(data)
        
        # 创建图表
        plt.figure(figsize=(10, 6))
        df.plot(
            x='name',
            y=['cpu', 'memory', 'disk'],
            kind='bar',
            width=0.8
        )
        plt.title('Resource Usage')
        plt.xlabel('Test Case')
        plt.ylabel('Usage (%)')
        plt.xticks(rotation=45)
        plt.legend(title='Resource')
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(charts_dir / 'resource_usage.png')
        plt.close()
    
    def _plot_baseline_comparison(self, charts_dir: Path):
        """生成基准比较图表"""
        # 准备数据
        data = []
        for result in self.results:
            comparison = result['baseline_comparison']
            test_info = result['test_info']
            
            # 响应时间比较
            for percentile, values in comparison['response_time'].items():
                data.append({
                    'name': test_info['name'],
                    'metric': f'response_time_{percentile}',
                    'baseline': values['baseline'],
                    'actual': values['actual'],
                    'diff_percent': values['diff_percent']
                })
            
            # 错误率比较
            if 'error_rate' in comparison:
                values = comparison['error_rate']
                data.append({
                    'name': test_info['name'],
                    'metric': 'error_rate',
                    'baseline': values['baseline'],
                    'actual': values['actual'],
                    'diff_percent': values['diff_percent']
                })
            
            # 吞吐量比较
            if 'throughput' in comparison:
                values = comparison['throughput']
                data.append({
                    'name': test_info['name'],
                    'metric': 'throughput',
                    'baseline': values['baseline'],
                    'actual': values['actual'],
                    'diff_percent': values['diff_percent']
                })
        
        df = pd.DataFrame(data)
        
        # 创建图表
        plt.figure(figsize=(12, 6))
        sns.barplot(data=df, x='metric', y='diff_percent', hue='name')
        plt.title('Baseline Comparison')
        plt.xlabel('Metric')
        plt.ylabel('Difference (%)')
        plt.xticks(rotation=45)
        plt.legend(title='Test Case', bbox_to_anchor=(1.05, 1), loc='upper left')
        plt.tight_layout()
        
        # 保存图表
        plt.savefig(charts_dir / 'baseline_comparison.png')
        plt.close()

def create_crawler_tests() -> List[PerformanceTest]:
    """创建爬虫测试用例"""
    tests = []
    
    # 为每个平台创建测试
    for platform in ['xhs', 'bilibili']:
        # 为每个负载级别创建测试
        for load_level in ['light_load', 'normal_load', 'heavy_load']:
            test = CrawlerPerformanceTest(
                name=f"{platform}_{load_level}",
                platform=platform,
                load_level=load_level
            )
            tests.append(test)
    
    return tests

async def main():
    """主函数"""
    # 创建测试运行器
    runner = TestRunner()
    
    # 添加测试用例
    for test in create_crawler_tests():
        runner.add_test(test)
    
    # 运行测试
    await runner.run_all()

if __name__ == '__main__':
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行测试
    asyncio.run(main()) 