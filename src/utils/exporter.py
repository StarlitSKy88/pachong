import json
import csv
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from .logger import get_logger
from .exceptions import CrawlerException

logger = get_logger(__name__)

class Exporter:
    """数据导出工具"""
    
    def __init__(self, output_dir: str = "exports"):
        """初始化导出工具
        
        Args:
            output_dir: 输出目录
        """
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def export_json(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        indent: int = 2,
        ensure_ascii: bool = False
    ) -> str:
        """导出JSON格式
        
        Args:
            data: 数据列表
            filename: 文件名
            indent: 缩进空格数
            ensure_ascii: 是否确保ASCII编码
            
        Returns:
            str: 输出文件路径
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=indent, ensure_ascii=ensure_ascii)
                
            logger.info(f"导出JSON文件：{filepath}")
            return filepath
            
        except Exception as e:
            raise CrawlerException(f"导出JSON失败：{str(e)}")
            
    def export_csv(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        headers: Optional[List[str]] = None,
        encoding: str = "utf-8-sig"
    ) -> str:
        """导出CSV格式
        
        Args:
            data: 数据列表
            filename: 文件名
            headers: 列标题
            encoding: 文件编码
            
        Returns:
            str: 输出文件路径
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            if not headers and data:
                headers = list(data[0].keys())
                
            with open(filepath, "w", encoding=encoding, newline="") as f:
                writer = csv.DictWriter(f, fieldnames=headers)
                writer.writeheader()
                writer.writerows(data)
                
            logger.info(f"导出CSV文件：{filepath}")
            return filepath
            
        except Exception as e:
            raise CrawlerException(f"导出CSV失败：{str(e)}")
            
    def export_excel(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        sheet_name: str = "Sheet1"
    ) -> str:
        """导出Excel格式
        
        Args:
            data: 数据列表
            filename: 文件名
            sheet_name: 工作表名称
            
        Returns:
            str: 输出文件路径
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            df = pd.DataFrame(data)
            df.to_excel(
                filepath,
                sheet_name=sheet_name,
                index=False,
                engine="openpyxl"
            )
            
            logger.info(f"导出Excel文件：{filepath}")
            return filepath
            
        except Exception as e:
            raise CrawlerException(f"导出Excel失败：{str(e)}")
            
    def export_markdown(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        headers: Optional[List[str]] = None
    ) -> str:
        """导出Markdown格式
        
        Args:
            data: 数据列表
            filename: 文件名
            headers: 列标题
            
        Returns:
            str: 输出文件路径
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            if not headers and data:
                headers = list(data[0].keys())
                
            with open(filepath, "w", encoding="utf-8") as f:
                # 写入表头
                f.write("| " + " | ".join(headers) + " |\n")
                f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")
                
                # 写入数据
                for item in data:
                    row = [str(item.get(h, "")) for h in headers]
                    f.write("| " + " | ".join(row) + " |\n")
                    
            logger.info(f"导出Markdown文件：{filepath}")
            return filepath
            
        except Exception as e:
            raise CrawlerException(f"导出Markdown失败：{str(e)}")
            
    def export_html(
        self,
        data: List[Dict[str, Any]],
        filename: str,
        title: str = "数据导出",
        headers: Optional[List[str]] = None
    ) -> str:
        """导出HTML格式
        
        Args:
            data: 数据列表
            filename: 文件名
            title: 页面标题
            headers: 列标题
            
        Returns:
            str: 输出文件路径
        """
        try:
            filepath = os.path.join(self.output_dir, filename)
            
            if not headers and data:
                headers = list(data[0].keys())
                
            df = pd.DataFrame(data)
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{title}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        margin: 20px;
                    }}
                    table {{
                        border-collapse: collapse;
                        width: 100%;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 8px;
                        text-align: left;
                    }}
                    th {{
                        background-color: #f2f2f2;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f9f9f9;
                    }}
                </style>
            </head>
            <body>
                <h1>{title}</h1>
                <p>导出时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                {df.to_html(index=False)}
            </body>
            </html>
            """
            
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
                
            logger.info(f"导出HTML文件：{filepath}")
            return filepath
            
        except Exception as e:
            raise CrawlerException(f"导出HTML失败：{str(e)}")
            
    def export_all(
        self,
        data: List[Dict[str, Any]],
        filename_prefix: str,
        **kwargs
    ) -> Dict[str, str]:
        """导出所有支持的格式
        
        Args:
            data: 数据列表
            filename_prefix: 文件名前缀
            **kwargs: 其他参数
            
        Returns:
            Dict[str, str]: 各格式输出文件路径
        """
        results = {}
        
        # 导出JSON
        json_file = f"{filename_prefix}.json"
        results["json"] = self.export_json(data, json_file, **kwargs)
        
        # 导出CSV
        csv_file = f"{filename_prefix}.csv"
        results["csv"] = self.export_csv(data, csv_file, **kwargs)
        
        # 导出Excel
        excel_file = f"{filename_prefix}.xlsx"
        results["excel"] = self.export_excel(data, excel_file, **kwargs)
        
        # 导出Markdown
        md_file = f"{filename_prefix}.md"
        results["markdown"] = self.export_markdown(data, md_file, **kwargs)
        
        # 导出HTML
        html_file = f"{filename_prefix}.html"
        results["html"] = self.export_html(data, html_file, **kwargs)
        
        return results 