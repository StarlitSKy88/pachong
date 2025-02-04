import asyncio
import httpx
import json
from typing import Dict, Any

async def test_tool_call(data: Dict[str, Any]) -> Dict[str, Any]:
    """测试工具调用
    
    Args:
        data: 要发送的测试数据
        
    Returns:
        响应数据
    """
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://127.0.0.1:8000/tools/test",
            json=data
        )
        return response.json()

async def main():
    # 测试数据
    test_data = {
        "tool_name": "test_tool",
        "parameters": {
            "param1": "测试参数1",
            "param2": 123,
            "param3": ["a", "b", "c"]
        }
    }
    
    try:
        # 测试工具调用
        result = await test_tool_call(test_data)
        print(f"测试结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
        
        # 测试健康检查
        async with httpx.AsyncClient() as client:
            health = await client.get("http://127.0.0.1:8000/health")
            print(f"健康检查: {health.json()}")
            
    except Exception as e:
        print(f"测试失败: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 