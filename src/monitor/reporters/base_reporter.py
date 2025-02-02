from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import pandas as pd
import logging
from abc import ABC, abstractmethod
from jinja2 import Environment, FileSystemLoader
import os
from ..database import content_dao, platform_dao, category_dao, tag_dao
from ..models.content import Content

class BaseReporter(ABC):
    """报告生成器基类"""
    
    def __init__(self):
        self.logger = logging.getLogger('Reporter')
        self.template_env = Environment(
            loader=FileSystemLoader('templates/reports')
        )
        
    async def generate_report(self, start_date: datetime, end_date: datetime,
                            platforms: Optional[List[str]] = None,
                            categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """生成报告"""
        try:
            # 获取数据
            data = await self.fetch_data(start_date, end_date, platforms, categories)
            
            # 分析数据
            analysis = await self.analyze_data(data)
            
            # 生成报告内容
            report = await self.create_report(analysis)
            
            return report
        except Exception as e:
            self.logger.error(f"Error generating report: {str(e)}")
            raise
    
    async def fetch_data(self, start_date: datetime, end_date: datetime,
                        platforms: Optional[List[str]] = None,
                        categories: Optional[List[str]] = None) -> pd.DataFrame:
        """获取数据"""
        try:
            # 构建查询条件
            conditions = {
                'start_date': start_date,
                'end_date': end_date
            }
            
            if platforms:
                platform_ids = []
                for platform_name in platforms:
                    platform = platform_dao.get_by_name(platform_name)
                    if platform:
                        platform_ids.append(platform.id)
                if platform_ids:
                    conditions['platform_ids'] = platform_ids
            
            if categories:
                category_ids = []
                for category_name in categories:
                    category = category_dao.get_by_name(category_name)
                    if category:
                        category_ids.append(category.id)
                if category_ids:
                    conditions['category_ids'] = category_ids
            
            # 获取内容数据
            contents = await self._fetch_contents(conditions)
            
            # 转换为DataFrame
            df = pd.DataFrame([
                {
                    'id': c.id,
                    'platform': c.platform.name if c.platform else None,
                    'category': c.category.name if c.category else None,
                    'title': c.title,
                    'content': c.content,
                    'summary': c.summary,
                    'url': c.url,
                    'author': c.author,
                    'publish_time': c.publish_time,
                    'collect_time': c.collect_time,
                    'likes': c.likes,
                    'comments': c.comments,
                    'shares': c.shares,
                    'tags': [tag.name for tag in c.tags]
                }
                for c in contents
            ])
            
            return df
            
        except Exception as e:
            self.logger.error(f"Error fetching data: {str(e)}")
            raise
    
    async def _fetch_contents(self, conditions: Dict) -> List[Content]:
        """获取内容数据"""
        # 这里需要实现具体的数据获取逻辑
        return []
    
    @abstractmethod
    async def analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析数据"""
        pass
    
    @abstractmethod
    async def create_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        pass
    
    def render_template(self, template_name: str, **kwargs) -> str:
        """渲染模板"""
        try:
            template = self.template_env.get_template(template_name)
            return template.render(**kwargs)
        except Exception as e:
            self.logger.error(f"Error rendering template: {str(e)}")
            raise
    
    def save_report(self, report_content: str, filename: str):
        """保存报告"""
        try:
            os.makedirs('output/reports', exist_ok=True)
            filepath = os.path.join('output/reports', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(report_content)
            self.logger.info(f"Report saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving report: {str(e)}")
            raise
    
    def get_date_range(self, days: int) -> tuple:
        """获取日期范围"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return start_date, end_date 