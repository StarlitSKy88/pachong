from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from typing import Dict, Any, List
import json
from datetime import datetime
import os
import sys
from loguru import logger
from src.database import init_db
from src.config import settings
from src.utils.logger import setup_logger

# 配置日志
setup_logger(
    name="crawler",
    level=settings.LOG_LEVEL,
    log_path=settings.LOG_DIR / "api.log"
)

# 创建应用
app = FastAPI(
    title=settings.APP_NAME,
    description="提供各种爬虫工具的API接口",
    version=settings.APP_VERSION,
    debug=settings.DEBUG
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 简化CORS配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """服务启动时的事件处理"""
    try:
        logger.info("API服务正在启动...")
        
        # 初始化数据库
        logger.info("正在初始化数据库...")
        await init_db()
        logger.info("数据库初始化完成")
        
        # 其他初始化工作
        logger.info(f"环境: {settings.APP_ENV}")
        logger.info(f"调试模式: {settings.DEBUG}")
        logger.info(f"数据库类型: {settings.DB_TYPE}")
        logger.info("API服务启动完成")
    except Exception as e:
        logger.error(f"服务启动失败: {str(e)}")
        raise e

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": f"{settings.APP_NAME} API服务正在运行",
        "version": settings.APP_VERSION,
        "time": datetime.now().isoformat(),
        "environment": settings.APP_ENV
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": settings.APP_VERSION,
        "environment": settings.APP_ENV,
        "database": settings.DB_TYPE
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    error_msg = f"发生错误: {str(exc)}"
    logger.error(error_msg)
    logger.exception(exc)
    
    status_code = 500
    if isinstance(exc, HTTPException):
        status_code = exc.status_code
    
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url),
            "status_code": status_code
        }
    )

# 在这里注册路由模块
# from src.api import router as api_router
# app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    
    try:
        logger.info("正在启动开发服务器...")
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",  # 直接使用固定值
            port=8888,       # 直接使用固定值
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        logger.exception(e)
        sys.exit(1) 