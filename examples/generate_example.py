from src.formatter.xhs_formatter import XHSFormatter
import os

# 测试数据
test_data = {
    'title': 'AI辅助编程：程序员的效率倍增器',
    'main_point': '人工智能正在革新传统的编程方式，掌握AI辅助编程将成为每个开发者的必备技能',
    'key_points': [
        '🚀 AI编程助手可以提升10倍开发效率',
        '💡 代码自动补全和智能建议大幅减少重复工作',
        '🔍 AI代码审查帮助提前发现潜在问题',
        '📚 自然语言转代码让编程更加直观'
    ],
    'details': [
        'AI编程助手已经成为现代开发者的重要工具。通过自然语言理解和代码生成能力，它能够准确理解开发者的意图，并提供高质量的代码建议。',
        '以Cursor为例，它不仅能提供实时的代码补全，还能理解整个项目上下文，给出更准确的建议。在处理复杂逻辑时，它就像一个经验丰富的搭档，帮助你快速实现想法。',
        '通过AI的帮助，开发者可以更专注于解决业务问题和架构设计，而不是被繁琐的代码细节所困扰。这不仅提高了开发效率，也提升了代码质量。'
    ],
    'recommendations': [
        '选择合适的AI编程助手，建议从Cursor、GitHub Copilot等主流工具开始',
        '培养与AI协作的习惯，学会用清晰的语言描述需求',
        '保持学习新技术，AI只是工具，核心竞争力在于解决问题的能力',
        '注意数据安全，不要在AI工具中输入敏感信息'
    ],
    'tags': [
        'AI编程',
        'Cursor',
        '效率工具',
        '技术成长',
        '编程技巧',
        '开发者必备',
        '技术分享',
        '程序员日常'
    ]
}

# 使用不同主题生成文章
themes = ['default', 'modern', 'elegant']

for theme in themes:
    print(f'\n生成 {theme} 主题的文章...')
    
    # 创建格式化器（使用指定主题）
    formatter = XHSFormatter(theme_name=theme)
    
    # 生成HTML内容
    html_content = formatter.format_topic_content(test_data)
    
    # 保存HTML文件
    html_file = f'example_article_{theme}.html'
    formatter.save_html(html_content, html_file)
    print(f'HTML文章已生成，请查看 {html_file}')
    
    # 生成图片
    output_dir = f'output/images/{theme}'
    image_files = formatter.generate_images(html_content, output_dir=output_dir)
    print(f'已生成 {len(image_files)} 张图片：')
    for image_file in image_files:
        print(f'- {image_file}') 