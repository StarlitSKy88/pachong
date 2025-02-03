import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from loguru import logger

from ..models.content import Content
from ..utils.llm_api import query_llm
from .base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class ContentAnalyzer(BaseProcessor):
    """内容分析器"""
    
    def __init__(self):
        """初始化分析器"""
        super().__init__()
        self.processed_count = 0
        self.success_count = 0
        self.fail_count = 0
        self.total_process_time = 0.0
        
        self.llm_provider = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4')
        self.quality_threshold = float(os.getenv('CONTENT_QUALITY_THRESHOLD', '0.8'))
        
        # 主题配置
        self.topics = set()
        
        # 加载提示词模板
        self.prompt_templates = self._load_prompt_templates()
    
    def add_topic(self, topic: str) -> None:
        """添加关注主题
        
        Args:
            topic: 主题名称
        """
        self.topics.add(topic.strip().lower())
        
    def remove_topic(self, topic: str) -> None:
        """移除关注主题
        
        Args:
            topic: 主题名称
        """
        topic = topic.strip().lower()
        if topic in self.topics:
            self.topics.remove(topic)
            
    def get_topics(self) -> list:
        """获取当前关注的主题列表
        
        Returns:
            主题列表
        """
        return sorted(list(self.topics))
        
    def clear_topics(self) -> None:
        """清空主题列表"""
        self.topics.clear()
    
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
    
    async def process(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """处理内容
        
        Args:
            content: 原始内容
            
        Returns:
            处理后的内容，包含分析结果
        """
        try:
            # 分析内容
            analysis = await self.analyze_content(content)
            
            # 更新内容
            content = content.copy()  # 创建副本以避免修改原始内容
            content['analysis'] = analysis
            content['processed_at'] = datetime.now().isoformat()
            
            return content
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            return content.copy()  # 返回原始内容的副本
            
    async def batch_process(self, contents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """批量处理内容
        
        Args:
            contents: 原始内容列表
            
        Returns:
            处理后的内容列表
        """
        results = []
        for content in contents:
            result = await self.process(content)
            results.append(result)
        return results
        
    async def analyze_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容
        
        Args:
            content: 原始内容
            
        Returns:
            分析结果
        """
        try:
            # 质量评估
            quality = await self._assess_quality(content)
            
            # 主题分析
            topic = await self._analyze_topic(content)
            
            # 相关性评估
            relevance = await self._assess_relevance(content)
            
            # 组合分析结果
            analysis = {
                'quality': quality,
                'topic': topic,
                'relevance': relevance,
                'analyzed_at': datetime.now().isoformat()
            }
            
            return analysis
            
        except Exception as e:
            logger.error(f"Content analysis failed: {str(e)}")
            raise  # 重新抛出异常，让上层处理
    
    async def _assess_quality(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """评估内容质量
        
        Args:
            content: 原始内容
            
        Returns:
            质量评估结果
        """
        try:
            # 构建提示词
            prompt = f"""
            请对以下内容进行质量评估，返回JSON格式的评估结果：
            
            {content['content']}
            
            评估维度包括：
            1. 内容完整性
            2. 表达清晰度
            3. 专业准确性
            4. 实用价值
            5. 原创性
            
            返回格式：
            {{
                "score": 8.5,  # 总体评分(0-10)
                "dimensions": {{  # 各维度评分
                    "completeness": 8.5,
                    "clarity": 8.5,
                    "accuracy": 8.5,
                    "value": 8.5,
                    "originality": 8.5
                }},
                "comments": {{  # 评价
                    "pros": ["优点1", "优点2"],
                    "cons": ["缺点1", "缺点2"]
                }},
                "suggestions": [  # 改进建议
                    "建议1",
                    "建议2"
                ]
            }}
            """
            
            # 调用LLM API
            response = await query_llm(prompt)
            
            # 解析响应
            result = json.loads(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {str(e)}")
            raise  # 重新抛出异常
    
    async def _analyze_topic(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """分析内容主题
        
        Args:
            content: 原始内容
            
        Returns:
            主题分析结果
        """
        try:
            # 构建提示词
            prompt = f"""
            请分析以下内容的主题，返回JSON格式的分析结果：
            
            {content['content']}
            
            分析内容包括：
            1. 主题分类
            2. 关键词提取
            3. 实体识别
            4. 内容摘要
            
            返回格式：
            {{
                "topics": {{  # 主题分类
                    "main": "主题",
                    "sub": ["子主题1", "子主题2"]
                }},
                "keywords": [  # 关键词
                    "关键词1",
                    "关键词2"
                ],
                "entities": {{  # 实体
                    "person": ["人名1", "人名2"],
                    "location": ["地点1", "地点2"],
                    "brand": ["品牌1", "品牌2"],
                    "other": ["其他1", "其他2"]
                }},
                "summary": "内容摘要"  # 200字以内的摘要
            }}
            """
            
            # 调用LLM API
            response = await query_llm(prompt)
            
            # 解析响应
            result = json.loads(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Topic analysis failed: {str(e)}")
            raise  # 重新抛出异常
    
    async def _assess_relevance(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """评估内容相关性
        
        Args:
            content: 原始内容
            
        Returns:
            相关性评估结果
        """
        try:
            # 构建提示词
            topics = ", ".join(self.get_topics()) if self.topics else "所有主题"
            prompt = f"""
            请评估以下内容与主题"{topics}"的相关性，返回JSON格式的评估结果：
            
            标题：{content.get('title', '')}
            标签：{', '.join(content.get('tags', []))}
            内容：{content['content']}
            
            评估内容包括：
            1. 主题相关性
            2. 标签相关性
            3. 内容一致性
            4. 整体相关性
            
            返回格式：
            {{
                "score": {{  # 相关性评分(0-10)
                    "topic_relevance": 8.5,
                    "tag_relevance": 8.5,
                    "content_consistency": 8.5,
                    "overall": 8.5
                }},
                "key_matches": [  # 关键匹配点
                    "匹配点1",
                    "匹配点2"
                ],
                "mismatches": [  # 不匹配点
                    "不匹配点1",
                    "不匹配点2"
                ],
                "explanation": "相关性分析说明"  # 100字以内的说明
            }}
            """
            
            # 调用LLM API
            response = await query_llm(prompt)
            
            # 解析响应
            result = json.loads(response)
            
            return result
            
        except Exception as e:
            logger.error(f"Relevance assessment failed: {str(e)}")
            raise  # 重新抛出异常
    
    def get_stats(self) -> Dict[str, Any]:
        """获取分析器统计信息
        
        Returns:
            统计信息
        """
        return {
            "processed_count": self.processed_count,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "avg_process_time": self.total_process_time / max(self.processed_count, 1)
        }

# 创建全局实例
content_analyzer = ContentAnalyzer() 