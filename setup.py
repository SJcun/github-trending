# -*- coding: utf-8 -*-
"""GitHub Trending 安装配置"""

import os
import sys
from setuptools import setup, find_packages

# 设置标准输出编码为 utf-8（Windows 兼容）
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# 读取 README（使用安全的方式）
def read_file(filepath, default=""):
    """安全读取文件，处理编码问题"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except (UnicodeDecodeError, IOError):
        try:
            with open(filepath, "r", encoding="gbk") as f:
                return f.read()
        except:
            return default

# 读取 README
long_description = read_file("README.md", "GitHub Trending - 获取并解读 GitHub Trending")

# 读取依赖
requirements = []
try:
    with open("requirements.txt", "r", encoding="utf-8") as f:
        requirements = [
            line.strip()
            for line in f.readlines()
            if line.strip() and not line.startswith("#")
        ]
except (UnicodeDecodeError, IOError):
    # 如果 UTF-8 失败，使用 GBK
    try:
        with open("requirements.txt", "r", encoding="gbk") as f:
            requirements = [
                line.strip()
                for line in f.readlines()
                if line.strip() and not line.startswith("#")
            ]
    except:
        requirements = []

setup(
    name="github-trending",
    version="0.1.0",
    description="获取并解读 GitHub Trending 界面，支持 AI 智能分析",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/github-trending",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "github-trending=cli:cli",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="github trending scraper ai analysis llm",
    license="MIT",
)
