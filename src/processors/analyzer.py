import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

from ..models.content import Content
from ..utils.llm_api import query_llm

logger = logging.getLogger(__name__)

class ContentAnalyzer:
    """内容分析器"""
    
    def __init__(self):
        """初始化分析器"""
        self.llm_provider = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4')
        self.quality_threshold = float(os.getenv('CONTENT_QUALITY_THRESHOLD', '0.8'))
        
        # 加载提示词模板
        self.prompt_templates = self._load_prompt_templates()
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """加载提示词模板"""
        template_file = os.getenv('PROMPT_TEMPLATE_FILE', 'prompts/analyzer.json')
        
        if not os.path.exists(template_file):
            # 创建默认模板
            templates = {
                'quality_assessment': """
请分析以下内容的质量，并给出评分（0-1）和详细评估。评估维度包括：
1. 内容完整性（20%）：信息是否完整、结构是否清晰
2. 表达质量（20%）：语言是否准确、流畅，排版是否规范
3. 专业程度（20%）：专业知识是否准确、深入
4. 创新性（20%）：是否有独特见解或创新观点
5. 实用价值（20%）：是否具有实际应用价值

内容：
{content}

请按以下格式输出：
{
    "score": 0.85,  # 总分（0-1）
    "dimensions": {
        "completeness": 0.9,  # 完整性
        "expression": 0.8,  # 表达质量
        "professionalism": 0.85,  # 专业程度
        "innovation": 0.8,  # 创新性
        "practicality": 0.9  # 实用价值
    },
    "comments": "这是一篇...",  # 总体评价
    "suggestions": [  # 改进建议
        "建议1",
        "建议2"
    ]
}
""",
                'topic_analysis': """
请分析以下内容的主题和关键信息，并提取重要实体。

内容：
{content}

请按以下格式输出：
{
    "topics": [  # 主题列表
        "主题1",
        "主题2"
    ],
    "keywords": [  # 关键词列表
        "关键词1",
        "关键词2"
    ],
    "entities": {  # 实体信息
        "person": [],  # 人物
        "organization": [],  # 组织
        "product": [],  # 产品
        "technology": []  # 技术
    },
    "summary": "这是一篇..."  # 内容摘要
}
""",
                'relevance_assessment': """
请评估以下内容与给定主题的相关性，并给出评分（0-1）。

主题：{topic}

内容：
{content}

请按以下格式输出：
{
    "score": 0.9,  # 相关性得分（0-1）
    "explanation": "这篇内容与主题相关，因为...",  # 相关性解释
    "key_matches": [  # 关键匹配点
        "匹配点1",
        "匹配点2"
    ]
}
""",
                'tag_suggestion': """
请为以下内容推荐合适的标签。标签应该：
1. 准确反映内容主题和特点
2. 包含通用标签和专业标签
3. 考虑热门度和搜索友好性
4. 数量在3-8个之间

内容：
{content}

请按以下格式输出：
{
    "tags": [  # 标签列表
        {
            "name": "标签1",
            "confidence": 0.9,  # 置信度（0-1）
            "category": "主题/技术/产品/其他",  # 标签类型
            "reason": "推荐原因"  # 推荐理由
        }
    ],
    "suggestions": [  # 标签优化建议
        "建议1",
        "建议2"
    ]
}
"""
            }
            
            # 保存默认模板
            os.makedirs(os.path.dirname(template_file), exist_ok=True)
            with open(template_file, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            
            return templates
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load prompt templates: {str(e)}")
            return {}
    
    async def analyze_content(self, content: Content) -> Dict[str, Any]:
        """分析内容
        
        Args:
            content: 内容对象
            
        Returns:
            分析结果
        """
        try:
            # 评估质量
            quality_result = await self._assess_quality(content)
            if quality_result:
                content.quality_score = quality_result.get('score', 0)
            
            # 分析主题
            topic_result = await self._analyze_topic(content)
            if topic_result:
                content.summary = topic_result.get('summary')
            
            # 评估相关性
            relevance_result = await self._assess_relevance(content)
            if relevance_result:
                content.relevance_score = relevance_result.get('score', 0)
            
            # 推荐标签
            tag_result = await self._suggest_tags(content)
            
            return {
                'quality': quality_result,
                'topic': topic_result,
                'relevance': relevance_result,
                'tags': tag_result
            }
            
        except Exception as e:
            logger.error(f"Failed to analyze content: {str(e)}")
            return {}
    
    async def _assess_quality(self, content: Content) -> Optional[Dict[str, Any]]:
        """评估内容质量
        
        Args:
            content: 内容对象
            
        Returns:
            质量评估结果
        """
        try:
            # 准备内容文本
            content_text = f"""
标题：{content.title}

内容：{content.content}

平台：{content.platform}
发布时间：{content.publish_time}
互动数据：
- 点赞：{content.likes}
- 评论：{content.comments}
- 分享：{content.shares}
- 浏览：{content.views}
"""
            
            # 发送评估请求
            response = await query_llm(
                prompt=self.prompt_templates['quality_assessment'].format(
                    content=content_text
                ),
                provider=self.llm_provider
            )
            
            if response:
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Failed to assess quality: {str(e)}")
        
        return None
    
    async def _analyze_topic(self, content: Content) -> Optional[Dict[str, Any]]:
        """分析主题
        
        Args:
            content: 内容对象
            
        Returns:
            主题分析结果
        """
        try:
            # 准备内容文本
            content_text = f"""
标题：{content.title}

内容：{content.content}
"""
            
            # 发送分析请求
            response = await query_llm(
                prompt=self.prompt_templates['topic_analysis'].format(
                    content=content_text
                ),
                provider=self.llm_provider
            )
            
            if response:
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Failed to analyze topic: {str(e)}")
        
        return None
    
    async def _assess_relevance(self, content: Content) -> Optional[Dict[str, Any]]:
        """评估相关性
        
        Args:
            content: 内容对象
            
        Returns:
            相关性评估结果
        """
        try:
            # 准备内容文本
            content_text = f"""
标题：{content.title}

内容：{content.content}
"""
            
            # 获取主题
            topic = content.category or 'Cursor开发/AI大模型/独立开发'
            
            # 发送评估请求
            response = await query_llm(
                prompt=self.prompt_templates['relevance_assessment'].format(
                    content=content_text,
                    topic=topic
                ),
                provider=self.llm_provider
            )
            
            if response:
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Failed to assess relevance: {str(e)}")
        
        return None
    
    async def _suggest_tags(self, content: Content) -> Optional[Dict[str, Any]]:
        """推荐标签
        
        Args:
            content: 内容对象
            
        Returns:
            标签推荐结果
        """
        try:
            # 准备内容文本
            content_text = f"""
标题：{content.title}

内容：{content.content}

平台：{content.platform}
分类：{content.category or '未分类'}
"""
            
            # 发送推荐请求
            response = await query_llm(
                prompt=self.prompt_templates['tag_suggestion'].format(
                    content=content_text
                ),
                provider=self.llm_provider
            )
            
            if response:
                return json.loads(response)
                
        except Exception as e:
            logger.error(f"Failed to suggest tags: {str(e)}")
        
        return None

# 全局内容分析器
content_analyzer = ContentAnalyzer() 