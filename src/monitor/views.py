from flask import render_template
from datetime import datetime, timedelta
from ..database import content_dao, error_log_dao

@app.route('/monitor/errors')
async def error_analysis():
    """错误分析页面"""
    # 获取错误统计
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    error_stats = {
        'total': await error_log_dao.count_errors(),
        'today': await error_log_dao.count_errors(start_time=start_time),
        'main_type': await error_log_dao.get_main_error_type()
    }
    
    # 获取最近错误
    recent_errors = await error_log_dao.get_recent_errors(limit=100)
    
    return render_template(
        'monitor/error_analysis.html',
        error_stats=error_stats,
        errors=recent_errors
    )

@app.route('/monitor/results')
async def result_analysis():
    """结果统计页面"""
    platforms = ['xhs', 'bilibili']
    stats = {}
    
    for platform in platforms:
        # 获取平台统计数据
        platform_stats = await content_dao.get_platform_stats(platform)
        
        # 计算成功率
        total = platform_stats['success'] + platform_stats['failed']
        success_rate = (platform_stats['success'] / total * 100) if total > 0 else 0
        
        stats[platform] = {
            'success': platform_stats['success'],
            'failed': platform_stats['failed'],
            'success_rate': round(success_rate, 2),
            'avg_time': round(platform_stats['avg_time'], 2),
            'content_count': platform_stats['content_count'],
            'last_update': platform_stats['last_update'].strftime('%Y-%m-%d %H:%M:%S')
        }
    
    return render_template(
        'monitor/result_analysis.html',
        platforms=platforms,
        stats=stats
    ) 