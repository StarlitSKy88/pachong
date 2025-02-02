import pytest
from src.formatter.xhs_formatter import XHSFormatter
from datetime import datetime

def test_daily_summary_format():
    formatter = XHSFormatter()
    
    # 测试数据
    test_data = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'key_points': [
            '今日Cursor发布重大更新，支持更多编程语言',
            '独立开发者小明的项目获得融资',
            'GPT-5即将发布，性能提升显著'
        ],
        'cursor_content': [
            {
                'title': 'Cursor更新通知',
                'summary': 'Cursor IDE发布新版本，支持Python、Java等更多语言，性能提升30%',
                'key_points': [
                    '新增多语言支持',
                    '性能优化显著',
                    '界面改进'
                ]
            }
        ],
        'indie_dev_content': [
            {
                'title': '独立开发者故事',
                'summary': '独立开发者小明开发的效率工具获得100万融资',
                'key_points': [
                    '项目估值1000万',
                    '月收入10万+',
                    '用户增长迅速'
                ]
            }
        ],
        'ai_news_content': [
            {
                'title': 'GPT-5预告',
                'summary': 'OpenAI暗示GPT-5即将发布，性能提升显著',
                'key_points': [
                    '理解能力提升',
                    '上下文长度增加',
                    '推理能力增强'
                ]
            }
        ]
    }
    
    # 生成HTML
    html_content = formatter.format_daily_summary(test_data)
    
    # 保存并预览
    formatter.save_html(html_content, 'test_daily_summary.html')
    # formatter.preview_in_browser(html_content)  # 取消注释可以在浏览器中预览
    
    # 基本验证
    assert '今日科技圈精选' in html_content
    assert test_data['date'] in html_content
    assert 'Cursor更新通知' in html_content
    assert '独立开发者故事' in html_content
    assert 'GPT-5预告' in html_content

def test_topic_format():
    formatter = XHSFormatter()
    
    # 测试数据
    test_data = {
        'title': '如何成为一名成功的独立开发者？',
        'main_point': '通过正确的方法和持续的努力，人人都可以成为成功的独立开发者',
        'key_points': [
            '选择正确的项目方向',
            '制定可行的商业模式',
            '持续学习和改进',
            '建立个人品牌'
        ],
        'details': [
            '首先要选择一个你熟悉且市场需要的领域',
            '制定清晰的盈利模式和发展规划',
            '保持技术栈的更新和学习',
            '通过社交媒体建立个人影响力'
        ],
        'recommendations': [
            '从小项目开始积累经验',
            '多参与开源社区',
            '建立稳定的收入来源',
            '注重用户反馈'
        ],
        'tags': [
            '独立开发',
            '创业指南',
            '技术成长',
            '经验分享',
            '程序人生'
        ]
    }
    
    # 生成HTML
    html_content = formatter.format_topic_content(test_data)
    
    # 保存并预览
    formatter.save_html(html_content, 'test_topic.html')
    # formatter.preview_in_browser(html_content)  # 取消注释可以在浏览器中预览
    
    # 基本验证
    assert test_data['title'] in html_content
    assert test_data['main_point'] in html_content
    for point in test_data['key_points']:
        assert point in html_content
    for tag in test_data['tags']:
        assert tag in html_content 