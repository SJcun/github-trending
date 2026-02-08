"""配置管理模块"""

import os
from pathlib import Path
from typing import Optional
import yaml


class Config:
    """全局配置"""

    # 项目路径
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = BASE_DIR / "data"
    CACHE_DIR = DATA_DIR / "cache"
    OUTPUT_DIR = BASE_DIR / "outputs"
    CONFIG_DIR = BASE_DIR / "config"

    # GitHub 配置
    GITHUB_BASE_URL = "https://github.com"
    GITHUB_TRENDING_URL = f"{GITHUB_BASE_URL}/trending"
    GITHUB_API_BASE = "https://api.github.com"

    # 爬虫配置
    DEFAULT_USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
    ]
    REQUEST_TIMEOUT = 30
    REQUEST_RETRY = 3
    REQUEST_DELAY_MIN = 1.0
    REQUEST_DELAY_MAX = 3.0

    # 数据库配置
    DB_PATH = DATA_DIR / "github_trending.db"

    # 输出配置
    DEFAULT_LIMIT = 25
    OUTPUT_FORMATS = ["table", "json", "markdown", "csv"]

    # 时间范围选项
    PERIOD_OPTIONS = ["daily", "weekly", "monthly"]

    # 常用语言列表
    POPULAR_LANGUAGES = [
        "python", "javascript", "typescript", "java", "go",
        "rust", "c++", "c", "ruby", "php", "swift", "kotlin",
        "dart", "shell", "html", "css", "vue", "react"
    ]

    @classmethod
    def ensure_dirs(cls):
        """确保必要的目录存在"""
        cls.DATA_DIR.mkdir(exist_ok=True)
        cls.CACHE_DIR.mkdir(exist_ok=True)
        cls.OUTPUT_DIR.mkdir(exist_ok=True)
        cls.CONFIG_DIR.mkdir(exist_ok=True)

    @classmethod
    def load_ai_config(cls) -> dict:
        """加载 AI 配置"""
        config_file = cls.CONFIG_DIR / "ai_config.yaml"
        if config_file.exists():
            with open(config_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        return {}

    @classmethod
    def get_env_var(cls, key: str, default: Optional[str] = None) -> Optional[str]:
        """获取环境变量"""
        return os.getenv(key, default)


class AIModelConfig:
    """AI 模型配置"""

    def __init__(self):
        self.config = Config.load_ai_config()

    @property
    def claude_api_key(self) -> Optional[str]:
        """Claude API Key"""
        return Config.get_env_var("ANTHROPIC_API_KEY") or self.config.get("claude", {}).get("api_key")

    @property
    def claude_model(self) -> str:
        """Claude 模型"""
        return self.config.get("claude", {}).get("model", "claude-3-5-sonnet-20241022")

    @property
    def openai_api_key(self) -> Optional[str]:
        """OpenAI API Key"""
        return Config.get_env_var("OPENAI_API_KEY") or self.config.get("openai", {}).get("api_key")

    @property
    def openai_model(self) -> str:
        """OpenAI 模型"""
        return self.config.get("openai", {}).get("model", "gpt-4")

    @property
    def deepseek_api_key(self) -> Optional[str]:
        """DeepSeek API Key"""
        return Config.get_env_var("DEEPSEEK_API_KEY") or self.config.get("deepseek", {}).get("api_key")

    @property
    def deepseek_model(self) -> str:
        """DeepSeek 模型"""
        return self.config.get("deepseek", {}).get("model", "deepseek-chat")

    @property
    def ollama_base_url(self) -> str:
        """Ollama 基础 URL"""
        return self.config.get("ollama", {}).get("base_url", "http://localhost:11434")

    @property
    def ollama_model(self) -> str:
        """Ollama 模型"""
        return self.config.get("ollama", {}).get("model", "llama3")

    @property
    def default_provider(self) -> str:
        """默认 AI 提供商"""
        return self.config.get("default_provider", "claude")

    @property
    def max_tokens(self) -> int:
        """最大 Token 数"""
        return self.config.get("max_tokens", 4096)

    @property
    def temperature(self) -> float:
        """温度参数"""
        return self.config.get("temperature", 0.7)

    @property
    def enable_cache(self) -> bool:
        """是否启用缓存"""
        return self.config.get("enable_cache", True)

    @property
    def cache_ttl_hours(self) -> int:
        """缓存有效期（小时）"""
        return self.config.get("cache_ttl_hours", 24)


# 确保目录存在
Config.ensure_dirs()
