import pytest
import os
import json
import pandas as pd
from src.utils.exporter import Exporter
from src.utils.exceptions import CrawlerException

@pytest.fixture
def test_data():
    """测试数据"""
    return [
        {
            "id": 1,
            "title": "测试标题1",
            "content": "测试内容1",
            "tags": ["标签1", "标签2"]
        },
        {
            "id": 2,
            "title": "测试标题2",
            "content": "测试内容2",
            "tags": ["标签2", "标签3"]
        }
    ]

@pytest.fixture
def exporter(tmp_path):
    """创建导出工具实例"""
    return Exporter(output_dir=str(tmp_path))

def test_init_exporter(tmp_path):
    """测试初始化导出工具"""
    output_dir = os.path.join(tmp_path, "exports")
    exporter = Exporter(output_dir=output_dir)
    
    assert os.path.exists(output_dir)
    assert exporter.output_dir == output_dir

def test_export_json(exporter, test_data):
    """测试导出JSON"""
    filepath = exporter.export_json(test_data, "test.json")
    
    assert os.path.exists(filepath)
    
    # 验证文件内容
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[1]["title"] == "测试标题2"

def test_export_csv(exporter, test_data):
    """测试导出CSV"""
    filepath = exporter.export_csv(test_data, "test.csv")
    
    assert os.path.exists(filepath)
    
    # 验证文件内容
    df = pd.read_csv(filepath)
    assert len(df) == 2
    assert list(df.columns) == ["id", "title", "content", "tags"]
    assert df.iloc[0]["title"] == "测试标题1"

def test_export_excel(exporter, test_data):
    """测试导出Excel"""
    filepath = exporter.export_excel(test_data, "test.xlsx")
    
    assert os.path.exists(filepath)
    
    # 验证文件内容
    df = pd.read_excel(filepath)
    assert len(df) == 2
    assert list(df.columns) == ["id", "title", "content", "tags"]
    assert df.iloc[1]["title"] == "测试标题2"

def test_export_markdown(exporter, test_data):
    """测试导出Markdown"""
    filepath = exporter.export_markdown(test_data, "test.md")
    
    assert os.path.exists(filepath)
    
    # 验证文件内容
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "| id | title | content | tags |" in content
    assert "| 1 | 测试标题1 | 测试内容1 |" in content
    assert "| 2 | 测试标题2 | 测试内容2 |" in content

def test_export_html(exporter, test_data):
    """测试导出HTML"""
    filepath = exporter.export_html(
        test_data,
        "test.html",
        title="测试导出"
    )
    
    assert os.path.exists(filepath)
    
    # 验证文件内容
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "<title>测试导出</title>" in content
    assert "测试标题1" in content
    assert "测试标题2" in content
    assert "测试内容1" in content
    assert "测试内容2" in content

def test_export_all(exporter, test_data):
    """测试导出所有格式"""
    results = exporter.export_all(test_data, "test_all")
    
    assert len(results) == 5  # json, csv, excel, markdown, html
    
    # 验证所有文件都存在
    for filepath in results.values():
        assert os.path.exists(filepath)
        
    # 验证文件扩展名
    assert results["json"].endswith(".json")
    assert results["csv"].endswith(".csv")
    assert results["excel"].endswith(".xlsx")
    assert results["markdown"].endswith(".md")
    assert results["html"].endswith(".html")

def test_export_empty_data(exporter):
    """测试导出空数据"""
    with pytest.raises(CrawlerException):
        exporter.export_json([], "empty.json")
        
    with pytest.raises(CrawlerException):
        exporter.export_csv([], "empty.csv")
        
    with pytest.raises(CrawlerException):
        exporter.export_excel([], "empty.xlsx")
        
    with pytest.raises(CrawlerException):
        exporter.export_markdown([], "empty.md")
        
    with pytest.raises(CrawlerException):
        exporter.export_html([], "empty.html")

def test_export_invalid_data(exporter):
    """测试导出无效数据"""
    invalid_data = [{"id": 1}, {"name": "test"}]  # 字段不一致的数据
    
    with pytest.raises(CrawlerException):
        exporter.export_csv(invalid_data, "invalid.csv")
        
    with pytest.raises(CrawlerException):
        exporter.export_excel(invalid_data, "invalid.xlsx")
        
    with pytest.raises(CrawlerException):
        exporter.export_markdown(invalid_data, "invalid.md")
        
    with pytest.raises(CrawlerException):
        exporter.export_html(invalid_data, "invalid.html")

def test_export_with_headers(exporter, test_data):
    """测试指定列标题导出"""
    headers = ["id", "title"]  # 只导出部分字段
    
    # 测试CSV
    csv_file = exporter.export_csv(test_data, "test.csv", headers=headers)
    df = pd.read_csv(csv_file)
    assert list(df.columns) == headers
    
    # 测试Markdown
    md_file = exporter.export_markdown(test_data, "test.md", headers=headers)
    with open(md_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "| id | title |" in content
        assert "content" not in content
        
    # 测试HTML
    html_file = exporter.export_html(
        test_data,
        "test.html",
        headers=headers
    )
    with open(html_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert "content" not in content
        assert "tags" not in content 