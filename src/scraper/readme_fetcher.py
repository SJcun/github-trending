"""README 获取器模块"""

import re
from typing import Optional, Tuple
from urllib.parse import quote

from bs4 import BeautifulSoup

from .client import HttpClient


class ReadmeFetcher:
    """README 内容获取器"""

    def __init__(self, client: Optional[HttpClient] = None):
        """
        初始化 README 获取器

        Args:
            client: HTTP 客户端，如果为 None 则创建新的
        """
        self.client = client or HttpClient()

    def parse_repo_name(self, repo_name: str) -> Tuple[str, str]:
        """
        解析仓库名称

        Args:
            repo_name: 仓库名，格式 owner/repo

        Returns:
            (owner, repo) 元组
        """
        parts = repo_name.strip("/").split("/")
        if len(parts) >= 2:
            return parts[0], parts[1]
        raise ValueError(f"无效的仓库名: {repo_name}")

    def fetch_readme(self, repo_name: str,
                     max_length: Optional[int] = None) -> Optional[str]:
        """
        获取 README 内容

        Args:
            repo_name: 仓库名，格式 owner/repo
            max_length: 最大内容长度，超过则截断

        Returns:
            README 内容，获取失败返回 None
        """
        try:
            owner, repo = self.parse_repo_name(repo_name)
        except ValueError:
            return None

        # 方法1: 尝试获取原始 README
        content = self.client.fetch_raw_readme(owner, repo)
        if content:
            return self._clean_content(content, max_length)

        # 方法2: 尝试通过 API 获取
        content = self.client.fetch_readme_via_api(owner, repo)
        if content:
            return self._clean_content(content, max_length)

        # 方法3: 从 HTML 页面解析（最后手段）
        content = self._fetch_readme_from_html(owner, repo)
        if content:
            return self._clean_content(content, max_length)

        return None

    def _fetch_readme_from_html(self, owner: str, repo: str) -> Optional[str]:
        """
        从仓库 HTML 页面提取 README

        Args:
            owner: 仓库所有者
            repo: 仓库名称

        Returns:
            README 内容
        """
        url = f"https://github.com/{owner}/{repo}"

        try:
            response = self.client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            # GitHub README 通常在 article 元素中
            article = soup.find("article", {"class": re.compile("markdown-body|readme")})
            if article:
                # 获取纯文本
                text = article.get_text(separator="\n", strip=True)
                return self._extract_markdown_from_article(article)

        except Exception:
            pass

        return None

    def _extract_markdown_from_article(self, article) -> str:
        """
        从 article 元素提取 Markdown 格式内容

        Args:
            article: BeautifulSoup 元素

        Returns:
            提取的文本内容
        """
        # 简化处理，直接获取文本
        lines = []
        for elem in article.descendants:
            if elem.name == "p":
                text = elem.get_text(strip=True)
                if text:
                    lines.append(text)
            elif elem.name == "h1":
                text = elem.get_text(strip=True)
                if text:
                    lines.append(f"# {text}")
            elif elem.name == "h2":
                text = elem.get_text(strip=True)
                if text:
                    lines.append(f"## {text}")
            elif elem.name == "h3":
                text = elem.get_text(strip=True)
                if text:
                    lines.append(f"### {text}")
            elif elem.name == "li":
                text = elem.get_text(strip=True)
                if text:
                    lines.append(f"- {text}")
            elif elem.name == "code":
                text = elem.get_text(strip=True)
                if text and len(text) < 100:  # 跳过长代码块
                    lines.append(f"`{text}`")

        return "\n\n".join(lines) if lines else article.get_text(separator="\n", strip=True)

    def _clean_content(self, content: str,
                      max_length: Optional[int] = None) -> str:
        """
        清理 README 内容

        Args:
            content: 原始内容
            max_length: 最大长度

        Returns:
            清理后的内容
        """
        # 移除多余的空行
        content = re.sub(r"\n{3,}", "\n\n", content)

        # 移除行首尾空白
        lines = [line.strip() for line in content.split("\n")]
        content = "\n".join(lines)

        # 截断
        if max_length and len(content) > max_length:
            content = content[:max_length]
            # 尝试在最近的新行处截断
            last_newline = content.rfind("\n")
            if last_newline > max_length * 0.8:  # 至少保留 80%
                content = content[:last_newline]
            content += "\n\n... (内容已截断)"

        return content.strip()

    def get_readme_metadata(self, repo_name: str) -> dict:
        """
        获取 README 元数据

        Args:
            repo_name: 仓库名

        Returns:
            元数据字典
        """
        try:
            owner, repo = self.parse_repo_name(repo_name)
            url = f"https://github.com/{owner}/{repo}"

            response = self.client.get(url)
            soup = BeautifulSoup(response.text, "html.parser")

            metadata = {
                "has_readme": False,
                "readme_type": None,
                "default_branch": "main",
            }

            # 检测是否有 README
            article = soup.find("article", {"class": re.compile("markdown-body|readme")})
            if article:
                metadata["has_readme"] = True

                # 尝试检测 README 类型
                readme_link = soup.find("a", href=re.compile(r"/blob/.*README"))
                if readme_link:
                    href = readme_link.get("href", "")
                    if "README.md" in href:
                        metadata["readme_type"] = "markdown"
                    elif "README.rst" in href:
                        metadata["readme_type"] = "rst"
                    elif "README.txt" in href:
                        metadata["readme_type"] = "text"

            # 获取默认分支
            branch_select = soup.find("summary", {"class": "select-menu-button"})
            if branch_select:
                branch_text = branch_select.get_text(strip=True)
                if branch_text and branch_text != "Switch branches/tags":
                    metadata["default_branch"] = branch_text

            return metadata

        except Exception:
            return {"has_readme": False, "readme_type": None, "default_branch": "main"}

    def close(self):
        """关闭客户端"""
        if hasattr(self.client, "close"):
            self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
