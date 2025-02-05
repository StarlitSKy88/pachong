import requests
import json
from datetime import datetime

# API配置
API_URL = "http://localhost:8000"
API_KEY = "dev-test-key-2024"

def test_health():
    """测试健康检查接口"""
    response = requests.get(f"{API_URL}/health")
    print("\n健康检查结果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    
def test_tool_execution():
    """测试工具执行接口"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "tool_name": "test_tool",
        "parameters": {
            "param1": "测试参数1",
            "param2": 123,
            "timestamp": datetime.now().isoformat()
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}/tools/execute",
            headers=headers,
            json=data
        )
        print("\n工具执行结果:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    print("开始API测试...")
    test_health()
    test_tool_execution()
    print("\n测试完成!") 