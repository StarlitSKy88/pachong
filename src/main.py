from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any, List
import json
from datetime import datetime
import os
import sys
from loguru import logger

# 配置日志
logger.remove()  # 移除默认的处理器
logger.add(
    sink=sys.stderr,
    level="DEBUG",
    format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# 创建应用
app = FastAPI(
    title="爬虫工具API",
    description="提供各种爬虫工具的API接口",
    version="1.0.0",
    debug=False  # 生产环境禁用调试模式
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # 本地开发环境
        "https://your-app.vercel.app",  # Vercel 部署的域名（需要替换）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """服务启动时的事件处理"""
    logger.info("API服务正在启动...")
    logger.info(f"环境: {os.getenv('VERCEL_ENV', 'local')}")
    logger.info(f"区域: {os.getenv('VERCEL_REGION', 'local')}")
    logger.info("API服务启动完成")

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "爬虫工具API服务正在运行",
        "time": datetime.now().isoformat(),
        "environment": os.getenv("VERCEL_ENV", "local"),
        "region": os.getenv("VERCEL_REGION", "local")
    }

@app.get("/health")
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "environment": os.getenv("VERCEL_ENV", "local"),
        "region": os.getenv("VERCEL_REGION", "local")
    }

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    error_msg = f"发生错误: {str(exc)}"
    logger.error(error_msg)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

if __name__ == "__main__":
    try:
        # 启动服务器
        logger.info("正在启动服务器...")
        
        # 使用最简单的配置
        uvicorn.run(
            app,  # 直接使用 app 实例
            host="0.0.0.0",  # 修改为监听所有网络接口
            port=9000,
            log_level="debug",
            reload=False  # 禁用热重载以避免编码问题
        )
        
    except Exception as e:
        logger.error(f"服务器启动失败: {str(e)}")
        logger.exception(e)  # 打印完整的堆栈跟踪
        sys.exit(1) 