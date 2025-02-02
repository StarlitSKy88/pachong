from typing import Dict, Any, List
from datetime import datetime
import asyncio
import json
from .base_scheduler import BaseScheduler
from ..crawlers import XHSCrawler, BiliBiliCrawler
from ..database import platform_dao, task_log_dao

class CrawlerScheduler(BaseScheduler):
    """爬虫任务调度器"""
    
    def __init__(self):
        """初始化爬虫调度器"""
        super().__init__()
        self.crawlers = {
            'xhs': XHSCrawler(),
            'bilibili': BiliBiliCrawler()
        }
        self.tasks: Dict[str, Dict[str, Any]] = {}  # 任务配置字典
        
    async def crawl_task(self, task_id: str):
        """执行爬虫任务"""
        # 创建任务日志
        task_log = task_log_dao.create_log(
            task_id=task_id,
            task_type='crawler',
            platform=self.tasks[task_id]['platform']
        )
        
        try:
            # 获取任务配置
            task_config = self.tasks.get(task_id)
            if not task_config:
                raise ValueError(f"Task config not found: {task_id}")
            
            # 获取爬虫实例
            crawler = self.crawlers.get(task_config['platform'])
            if not crawler:
                raise ValueError(f"Crawler not found for platform: {task_config['platform']}")
            
            # 执行爬取
            self.logger.info(f"Start crawling task: {task_id}")
            await crawler.crawl(
                keyword=task_config['keyword'],
                max_pages=task_config.get('max_pages', 5)
            )
            self.logger.info(f"Finished crawling task: {task_id}")
            
            # 更新任务日志状态为成功
            task_log_dao.update_log_status(
                log_id=task_log.id,
                status='success',
                result=json.dumps({
                    'keyword': task_config['keyword'],
                    'max_pages': task_config.get('max_pages', 5)
                })
            )
            
        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error executing crawl task {task_id}: {error_msg}")
            
            # 更新任务日志状态为失败
            task_log_dao.update_log_status(
                log_id=task_log.id,
                status='failed',
                error_message=error_msg
            )
    
    def add_crawl_task(self, task_id: str, platform: str, keyword: str,
                      schedule: str = '0 */4 * * *',  # 每4小时执行一次
                      max_pages: int = 5) -> bool:
        """添加爬虫任务"""
        try:
            # 验证平台
            if platform not in self.crawlers:
                self.logger.error(f"Invalid platform: {platform}")
                return False
            
            # 保存任务配置
            self.tasks[task_id] = {
                'platform': platform,
                'keyword': keyword,
                'max_pages': max_pages,
                'schedule': schedule,
                'status': 'active'
            }
            
            # 添加定时任务
            job = self.add_job(
                job_id=task_id,
                func=lambda: asyncio.create_task(self.crawl_task(task_id)),
                trigger='cron',
                **self._parse_schedule(schedule)
            )
            
            return job is not None
            
        except Exception as e:
            self.logger.error(f"Error adding crawl task {task_id}: {str(e)}")
            return False
    
    def _parse_schedule(self, schedule: str) -> Dict[str, Any]:
        """解析cron表达式"""
        try:
            minute, hour, day, month, day_of_week = schedule.split()
            return {
                'minute': minute,
                'hour': hour,
                'day': day,
                'month': month,
                'day_of_week': day_of_week
            }
        except:
            # 默认每4小时执行一次
            return {
                'minute': '0',
                'hour': '*/4'
            }
    
    def update_task_config(self, task_id: str, **config) -> bool:
        """更新任务配置"""
        try:
            if task_id not in self.tasks:
                return False
            
            # 更新配置
            self.tasks[task_id].update(config)
            
            # 如果更新了调度时间，重新调度任务
            if 'schedule' in config:
                return self.reschedule_task(task_id, config['schedule'])
                
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating task config {task_id}: {str(e)}")
            return False
    
    def reschedule_task(self, task_id: str, schedule: str) -> bool:
        """重新调度任务"""
        try:
            if task_id not in self.tasks:
                return False
            
            # 更新任务调度
            job = self.modify_job(
                job_id=task_id,
                trigger='cron',
                **self._parse_schedule(schedule)
            )
            
            return job is not None
            
        except Exception as e:
            self.logger.error(f"Error rescheduling task {task_id}: {str(e)}")
            return False
    
    def get_task_config(self, task_id: str) -> Dict[str, Any]:
        """获取任务配置"""
        return self.tasks.get(task_id, {})
    
    def get_all_task_configs(self) -> Dict[str, Dict[str, Any]]:
        """获取所有任务配置"""
        return self.tasks
    
    def get_platform_tasks(self, platform: str) -> List[Dict[str, Any]]:
        """获取平台任务"""
        return [
            {'task_id': task_id, **config}
            for task_id, config in self.tasks.items()
            if config['platform'] == platform
        ]
    
    def get_task_logs(self, task_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取任务执行记录"""
        logs = task_log_dao.get_task_logs(task_id, limit)
        return [log.to_dict() for log in logs]
    
    def get_platform_logs(self, platform: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取平台执行记录"""
        logs = task_log_dao.get_platform_logs(platform, limit)
        return [log.to_dict() for log in logs]
    
    def get_task_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取任务统计信息"""
        return task_log_dao.get_task_stats(days) 