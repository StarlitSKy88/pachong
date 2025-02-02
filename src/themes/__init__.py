from .base import Theme
from .default import DefaultTheme
from .modern import ModernTheme
from .elegant import ElegantTheme

# 主题注册表
THEMES = {
    'default': DefaultTheme,
    'modern': ModernTheme,
    'elegant': ElegantTheme
}

def get_theme(name: str = 'default') -> Theme:
    """获取主题实例"""
    theme_class = THEMES.get(name, DefaultTheme)
    return theme_class() 