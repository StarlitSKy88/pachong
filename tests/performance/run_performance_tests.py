#!/usr/bin/env python
"""性能测试运行脚本"""

import os
import sys
import json
import asyncio
import pytest
import argparse
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

def setup_test_environment():
    """设置测试环境"""
    # 添加项目根目录到Python路径
    project_root = str(Path(__file__).parent.parent.parent)
    sys.path.insert(0, project_root)
    
    # 创建性能测试结果目录
    results_dir = Path(project_root) / "test_results" / "performance"
    results_dir.mkdir(parents=True, exist_ok=True)
    
    return results_dir

def run_performance_tests(test_names: List[str] = None, save_results: bool = True) -> Dict[str, Any]:
    """运行性能测试
    
    Args:
        test_names: 要运行的测试名称列表，为None时运行所有测试
        save_results: 是否保存测试结果
        
    Returns:
        Dict[str, Any]: 测试结果
    """
    # 设置测试环境
    results_dir = setup_test_environment()
    
    # 准备测试参数
    test_path = str(Path(__file__).parent)
    pytest_args = [
        test_path,
        "-v",
        "-m", "performance",
        "--capture=no"
    ]
    
    if test_names:
        test_files = [f"{test_path}/test_performance.py::{name}" for name in test_names]
        pytest_args.extend(test_files)
    
    # 运行测试
    results = {
        "timestamp": datetime.now().isoformat(),
        "test_names": test_names or "all",
        "results": {}
    }
    
    exit_code = pytest.main(pytest_args)
    results["exit_code"] = exit_code
    
    # 读取性能指标
    metrics_file = Path(test_path) / "performance_metrics.json"
    if metrics_file.exists():
        with open(metrics_file, "r", encoding="utf-8") as f:
            results["metrics"] = json.load(f)
    
    # 保存结果
    if save_results:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = results_dir / f"performance_test_results_{timestamp}.json"
        with open(result_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    return results

def generate_report(results: Dict[str, Any]) -> str:
    """生成测试报告
    
    Args:
        results: 测试结果
        
    Returns:
        str: 测试报告
    """
    report = []
    report.append("# 性能测试报告")
    report.append(f"\n## 测试时间: {results['timestamp']}")
    report.append(f"\n## 测试范围: {results['test_names']}")
    report.append(f"\n## 测试结果: {'成功' if results['exit_code'] == 0 else '失败'}")
    
    if "metrics" in results:
        report.append("\n## 性能指标")
        metrics = results["metrics"]
        
        for test_name, test_metrics in metrics.items():
            report.append(f"\n### {test_name}")
            report.append("```")
            report.append(f"执行时间: {test_metrics['duration']:.2f}秒")
            report.append(f"CPU使用率: 平均{test_metrics['cpu']['average']:.1f}%, 最大{test_metrics['cpu']['max']:.1f}%")
            report.append(f"内存使用率: 平均{test_metrics['memory']['average']:.1f}%, 最大{test_metrics['memory']['max']:.1f}%")
            report.append(f"IO读取: {test_metrics['io']['read'] / 1024:.1f}KB")
            report.append(f"IO写入: {test_metrics['io']['write'] / 1024:.1f}KB")
            report.append("```")
    
    return "\n".join(report)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行性能测试")
    parser.add_argument("--tests", nargs="*", help="要运行的测试名称列表")
    parser.add_argument("--no-save", action="store_true", help="不保存测试结果")
    parser.add_argument("--report", action="store_true", help="生成测试报告")
    args = parser.parse_args()
    
    # 运行测试
    results = run_performance_tests(args.tests, not args.no_save)
    
    # 生成报告
    if args.report:
        report = generate_report(results)
        print(report)
        
        # 保存报告
        if not args.no_save:
            results_dir = Path(__file__).parent.parent.parent / "test_results" / "performance"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = results_dir / f"performance_test_report_{timestamp}.md"
            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)

if __name__ == "__main__":
    main() 