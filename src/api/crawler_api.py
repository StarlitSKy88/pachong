from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import uuid
from datetime import datetime, timedelta
import json
import os
import random
from ..crawlers.xhs_crawler import XHSCrawler
from ..crawlers.bilibili_crawler import BiliBiliCrawler

# 数据模型
class CrawlerTask(BaseModel):
    keywords: List[str]
    platforms: List[str]
    time_range: str
    limit: int

class TaskProgress(BaseModel):
    current: int
    total: int
    status: str  # active, success, exception
    estimated_time: Optional[int] = None  # 预估剩余时间（秒）
    speed: Optional[float] = None  # 每秒处理数量

# 全局变量
app = FastAPI()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tasks = {}  # 存储任务信息
task_results = {}  # 存储任务结果
task_progress = {}  # 存储任务进度

# 爬虫配置
CRAWLER_CLASSES = {
    'xhs': XHSCrawler,
    'bilibili': BiliBiliCrawler
}

# 工具函数
def save_task_info(task_id: str, task_info: dict):
    """保存任务信息到本地文件"""
    os.makedirs('data/tasks', exist_ok=True)
    with open(f'data/tasks/{task_id}.json', 'w', encoding='utf-8') as f:
        json.dump(task_info, f, ensure_ascii=False, indent=2)

def save_task_results(task_id: str, results: list):
    """保存任务结果到本地文件"""
    os.makedirs('data/results', exist_ok=True)
    with open(f'data/results/{task_id}.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def calculate_estimated_time(current: int, total: int, start_time: datetime, platform: str) -> dict:
    """计算预估剩余时间和处理速度"""
    now = datetime.now()
    elapsed = (now - start_time).total_seconds()
    if elapsed < 1 or current == 0:
        return {
            'estimated_time': total * 2,  # 粗略估计
            'speed': 0.5  # 初始速度
        }
    
    speed = current / elapsed  # 实际速度
    remaining = total - current
    estimated_time = remaining / speed if speed > 0 else 0
    
    return {
        'estimated_time': round(estimated_time),
        'speed': round(speed, 2)
    }

async def crawl_platform(platform: str, keywords: List[str], time_range: str, limit: int, task_id: str):
    """使用实际爬虫采集数据"""
    try:
        crawler_class = CRAWLER_CLASSES.get(platform)
        if not crawler_class:
            raise ValueError(f"不支持的平台: {platform}")
            
        async with crawler_class() as crawler:
            results = []
            total = limit
            current = 0
            
            # 更新进度初始状态
            task_progress[task_id][platform].update({
                'total': total,
                'start_time': datetime.now().isoformat()
            })
            
            # 对每个关键词进行搜索
            for keyword in keywords:
                try:
                    # 搜索内容
                    items = await crawler.search(keyword, time_range, limit // len(keywords))
                    results.extend(items)
                    
                    # 更新进度
                    current += len(items)
                    task_progress[task_id][platform].update({
                        'current': current,
                        **calculate_estimated_time(
                            current,
                            total,
                            datetime.fromisoformat(task_progress[task_id][platform]['start_time']),
                            platform
                        )
                    })
                    
                except Exception as e:
                    print(f"关键词 {keyword} 搜索失败: {str(e)}")
                    continue
            
            # 获取详情（可选）
            if results:
                detailed_results = []
                for item in results[:limit]:
                    try:
                        detail = await crawler.get_detail(item['id'])
                        detailed_results.append(detail)
                    except Exception as e:
                        print(f"获取详情失败: {str(e)}")
                        detailed_results.append(item)
                results = detailed_results
            
            # 更新状态为成功
            task_progress[task_id][platform]['status'] = 'success'
            return results
            
    except Exception as e:
        # 更新状态为异常
        task_progress[task_id][platform]['status'] = 'exception'
        print(f"Platform {platform} failed: {str(e)}")
        raise e

async def process_task(task_id: str, task: CrawlerTask):
    """处理爬虫任务"""
    try:
        # 初始化任务进度
        task_progress[task_id] = {
            platform: {
                'current': 0,
                'total': 0,
                'status': 'active',
                'estimated_time': None,
                'speed': None,
                'start_time': datetime.now().isoformat()
            }
            for platform in task.platforms
        }
        
        # 并发爬取各平台
        platform_tasks = [
            crawl_platform(platform, task.keywords, task.time_range, task.limit, task_id)
            for platform in task.platforms
        ]
        
        try:
            results = await asyncio.gather(*platform_tasks, return_exceptions=True)
            
            # 合并结果
            all_results = []
            for platform_results in results:
                if isinstance(platform_results, list):
                    all_results.extend(platform_results)
                elif isinstance(platform_results, Exception):
                    print(f"Platform task failed: {str(platform_results)}")
            
            # 保存结果
            if all_results:
                task_results[task_id] = all_results
                save_task_results(task_id, all_results)
            
        except Exception as e:
            print(f"Task gathering failed: {str(e)}")
            # 更新所有未完成平台的状态为异常
            for platform in task.platforms:
                if task_progress[task_id][platform]['status'] == 'active':
                    task_progress[task_id][platform]['status'] = 'exception'
            raise e
        
    except Exception as e:
        print(f"Task {task_id} failed: {str(e)}")
        raise e

# API路由
@app.post("/api/crawler/task")
async def create_task(task: CrawlerTask, background_tasks: BackgroundTasks):
    """创建新的爬虫任务"""
    try:
        # 验证输入
        if not task.keywords:
            raise HTTPException(status_code=400, detail="Keywords cannot be empty")
        if not task.platforms:
            raise HTTPException(status_code=400, detail="Platforms cannot be empty")
        if task.limit < 1:
            raise HTTPException(status_code=400, detail="Limit must be greater than 0")
        
        # 验证平台支持
        unsupported = set(task.platforms) - set(CRAWLER_CLASSES.keys())
        if unsupported:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported platforms: {', '.join(unsupported)}"
            )
            
        task_id = str(uuid.uuid4())
        
        # 保存任务信息
        task_info = {
            'id': task_id,
            'keywords': task.keywords,
            'platforms': task.platforms,
            'time_range': task.time_range,
            'limit': task.limit,
            'start_time': datetime.now().isoformat()
        }
        tasks[task_id] = task_info
        save_task_info(task_id, task_info)
        
        # 启动后台任务
        background_tasks.add_task(process_task, task_id, task)
        
        return {"task_id": task_id}
        
    except Exception as e:
        print(f"Create task failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawler/progress/{task_id}")
async def get_task_progress(task_id: str):
    """获取任务进度"""
    try:
        if task_id not in task_progress:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # 更新每个平台的预估时间
        for platform, progress in task_progress[task_id].items():
            if progress['status'] == 'active' and 'start_time' in progress:
                start_time = datetime.fromisoformat(progress['start_time'])
                progress.update(calculate_estimated_time(
                    progress['current'],
                    progress['total'],
                    start_time,
                    platform
                ))
                
        return task_progress[task_id]
        
    except Exception as e:
        print(f"Get progress failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/crawler/results/{task_id}")
async def get_task_results(task_id: str):
    """获取任务结果"""
    try:
        if task_id not in task_results:
            # 尝试从文件加载结果
            try:
                with open(f'data/results/{task_id}.json', 'r', encoding='utf-8') as f:
                    results = json.load(f)
                    task_results[task_id] = results
                    return results
            except FileNotFoundError:
                raise HTTPException(status_code=404, detail="Results not found")
        
        return task_results[task_id]
        
    except Exception as e:
        print(f"Get results failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 