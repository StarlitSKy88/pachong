"""告警系统API接口模块"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

from monitor.alert_engine import AlertEngine
from monitor.alert_rule import AlertRule, AlertRuleGroup, AlertStatus, AlertSeverity
from monitor.metrics_collector import MetricsCollector
from monitor.alert_notifier import AlertNotifier
from monitor.alert_aggregator import AlertAggregator

app = FastAPI(title="告警系统API", description="提供告警系统的Web管理接口")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化组件
metrics_collector = MetricsCollector()
notifier = AlertNotifier()
aggregator = AlertAggregator()
alert_engine = AlertEngine(metrics_collector, notifier, aggregator)

@app.get("/api/rules", response_model=List[Dict])
async def get_rules():
    """获取所有告警规则"""
    rules = []
    for group in alert_engine.rule_groups.values():
        group_data = {
            "name": group.name,
            "description": group.description,
            "enabled": group.enabled,
            "rules": []
        }
        
        for rule in group.rules:
            rule_data = {
                "name": rule.name,
                "metric": rule.metric,
                "operator": rule.operator,
                "threshold": rule.threshold,
                "severity": rule.severity,
                "description": rule.description,
                "interval": rule.interval,
                "enabled": rule.enabled,
                "status": rule.status
            }
            group_data["rules"].append(rule_data)
        
        rules.append(group_data)
    
    return rules

@app.post("/api/rules/group")
async def create_rule_group(group: Dict):
    """创建规则组"""
    try:
        new_group = AlertRuleGroup(
            name=group["name"],
            description=group.get("description", "")
        )
        alert_engine.add_rule_group(new_group)
        return {"message": "规则组创建成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/rules/rule")
async def create_rule(rule: Dict):
    """创建告警规则"""
    try:
        new_rule = AlertRule(
            name=rule["name"],
            metric=rule["metric"],
            operator=rule["operator"],
            threshold=float(rule["threshold"]),
            severity=rule["severity"],
            description=rule.get("description", ""),
            interval=int(rule.get("interval", 60))
        )
        
        group_name = rule.get("group")
        if group_name:
            if group_name not in alert_engine.rule_groups:
                raise HTTPException(status_code=404, detail=f"规则组不存在: {group_name}")
            alert_engine.rule_groups[group_name].add_rule(new_rule)
        else:
            alert_engine.add_rule(new_rule)
            
        return {"message": "规则创建成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.put("/api/rules/group/{name}/enable")
async def enable_rule_group(name: str):
    """启用规则组"""
    if name not in alert_engine.rule_groups:
        raise HTTPException(status_code=404, detail=f"规则组不存在: {name}")
    alert_engine.rule_groups[name].enable()
    return {"message": "规则组已启用"}

@app.put("/api/rules/group/{name}/disable")
async def disable_rule_group(name: str):
    """禁用规则组"""
    if name not in alert_engine.rule_groups:
        raise HTTPException(status_code=404, detail=f"规则组不存在: {name}")
    alert_engine.rule_groups[name].disable()
    return {"message": "规则组已禁用"}

@app.get("/api/alerts/active")
async def get_active_alerts():
    """获取活动告警"""
    alerts = []
    for alert in alert_engine.get_active_alerts():
        alerts.append({
            "name": alert.rule.name,
            "description": alert.rule.description,
            "metric": alert.rule.metric,
            "value": alert.value,
            "threshold": alert.rule.threshold,
            "severity": alert.rule.severity,
            "status": alert.status,
            "timestamp": alert.timestamp.isoformat()
        })
    return alerts

@app.get("/api/alerts/history")
async def get_alert_history(
    hours: Optional[int] = 24,
    severity: Optional[str] = None,
    status: Optional[str] = None
):
    """获取告警历史"""
    alerts = alert_engine.get_alerts(
        severity=severity,
        status=status,
        start_time=datetime.now() - timedelta(hours=hours)
    )
    
    return [{
        "name": alert.rule.name,
        "description": alert.rule.description,
        "metric": alert.rule.metric,
        "value": alert.value,
        "threshold": alert.rule.threshold,
        "severity": alert.rule.severity,
        "status": alert.status,
        "timestamp": alert.timestamp.isoformat()
    } for alert in alerts]

@app.get("/api/stats/aggregation")
async def get_aggregation_stats():
    """获取告警聚合统计"""
    return alert_engine.get_aggregation_stats()

@app.get("/api/metrics")
async def get_metrics():
    """获取当前指标值"""
    return metrics_collector.get_metrics()

@app.post("/api/notifier/config")
async def configure_notifier(config: Dict):
    """配置通知器"""
    try:
        if "email" in config:
            notifier.configure_email(**config["email"])
        
        if "webhook" in config:
            notifier.configure_webhook(**config["webhook"])
        
        if "dingtalk" in config:
            notifier.configure_dingtalk(**config["dingtalk"])
        
        if "wechat" in config:
            notifier.configure_wechat(**config["wechat"])
        
        return {"message": "通知器配置成功"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e)) 