"""测试进度跟踪"""
import re
import json
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np

def parse_progress(readme_path: str = "tests/README.md") -> dict:
    """解析测试进度
    
    Args:
        readme_path: README文件路径
        
    Returns:
        进度数据字典
    """
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 解析总体进度
    total_progress = {}
    total_match = re.search(r"总体完成度: (\d+\.\d+)%", content)
    if total_match:
        total_progress["total"] = float(total_match.group(1))
    
    # 解析模块进度
    module_progress = {}
    module_matches = re.finditer(r"(\d+)\. (.+?): (\d+)% \((\d+)/(\d+)\)", content)
    for match in module_matches:
        module_name = match.group(2)
        progress = int(match.group(3))
        completed = int(match.group(4))
        total = int(match.group(5))
        module_progress[module_name] = {
            "progress": progress,
            "completed": completed,
            "total": total
        }
    
    return {
        "total": total_progress,
        "modules": module_progress,
        "timestamp": datetime.now().isoformat()
    }

def save_progress(progress: dict, output_path: str = "tests/progress.json"):
    """保存进度数据
    
    Args:
        progress: 进度数据
        output_path: 输出文件路径
    """
    try:
        with open(output_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []
    
    history.append(progress)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def plot_burndown(progress_path: str = "tests/progress.json", output_path: str = "tests/burndown.png"):
    """绘制燃尽图
    
    Args:
        progress_path: 进度数据文件路径
        output_path: 输出图片路径
    """
    with open(progress_path, "r", encoding="utf-8") as f:
        history = json.load(f)
    
    # 提取数据
    dates = [datetime.fromisoformat(entry["timestamp"]) for entry in history]
    total_progress = [100 - entry["total"]["total"] for entry in history]
    
    # 理想燃尽线
    ideal_dates = [dates[0], dates[-1]]
    ideal_progress = [total_progress[0], 0]
    
    # 绘制图表
    plt.figure(figsize=(12, 6))
    plt.plot(dates, total_progress, "b-", label="实际进度")
    plt.plot(ideal_dates, ideal_progress, "r--", label="理想进度")
    
    # 设置标签
    plt.title("测试进度燃尽图")
    plt.xlabel("日期")
    plt.ylabel("剩余工作量 (%)")
    plt.grid(True)
    plt.legend()
    
    # 旋转x轴标签
    plt.xticks(rotation=45)
    
    # 保存图片
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

def plot_module_progress(progress_path: str = "tests/progress.json", output_path: str = "tests/module_progress.png"):
    """绘制模块进度图
    
    Args:
        progress_path: 进度数据文件路径
        output_path: 输出图片路径
    """
    with open(progress_path, "r", encoding="utf-8") as f:
        history = json.load(f)
    
    # 获取最新进度
    latest = history[-1]
    modules = latest["modules"]
    
    # 提取数据
    names = list(modules.keys())
    progress = [modules[name]["progress"] for name in names]
    
    # 绘制图表
    plt.figure(figsize=(12, 6))
    bars = plt.bar(names, progress)
    
    # 添加数值标签
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f"{height}%", ha="center", va="bottom")
    
    # 设置标签
    plt.title("模块测试进度")
    plt.xlabel("模块")
    plt.ylabel("完成度 (%)")
    plt.grid(True, axis="y")
    
    # 旋转x轴标签
    plt.xticks(rotation=45, ha="right")
    
    # 保存图片
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

if __name__ == "__main__":
    # 解析进度
    progress = parse_progress()
    
    # 保存进度
    save_progress(progress)
    
    # 绘制燃尽图
    plot_burndown()
    
    # 绘制模块进度图
    plot_module_progress()
    
    print("进度跟踪完成！") 