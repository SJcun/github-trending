"""HTML 解析模块"""

import re
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bs4 import Tag

from ..models import Repository
from ..config import Config


class TrendingParser:
    """Trending 页面解析器"""

    def __init__(self, html: str, period: str = "daily"):
        """
        初始化解析器

        Args:
            html: Trending 页面 HTML 内容
            period: 时间周期
        """
        self.soup = BeautifulSoup(html, "html.parser")
        self.period = period

    def parse(self) -> List[Repository]:
        """
        解析 Trending 页面

        Returns:
            仓库列表
        """
        repositories = []

        # GitHub Trending 页面结构：每个仓库在一个 article 元素中
        # 查找所有仓库条目
        repo_articles = self._find_repo_articles()

        for article in repo_articles:
            try:
                repo = self._parse_repo_article(article)
                if repo and repo.repo_name:
                    repositories.append(repo)
            except Exception:
                # 解析失败时跳过该仓库
                continue

        return repositories

    def _find_repo_articles(self) -> List[Tag]:
        """
        查找所有仓库文章元素

        Returns:
            BeautifulSoup Tag 列表
        """
        # GitHub 的 DOM 结构可能变化，尝试多种选择器
        selectors = [
            "article.Box-row",
            "article[data-test-id='repo-row']",
            "div.Box-row",
            "li.js-repo-list-item",  # 旧版结构
        ]

        for selector in selectors:
            articles = self.soup.select(selector)
            if articles:
                return articles

        # 如果以上都找不到，尝试根据 class 模式查找
        return self.soup.find_all("article", class_=re.compile(r"Box|repo"))

    def _parse_repo_article(self, article: Tag) -> Optional[Repository]:
        """
        解析单个仓库文章元素

        Args:
            article: BeautifulSoup 元素

        Returns:
            Repository 对象
        """
        # 获取仓库名和链接
        repo_name, repo_url = self._extract_repo_name(article)

        if not repo_name:
            return None

        # 获取描述
        description = self._extract_description(article)

        # 获取编程语言
        language, language_color = self._extract_language(article)

        # 获取星标数据
        stars, forks, today_stars = self._extract_stats(article)

        # 获取贡献者
        contributors = self._extract_contributors(article)

        return Repository(
            repo_name=repo_name,
            description=description,
            language=language,
            stars=stars,
            forks=forks,
            today_stars=today_stars,
            contributors=contributors,
            period=self.period,
            url=repo_url or f"{Config.GITHUB_BASE_URL}/{repo_name}",
        )

    def _extract_repo_name(self, article: Tag) -> tuple[str, str]:
        """
        提取仓库名和 URL

        Args:
            article: BeautifulSoup 元素

        Returns:
            (仓库名, URL) 元组
        """
        # 查找仓库名链接
        link_selectors = [
            "h2 a[href]",
            "h1 a[href]",
            "a[href^='/']",
        ]

        for selector in link_selectors:
            link = article.select_one(selector)
            if link:
                href = link.get("href", "")
                # 移除开头的 / 和可能的尾部斜杠
                repo_path = href.strip("/ ").split("/")[0:2]
                if len(repo_path) == 2:
                    repo_name = f"{repo_path[0]}/{repo_path[1]}"
                    repo_url = urljoin(Config.GITHUB_BASE_URL, href)
                    return repo_name, repo_url

        return "", ""

    def _extract_description(self, article: Tag) -> str:
        """
        提取项目描述

        Args:
            article: BeautifulSoup 元素

        Returns:
            描述文本
        """
        selectors = [
            "p.col-9",               # 2024年新结构
            "p.color-fg-muted",      # 备用选择器
            "p.ws-normal",           # 旧结构（兼容）
            "div[dir='auto']",
            "p[colored-text]",
        ]

        for selector in selectors:
            elem = article.select_one(selector)
            if elem:
                text = elem.get_text(strip=True)
                # 过滤掉可能是统计数据的短文本
                if text and len(text) > 10:
                    return text

        return ""

    def _extract_language(self, article: Tag) -> tuple[str, Optional[str]]:
        """
        提取编程语言和颜色

        Args:
            article: BeautifulSoup 元素

        Returns:
            (语言名, 颜色) 元组
        """
        # 查找语言信息
        language_span = article.find("span", itemprop="programmingLanguage")
        if language_span:
            language = language_span.get_text(strip=True)
            # 获取语言颜色（如果有）
            color_elem = language_span.find_previous("span", class_=re.compile(r"color-fg"))
            color = color_elem.get("style", "").replace("color:", "").strip() if color_elem else None
            return language, color

        # 尝试其他选择器
        fallback_selectors = [
            "span[itemprop='programmingLanguage']",
            "div[d-flex] > span:nth-child(2)",
        ]

        for selector in fallback_selectors:
            elem = article.select_one(selector)
            if elem:
                return elem.get_text(strip=True), None

        return "", None

    def _extract_stats(self, article: Tag) -> tuple[int, int, int]:
        """
        提取统计数据（星标、Fork、今日星标）

        Args:
            article: BeautifulSoup 元素

        Returns:
            (stars, forks, today_stars) 元组
        """
        stars = 0
        forks = 0
        today_stars = 0

        # 查找所有链接元素，统计数据通常在链接中
        links = article.find_all("a", href=re.compile(r"/stargazers|/forks|/graphs"))

        for link in links:
            href = link.get("href", "")
            text = link.get_text(strip=True)

            # 清理数字（移除逗号、k 等）
            num = self._parse_number(text)

            if "/stargazers" in href:
                stars = num
            elif "/forks" in href:
                forks = num

        # 查找今日星标（通常在特定元素中）
        today_elem = article.find("span", class_=re.compile(r"d-inline|float-sm-right"))
        if today_elem:
            text = today_elem.get_text(strip=True)
            # 匹配 "stars today" 或 "星标 today" 等模式
            today_match = re.search(r"([\d,]+)\s*stars?\s*today", text, re.IGNORECASE)
            if today_match:
                today_stars = self._parse_number(today_match.group(1))

        return stars, forks, today_stars

    def _parse_number(self, text: str) -> int:
        """
        解析数字字符串

        Args:
            text: 数字文本，如 "1.5k", "1,234"

        Returns:
            整数
        """
        text = text.strip().replace(",", "")

        # 处理 k 后缀
        k_match = re.match(r"([\d.]+)k", text, re.IGNORECASE)
        if k_match:
            return int(float(k_match.group(1)) * 1000)

        # 直接转换
        try:
            return int(text)
        except ValueError:
            return 0

    def _extract_contributors(self, article: Tag) -> List[str]:
        """
        提取贡献者头像 URL

        Args:
            article: BeautifulSoup 元素

        Returns:
            头像 URL 列表
        """
        contributors = []

        # 查找贡献者头像
        avatars = article.find_all("a", href=re.compile(r"/users/"))
        for avatar in avatars:
            img = avatar.find("img")
            if img:
                src = img.get("src", "")
                # 过滤掉非头像链接
                if "avatar" in src or "u/" in src:
                    # 移除尺寸参数以获取原始图片
                    src = re.sub(r"\?s=\d+", "", src)
                    contributors.append(src)

        return contributors[:5]  # 限制最多 5 个

    def has_next_page(self) -> bool:
        """
        检查是否有下一页

        Returns:
            是否有更多结果
        """
        # GitHub Trending 通常不分页
        return False

    def get_total_count(self) -> int:
        """
        获取总结果数

        Returns:
            结果数量
        """
        articles = self._find_repo_articles()
        return len(articles)
