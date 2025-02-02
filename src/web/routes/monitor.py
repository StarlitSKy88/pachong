from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.concurrency import run_in_threadpool
import asyncio
import json
from typing import Optional, Dict

from metrics import MetricsCollector
from alert import AlertEngine

router = APIRouter()
templates = Jinja2Templates(directory="templates")

metrics_collector = MetricsCollector()
alert_engine = AlertEngine()

# 缓存配置
CACHE_DURATION = 5  # 缓存时间（秒）
metrics_cache = {
    "data": None,
    "timestamp": None,
    "etag": None
}

async def get_cached_metrics():
    """获取缓存的指标数据"""
    current_time = datetime.now()
    
    # 检查缓存是否有效
    if (metrics_cache["data"] and metrics_cache["timestamp"] and 
        (current_time - metrics_cache["timestamp"]).total_seconds() < CACHE_DURATION):
        return metrics_cache["data"], metrics_cache["etag"]
    
    # 收集新数据
    metrics = await metrics_collector.collect_all_metrics()
    history_data = await metrics_collector.get_history_data(hours=24)
    
    # 构建响应数据
    data = {
        "metrics": metrics,
        "system_timestamps": history_data["timestamps"],
        "system_cpu_history": history_data["cpu_usage"],
        "system_memory_history": history_data["memory_usage"],
        "system_disk_history": history_data["disk_usage"]
    }
    
    # 生成新的ETag
    etag = str(hash(json.dumps(data, sort_keys=True)))
    
    # 更新缓存
    metrics_cache.update({
        "data": data,
        "timestamp": current_time,
        "etag": etag
    })
    
    return data, etag

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    """
    渲染监控面板
    """
    # 使用缓存的数据
    data, _ = await get_cached_metrics()
    
    # 获取最新告警
    alerts = await run_in_threadpool(alert_engine.get_recent_alerts, limit=10)
    
    # 检查系统健康状态
    health_status = all([
        data["metrics"]["system.cpu.usage"].value < 80,
        data["metrics"]["system.memory.percent"].value < 80,
        data["metrics"]["system.disk.percent"].value < 80,
        data["metrics"]["task.success_rate"].value > 0.8,
        data["metrics"]["crawler.error.count"].value < 50
    ])
    
    return templates.TemplateResponse(
        "monitor/dashboard.html",
        {
            "request": request,
            "metrics": data["metrics"],
            "alerts": alerts,
            "health_status": health_status,
            "update_time": datetime.now(),
            "system_timestamps": data["system_timestamps"],
            "system_cpu_history": data["system_cpu_history"],
            "system_memory_history": data["system_memory_history"],
            "system_disk_history": data["system_disk_history"]
        }
    )

@router.get("/api/metrics/history")
async def get_metrics_history(request: Request, response: Response):
    """
    获取历史指标数据的API接口，支持缓存和增量更新
    """
    # 获取客户端的ETag
    if_none_match = request.headers.get("if-none-match")
    
    # 获取缓存的数据
    data, etag = await get_cached_metrics()
    
    # 如果ETag匹配，返回304
    if if_none_match == etag:
        return Response(status_code=304)
    
    # 设置缓存头
    response.headers["Cache-Control"] = f"max-age={CACHE_DURATION}"
    response.headers["ETag"] = etag
    
    return JSONResponse(data)

@router.get("/api/metrics/current")
async def get_current_metrics():
    """
    获取当前指标数据的API接口（轻量级）
    """
    metrics = await metrics_collector.collect_all_metrics()
    return JSONResponse({
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }) 