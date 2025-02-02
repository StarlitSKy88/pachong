import json
from typing import Dict, List, Tuple
from pathlib import Path
import emoji
from jinja2 import Environment, FileSystemLoader
import random
import os
import asyncio
from playwright.async_api import async_playwright
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import io
from ..config import config
from ..themes import get_theme

class XHSFormatter:
    def __init__(self, theme_name: str = None):
        self.template_dir = Path(config.get('paths.templates', 'templates'))
        self.template_dir.mkdir(exist_ok=True)
        self.env = Environment(loader=FileSystemLoader(str(self.template_dir)))
        
        # 加载主题
        self.theme = get_theme(theme_name or config.get('theme.current', 'default'))
        
        # 加载配置
        self.image_width = config.get('image.width', 390)
        self.max_image_height = config.get('image.max_height', 1200)
        self.image_padding = config.get('image.padding', 20)
        self.watermark_text = config.get('image.watermark.text', '关注我，了解更多精彩内容')
        
        self._init_templates()
        self._load_emoji_mapping()

    def _init_templates(self):
        """初始化HTML模板"""
        self._create_base_template()
        self._create_daily_template()
        self._create_topic_template()

    def _create_base_template(self):
        """创建基础模板"""
        base_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        {self.theme.get_template_styles()}
    </style>
</head>
<body>
    {{% block content %}}{{% endblock %}}
</body>
</html>
"""
        self._save_template("base.html", base_template)

    def _create_daily_template(self):
        """创建每日总结模板"""
        daily_template = """
{% extends "base.html" %}
{% block content %}
<div class="title">{{ title }} {{ emoji.sparkles }}</div>

<div class="subtitle">
    {{ emoji.calendar }} 今日精选 | {{ date }}
</div>

<div class="content">
    <div class="highlight">
        {{ emoji.bulb }} 今日要点：
        {% for point in key_points %}
        • {{ point }}
        {% endfor %}
    </div>

    {% for category in categories %}
    <div class="category">
        <h2>{{ category.title }} {{ category.emoji }}</h2>
        {% for item in category.items %}
        <div class="item">
            <div class="quote">{{ item.summary }}</div>
            {% if item.key_points %}
            <ul>
                {% for point in item.key_points %}
                <li>{{ point }}</li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        {% endfor %}
    </div>
    <div class="divider"></div>
    {% endfor %}

    <div class="tips">
        {{ emoji.light_bulb }} 小贴士：关注我，每天为您精选科技圈最新动态！
    </div>

    <div class="tags">
        {% for tag in tags %}
        <span class="tag">#{{ tag }}</span>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""
        self._save_template("daily.html", daily_template)

    def _create_topic_template(self):
        """创建主题模板"""
        topic_template = """
{% extends "base.html" %}
{% block content %}
<div class="title">{{ title }} {{ emoji.star }}</div>

<div class="content">
    <div class="highlight">
        {{ emoji.memo }} 核心观点：
        {{ main_point }}
    </div>

    {% if key_points %}
    <div class="points">
        <h3>{{ emoji.pushpin }} 重点解析：</h3>
        {% for point in key_points %}
        <div class="quote">{{ point }}</div>
        {% endfor %}
    </div>
    <div class="page-break"></div>
    {% endif %}

    {% if details %}
    <div class="details">
        <h3>{{ emoji.magnifying_glass }} 深度分析：</h3>
        {% for detail in details %}
        <p>{{ detail }}</p>
        {% endfor %}
    </div>
    <div class="page-break"></div>
    {% endif %}

    {% if recommendations %}
    <div class="tips">
        {{ emoji.light_bulb }} 实用建议：
        <ul>
        {% for rec in recommendations %}
            <li>{{ rec }}</li>
        {% endfor %}
        </ul>
    </div>
    {% endif %}

    <div class="tags">
        {% for tag in tags %}
        <span class="tag">#{{ tag }}</span>
        {% endfor %}
    </div>
</div>
{% endblock %}
"""
        self._save_template("topic.html", topic_template)

    def _save_template(self, name: str, content: str):
        """保存模板文件"""
        template_path = self.template_dir / name
        template_path.write_text(content, encoding='utf-8')

    def _load_emoji_mapping(self):
        """加载表情符号映射"""
        self.emoji_mapping = {
            'title': ['✨', '🌟', '⭐️', '💫'],
            'tech': ['💻', '⌨️', '🖥️', '🤖'],
            'idea': ['💡', '🎯', '🔍', '🎨'],
            'tips': ['📌', '📍', '🔖', '📎'],
            'warning': ['⚠️', '❗️', '❓', '⁉️'],
            'good': ['👍', '🙌', '👏', '💪'],
            'bad': ['👎', '😢', '💔', '😱'],
            'time': ['⏰', '⌚️', '📅', '🗓️'],
            'money': ['💰', '💵', '💸', '🤑'],
            'chart': ['📊', '📈', '📉', '📋'],
        }

    def get_random_emoji(self, category: str) -> str:
        """获取随机表情符号"""
        if category in self.emoji_mapping:
            return random.choice(self.emoji_mapping[category])
        return ''

    def format_daily_summary(self, data: Dict) -> str:
        """格式化每日总结"""
        template = self.env.get_template("daily.html")
        template_data = {
            'title': data['title'],
            'date': data['date'],
            'emoji': emoji,
            'key_points': data['key_points'],
            'categories': data['categories'],
            'tags': data['tags']
        }
        return template.render(**template_data)

    def format_topic_content(self, data: Dict) -> str:
        """格式化主题内容"""
        template = self.env.get_template("topic.html")
        template_data = {
            'title': data['title'],
            'emoji': emoji,
            'main_point': data['main_point'],
            'key_points': data['key_points'],
            'details': data.get('details', []),
            'recommendations': data.get('recommendations', []),
            'tags': data['tags']
        }
        return template.render(**template_data)

    def save_html(self, content: str, output_path: str):
        """保存HTML文件"""
        output_file = Path(output_path)
        output_file.write_text(content, encoding='utf-8')

    async def _generate_image(self, html_path: str, output_path: str) -> List[str]:
        """使用Playwright生成图片"""
        image_files = []
        
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # 设置移动设备视口
            await page.set_viewport_size({"width": self.image_width, "height": self.max_image_height})
            
            # 加载HTML文件
            await page.goto(f"file://{html_path}")
            
            # 等待内容加载完成
            await page.wait_for_load_state("networkidle")
            
            # 获取内容总高度
            total_height = await page.evaluate('document.documentElement.scrollHeight')
            
            # 计算需要生成的图片数量
            num_images = (total_height + self.max_image_height - 1) // self.max_image_height
            
            for i in range(num_images):
                # 计算当前图片的起始位置和高度
                start_pos = i * self.max_image_height
                current_height = min(self.max_image_height, total_height - start_pos)
                
                # 设置视口位置和大小
                await page.evaluate(f'window.scrollTo(0, {start_pos})')
                await page.set_viewport_size({"width": self.image_width, "height": current_height})
                
                # 生成图片文件名
                image_file = str(Path(output_path).parent / f'article_{i+1}.png')
                
                # 截图
                await page.screenshot(path=image_file, full_page=False)
                
                # 优化图片
                self._enhance_image(image_file)
                
                image_files.append(image_file)
            
            await browser.close()
            
        return image_files

    def _enhance_image(self, image_path: str):
        """优化图片质量并添加水印"""
        # 打开图片
        img = Image.open(image_path)
        
        # 增强对比度
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.1)
        
        # 增强清晰度
        enhancer = ImageEnhance.Sharpness(img)
        img = enhancer.enhance(1.2)
        
        # 添加水印
        draw = ImageDraw.Draw(img)
        # 使用系统默认字体，也可以加载自定义字体
        try:
            font = ImageFont.truetype("msyh.ttc", config.get('image.watermark.font_size', 20))
        except:
            font = ImageFont.load_default()
            
        # 计算水印位置（右下角）
        text_bbox = draw.textbbox((0, 0), self.watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = img.width - text_width - self.image_padding
        y = img.height - text_height - self.image_padding
        
        # 绘制半透明背景
        padding = 5
        draw.rectangle(
            [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
            fill=tuple(config.get('image.watermark.background', [255, 255, 255, 128]))
        )
        
        # 绘制水印文字
        draw.text((x, y), self.watermark_text, font=font, 
                 fill=tuple(config.get('image.watermark.color', [100, 100, 100, 255])))
        
        # 保存优化后的图片
        img.save(image_path, quality=config.get('image.quality', 95), optimize=True)

    def generate_images(self, html_content: str, output_dir: str = None) -> List[str]:
        """生成多张图片"""
        # 使用配置的输出目录
        output_dir = output_dir or os.path.join(config.get('paths.output', 'output'), 'images')
        
        # 创建输出目录
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 创建临时HTML文件
        temp_html = output_path / 'temp.html'
        self.save_html(html_content, str(temp_html))
        
        # 生成图片
        image_file = str(output_path / 'article_1.png')
        
        # 运行异步函数
        image_files = asyncio.run(self._generate_image(str(temp_html.absolute()), image_file))
        
        # 删除临时文件
        temp_html.unlink()
        
        return image_files

    def preview_in_browser(self, content: str):
        """在浏览器中预览"""
        import tempfile
        import webbrowser
        
        with tempfile.NamedTemporaryFile('w', delete=False, suffix='.html', encoding='utf-8') as f:
            f.write(content)
            webbrowser.open('file://' + f.name) 