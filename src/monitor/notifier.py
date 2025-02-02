import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import List

class EmailNotifier:
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str):
        """
        初始化邮件通知器
        
        Args:
            smtp_host: SMTP服务器地址
            smtp_port: SMTP服务器端口
            username: 邮箱账号
            password: 邮箱密码
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        
    def send_alert(self, to_addr: str, alerts: List[dict]) -> bool:
        """
        发送告警邮件
        
        Args:
            to_addr: 接收邮箱地址
            alerts: 告警列表
        
        Returns:
            是否发送成功
        """
        if not alerts:
            return True
            
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.username
            msg['To'] = to_addr
            msg['Subject'] = f'监控告警通知 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
            
            # 构建邮件内容
            content = []
            content.append("<h2>监控系统告警通知</h2>")
            
            for alert in alerts:
                content.append(f"""
                <div style="margin-bottom: 15px; padding: 10px; border-left: 4px solid #e74c3c;">
                    <h3 style="color: #e74c3c; margin: 0;">{alert['rule'].name}</h3>
                    <p>{alert['rule'].description}</p>
                    <p>触发值: {alert['value']} {alert['rule'].operator} {alert['rule'].threshold}</p>
                    <p>时间: {alert['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
                """)
            
            msg.attach(MIMEText('\n'.join(content), 'html', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                server.send_message(msg)
                
            logging.info(f"成功发送告警邮件到 {to_addr}")
            return True
            
        except Exception as e:
            logging.error(f"发送告警邮件失败: {str(e)}")
            return False 