"""LLM 客户端模块"""

import json
import time
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from ..config import AIModelConfig
from ..models import AIAnalysis


class LLMProvider(ABC):
    """LLM 提供商抽象基类"""

    @abstractmethod
    def call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用 LLM

        Args:
            prompt: 用户提示
            system_prompt: 系统提示

        Returns:
            模型返回的文本
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """检查提供商是否可用"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """获取模型名称"""
        pass


class AnthropicProvider(LLMProvider):
    """Anthropic Claude 提供商"""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.api_key = api_key
        self.model = model
        self._client = None

    @property
    def client(self):
        """延迟加载客户端"""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("请安装 anthropic 库: pip install anthropic")
        return self._client

    def call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用 Claude API"""
        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages,
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text

    def is_available(self) -> bool:
        """检查是否可用"""
        return bool(self.api_key)

    @property
    def model_name(self) -> str:
        return self.model


class OpenAIProvider(LLMProvider):
    """OpenAI GPT 提供商"""

    def __init__(self, api_key: str, model: str = "gpt-4",
                 base_url: Optional[str] = None):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None

    @property
    def client(self):
        """延迟加载客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = OpenAI(**kwargs)
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")
        return self._client

    def call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用 OpenAI API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    def is_available(self) -> bool:
        """检查是否可用"""
        return bool(self.api_key)

    @property
    def model_name(self) -> str:
        return self.model


class DeepSeekProvider(LLMProvider):
    """DeepSeek 提供商"""

    def __init__(self, api_key: str, model: str = "deepseek-chat",
                 base_url: str = "https://api.deepseek.com"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self._client = None

    @property
    def client(self):
        """延迟加载客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url
                )
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")
        return self._client

    def call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用 DeepSeek API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096,
        )
        return response.choices[0].message.content

    def is_available(self) -> bool:
        """检查是否可用"""
        return bool(self.api_key)

    @property
    def model_name(self) -> str:
        return self.model


class OllamaProvider(LLMProvider):
    """Ollama 本地提供商"""

    def __init__(self, base_url: str = "http://localhost:11434",
                 model: str = "llama3"):
        self.base_url = base_url
        self.model = model
        self._client = None

    @property
    def client(self):
        """延迟加载客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(
                    base_url=f"{self.base_url}/v1",
                    api_key="ollama"  # Ollama 不需要真实 API key
                )
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")
        return self._client

    def call(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """调用 Ollama API"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise ConnectionError(f"Ollama 调用失败: {e}")

    def is_available(self) -> bool:
        """检查是否可用"""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except Exception:
            return False

    @property
    def model_name(self) -> str:
        return self.model


class AIClient:
    """AI 客户端统一接口"""

    def __init__(self, provider: Optional[str] = None):
        """
        初始化 AI 客户端

        Args:
            provider: 指定提供商 (claude/openai/deepseek/ollama)
                     如果为 None 则使用配置默认值
        """
        self.config = AIModelConfig()
        self.provider_name = provider or self.config.default_provider
        self._provider: Optional[LLMProvider] = None
        self._initialize_provider()

    def _initialize_provider(self):
        """初始化 LLM 提供商"""
        providers = {
            "claude": self._create_anthropic_provider,
            "openai": self._create_openai_provider,
            "deepseek": self._create_deepseek_provider,
            "ollama": self._create_ollama_provider,
        }

        init_func = providers.get(self.provider_name)
        if init_func:
            self._provider = init_func()
        else:
            raise ValueError(f"不支持的提供商: {self.provider_name}")

    def _create_anthropic_provider(self) -> Optional[LLMProvider]:
        """创建 Anthropic 提供商"""
        api_key = self.config.claude_api_key
        if api_key:
            return AnthropicProvider(api_key, self.config.claude_model)
        return None

    def _create_openai_provider(self) -> Optional[LLMProvider]:
        """创建 OpenAI 提供商"""
        api_key = self.config.openai_api_key
        if api_key:
            return OpenAIProvider(api_key, self.config.openai_model)
        return None

    def _create_deepseek_provider(self) -> Optional[LLMProvider]:
        """创建 DeepSeek 提供商"""
        api_key = self.config.deepseek_api_key
        if api_key:
            return DeepSeekProvider(api_key, self.config.deepseek_model)
        return None

    def _create_ollama_provider(self) -> Optional[LLMProvider]:
        """创建 Ollama 提供商"""
        provider = OllamaProvider(self.config.ollama_base_url,
                                 self.config.ollama_model)
        if provider.is_available():
            return provider
        return None

    def analyze_repository(self, repo_name: str, description: str,
                          language: str, stars: int, today_stars: int,
                          readme_content: str,
                          system_prompt: Optional[str] = None) -> AIAnalysis:
        """
        分析仓库

        Args:
            repo_name: 仓库名
            description: 项目描述
            language: 编程语言
            stars: 星标数
            today_stars: 今日星标
            readme_content: README 内容
            system_prompt: 系统提示

        Returns:
            AI 分析结果
        """
        from .prompts import PromptManager

        prompt_manager = PromptManager()
        prompt = prompt_manager.build_analysis_prompt(
            repo_name=repo_name,
            description=description,
            language=language,
            stars=stars,
            today_stars=today_stars,
            readme_content=readme_content
        )

        analysis = AIAnalysis(
            analysis_status="analyzing",
            model_used=self._provider.model_name if self._provider else None
        )

        try:
            response = self._provider.call(
                prompt=prompt,
                system_prompt=system_prompt or prompt_manager.get_system_prompt()
            )

            from .parser import AIResultParser
            parser = AIResultParser()
            parsed = parser.parse_analysis_result(response)

            # 更新分析结果
            analysis.summary = parsed.get("summary", "")
            analysis.key_features = parsed.get("key_features", [])
            analysis.tech_stack = parsed.get("tech_stack", [])
            analysis.use_cases = parsed.get("use_cases", [])
            analysis.learning_value = parsed.get("learning_value", "medium")
            analysis.score = parsed.get("score", 5.0)
            analysis.is_worthwhile = parsed.get("is_worthwhile", False)
            analysis.reason = parsed.get("reason", "")
            analysis.analysis_status = "completed"
            analysis.analyzed_at = time.time()

        except Exception as e:
            analysis.analysis_status = "failed"
            analysis.error_message = str(e)

        return analysis

    def is_available(self) -> bool:
        """检查 AI 客户端是否可用"""
        return self._provider is not None and self._provider.is_available()

    def get_model_name(self) -> str:
        """获取当前使用的模型名称"""
        if self._provider:
            return self._provider.model_name
        return "unknown"

    def switch_provider(self, provider: str):
        """
        切换提供商

        Args:
            provider: 新的提供商名称
        """
        self.provider_name = provider
        self._initialize_provider()
