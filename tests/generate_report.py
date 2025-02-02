"""测试进度报告"""
import os
import json
import re
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from jinja2 import Template

def parse_tasks(readme_path="tests/README.md"):
    """从README文件中解析任务列表"""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    module_tasks = {}
    current_module = None
    
    for line in content.split('\n'):
        if line.startswith('## '):
            current_module = line[3:].strip()
            module_tasks[current_module] = []
        elif line.startswith('- [') and current_module:
            completed = 'x' in line[0:5]
            task_name = line[6:].strip()
            module_tasks[current_module].append({
                'name': task_name,
                'completed': completed
            })
    
    return module_tasks

def load_progress(progress_path="tests/progress.json"):
    """加载进度数据"""
    if not os.path.exists(progress_path):
        return None
    
    with open(progress_path, 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    return history[-1] if history else None

def generate_report(template_path="tests/report_template.html", output_path="tests/report.html"):
    """生成HTML报告"""
    # 加载模板
    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())
    
    # 加载进度数据
    progress_data = load_progress()
    if not progress_data:
        print("未找到进度数据")
        return
    
    # 解析任务列表
    module_tasks = parse_tasks()
    
    # 渲染模板
    html = template.render(
        total_progress=progress_data['total_progress'],
        module_progress=progress_data['module_progress'],
        module_tasks=module_tasks,
        last_update=progress_data['date']
    )
    
    # 保存报告
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"报告已生成：{output_path}")

def main():
    try:
        generate_report()
    except Exception as e:
        print(f"生成报告时出错：{str(e)}")

if __name__ == '__main__':
    main() 