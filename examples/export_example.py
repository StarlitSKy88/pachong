"""导出功能示例

该示例展示了如何使用导出功能：
1. 基本导出
2. 批量导出
3. 自定义模板
4. 错误处理
"""

import os
import asyncio
import logging
from pathlib import Path
from src.export.base import ExportManager
from src.export.html import HTMLExport

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# 示例文章
EXAMPLE_ARTICLE = {
    "title": "Python异步编程指南",
    "author": "张三",
    "date": "2024-03-27",
    "category": "编程",
    "tags": ["Python", "异步", "教程"],
    "content": """
    <h2>什么是异步编程？</h2>
    <p>异步编程是一种编程范式，它允许程序在等待I/O操作完成时继续执行其他任务。</p>
    
    <h2>为什么需要异步编程？</h2>
    <p>在处理I/O密集型任务时，异步编程可以显著提高程序的性能和响应性。</p>
    
    <h2>Python中的异步编程</h2>
    <p>Python通过<code>async</code>和<code>await</code>关键字提供了对异步编程的原生支持。</p>
    
    <h3>示例代码</h3>
    <pre><code>
    async def fetch_data():
        async with aiohttp.ClientSession() as session:
            async with session.get('http://example.com/data') as response:
                return await response.json()
    </code></pre>
    
    <h2>最佳实践</h2>
    <img src="https://example.com/async-flow.png" alt="异步流程图">
    <p>在使用异步编程时，需要注意以下几点：</p>
    <ul>
        <li>避免在异步函数中使用阻塞操作</li>
        <li>合理使用并发控制</li>
        <li>注意异常处理</li>
        <li>使用适当的测试工具</li>
    </ul>
    """
}

async def export_single_article():
    """导出单篇文章示例"""
    try:
        # 创建导出管理器
        manager = ExportManager()
        manager.register_format("html", HTMLExport)
        
        # 确保输出目录存在
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        
        # 导出文章
        output_path = output_dir / "async-guide.html"
        await manager.export(
            EXAMPLE_ARTICLE,
            "html",
            "article",
            str(output_path)
        )
        
        logger.info(f"文章已导出到：{output_path}")
        
    except Exception as e:
        logger.error(f"导出失败：{e}")
        raise

async def export_multiple_articles():
    """批量导出示例"""
    try:
        # 创建示例文章
        articles = []
        topics = ["变量和数据类型", "控制流", "函数", "类和对象", "模块和包"]
        
        for i, topic in enumerate(topics, 1):
            article = {
                **EXAMPLE_ARTICLE,
                "title": f"Python基础教程（{i}）：{topic}",
                "content": f"""
                <h2>{topic}</h2>
                <p>这是关于{topic}的基础教程。</p>
                <img src="https://example.com/python-{i}.png" alt="{topic}示意图">
                <p>更多内容请参考下一章。</p>
                """
            }
            articles.append(article)
        
        # 创建导出管理器
        manager = ExportManager()
        manager.register_format("html", HTMLExport)
        
        # 确保输出目录存在
        output_dir = Path("output/tutorial")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 批量导出
        await manager.batch_export(
            articles,
            "html",
            "article",
            str(output_dir)
        )
        
        logger.info(f"教程已导出到：{output_dir}")
        
    except Exception as e:
        logger.error(f"批量导出失败：{e}")
        raise

async def main():
    """主函数"""
    # 导出单篇文章
    logger.info("开始导出单篇文章...")
    await export_single_article()
    
    # 批量导出教程
    logger.info("开始批量导出教程...")
    await export_multiple_articles()

if __name__ == "__main__":
    # 运行示例
    asyncio.run(main()) 