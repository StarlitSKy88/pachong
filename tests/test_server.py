from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any
import json

app = FastAPI(title="工具测试服务器")

@app.post("/tools/test")
async def test_tool(request: Request) -> Dict[str, Any]:
    """测试工具的输入输出"""
    try:
        data = await request.json()
        # 记录输入
        print(f"收到输入: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        # 返回测试响应
        response = {
            "status": "success",
            "message": "工具调用成功",
            "input_received": data,
            "test_output": {
                "result": "这是测试输出",
                "timestamp": "2024-03-27 12:00:00"
            }
        }
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000) 