from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import desc
from .base_dao import BaseDAO
from ..models.report import Report
from ..models.content import Content

class ReportDAO(BaseDAO):
    """报告DAO类"""
    
    def __init__(self):
        super().__init__(Report)
    
    def create_report(self, data: Dict[str, Any], content_ids: List[int]) -> Optional[Report]:
        """创建报告"""
        try:
            with self.get_session() as session:
                # 创建报告
                report = Report(**data)
                session.add(report)
                
                # 添加内容关联
                if content_ids:
                    contents = session.query(Content)\
                        .filter(Content.id.in_(content_ids))\
                        .all()
                    report.contents.extend(contents)
                
                session.commit()
                session.refresh(report)
                return report
        except:
            return None
    
    def get_latest_report(self, report_type: str) -> Optional[Report]:
        """获取最新报告"""
        with self.get_session() as session:
            return session.query(Report)\
                .filter_by(report_type=report_type, status=1)\
                .order_by(desc(Report.report_date))\
                .first()
    
    def get_report_by_date(self, report_date: datetime, report_type: str) -> Optional[Report]:
        """获取指定日期的报告"""
        with self.get_session() as session:
            return session.query(Report)\
                .filter_by(
                    report_type=report_type,
                    report_date=report_date.date()
                )\
                .first()
    
    def get_reports_by_date_range(self, start_date: datetime, end_date: datetime,
                                report_type: Optional[str] = None) -> List[Report]:
        """获取日期范围内的报告"""
        with self.get_session() as session:
            query = session.query(Report)\
                .filter(Report.report_date >= start_date.date())\
                .filter(Report.report_date <= end_date.date())\
                .filter(Report.status == 1)
            
            if report_type:
                query = query.filter(Report.report_type == report_type)
            
            return query.order_by(desc(Report.report_date)).all()
    
    def publish_report(self, id: int) -> bool:
        """发布报告"""
        return self.update(id, {'status': 1}) is not None
    
    def unpublish_report(self, id: int) -> bool:
        """取消发布报告"""
        return self.update(id, {'status': 0}) is not None
    
    def add_contents(self, report_id: int, content_ids: List[int]) -> bool:
        """添加内容到报告"""
        try:
            with self.get_session() as session:
                report = session.query(Report).get(report_id)
                if not report:
                    return False
                
                contents = session.query(Content)\
                    .filter(Content.id.in_(content_ids))\
                    .all()
                
                for content in contents:
                    if content not in report.contents:
                        report.contents.append(content)
                
                session.commit()
                return True
        except:
            return False
    
    def remove_contents(self, report_id: int, content_ids: List[int]) -> bool:
        """从报告中移除内容"""
        try:
            with self.get_session() as session:
                report = session.query(Report).get(report_id)
                if not report:
                    return False
                
                contents = session.query(Content)\
                    .filter(Content.id.in_(content_ids))\
                    .all()
                
                for content in contents:
                    if content in report.contents:
                        report.contents.remove(content)
                
                session.commit()
                return True
        except:
            return False
    
    def get_report_stats(self, days: int = 30) -> Dict[str, Any]:
        """获取报告统计信息"""
        with self.get_session() as session:
            start_date = datetime.now() - timedelta(days=days)
            
            # 获取各类型报告数量
            report_counts = session.query(
                Report.report_type,
                func.count(Report.id).label('count')
            )\
                .filter(Report.report_date >= start_date.date())\
                .group_by(Report.report_type)\
                .all()
            
            # 获取发布状态统计
            status_counts = session.query(
                Report.status,
                func.count(Report.id).label('count')
            )\
                .filter(Report.report_date >= start_date.date())\
                .group_by(Report.status)\
                .all()
            
            return {
                'report_counts': {r[0]: r[1] for r in report_counts},
                'status_counts': {s[0]: s[1] for s in status_counts}
            } 