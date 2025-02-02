from .base import Theme

class ModernTheme(Theme):
    """现代主题"""
    
    def __init__(self):
        super().__init__()
        self.name = "modern"
        self._update_styles()
    
    def _update_styles(self):
        """更新现代主题样式"""
        self.styles.update({
            "colors": {
                "primary": "#2d3436",
                "secondary": "#636e72",
                "background": "#ffffff",
                "highlight": "#dfe6e9",
                "border": "#b2bec3",
                "link": "#0984e3"
            },
            "fonts": {
                "title": {
                    "size": "28px",
                    "weight": "800",
                    "color": "var(--primary-color)"
                },
                "subtitle": {
                    "size": "20px",
                    "weight": "600",
                    "color": "var(--secondary-color)"
                }
            },
            "effects": {
                "shadow": "0 4px 6px rgba(0,0,0,0.1)",
                "transition": "all 0.4s cubic-bezier(0.4, 0, 0.2, 1)"
            }
        })
    
    def get_base_styles(self) -> str:
        """获取现代主题的基础样式"""
        base_styles = super().get_base_styles()
        
        # 添加现代主题特有的样式
        additional_styles = f"""
            .highlight {{
                background: linear-gradient(135deg, var(--highlight-color) 0%, #fff 100%);
                border-left: 4px solid var(--link-color);
            }}
            
            .tag {{
                background-color: var(--background-color);
                border: 1px solid var(--link-color);
                color: var(--link-color);
                font-weight: 500;
            }}
            
            .tag:hover {{
                background-color: var(--link-color);
                color: var(--background-color);
                transform: translateY(-2px);
            }}
            
            .quote {{
                border-left: 4px solid var(--link-color);
                padding-left: 1em;
                margin: 1em 0;
                font-style: italic;
                background-color: var(--highlight-color);
                border-radius: 0 {self.get_style('spacing.border_radius')} {self.get_style('spacing.border_radius')} 0;
            }}
        """
        
        return base_styles + additional_styles 