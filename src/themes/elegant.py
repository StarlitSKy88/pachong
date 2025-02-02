from .base import Theme

class ElegantTheme(Theme):
    """优雅主题"""
    
    def __init__(self):
        super().__init__()
        self.name = "elegant"
        self._update_styles()
    
    def _update_styles(self):
        """更新优雅主题样式"""
        self.styles.update({
            "colors": {
                "primary": "#2c3e50",
                "secondary": "#7f8c8d",
                "background": "#f8f9fa",
                "highlight": "#f1f3f5",
                "border": "#e9ecef",
                "link": "#3498db"
            },
            "fonts": {
                "title": {
                    "size": "32px",
                    "weight": "300",  # 使用细体
                    "color": "var(--primary-color)"
                },
                "subtitle": {
                    "size": "22px",
                    "weight": "300",
                    "color": "var(--secondary-color)"
                },
                "body": {
                    "size": "16px",
                    "weight": "400",
                    "color": "var(--primary-color)"
                }
            },
            "spacing": {
                "padding": "20px",
                "margin": "25px",
                "border_radius": "12px"
            },
            "effects": {
                "shadow": "0 8px 16px rgba(0,0,0,0.05)",
                "transition": "all 0.5s cubic-bezier(0.4, 0, 0.2, 1)"
            }
        })
    
    def get_base_styles(self) -> str:
        """获取优雅主题的基础样式"""
        base_styles = super().get_base_styles()
        
        # 添加优雅主题特有的样式
        additional_styles = f"""
            body {{
                background-color: var(--background-color);
                letter-spacing: 0.3px;
            }}
            
            .title {{
                letter-spacing: 1px;
                margin-bottom: 30px;
            }}
            
            .subtitle {{
                letter-spacing: 0.5px;
                margin-bottom: 25px;
            }}
            
            .highlight {{
                background-color: var(--background-color);
                border: 1px solid var(--border-color);
                box-shadow: {self.get_style('effects.shadow')};
            }}
            
            .tag {{
                background-color: transparent;
                border: 1px solid var(--link-color);
                color: var(--link-color);
                font-weight: 400;
                letter-spacing: 0.5px;
                padding: 6px 16px;
            }}
            
            .tag:hover {{
                background-color: var(--link-color);
                color: var(--background-color);
                transform: translateY(-1px);
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            
            .quote {{
                font-style: italic;
                color: var(--secondary-color);
                border-left: 2px solid var(--link-color);
                padding: 15px 20px;
                margin: 20px 0;
                background-color: var(--highlight-color);
                border-radius: 0 {self.get_style('spacing.border_radius')} {self.get_style('spacing.border_radius')} 0;
            }}
            
            .content p {{
                line-height: 1.8;
                margin-bottom: 20px;
            }}
            
            .tips {{
                background-color: var(--background-color);
                border: 1px solid var(--border-color);
                padding: 20px;
                border-radius: {self.get_style('spacing.border_radius')};
                box-shadow: {self.get_style('effects.shadow')};
            }}
        """
        
        return base_styles + additional_styles 