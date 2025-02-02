import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库配置
DATABASE_URL = "sqlite:///content_crawler.db"

# Deepseek配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "sk-4e8e23e071184186b1a70bd7b87cbff3")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"

# OpenAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# 爬虫配置
CRAWLER_CONFIG = {
    "xiaohongshu": {
        "keywords": ["cursor开发", "独立开发者", "一人公司", "AI模型"],
        "max_items_per_keyword": 5
    },
    "bilibili": {
        "keywords": ["cursor开发", "独立开发者", "一人公司", "AI模型"],
        "max_items_per_keyword": 5
    }
}

# 定时任务配置
SCHEDULE_CONFIG = {
    "crawl_interval": "0 */12 * * *"  # 每12小时执行一次
}

# 日志配置
LOG_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "logs/crawler.log"
}

# 内容分类关键词
CONTENT_CATEGORIES = {
    "cursor": ["cursor", "开发工具", "IDE"],
    "indie_dev": ["独立开发", "一人公司", "个人项目", "独立开发者"],
    "ai_news": ["AI模型", "人工智能", "机器学习", "深度学习"]
}

# 总结提示词模板
SUMMARY_PROMPTS = {
    "content_summary": """
    请分析以下内容，并按照如下格式输出：
    
    1. 主题分类：（判断是否属于：Cursor开发、独立开发者项目、AI模型）
    2. 主要内容：（200字以内的核心内容概述）
    3. 关键信息：（以要点形式列出3-5个关键信息）
    4. 价值评估：（对内容的实用性和重要性评分1-5星，并简要说明原因）
    
    原文内容：
    {content}
    """,
    
    "daily_report": """
    请对今天爬取的内容进行汇总，按以下格式输出：
    
    # 每日资讯汇总 ({date})
    
    ## Cursor开发相关
    {cursor_content}
    
    ## 独立开发者项目
    {indie_dev_content}
    
    ## AI模型动态
    {ai_news_content}
    
    ## 总结
    （对当天内容的整体价值和趋势进行简要点评）
    """
} 