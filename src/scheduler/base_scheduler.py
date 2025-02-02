from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
import logging

class BaseScheduler:
    """基础任务调度器"""
    
    def __init__(self):
        """初始化调度器"""
        self.scheduler = AsyncIOScheduler()
        self.jobs: Dict[str, Job] = {}  # 任务字典
        self._setup_logging()
        
    def _setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('scheduler.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger('Scheduler')
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            self.logger.info("Scheduler started")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.logger.info("Scheduler shutdown")
    
    def add_job(self, job_id: str, func: callable, trigger: str = 'cron', **trigger_args) -> Optional[Job]:
        """添加任务"""
        try:
            # 如果任务已存在，先移除
            if job_id in self.jobs:
                self.remove_job(job_id)
            
            # 创建新任务
            job = self.scheduler.add_job(
                func=func,
                trigger=trigger,
                id=job_id,
                **trigger_args
            )
            
            self.jobs[job_id] = job
            self.logger.info(f"Added job: {job_id}")
            return job
        except Exception as e:
            self.logger.error(f"Error adding job {job_id}: {str(e)}")
            return None
    
    def remove_job(self, job_id: str) -> bool:
        """移除任务"""
        try:
            if job_id in self.jobs:
                self.scheduler.remove_job(job_id)
                del self.jobs[job_id]
                self.logger.info(f"Removed job: {job_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error removing job {job_id}: {str(e)}")
            return False
    
    def pause_job(self, job_id: str) -> bool:
        """暂停任务"""
        try:
            if job_id in self.jobs:
                self.scheduler.pause_job(job_id)
                self.logger.info(f"Paused job: {job_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error pausing job {job_id}: {str(e)}")
            return False
    
    def resume_job(self, job_id: str) -> bool:
        """恢复任务"""
        try:
            if job_id in self.jobs:
                self.scheduler.resume_job(job_id)
                self.logger.info(f"Resumed job: {job_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error resuming job {job_id}: {str(e)}")
            return False
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """获取任务"""
        return self.jobs.get(job_id)
    
    def get_all_jobs(self) -> List[Job]:
        """获取所有任务"""
        return list(self.jobs.values())
    
    def modify_job(self, job_id: str, **changes) -> Optional[Job]:
        """修改任务"""
        try:
            if job_id in self.jobs:
                job = self.scheduler.modify_job(job_id, **changes)
                self.logger.info(f"Modified job: {job_id}")
                return job
            return None
        except Exception as e:
            self.logger.error(f"Error modifying job {job_id}: {str(e)}")
            return None
    
    async def execute_job(self, job_id: str) -> bool:
        """立即执行任务"""
        try:
            if job_id in self.jobs:
                job = self.jobs[job_id]
                await job.func()
                self.logger.info(f"Executed job: {job_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error executing job {job_id}: {str(e)}")
            return False 