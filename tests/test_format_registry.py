import pytest
from typing import Dict, Any
from pathlib import Path

from src.export.base import ExportFormat
from src.export.registry import FormatRegistry
from src.export.html import HTMLExport
from src.utils.errors import ExportError

class MockFormat(ExportFormat):
    """测试用导出格式类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.exported_data = []

    async def export(self, data: Dict[str, Any], output_path: Path) -> Path:
        self.exported_data.append((data, output_path))
        return output_path

    async def batch_export(self, items: list[Dict[str, Any]], output_dir: Path) -> list[Path]:
        paths = []
        for item in items:
            path = await self.export(item, output_dir / f"{item.get('id', 'test')}.mock")
            paths.append(path)
        return paths

@pytest.fixture
def registry():
    """创建格式注册表实例"""
    return FormatRegistry()

@pytest.fixture
def format_config():
    """创建格式配置"""
    return {
        "enabled": True,
        "templates": {
            "article": "templates/mock/article.mock",
            "post": "templates/mock/post.mock"
        },
        "options": {
            "quality": "high",
            "compress": True
        }
    }

class TestFormatRegistry:
    """格式注册表测试类"""

    def test_register_format(self, registry, format_config):
        """测试格式注册"""
        registry.register("mock", MockFormat, format_config)
        assert "mock" in registry.formats
        assert isinstance(registry.get_format("mock"), MockFormat)
        assert registry.get_format("mock").config == format_config

    def test_register_duplicate_format(self, registry, format_config):
        """测试重复注册格式"""
        registry.register("mock", MockFormat, format_config)
        with pytest.raises(ExportError):
            registry.register("mock", MockFormat, format_config)

    def test_register_invalid_format(self, registry, format_config):
        """测试注册无效格式"""
        class InvalidFormat:
            pass

        with pytest.raises(ExportError):
            registry.register("invalid", InvalidFormat, format_config)

    def test_get_nonexistent_format(self, registry):
        """测试获取不存在的格式"""
        with pytest.raises(ExportError):
            registry.get_format("nonexistent")

    def test_format_enable_disable(self, registry, format_config):
        """测试格式启用/禁用"""
        registry.register("mock", MockFormat, format_config)
        
        # 测试禁用
        registry.disable_format("mock")
        with pytest.raises(ExportError):
            registry.get_format("mock")
        
        # 测试启用
        registry.enable_format("mock")
        assert isinstance(registry.get_format("mock"), MockFormat)

    def test_format_config_update(self, registry, format_config):
        """测试格式配置更新"""
        registry.register("mock", MockFormat, format_config)
        
        new_config = format_config.copy()
        new_config["options"]["quality"] = "low"
        
        registry.update_format_config("mock", new_config)
        assert registry.get_format("mock").config["options"]["quality"] == "low"

    def test_format_config_validation(self, registry):
        """测试格式配置验证"""
        invalid_config = {
            "enabled": "invalid",  # 应该是布尔值
            "templates": "invalid",  # 应该是字典
            "options": []  # 应该是字典
        }
        
        with pytest.raises(ExportError):
            registry.register("mock", MockFormat, invalid_config)

    def test_format_list(self, registry, format_config):
        """测试获取格式列表"""
        registry.register("mock1", MockFormat, format_config)
        registry.register("mock2", MockFormat, format_config)
        
        formats = registry.list_formats()
        assert "mock1" in formats
        assert "mock2" in formats
        assert len(formats) == 2

    def test_format_clear(self, registry, format_config):
        """测试清除格式"""
        registry.register("mock1", MockFormat, format_config)
        registry.register("mock2", MockFormat, format_config)
        
        registry.clear_formats()
        assert len(registry.list_formats()) == 0

    def test_html_format_registration(self, registry):
        """测试HTML格式注册"""
        config = {
            "enabled": True,
            "templates": {
                "article": "templates/html/article.html",
                "post": "templates/html/post.html"
            },
            "options": {
                "minify": True,
                "image_quality": 85
            }
        }
        
        registry.register("html", HTMLExport, config)
        html_format = registry.get_format("html")
        
        assert isinstance(html_format, HTMLExport)
        assert html_format.config["options"]["minify"] is True
        assert html_format.config["options"]["image_quality"] == 85

    def test_format_dependency_check(self, registry, format_config):
        """测试格式依赖检查"""
        # 模拟缺少依赖的情况
        class DependentFormat(MockFormat):
            @classmethod
            def check_dependencies(cls) -> bool:
                return False

        with pytest.raises(ExportError):
            registry.register("dependent", DependentFormat, format_config)

    def test_format_cleanup(self, registry, format_config):
        """测试格式清理"""
        class CleanableFormat(MockFormat):
            def __init__(self, config):
                super().__init__(config)
                self.cleaned_up = False

            async def cleanup(self):
                self.cleaned_up = True

        registry.register("cleanable", CleanableFormat, format_config)
        format_instance = registry.get_format("cleanable")
        
        # 测试清理
        registry.clear_formats()
        assert format_instance.cleaned_up 