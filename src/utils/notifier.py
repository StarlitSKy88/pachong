"""通知器模块。"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional

from src.config import Config

class BaseNotifier:
    """基础通知器"""

    def __init__(self, config: Config):
        """初始化。

        Args:
            config: 配置对象
        """
        self.config = config

    def send(self, subject: str, message: str, **kwargs) -> bool:
        """发送通知。

        Args:
            subject: 主题
            message: 消息内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        raise NotImplementedError

class EmailNotifier(BaseNotifier):
    """邮件通知器"""

    def __init__(self, config: Config):
        """初始化。

        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.smtp_server = config.SMTP_SERVER
        self.smtp_port = config.SMTP_PORT
        self.smtp_username = config.SMTP_USERNAME
        self.smtp_password = config.SMTP_PASSWORD
        self.sender = config.EMAIL_SENDER
        self.recipients = config.EMAIL_RECIPIENTS

    def send(
        self,
        subject: str,
        message: str,
        recipients: Optional[List[str]] = None,
        html: bool = False,
    ) -> bool:
        """发送邮件。

        Args:
            subject: 主题
            message: 消息内容
            recipients: 收件人列表
            html: 是否为HTML格式

        Returns:
            是否发送成功
        """
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg["Subject"] = subject
            msg["From"] = self.sender
            msg["To"] = ", ".join(recipients or self.recipients)

            # 添加正文
            content_type = "html" if html else "plain"
            msg.attach(MIMEText(message, content_type, "utf-8"))

            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to send email: {str(e)}")
            return False

class DingTalkNotifier(BaseNotifier):
    """钉钉通知器"""

    def __init__(self, config: Config):
        """初始化。

        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.webhook_url = config.DINGTALK_WEBHOOK_URL
        self.secret = config.DINGTALK_SECRET

    def send(self, subject: str, message: str, **kwargs) -> bool:
        """发送钉钉消息。

        Args:
            subject: 主题
            message: 消息内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        try:
            # TODO: 实现钉钉消息发送
            return True
        except Exception as e:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to send DingTalk message: {str(e)}")
            return False

class WeChatNotifier(BaseNotifier):
    """微信通知器"""

    def __init__(self, config: Config):
        """初始化。

        Args:
            config: 配置对象
        """
        super().__init__(config)
        self.webhook_url = config.WECHAT_WEBHOOK_URL
        self.secret = config.WECHAT_SECRET

    def send(self, subject: str, message: str, **kwargs) -> bool:
        """发送微信消息。

        Args:
            subject: 主题
            message: 消息内容
            **kwargs: 其他参数

        Returns:
            是否发送成功
        """
        try:
            # TODO: 实现微信消息发送
            return True
        except Exception as e:
            from src.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to send WeChat message: {str(e)}")
            return False 