import os
import re
import json
from datetime import datetime
import matplotlib.pyplot as plt

def parse_progress(readme_path="tests/README.md"):
    """从README文件中解析进度信息"""
    if not os.path.exists(readme_path):
        return None
    
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 解析总体进度
    total_pattern = r'总体进度：(\d+)%'
    total_match = re.search(total_pattern, content)
    total_progress = int(total_match.group(1)) if total_match else 0
    
    # 解析模块进度
    module_pattern = r'## (.+?)\n.*?进度：(\d+)%'
    module_matches = re.finditer(module_pattern, content)
    module_progress = {m.group(1): int(m.group(2)) for m in module_matches}
    
    return {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'total_progress': total_progress,
        'module_progress': module_progress
    }

def save_progress(progress_data, output_path="tests/progress.json"):
    """保存进度数据到JSON文件"""
    if not os.path.exists(os.path.dirname(output_path)):
        os.makedirs(os.path.dirname(output_path))
    
    # 读取现有数据
    if os.path.exists(output_path):
        with open(output_path, 'r', encoding='utf-8') as f:
            history = json.load(f)
    else:
        history = []
    
    # 添加新数据
    history.append(progress_data)
    
    # 保存数据
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def plot_burndown(history, output_path="tests/burndown.png"):
    """绘制燃尽图"""
    dates = [item['date'] for item in history]
    progress = [item['total_progress'] for item in history]
    
    plt.figure(figsize=(10, 6))
    plt.plot(dates, progress, marker='o')
    plt.title('测试进度燃尽图')
    plt.xlabel('日期')
    plt.ylabel('完成进度 (%)')
    plt.grid(True)
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_module_progress(latest_progress, output_path="tests/module_progress.png"):
    """绘制模块进度对比图"""
    modules = list(latest_progress['module_progress'].keys())
    progress = list(latest_progress['module_progress'].values())
    
    plt.figure(figsize=(10, 6))
    plt.bar(modules, progress)
    plt.title('模块进度对比')
    plt.xlabel('模块')
    plt.ylabel('完成进度 (%)')
    plt.xticks(rotation=45)
    plt.grid(True, axis='y')
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def main():
    # 解析进度
    progress_data = parse_progress()
    if not progress_data:
        print("未找到README文件或解析失败")
        return
    
    # 保存进度
    save_progress(progress_data)
    
    # 读取历史数据
    with open("tests/progress.json", 'r', encoding='utf-8') as f:
        history = json.load(f)
    
    # 生成图表
    plot_burndown(history)
    plot_module_progress(progress_data)
    
    print("进度跟踪更新完成！")

if __name__ == '__main__':
    main() 