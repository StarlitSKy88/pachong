from .base import Theme

class DefaultTheme(Theme):
    """默认主题"""
    
    def __init__(self):
        super().__init__()
        self.name = "default"
        self._update_styles()
    
    def _update_styles(self):
        """更新默认主题样式"""
        self.styles.update({
            "colors": {
                "primary": "#333333",
                "secondary": "#666666",
                "background": "#ffffff",
                "highlight": "#fff9e6",
                "border": "#eeeeee",
                "link": "#0066cc"
            },
            "effects": {
                "shadow": "0 2px 4px rgba(0,0,0,0.1)",
                "transition": "all 0.3s ease"
            }
        }) 