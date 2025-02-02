import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import asyncio

from ..models.content import Content
from ..models.generated_content import GeneratedContent
from ..utils.llm_api import query_llm
from ..utils.screenshot_utils import take_screenshot_sync

logger = logging.getLogger(__name__)

class ContentGenerator:
    """内容生成器"""
    
    def __init__(self):
        """初始化生成器"""
        self.llm_provider = os.getenv('DEFAULT_LLM_MODEL', 'gpt-4')
        self.max_retries = int(os.getenv('MAX_RETRIES', '3'))
        
        # 加载提示词模板
        self.prompt_templates = self._load_prompt_templates()
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """加载提示词模板"""
        template_file = os.getenv('PROMPT_TEMPLATE_FILE', 'prompts/generator.json')
        
        if not os.path.exists(template_file):
            # 创建默认模板
            templates = {
                'xiaohongshu': """
请将以下内容改写成小红书风格的笔记。要求：
1. 标题吸引人，使用数字、emoji等增加点击率
2. 内容分段清晰，重点突出
3. 语言亲切自然，有互动感
4. 适当添加标签，3-5个
5. 图文结合，指出配图建议

原始内容：
{content}

请按以下格式输出：
{
    "title": "✨10个超实用的...",
    "content": "大家好...",
    "image_suggestions": [
        {
            "position": "开头",
            "description": "...",
            "style": "..."
        }
    ],
    "tags": ["标签1", "标签2"]
}
""",
                'podcast': """
请将以下内容改写成3分钟播客脚本。要求：
1. 开场简短有力，直入主题
2. 语言口语化，适合朗读
3. 结构清晰，重点突出
4. 结尾总结关键信息
5. 添加音乐/音效建议

原始内容：
{content}

请按以下格式输出：
{
    "title": "...",
    "script": "大家好...",
    "duration": "180",  # 预计时长（秒）
    "segments": [
        {
            "type": "speech/music/effect",
            "content": "...",
            "duration": "30"
        }
    ],
    "background_music": "建议使用..."
}
""",
                'html_article': """
请将以下内容改写成HTML文章。要求：
1. 标题SEO友好
2. 内容结构清晰，适合Web阅读
3. 添加适当的HTML标签和样式
4. 优化图片布局和展示
5. 考虑移动端适配

原始内容：
{content}

请按以下格式输出：
{
    "title": "...",
    "meta_description": "...",
    "html_content": "<!DOCTYPE html>...",
    "css_styles": "...",
    "image_layout": [
        {
            "position": "...",
            "size": "...",
            "style": "..."
        }
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
    
    async def generate_content(
        self,
        content: Content,
        content_type: str,
        format_config: Optional[Dict] = None
    ) -> Optional[GeneratedContent]:
        """生成内容
        
        Args:
            content: 源内容对象
            content_type: 内容类型（xiaohongshu/podcast/html）
            format_config: 格式配置
            
        Returns:
            生成的内容对象
        """
        try:
            # 准备内容文本
            content_text = f"""
标题：{content.title}

内容：{content.content}

平台：{content.platform}
分类：{content.category or '未分类'}
标签：{', '.join(tag.name for tag in content.tags)}

质量评分：{content.quality_score or 0}
相关性评分：{content.relevance_score or 0}
"""
            
            # 生成内容
            for attempt in range(self.max_retries):
                try:
                    # 发送生成请求
                    response = await query_llm(
                        prompt=self.prompt_templates[content_type].format(
                            content=content_text
                        ),
                        provider=self.llm_provider
                    )
                    
                    if response:
                        result = json.loads(response)
                        
                        # 创建生成内容对象
                        generated = GeneratedContent(
                            source_content_id=content.id,
                            content_type=content_type,
                            format_config=format_config or {},
                            generation_config={
                                'provider': self.llm_provider,
                                'template': content_type
                            },
                            prompt_used=self.prompt_templates[content_type],
                            model_used=self.llm_provider
                        )
                        
                        # 根据内容类型处理结果
                        if content_type == 'xiaohongshu':
                            await self._process_xiaohongshu(generated, result)
                        elif content_type == 'podcast':
                            await self._process_podcast(generated, result)
                        elif content_type == 'html':
                            await self._process_html(generated, result)
                        
                        return generated
                        
                except Exception as e:
                    logger.error(f"Generation attempt {attempt + 1} failed: {str(e)}")
                    if attempt == self.max_retries - 1:
                        raise
                    await asyncio.sleep(2 ** attempt)  # 指数退避
            
        except Exception as e:
            logger.error(f"Failed to generate content: {str(e)}")
        
        return None
    
    async def _process_xiaohongshu(
        self,
        generated: GeneratedContent,
        result: Dict[str, Any]
    ) -> None:
        """处理小红书内容
        
        Args:
            generated: 生成内容对象
            result: 生成结果
        """
        generated.title = result['title']
        generated.content = result['content']
        generated.format_config['image_suggestions'] = result['image_suggestions']
        generated.format_config['tags'] = result['tags']
    
    async def _process_podcast(
        self,
        generated: GeneratedContent,
        result: Dict[str, Any]
    ) -> None:
        """处理播客内容
        
        Args:
            generated: 生成内容对象
            result: 生成结果
        """
        generated.title = result['title']
        generated.content = result['script']
        generated.format_config['segments'] = result['segments']
        generated.format_config['background_music'] = result['background_music']
        generated.format_config['duration'] = result['duration']
    
    async def _process_html(
        self,
        generated: GeneratedContent,
        result: Dict[str, Any]
    ) -> None:
        """处理HTML内容
        
        Args:
            generated: 生成内容对象
            result: 生成结果
        """
        generated.title = result['title']
        generated.content = result['html_content']
        generated.format_config['meta_description'] = result['meta_description']
        generated.format_config['css_styles'] = result['css_styles']
        generated.format_config['image_layout'] = result['image_layout']
        
        # 生成预览图
        try:
            screenshot = take_screenshot_sync(
                html_content=result['html_content'],
                css_content=result['css_styles'],
                width=1200,
                height=800
            )
            if screenshot:
                generated.images = [screenshot]
        except Exception as e:
            logger.error(f"Failed to generate preview: {str(e)}")

# 全局内容生成器
content_generator = ContentGenerator() 