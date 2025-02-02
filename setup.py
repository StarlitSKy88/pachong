"""项目安装配置"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="crawler",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="智能内容分析和生成系统",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/your-repo",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=[
        "aiohttp>=3.8.0",
        "loguru>=0.7.0",
        "sqlalchemy>=2.0.0",
        "pytest>=7.0.0",
        "pytest-asyncio>=0.23.0",
        "pytest-mock>=3.12.0"
    ],
    entry_points={
        "console_scripts": [
            "crawler=src.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.json", "*.yaml", "*.yml", "*.txt"],
    },
    zip_safe=False,
) 