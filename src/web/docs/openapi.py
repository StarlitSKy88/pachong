"""API文档生成模块"""

from fastapi.openapi.utils import get_openapi
from typing import Dict, Any

def custom_openapi(app) -> Dict[str, Any]:
    """生成自定义OpenAPI文档
    
    Args:
        app: FastAPI应用实例
        
    Returns:
        Dict[str, Any]: OpenAPI文档字典
    """
    if app.openapi_schema:
        return app.openapi_schema
        
    openapi_schema = get_openapi(
        title="爬虫系统API",
        version="1.0.0",
        description="多平台内容采集和处理系统API文档",
        routes=app.routes
    )
    
    # 添加安全模式
    openapi_schema["components"]["securitySchemes"] = {
        "bearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        },
        "oauth2": {
            "type": "oauth2",
            "flows": {
                "password": {
                    "tokenUrl": "/auth/token",
                    "scopes": {
                        "read": "读取权限",
                        "write": "写入权限",
                        "admin": "管理权限"
                    }
                }
            }
        }
    }
    
    # 添加全局安全要求
    openapi_schema["security"] = [
        {"bearerAuth": []},
        {"oauth2": ["read", "write"]}
    ]
    
    # 添加标签说明
    openapi_schema["tags"] = [
        {
            "name": "爬虫",
            "description": "爬虫相关接口"
        },
        {
            "name": "内容",
            "description": "内容管理接口"
        },
        {
            "name": "监控",
            "description": "系统监控接口"
        },
        {
            "name": "用户",
            "description": "用户管理接口"
        }
    ]
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema 