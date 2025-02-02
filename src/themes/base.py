from typing import Dict, Any
from ..config import config

class Theme:
    """基础主题类"""
    
    def __init__(self):
        self.name = "base"
        self.font_family = config.get('theme.font_family')
        self._init_styles()
    
    def _init_styles(self):
        """初始化样式"""
        self.styles = {
            "colors": {
                "primary": "#333333",
                "secondary": "#666666",
                "background": "#ffffff",
                "highlight": "#fff9e6",
                "border": "#eeeeee",
                "link": "#0066cc"
            },
            "fonts": {
                "title": {
                    "size": "24px",
                    "weight": "bold",
                    "color": "var(--primary-color)"
                },
                "subtitle": {
                    "size": "18px",
                    "weight": "normal",
                    "color": "var(--secondary-color)"
                },
                "body": {
                    "size": "16px",
                    "weight": "normal",
                    "color": "var(--primary-color)"
                }
            },
            "spacing": {
                "padding": "15px",
                "margin": "20px",
                "border_radius": "8px"
            },
            "effects": {
                "shadow": "0 2px 4px rgba(0,0,0,0.1)",
                "transition": "all 0.3s ease"
            }
        }
    
    def get_style(self, key: str, default: Any = None) -> Any:
        """获取样式值"""
        keys = key.split('.')
        value = self.styles
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def get_css_variables(self) -> str:
        """获取CSS变量定义"""
        colors = self.styles["colors"]
        return f"""
            :root {{
                --primary-color: {colors["primary"]};
                --secondary-color: {colors["secondary"]};
                --background-color: {colors["background"]};
                --highlight-color: {colors["highlight"]};
                --border-color: {colors["border"]};
                --link-color: {colors["link"]};
                --font-family: {self.font_family};
            }}
        """
    
    def get_base_styles(self) -> str:
        """获取基础样式"""
        return f"""
            body {{
                font-family: var(--font-family);
                line-height: 1.6;
                color: var(--primary-color);
                background-color: var(--background-color);
                margin: 0 auto;
                padding: {self.get_style('spacing.padding')};
            }}
            
            .title {{
                font-size: {self.get_style('fonts.title.size')};
                font-weight: {self.get_style('fonts.title.weight')};
                color: {self.get_style('fonts.title.color')};
                margin-bottom: {self.get_style('spacing.margin')};
                text-align: center;
            }}
            
            .subtitle {{
                font-size: {self.get_style('fonts.subtitle.size')};
                color: {self.get_style('fonts.subtitle.color')};
                margin-bottom: {self.get_style('spacing.margin')};
                text-align: center;
            }}
            
            .content {{
                font-size: {self.get_style('fonts.body.size')};
                color: {self.get_style('fonts.body.color')};
                margin-bottom: {self.get_style('spacing.margin')};
            }}
            
            .highlight {{
                background-color: var(--highlight-color);
                padding: {self.get_style('spacing.padding')};
                border-radius: {self.get_style('spacing.border_radius')};
                box-shadow: {self.get_style('effects.shadow')};
            }}
            
            .tags {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
                margin-top: {self.get_style('spacing.margin')};
            }}
            
            .tag {{
                background-color: var(--highlight-color);
                color: var(--link-color);
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 14px;
                transition: {self.get_style('effects.transition')};
            }}
            
            .tag:hover {{
                background-color: var(--link-color);
                color: var(--background-color);
            }}
            
            @media screen and (max-width: 768px) {{
                body {{
                    padding: 10px;
                }}
                .title {{
                    font-size: 20px;
                }}
                .content {{
                    font-size: 16px;
                }}
            }}
        """
    
    def get_template_styles(self) -> str:
        """获取模板样式"""
        return self.get_css_variables() + self.get_base_styles() 