import asyncio
import logging
from datetime import datetime
from .metrics_collector import MetricsCollector
from .alert_engine import AlertEngine, AlertRule
from .alert_notifier import AlertNotifier

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_metrics_collector():
    """测试指标收集器"""
    print("\nTesting Metrics Collector...")
    collector = MetricsCollector()
    
    # 收集指标
    print("\nCollecting metrics...")
    await collector.collect_all_metrics()
    
    # 打印系统指标
    system_metrics = collector.get_metrics_by_prefix('system.')
    print("\nSystem Metrics:")
    for name, metric in system_metrics.items():
        print(f"{name}: {metric['value']} {metric['unit']}")
    
    # 打印爬虫指标
    crawler_metrics = collector.get_metrics_by_prefix('crawler.')
    print("\nCrawler Metrics:")
    for name, metric in crawler_metrics.items():
        print(f"{name}: {metric['value']} {metric['unit']}")
    
    # 打印任务指标
    task_metrics = collector.get_metrics_by_prefix('task.')
    print("\nTask Metrics:")
    for name, metric in task_metrics.items():
        print(f"{name}: {metric['value']} {metric['unit']}")

async def test_alert_engine():
    """测试告警引擎"""
    print("\nTesting Alert Engine...")
    collector = MetricsCollector()
    engine = AlertEngine(collector)
    
    # 添加测试规则
    print("\nAdding test rules...")
    engine.add_rule(AlertRule(
        name='test_cpu_usage',
        metric='system.cpu.usage',
        operator='>',
        threshold=50,
        severity='warning',
        description='测试CPU使用率告警',
        interval=60
    ))
    
    engine.add_rule(AlertRule(
        name='test_memory_usage',
        metric='system.memory.percent',
        operator='>',
        threshold=50,
        severity='warning',
        description='测试内存使用率告警',
        interval=60
    ))
    
    # 收集指标并检查规则
    print("\nCollecting metrics and checking rules...")
    await collector.collect_all_metrics()
    await engine.check_rules()
    
    # 打印告警
    alerts = engine.get_alerts()
    print("\nAlerts:")
    for alert in alerts:
        print(f"Rule: {alert.rule.name}")
        print(f"Severity: {alert.rule.severity}")
        print(f"Value: {alert.value}")
        print(f"Threshold: {alert.rule.operator} {alert.rule.threshold}")
        print(f"Time: {alert.timestamp}")
        print("---")

async def test_alert_notifier():
    """测试告警通知器"""
    print("\nTesting Alert Notifier...")
    notifier = AlertNotifier()
    
    # 配置邮件通知
    print("\nConfiguring email notification...")
    notifier.configure_email(
        host='smtp.example.com',
        port=587,
        username='your-email@example.com',
        password='your-password',
        recipients=['admin@example.com']
    )
    
    # 配置钉钉通知
    print("\nConfiguring DingTalk notification...")
    notifier.configure_dingtalk(
        access_token='your-access-token',
        secret='your-secret'
    )
    
    # 配置企业微信通知
    print("\nConfiguring WeChat notification...")
    notifier.configure_wechat(
        corp_id='your-corp-id',
        corp_secret='your-corp-secret',
        agent_id='your-agent-id'
    )
    
    # 创建测试告警
    print("\nCreating test alert...")
    rule = AlertRule(
        name='test_alert',
        metric='test.metric',
        operator='>',
        threshold=100,
        severity='warning',
        description='测试告警通知'
    )
    
    alert = Alert(rule=rule, value=150)
    
    # 发送通知
    print("\nSending notifications...")
    await notifier.send_all(alert)

async def main():
    """主函数"""
    try:
        # 测试指标收集器
        await test_metrics_collector()
        
        # 测试告警引擎
        await test_alert_engine()
        
        # 测试告警通知器
        await test_alert_notifier()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 