"""测试运行脚本"""

import os
import sys
import pytest
import logging
from pathlib import Path

def setup_logging():
    """配置日志"""
    log_dir = Path("logs")
    if not log_dir.exists():
        log_dir.mkdir(parents=True)
        
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/test.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

def main():
    """运行测试"""
    # 配置日志
    setup_logging()
    
    # 获取测试目录
    test_path = sys.argv[1] if len(sys.argv) > 1 else "tests"
    
    # 运行测试
    logging.info(f"开始运行测试: {test_path}")
    pytest.main([
        test_path,
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:coverage_html",
        "-n", "auto"
    ])
    
if __name__ == "__main__":
    main() 