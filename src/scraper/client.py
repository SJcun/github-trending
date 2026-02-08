"""HTTP 客户端模块"""

import random
import time
from typing import Optional, Dict, Any
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..config import Config


class HttpClient:
    """HTTP 客户端，处理请求、重试和代理"""

    def __init__(self, proxy: Optional[str] = None):
        """
        初始化 HTTP 客户端

        Args:
            proxy: 代理地址，如 http://127.0.0.1:7890
        """
        self.session = self._create_session()
        self.proxy = proxy
        self._setup_session()

    def _create_session(self) -> requests.Session:
        """创建带重试策略的 Session"""
        session = requests.Session()

        # 配置重试策略
        retry_strategy = Retry(
            total=Config.REQUEST_RETRY,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _setup_session(self):
        """设置 Session 参数"""
        # 设置默认 headers
        self.session.headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        })

    def _get_random_user_agent(self) -> str:
        """获取随机 User-Agent"""
        return random.choice(Config.DEFAULT_USER_AGENTS)

    def get(self, url: str, params: Optional[Dict] = None,
            headers: Optional[Dict] = None, timeout: Optional[int] = None) -> requests.Response:
        """
        发送 GET 请求

        Args:
            url: 请求 URL
            params: 查询参数
            headers: 额外的请求头
            timeout: 超时时间（秒）

        Returns:
            响应对象

        Raises:
            requests.RequestException: 请求失败
        """
        # 合并 headers
        request_headers = {}
        if headers:
            request_headers.update(headers)

        # 随机 User-Agent
        request_headers["User-Agent"] = self._get_random_user_agent()

        # 准备请求参数
        request_kwargs = {
            "params": params,
            "headers": request_headers,
            "timeout": timeout or Config.REQUEST_TIMEOUT,
        }

        # 添加代理
        if self.proxy:
            request_kwargs["proxies"] = {
                "http": self.proxy,
                "https": self.proxy,
            }

        try:
            response = self.session.get(url, **request_kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            raise requests.RequestException(f"请求失败: {url}, 错误: {e}")

    def fetch_trending_page(self, language: str = "",
                           period: str = "daily") -> str:
        """
        获取 Trending 页面 HTML

        Args:
            language: 编程语言筛选
            period: 时间周期 (daily/weekly/monthly)

        Returns:
            页面 HTML 内容

        Raises:
            requests.RequestException: 请求失败
        """
        url = Config.GITHUB_TRENDING_URL

        params = {}
        if language:
            params["language"] = language
        if period != "daily":
            params["since"] = period

        response = self.get(url, params=params)
        return response.text

    def fetch_raw_readme(self, owner: str, repo: str,
                        default_branch: str = "main") -> Optional[str]:
        """
        获取原始 README 内容

        Args:
            owner: 仓库所有者
            repo: 仓库名称
            default_branch: 默认分支

        Returns:
            README 内容，如果获取失败返回 None
        """
        # 尝试多个可能的 README 文件名
        readme_names = [
            "README.md",
            "readme.md",
            "README.MD",
            "README.rst",
            "README.txt",
            "README",
        ]

        for branch in ["main", "master"]:
            for readme_name in readme_names:
                url = f"{Config.GITHUB_BASE_URL}/{owner}/{repo}/raw/{branch}/{readme_name}"

                try:
                    response = self.get(url, timeout=15)
                    if response.status_code == 200:
                        return response.text
                except requests.RequestException:
                    continue

        return None

    def fetch_readme_via_api(self, owner: str, repo: str) -> Optional[str]:
        """
        通过 GitHub API 获取 README

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README 内容（Base64 解码后），如果获取失败返回 None
        """
        import base64

        url = f"{Config.GITHUB_API_BASE}/repos/{owner}/{repo}/readme"

        try:
            response = self.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", "")
                # GitHub API 返回的是 Base64 编码的内容
                decoded = base64.b64decode(content).decode("utf-8", errors="ignore")
                return decoded
        except requests.RequestException:
            pass

        return None

    def close(self):
        """关闭 Session"""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
