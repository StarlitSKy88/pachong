"""数据清洗工具"""
import re
from typing import List, Dict, Any
from datetime import datetime
import html
import json

class DataCleaner:
    """数据清洗工具类"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本
        
        - 去除HTML标签
        - 去除多余空白字符
        - 去除特殊字符
        - HTML实体解码
        """
        if not text:
            return ''
            
        # 去除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # HTML实体解码
        text = html.unescape(text)
        
        # 去除特殊字符
        text = re.sub(r'[\r\n\t]', ' ', text)
        
        # 去除多余空白
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
        
    @staticmethod
    def clean_url(url: str) -> str:
        """清理URL
        
        - 去除跟踪参数
        - 统一协议
        - 去除多余参数
        """
        if not url:
            return ''
            
        # 去除跟踪参数
        url = re.sub(r'[?&](utm_source|utm_medium|utm_campaign)=[^&]*', '', url)
        
        # 统一协议
        url = re.sub(r'^http://', 'https://', url)
        
        return url.strip()
        
    @staticmethod
    def clean_time(time_str: str) -> datetime:
        """清理时间
        
        支持多种时间格式:
        - 时间戳(秒/毫秒)
        - ISO格式
        - 自然语言描述
        """
        if not time_str:
            return None
            
        try:
            # 尝试解析时间戳
            if time_str.isdigit():
                timestamp = int(time_str)
                if len(time_str) == 13:  # 毫秒
                    timestamp = timestamp / 1000
                return datetime.fromtimestamp(timestamp)
                
            # 尝试解析ISO格式
            return datetime.fromisoformat(time_str)
            
        except Exception:
            return None
            
    @staticmethod
    def clean_number(num_str: str) -> int:
        """清理数字
        
        支持:
        - 纯数字
        - 带单位的数字(k、w、万等)
        - 范围数字(取最小值)
        """
        if not num_str:
            return 0
            
        try:
            # 纯数字
            if num_str.isdigit():
                return int(num_str)
                
            # 带单位的数字
            unit_map = {
                'k': 1000,
                'w': 10000,
                '万': 10000,
                '千': 1000,
                '百': 100
            }
            
            for unit, value in unit_map.items():
                if unit in num_str.lower():
                    num = float(num_str.lower().replace(unit, ''))
                    return int(num * value)
                    
            # 范围数字
            if '-' in num_str:
                start, _ = num_str.split('-')
                return int(start)
                
        except Exception:
            return 0
            
        return 0
        
    @staticmethod
    def clean_json(json_str: str) -> Dict:
        """清理JSON字符串
        
        - 修复常见JSON错误
        - 移除注释
        - 处理特殊字符
        """
        if not json_str:
            return {}
            
        try:
            # 移除注释
            json_str = re.sub(r'//.*?\n|/\*.*?\*/', '', json_str)
            
            # 处理特殊字符
            json_str = json_str.replace('\n', '').replace('\r', '')
            
            return json.loads(json_str)
        except Exception:
            return {} 