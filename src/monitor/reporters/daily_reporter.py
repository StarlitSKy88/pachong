from typing import Dict, List, Any
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from collections import Counter
from .base_reporter import BaseReporter
from ..database import content_dao, report_dao
from ..models.content import Content

class DailyReporter(BaseReporter):
    """日报生成器"""
    
    async def _fetch_contents(self, conditions: Dict) -> List[Content]:
        """获取内容数据"""
        start_date = conditions['start_date']
        end_date = conditions['end_date']
        platform_ids = conditions.get('platform_ids')
        category_ids = conditions.get('category_ids')
        
        # 从数据库获取内容
        contents = await content_dao.get_by_date_range(
            start_date=start_date,
            end_date=end_date,
            platform_ids=platform_ids,
            category_ids=category_ids
        )
        
        return contents
    
    async def analyze_data(self, data: pd.DataFrame) -> Dict[str, Any]:
        """分析数据"""
        if data.empty:
            return {}
            
        analysis = {}
        
        # 1. 基础统计
        analysis['basic_stats'] = {
            'total_contents': len(data),
            'total_platforms': data['platform'].nunique(),
            'total_categories': data['category'].nunique(),
            'total_authors': data['author'].nunique()
        }
        
        # 2. 平台分布
        platform_stats = data['platform'].value_counts().to_dict()
        analysis['platform_stats'] = {
            'distribution': platform_stats,
            'percentage': {k: v/len(data)*100 for k, v in platform_stats.items()}
        }
        
        # 3. 分类分布
        category_stats = data['category'].value_counts().to_dict()
        analysis['category_stats'] = {
            'distribution': category_stats,
            'percentage': {k: v/len(data)*100 for k, v in category_stats.items()}
        }
        
        # 4. 互动数据分析
        engagement_stats = {
            'likes': {
                'total': data['likes'].sum(),
                'avg': data['likes'].mean(),
                'max': data['likes'].max(),
                'min': data['likes'].min()
            },
            'comments': {
                'total': data['comments'].sum(),
                'avg': data['comments'].mean(),
                'max': data['comments'].max(),
                'min': data['comments'].min()
            },
            'shares': {
                'total': data['shares'].sum(),
                'avg': data['shares'].mean(),
                'max': data['shares'].max(),
                'min': data['shares'].min()
            }
        }
        analysis['engagement_stats'] = engagement_stats
        
        # 5. 热门内容
        top_contents = data.nlargest(10, 'likes')[
            ['title', 'platform', 'author', 'likes', 'comments', 'shares', 'url']
        ].to_dict('records')
        analysis['top_contents'] = top_contents
        
        # 6. 标签分析
        all_tags = [tag for tags in data['tags'] for tag in tags]
        tag_counter = Counter(all_tags)
        analysis['tag_stats'] = {
            'top_tags': dict(tag_counter.most_common(20)),
            'total_tags': len(tag_counter)
        }
        
        # 7. 发布时间分析
        data['hour'] = data['publish_time'].dt.hour
        hourly_stats = data['hour'].value_counts().sort_index().to_dict()
        analysis['time_stats'] = {
            'hourly_distribution': hourly_stats
        }
        
        # 8. 作者分析
        author_stats = data.groupby('author').agg({
            'platform': 'first',
            'likes': 'sum',
            'comments': 'sum',
            'shares': 'sum'
        }).sort_values('likes', ascending=False)
        
        analysis['author_stats'] = {
            'top_authors': author_stats.head(10).to_dict('records'),
            'total_authors': len(author_stats)
        }
        
        return analysis
    
    async def create_report(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """生成报告"""
        if not analysis:
            return {
                'title': '每日内容报告',
                'date': datetime.now().strftime('%Y-%m-%d'),
                'content': '无数据',
                'status': 'empty'
            }
        
        # 生成报告内容
        report_content = self.render_template(
            'daily_report.html',
            analysis=analysis,
            date=datetime.now().strftime('%Y-%m-%d')
        )
        
        # 保存报告
        filename = f"daily_report_{datetime.now().strftime('%Y%m%d')}.html"
        self.save_report(report_content, filename)
        
        # 创建报告记录
        report = await report_dao.create_report({
            'title': f"每日内容报告 - {datetime.now().strftime('%Y-%m-%d')}",
            'summary': f"共采集{analysis['basic_stats']['total_contents']}条内容",
            'report_type': 'daily',
            'report_date': datetime.now(),
            'status': 1
        })
        
        return {
            'title': report.title,
            'date': report.report_date.strftime('%Y-%m-%d'),
            'content': report_content,
            'status': 'success',
            'stats': analysis['basic_stats']
        }
    
    async def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日报告"""
        # 获取昨天的日期范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=1)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        # 生成报告
        return await self.generate_report(start_date, end_date) 