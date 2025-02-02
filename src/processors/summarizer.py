import requests
import json
from typing import Dict, List, Optional
from config.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, DEEPSEEK_MODEL, SUMMARY_PROMPTS

class DeepseekClient:
    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.model = DEEPSEEK_MODEL
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def _make_request(self, messages: List[Dict[str, str]]) -> Optional[str]:
        """发送请求到Deepseek API"""
        try:
            data = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 2000
            }
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"API调用错误: {str(e)}")
            return None

    def summarize_content(self, content: str) -> Optional[Dict]:
        """总结单个内容"""
        prompt = SUMMARY_PROMPTS["content_summary"].format(content=content)
        messages = [
            {"role": "system", "content": "你是一个专业的内容分析师，擅长总结和分类技术相关内容。"},
            {"role": "user", "content": prompt}
        ]
        
        response = self._make_request(messages)
        if not response:
            return None
            
        return self._parse_summary_response(response)

    def generate_daily_report(self, date: str, cursor_content: List[Dict], 
                            indie_dev_content: List[Dict], ai_news_content: List[Dict]) -> Optional[str]:
        """生成每日报告"""
        # 格式化每个类别的内容
        cursor_summary = self._format_category_content(cursor_content)
        indie_dev_summary = self._format_category_content(indie_dev_content)
        ai_news_summary = self._format_category_content(ai_news_content)
        
        prompt = SUMMARY_PROMPTS["daily_report"].format(
            date=date,
            cursor_content=cursor_summary,
            indie_dev_content=indie_dev_summary,
            ai_news_content=ai_news_summary
        )
        
        messages = [
            {"role": "system", "content": "你是一个专业的技术趋势分析师，请对今日的技术内容进行总结。"},
            {"role": "user", "content": prompt}
        ]
        
        return self._make_request(messages)

    def _parse_summary_response(self, response: str) -> Dict:
        """解析API返回的总结内容"""
        try:
            lines = response.strip().split("\n")
            result = {
                "category": "",
                "summary": "",
                "key_points": [],
                "value_score": 0,
                "value_explanation": ""
            }
            
            current_section = ""
            for line in lines:
                line = line.strip()
                if "主题分类：" in line:
                    result["category"] = line.split("：", 1)[1].strip()
                elif "主要内容：" in line:
                    result["summary"] = line.split("：", 1)[1].strip()
                elif "关键信息：" in line:
                    current_section = "key_points"
                elif "价值评估：" in line:
                    value_info = line.split("：", 1)[1].strip()
                    # 提取星级评分
                    result["value_score"] = value_info.count("★")
                    result["value_explanation"] = value_info
                elif current_section == "key_points" and line.startswith("- "):
                    result["key_points"].append(line[2:])
                    
            return result
        except Exception as e:
            print(f"解析响应错误: {str(e)}")
            return None

    def _format_category_content(self, content_list: List[Dict]) -> str:
        """格式化分类内容"""
        if not content_list:
            return "暂无相关内容"
            
        formatted = []
        for item in content_list:
            formatted.append(f"### {item['title']}\n")
            formatted.append(f"- 主要内容：{item['summary']}\n")
            formatted.append("- 关键点：\n")
            for point in item['key_points']:
                formatted.append(f"  * {point}\n")
            formatted.append(f"- 价值评估：{'★' * item['value_score']} ({item['value_explanation']})\n")
            
        return "\n".join(formatted) 