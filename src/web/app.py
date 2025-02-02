"""Web应用主模块"""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from .docs.openapi import custom_openapi
from .auth.jwt import jwt_handler
from .middleware.rate_limit import rate_limit_middleware
from ..config import Config

config = Config()

def create_app() -> FastAPI:
    """创建FastAPI应用
    
    Returns:
        FastAPI: FastAPI应用实例
    """
    app = FastAPI(
        title="爬虫系统",
        description="多平台内容采集和处理系统",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # 配置CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.get("cors.origins", ["*"]),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )
    
    # 添加限流中间件
    app.middleware("http")(rate_limit_middleware)
    
    # 配置OpenAPI文档
    app.openapi = lambda: custom_openapi(app)
    
    # 注册路由
    from .routes import crawler, content, monitor, user
    
    app.include_router(
        crawler.router,
        prefix="/api/crawler",
        tags=["爬虫"],
        dependencies=[Depends(jwt_handler.verify_token)]
    )
    
    app.include_router(
        content.router,
        prefix="/api/content",
        tags=["内容"],
        dependencies=[Depends(jwt_handler.verify_token)]
    )
    
    app.include_router(
        monitor.router,
        prefix="/api/monitor",
        tags=["监控"],
        dependencies=[Depends(jwt_handler.verify_token)]
    )
    
    app.include_router(
        user.router,
        prefix="/api/user",
        tags=["用户"]
    )
    
    @app.get("/")
    async def root():
        """根路由"""
        return {
            "message": "Welcome to Crawler System API",
            "docs": "/api/docs",
            "version": "1.0.0"
        }
        
    return app
    
app = create_app() 