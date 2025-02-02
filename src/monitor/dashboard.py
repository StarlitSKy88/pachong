import os
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import json
from aiohttp import web
import aiohttp_jinja2
import jinja2

from .metrics import metrics_collector
from .alert import alert_engine

logger = logging.getLogger(__name__)

class DashboardServer:
    """监控面板服务器"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        """初始化服务器
        
        Args:
            host: 监听地址
            port: 监听端口
        """
        self.host = host
        self.port = port
        self.app = web.Application()
        self.setup_routes()
        self.setup_templates()
    
    def setup_routes(self) -> None:
        """设置路由"""
        self.app.router.add_get('/', self.handle_index)
        self.app.router.add_get('/api/metrics', self.handle_metrics)
        self.app.router.add_get('/api/alerts', self.handle_alerts)
        self.app.router.add_get('/api/platform_stats', self.handle_platform_stats)
        self.app.router.add_static('/static', 'src/monitor/static')
    
    def setup_templates(self) -> None:
        """设置模板"""
        aiohttp_jinja2.setup(
            self.app,
            loader=jinja2.FileSystemLoader('src/monitor/templates')
        )
    
    @aiohttp_jinja2.template('index.html')
    async def handle_index(self, request: web.Request) -> Dict[str, Any]:
        """处理首页请求
        
        Args:
            request: 请求对象
            
        Returns:
            模板数据
        """
        return {
            'title': '监控面板',
            'refresh_interval': 5000  # 5秒刷新一次
        }
    
    async def handle_metrics(self, request: web.Request) -> web.Response:
        """处理指标请求
        
        Args:
            request: 请求对象
            
        Returns:
            响应对象
        """
        metrics = {}
        for platform, m in metrics_collector.metrics.items():
            metrics[platform] = {
                'total_requests': m.total_requests,
                'success_requests': m.success_requests,
                'failed_requests': m.failed_requests,
                'success_rate': m.success_rate,
                'total_items': m.total_items,
                'success_items': m.success_items,
                'failed_items': m.failed_items,
                'item_success_rate': m.item_success_rate,
                'average_response_time': m.average_response_time,
                'error_messages': m.error_messages[-10:],  # 最近10条错误
                'duration': str(m.duration),
                'start_time': m.start_time.isoformat(),
                'end_time': m.end_time.isoformat() if m.end_time else None
            }
        
        return web.json_response(metrics)
    
    async def handle_alerts(self, request: web.Request) -> web.Response:
        """处理告警请求
        
        Args:
            request: 请求对象
            
        Returns:
            响应对象
        """
        # 获取时间范围
        start = request.query.get('start')
        end = request.query.get('end')
        severity = request.query.get('severity')
        
        alerts = alert_engine.alert_history
        
        # 按时间过滤
        if start:
            start_time = datetime.fromisoformat(start)
            alerts = [
                alert for alert in alerts
                if datetime.fromisoformat(alert['time']) >= start_time
            ]
        
        if end:
            end_time = datetime.fromisoformat(end)
            alerts = [
                alert for alert in alerts
                if datetime.fromisoformat(alert['time']) <= end_time
            ]
        
        # 按严重程度过滤
        if severity:
            alerts = [
                alert for alert in alerts
                if alert['severity'] == severity
            ]
        
        return web.json_response(alerts)
    
    async def handle_platform_stats(self, request: web.Request) -> web.Response:
        """处理平台统计请求
        
        Args:
            request: 请求对象
            
        Returns:
            响应对象
        """
        stats = await metrics_collector.get_platform_stats()
        return web.json_response(stats)
    
    async def run(self) -> None:
        """运行服务器"""
        runner = web.AppRunner(self.app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        
        logger.info(f"Starting dashboard server at http://{self.host}:{self.port}")
        await site.start()

# 创建HTML模板
def create_templates() -> None:
    """创建HTML模板"""
    template_dir = 'src/monitor/templates'
    os.makedirs(template_dir, exist_ok=True)
    
    # 创建基础模板
    base_template = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/">监控面板</a>
        </div>
    </nav>
    
    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="/static/app.js"></script>
</body>
</html>
"""
    
    with open(os.path.join(template_dir, 'base.html'), 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    # 创建首页模板
    index_template = """
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title">平台状态</h5>
            </div>
            <div class="card-body">
                <div id="platform-stats"></div>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-6 mb-4">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title">请求统计</h5>
            </div>
            <div class="card-body">
                <canvas id="request-chart"></canvas>
            </div>
        </div>
    </div>
    
    <div class="col-md-6 mb-4">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title">内容统计</h5>
            </div>
            <div class="card-body">
                <canvas id="content-chart"></canvas>
            </div>
        </div>
    </div>
</div>

<div class="row">
    <div class="col-md-12 mb-4">
        <div class="card">
            <div class="card-header">
                <h5 class="card-title">告警历史</h5>
            </div>
            <div class="card-body">
                <div id="alert-history"></div>
            </div>
        </div>
    </div>
</div>

<script>
    const refreshInterval = {{ refresh_interval }};
</script>
{% endblock %}
"""
    
    with open(os.path.join(template_dir, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(index_template)
    
    # 创建静态目录
    static_dir = 'src/monitor/static'
    os.makedirs(static_dir, exist_ok=True)
    
    # 创建样式文件
    style_css = """
body {
    background-color: #f8f9fa;
}

.card {
    box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
}

.card-header {
    background-color: #f8f9fa;
    border-bottom: 1px solid rgba(0, 0, 0, 0.125);
}

.table th {
    font-weight: 500;
}

.badge {
    font-size: 0.875rem;
}

.badge-info {
    background-color: #17a2b8;
}

.badge-warning {
    background-color: #ffc107;
}

.badge-error {
    background-color: #dc3545;
}

.badge-critical {
    background-color: #6610f2;
}
"""
    
    with open(os.path.join(static_dir, 'style.css'), 'w', encoding='utf-8') as f:
        f.write(style_css)
    
    # 创建JavaScript文件
    app_js = """
// 更新平台状态
async function updatePlatformStats() {
    const response = await fetch('/api/platform_stats');
    const stats = await response.json();
    
    const container = document.getElementById('platform-stats');
    container.innerHTML = '';
    
    for (const [platform, data] of Object.entries(stats)) {
        const card = document.createElement('div');
        card.className = 'card mb-3';
        card.innerHTML = `
            <div class="card-body">
                <h5 class="card-title">${platform}</h5>
                <div class="row">
                    <div class="col-md-4">
                        <p>状态：${data.is_active ? '活跃' : '停用'}</p>
                        <p>错误次数：${data.error_count}</p>
                        <p>最后错误：${data.last_error || '无'}</p>
                    </div>
                    <div class="col-md-4">
                        <p>内容总数：${data.content_stats.total}</p>
                        <p>活跃内容：${data.content_stats.active}</p>
                        <p>待审核：${data.content_stats.pending}</p>
                    </div>
                    <div class="col-md-4">
                        <p>平均质量：${data.content_stats.avg_quality.toFixed(2)}</p>
                        <p>平均相关度：${data.content_stats.avg_relevance.toFixed(2)}</p>
                        <p>总浏览量：${data.content_stats.total_views}</p>
                    </div>
                </div>
            </div>
        `;
        container.appendChild(card);
    }
}

// 更新请求统计图表
async function updateRequestChart() {
    const response = await fetch('/api/metrics');
    const metrics = await response.json();
    
    const labels = Object.keys(metrics);
    const successData = labels.map(platform => metrics[platform].success_rate * 100);
    const responseTimeData = labels.map(platform => metrics[platform].average_response_time);
    
    const ctx = document.getElementById('request-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '成功率 (%)',
                    data: successData,
                    backgroundColor: 'rgba(40, 167, 69, 0.5)',
                    borderColor: 'rgb(40, 167, 69)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                },
                {
                    label: '响应时间 (秒)',
                    data: responseTimeData,
                    backgroundColor: 'rgba(0, 123, 255, 0.5)',
                    borderColor: 'rgb(0, 123, 255)',
                    borderWidth: 1,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y1: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: '成功率 (%)'
                    }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    min: 0,
                    title: {
                        display: true,
                        text: '响应时间 (秒)'
                    }
                }
            }
        }
    });
}

// 更新内容统计图表
async function updateContentChart() {
    const response = await fetch('/api/metrics');
    const metrics = await response.json();
    
    const labels = Object.keys(metrics);
    const successData = labels.map(platform => metrics[platform].item_success_rate * 100);
    const totalData = labels.map(platform => metrics[platform].total_items);
    
    const ctx = document.getElementById('content-chart').getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: '成功率 (%)',
                    data: successData,
                    backgroundColor: 'rgba(40, 167, 69, 0.5)',
                    borderColor: 'rgb(40, 167, 69)',
                    borderWidth: 1,
                    yAxisID: 'y1'
                },
                {
                    label: '总数量',
                    data: totalData,
                    backgroundColor: 'rgba(0, 123, 255, 0.5)',
                    borderColor: 'rgb(0, 123, 255)',
                    borderWidth: 1,
                    yAxisID: 'y2'
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y1: {
                    type: 'linear',
                    position: 'left',
                    min: 0,
                    max: 100,
                    title: {
                        display: true,
                        text: '成功率 (%)'
                    }
                },
                y2: {
                    type: 'linear',
                    position: 'right',
                    min: 0,
                    title: {
                        display: true,
                        text: '总数量'
                    }
                }
            }
        }
    });
}

// 更新告警历史
async function updateAlertHistory() {
    const response = await fetch('/api/alerts');
    const alerts = await response.json();
    
    const container = document.getElementById('alert-history');
    container.innerHTML = `
        <table class="table">
            <thead>
                <tr>
                    <th>时间</th>
                    <th>规则</th>
                    <th>严重程度</th>
                    <th>消息</th>
                </tr>
            </thead>
            <tbody>
                ${alerts.map(alert => `
                    <tr>
                        <td>${new Date(alert.time).toLocaleString()}</td>
                        <td>${alert.rule}</td>
                        <td><span class="badge badge-${alert.severity}">${alert.severity}</span></td>
                        <td>${alert.message}</td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
}

// 定时更新
async function update() {
    await Promise.all([
        updatePlatformStats(),
        updateRequestChart(),
        updateContentChart(),
        updateAlertHistory()
    ]);
}

// 初始化
update();
setInterval(update, refreshInterval);
"""
    
    with open(os.path.join(static_dir, 'app.js'), 'w', encoding='utf-8') as f:
        f.write(app_js)

# 创建模板文件
create_templates()

# 全局面板服务器
dashboard_server = DashboardServer() 