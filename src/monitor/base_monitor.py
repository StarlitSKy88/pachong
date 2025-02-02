from typing import Dict, List, Any, Optional
import logging
from abc import ABC, abstractmethod
from datetime import datetime
import psutil
import os
import json

class BaseMonitor(ABC):
    """监控器基类"""
    
    def __init__(self):
        self.logger = logging.getLogger('Monitor')
        self.metrics: Dict[str, Any] = {}
        self.alerts: List[Dict] = []
        self.alert_rules: Dict[str, Dict] = {}
    
    def add_metric(self, name: str, value: Any, labels: Optional[Dict] = None):
        """添加监控指标"""
        self.metrics[name] = {
            'value': value,
            'labels': labels or {},
            'timestamp': datetime.now()
        }
    
    def get_metric(self, name: str) -> Optional[Dict]:
        """获取监控指标"""
        return self.metrics.get(name)
    
    def clear_metrics(self):
        """清除监控指标"""
        self.metrics.clear()
    
    def add_alert_rule(self, name: str, rule: Dict):
        """添加告警规则"""
        self.alert_rules[name] = rule
        self.logger.info(f"Added alert rule: {name}")
    
    def remove_alert_rule(self, name: str):
        """移除告警规则"""
        if name in self.alert_rules:
            del self.alert_rules[name]
            self.logger.info(f"Removed alert rule: {name}")
    
    def add_alert(self, alert: Dict):
        """添加告警"""
        alert['timestamp'] = datetime.now()
        self.alerts.append(alert)
        self.logger.warning(f"Alert: {alert['message']}")
    
    def get_alerts(self, limit: int = 100) -> List[Dict]:
        """获取告警列表"""
        return sorted(
            self.alerts,
            key=lambda x: x['timestamp'],
            reverse=True
        )[:limit]
    
    def clear_alerts(self):
        """清除告警"""
        self.alerts.clear()
    
    def check_alert_rules(self):
        """检查告警规则"""
        for name, rule in self.alert_rules.items():
            try:
                metric = self.get_metric(rule['metric'])
                if not metric:
                    continue
                
                value = metric['value']
                threshold = rule['threshold']
                operator = rule.get('operator', '>')
                
                is_triggered = False
                if operator == '>':
                    is_triggered = value > threshold
                elif operator == '<':
                    is_triggered = value < threshold
                elif operator == '>=':
                    is_triggered = value >= threshold
                elif operator == '<=':
                    is_triggered = value <= threshold
                elif operator == '==':
                    is_triggered = value == threshold
                elif operator == '!=':
                    is_triggered = value != threshold
                
                if is_triggered:
                    self.add_alert({
                        'rule': name,
                        'metric': rule['metric'],
                        'value': value,
                        'threshold': threshold,
                        'message': rule.get('message', f"{rule['metric']} {operator} {threshold}")
                    })
                    
            except Exception as e:
                self.logger.error(f"Error checking alert rule {name}: {str(e)}")
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            self.add_metric('system.cpu.usage', cpu_percent, {'unit': '%'})
            self.add_metric('system.memory.total', memory.total, {'unit': 'bytes'})
            self.add_metric('system.memory.used', memory.used, {'unit': 'bytes'})
            self.add_metric('system.memory.percent', memory.percent, {'unit': '%'})
            self.add_metric('system.disk.total', disk.total, {'unit': 'bytes'})
            self.add_metric('system.disk.used', disk.used, {'unit': 'bytes'})
            self.add_metric('system.disk.percent', disk.percent, {'unit': '%'})
            
            return {
                'cpu': {
                    'usage': cpu_percent
                },
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'percent': memory.percent
                },
                'disk': {
                    'total': disk.total,
                    'used': disk.used,
                    'percent': disk.percent
                }
            }
        except Exception as e:
            self.logger.error(f"Error getting system metrics: {str(e)}")
            return {}
    
    def save_metrics(self, filename: str):
        """保存监控指标"""
        try:
            os.makedirs('output/metrics', exist_ok=True)
            filepath = os.path.join('output/metrics', filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.metrics, f, indent=2, default=str)
            self.logger.info(f"Metrics saved to {filepath}")
        except Exception as e:
            self.logger.error(f"Error saving metrics: {str(e)}")
    
    def load_metrics(self, filename: str):
        """加载监控指标"""
        try:
            filepath = os.path.join('output/metrics', filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                self.metrics = json.load(f)
            self.logger.info(f"Metrics loaded from {filepath}")
        except Exception as e:
            self.logger.error(f"Error loading metrics: {str(e)}")
    
    @abstractmethod
    async def collect_metrics(self):
        """收集监控指标"""
        pass
    
    @abstractmethod
    async def check_health(self) -> bool:
        """检查健康状态"""
        pass 