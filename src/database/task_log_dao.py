"""任务日志数据访问对象模块。"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy import desc, and_
from sqlalchemy.future import select
from pydantic import BaseModel
from .base_dao import BaseDAO
from ..models import TaskLog

class TaskLogCreate(BaseModel):
    """任务日志创建模型"""
    task_id: int
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    error: Optional[str] = None
    result: Optional[dict] = None

class TaskLogUpdate(BaseModel):
    """任务日志更新模型"""
    status: Optional[str] = None
    end_time: Optional[datetime] = None
    duration: Optional[int] = None
    error: Optional[str] = None
    result: Optional[dict] = None

class TaskLogDAO(BaseDAO[TaskLog, TaskLogCreate, TaskLogUpdate]):
    """任务日志数据访问对象"""
    
    def __init__(self):
        """初始化任务日志数据访问对象。"""
        super().__init__(TaskLog)
    
    def create_log(self, task_id: str, task_type: str, platform: Optional[str] = None) -> TaskLog:
        """创建任务日志"""
        return self.add({
            'task_id': task_id,
            'task_type': task_type,
            'platform': platform,
            'status': 'running'
        })
    
    def update_log_status(self, log_id: int, status: str,
                         error_message: Optional[str] = None,
                         result: Optional[str] = None) -> bool:
        """更新任务日志状态"""
        data = {
            'status': status,
            'end_time': datetime.now()
        }
        
        if error_message:
            data['error_message'] = error_message
        if result:
            data['result'] = result
            
        return self.update(log_id, data) is not None
    
    def get_task_logs(self, task_id: str, limit: int = 10) -> List[TaskLog]:
        """获取任务的执行记录"""
        with self.get_session() as session:
            return session.query(TaskLog)\
                .filter_by(task_id=task_id)\
                .order_by(desc(TaskLog.start_time))\
                .limit(limit)\
                .all()
    
    def get_platform_logs(self, platform: str, limit: int = 10) -> List[TaskLog]:
        """获取平台的执行记录"""
        with self.get_session() as session:
            return session.query(TaskLog)\
                .filter_by(platform=platform)\
                .order_by(desc(TaskLog.start_time))\
                .limit(limit)\
                .all()
    
    def get_recent_logs(self, days: int = 7) -> List[TaskLog]:
        """获取最近的执行记录"""
        with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            return session.query(TaskLog)\
                .filter(TaskLog.start_time >= start_date)\
                .order_by(desc(TaskLog.start_time))\
                .all()
    
    def get_failed_logs(self, days: int = 1) -> List[TaskLog]:
        """获取失败的执行记录"""
        with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            return session.query(TaskLog)\
                .filter(TaskLog.start_time >= start_date)\
                .filter_by(status='failed')\
                .order_by(desc(TaskLog.start_time))\
                .all()
    
    def get_running_logs(self) -> List[TaskLog]:
        """获取正在运行的任务记录"""
        with self.get_session() as session:
            return session.query(TaskLog)\
                .filter_by(status='running')\
                .order_by(desc(TaskLog.start_time))\
                .all()
    
    def get_task_stats(self, days: int = 7) -> Dict[str, Any]:
        """获取任务统计信息"""
        with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            
            # 获取任务类型统计
            type_stats = session.query(
                TaskLog.task_type,
                func.count(TaskLog.id).label('count')
            )\
                .filter(TaskLog.start_time >= start_date)\
                .group_by(TaskLog.task_type)\
                .all()
            
            # 获取状态统计
            status_stats = session.query(
                TaskLog.status,
                func.count(TaskLog.id).label('count')
            )\
                .filter(TaskLog.start_time >= start_date)\
                .group_by(TaskLog.status)\
                .all()
            
            # 获取平台统计
            platform_stats = session.query(
                TaskLog.platform,
                func.count(TaskLog.id).label('count')
            )\
                .filter(TaskLog.start_time >= start_date)\
                .filter(TaskLog.platform.isnot(None))\
                .group_by(TaskLog.platform)\
                .all()
            
            return {
                'type_stats': {t[0]: t[1] for t in type_stats},
                'status_stats': {s[0]: s[1] for s in status_stats},
                'platform_stats': {p[0]: p[1] for p in platform_stats}
            }

    async def get_logs_by_task_id(self, task_id: int) -> List[TaskLog]:
        """获取任务的日志列表。

        Args:
            task_id: 任务ID

        Returns:
            任务日志列表
        """
        query = select(TaskLog).where(TaskLog.task_id == task_id).order_by(desc(TaskLog.create_time))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_logs_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[TaskLog]:
        """获取时间范围内的日志列表。

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            任务日志列表
        """
        query = select(TaskLog).where(
            and_(
                TaskLog.create_time >= start_time,
                TaskLog.create_time <= end_time
            )
        ).order_by(desc(TaskLog.create_time))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_failed_logs_by_time_range(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[TaskLog]:
        """获取时间范围内的失败日志列表。

        Args:
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            失败的任务日志列表
        """
        query = select(TaskLog).where(
            and_(
                TaskLog.create_time >= start_time,
                TaskLog.create_time <= end_time,
                TaskLog.status == 'failed'
            )
        ).order_by(desc(TaskLog.create_time))
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_latest_log(self, task_id: int) -> Optional[TaskLog]:
        """获取任务的最新日志。

        Args:
            task_id: 任务ID

        Returns:
            最新的任务日志，如果不存在则返回None
        """
        query = select(TaskLog).where(
            TaskLog.task_id == task_id
        ).order_by(desc(TaskLog.create_time)).limit(1)
        result = await self.session.execute(query)
        return result.scalar_one_or_none() 