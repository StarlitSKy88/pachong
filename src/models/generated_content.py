"""生成内容模型"""

from datetime import datetime
from typing import Dict, Any
from sqlalchemy import Column, Integer, String, Text, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .base import Base

class GeneratedContent(Base):
    """生成内容模型"""
    __tablename__ = 'generated_contents'

    # 基本信息
    title = Column(String(500))  # 标题
    content = Column(Text)  # 内容
    content_type = Column(String(50))  # 内容类型（小红书/播客/HTML等）
    format_config = Column(JSON)  # 格式配置
    
    # 生成信息
    source_content_id = Column(Integer, ForeignKey('contents.id'))  # 源内容ID
    source_content = relationship("Content", back_populates="generated_contents", lazy='joined')
    generation_config = Column(JSON)  # 生成配置
    prompt_used = Column(Text)  # 使用的提示词
    model_used = Column(String(100))  # 使用的模型
    
    # 媒体信息
    images = Column(JSON)  # 图片列表
    audio_url = Column(String(500))  # 音频链接（播客）
    subtitles = Column(Text)  # 字幕内容
    
    # 时间信息
    generate_time = Column(DateTime, default=datetime.now)  # 生成时间
    publish_time = Column(DateTime)  # 发布时间
    
    # 状态信息
    status = Column(Integer, default=0)  # 状态：0-待审核, 1-已发布, 2-已拒绝
    review_comment = Column(Text)  # 审核意见
    
    # 质量评估
    quality_score = Column(Integer)  # 质量评分
    engagement_prediction = Column(JSON)  # 互动预测
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = super().to_dict()
        result.update({
            'title': self.title,
            'content': self.content,
            'content_type': self.content_type,
            'format_config': self.format_config,
            'source_content_id': self.source_content_id,
            'generation_config': self.generation_config,
            'prompt_used': self.prompt_used,
            'model_used': self.model_used,
            'images': self.images,
            'audio_url': self.audio_url,
            'subtitles': self.subtitles,
            'generate_time': self.generate_time.isoformat() if self.generate_time else None,
            'publish_time': self.publish_time.isoformat() if self.publish_time else None,
            'status': self.status,
            'review_comment': self.review_comment,
            'quality_score': self.quality_score,
            'engagement_prediction': self.engagement_prediction
        })
        return result

    def __repr__(self):
        return f'<GeneratedContent {self.title}>' 