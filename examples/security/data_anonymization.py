"""数据脱敏示例"""

from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from typing import Dict, Any

class DataAnonymizer:
    """数据脱敏器"""
    
    def __init__(self):
        """初始化数据脱敏器"""
        self.analyzer = AnalyzerEngine()
        self.anonymizer = AnonymizerEngine()
        
    def anonymize_text(self, text: str) -> str:
        """文本脱敏
        
        Args:
            text: 原始文本
            
        Returns:
            str: 脱敏后的文本
        """
        results = self.analyzer.analyze(
            text=text,
            language='zh'
        )
        return self.anonymizer.anonymize(text, results)
        
    def anonymize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """字典脱敏
        
        Args:
            data: 原始数据字典
            
        Returns:
            Dict[str, Any]: 脱敏后的数据字典
        """
        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self.anonymize_text(value)
            elif isinstance(value, dict):
                result[key] = self.anonymize_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    self.anonymize_dict(item) if isinstance(item, dict)
                    else self.anonymize_text(item) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                result[key] = value
        return result

# 使用示例
if __name__ == "__main__":
    anonymizer = DataAnonymizer()
    
    # 文本脱敏
    text = "张三的手机号是13812345678，邮箱是zhangsan@example.com"
    anonymized_text = anonymizer.anonymize_text(text)
    print(f"原始文本: {text}")
    print(f"脱敏文本: {anonymized_text}")
    
    # 字典脱敏
    data = {
        "user": {
            "name": "张三",
            "phone": "13812345678",
            "email": "zhangsan@example.com",
            "age": 25,
            "addresses": [
                {
                    "city": "北京",
                    "detail": "朝阳区xxx街道"
                }
            ]
        }
    }
    anonymized_data = anonymizer.anonymize_dict(data)
    print("\n原始数据:", data)
    print("\n脱敏数据:", anonymized_data) 