import requests
import json
from datetime import datetime
from typing import Dict, Any
import sys
from loguru import logger

# API配置
API_URL = "http://localhost:8000"
API_KEY = "dev-test-key-2024"

def make_request(url: str, method: str = "GET", **kwargs) -> Dict[str, Any]:
    """发送HTTP请求
    
    Args:
        url: 请求URL
        method: 请求方法
        **kwargs: 其他参数
        
    Returns:
        响应数据
    """
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()  # 检查响应状态
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"请求失败: {str(e)}")
        return {"error": str(e)}
    except json.JSONDecodeError as e:
        logger.error(f"JSON解析失败: {str(e)}")
        return {"error": "响应格式错误"}

def test_bilibili_crawler():
    """测试B站爬虫"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "keyword": "Python教程",
        "content_type": "video",
        "limit": 5
    }
    
    logger.info("开始测试B站爬虫...")
    result = make_request(
        f"{API_URL}/crawl/bilibili",
        method="POST",
        headers=headers,
        json=data
    )
    
    print("\nB站爬取结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

def test_xiaohongshu_crawler():
    """测试小红书爬虫"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "keyword": "Python入门",
        "limit": 5
    }
    
    logger.info("开始测试小红书爬虫...")
    result = make_request(
        f"{API_URL}/crawl/xiaohongshu",
        method="POST",
        headers=headers,
        json=data
    )
    
    print("\n小红书爬取结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

def test_health():
    """测试健康检查"""
    logger.info("开始测试健康检查...")
    result = make_request(f"{API_URL}/health")
    
    print("\n健康检查结果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    return result

def main():
    """主函数"""
    try:
        print("开始爬虫测试...")
        
        # 测试健康检查
        health_result = test_health()
        if "error" in health_result:
            logger.error("健康检查失败，终止测试")
            sys.exit(1)
            
        # 测试B站爬虫
        bilibili_result = test_bilibili_crawler()
        if "error" in bilibili_result:
            logger.error("B站爬虫测试失败")
            
        # 测试小红书爬虫
        xiaohongshu_result = test_xiaohongshu_crawler()
        if "error" in xiaohongshu_result:
            logger.error("小红书爬虫测试失败")
            
        print("\n测试完成!")
        
    except Exception as e:
        logger.error(f"测试过程出错: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 