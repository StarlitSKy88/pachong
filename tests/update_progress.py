"""测试进度更新"""
import re
from datetime import datetime
from pathlib import Path

def count_tests(test_file: str) -> tuple:
    """统计测试用例数量
    
    Args:
        test_file: 测试文件路径
        
    Returns:
        (总数, 通过数)
    """
    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 统计测试函数数量
    total = len(re.findall(r"def test_\w+", content))
    
    # 统计跳过的测试
    skipped = len(re.findall(r"@pytest.mark.skip", content))
    
    # 统计待实现的测试
    todo = len(re.findall(r"# TODO:", content))
    
    return total, total - skipped - todo

def update_readme(readme_path: str = "tests/README.md"):
    """更新README文件
    
    Args:
        readme_path: README文件路径
    """
    tests_dir = Path("tests")
    test_files = list(tests_dir.glob("test_*.py"))
    
    # 统计测试用例
    total_tests = 0
    passed_tests = 0
    module_stats = {}
    
    for test_file in test_files:
        module_name = test_file.stem.replace("test_", "")
        total, passed = count_tests(str(test_file))
        total_tests += total
        passed_tests += passed
        module_stats[module_name] = {
            "total": total,
            "passed": passed,
            "progress": round(passed / total * 100 if total > 0 else 0, 1)
        }
    
    # 读取README内容
    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 更新总体进度
    total_progress = round(passed_tests / total_tests * 100 if total_tests > 0 else 0, 1)
    content = re.sub(
        r"总体完成度: \d+\.\d+%",
        f"总体完成度: {total_progress}%",
        content
    )
    
    # 更新模块进度
    for module_name, stats in module_stats.items():
        pattern = rf"{module_name}测试: \d+% \(\d+/\d+\)"
        replacement = f"{module_name}测试: {stats['progress']}% ({stats['passed']}/{stats['total']})"
        content = re.sub(pattern, replacement, content)
    
    # 更新测试日志
    today = datetime.now().strftime("%Y-%m-%d")
    log_entry = f"\n### {today}\n"
    log_entry += f"- 总测试用例: {total_tests}\n"
    log_entry += f"- 通过用例: {passed_tests}\n"
    log_entry += f"- 完成度: {total_progress}%\n"
    
    content = re.sub(
        r"## 测试日志\n",
        f"## 测试日志\n{log_entry}",
        content
    )
    
    # 保存更新后的内容
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(content)

if __name__ == "__main__":
    # 更新README
    update_readme()
    
    print("进度更新完成！") 