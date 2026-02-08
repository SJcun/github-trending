"""输出格式化模块"""

import json
import csv
from pathlib import Path
from typing import List, Optional, TextIO
from datetime import datetime

from ..models import Repository, RepositoryWithAI, AnalysisSummary


class OutputFormatter:
    """输出格式化器"""

    def __init__(self, use_color: bool = True):
        """
        初始化格式化器

        Args:
            use_color: 是否使用颜色
        """
        self.use_color = use_color

        # ANSI 颜色代码
        self.colors = {
            "reset": "\033[0m",
            "bold": "\033[1m",
            "dim": "\033[2m",
            "red": "\033[31m",
            "green": "\033[32m",
            "yellow": "\033[33m",
            "blue": "\033[34m",
            "magenta": "\033[35m",
            "cyan": "\033[36m",
            "white": "\033[37m",
        }

    def _colorize(self, text: str, color: str) -> str:
        """给文本添加颜色"""
        if not self.use_color:
            return text
        return f"{self.colors.get(color, '')}{text}{self.colors['reset']}"

    def format_table(self, repos: List[RepositoryWithAI],
                    show_ai: bool = False,
                    limit: Optional[int] = None) -> str:
        """
        格式化为表格输出

        Args:
            repos: 仓库列表
            show_ai: 是否显示 AI 分析
            limit: 限制显示数量

        Returns:
            格式化的表格字符串
        """
        if limit:
            repos = repos[:limit]

        if not repos:
            return self._colorize("没有找到任何仓库", "yellow")

        lines = []

        # 表头
        header = self._format_header(show_ai)
        lines.append(header)
        lines.append(self._separator(header))

        # 仓库列表
        for i, repo in enumerate(repos, 1):
            lines.append(self._format_repo_row(repo, i, show_ai))

        # AI 分析摘要
        if show_ai:
            lines.append("")
            summary = AnalysisSummary()
            summary.calculate_from_repositories(repos)
            lines.append(self._format_summary(summary))

        return "\n".join(lines)

    def _format_header(self, show_ai: bool) -> str:
        """格式化表头"""
        if show_ai:
            return (f" {'#':<3} | {'仓库名':<35} | {'⭐ 星标':<10} | "
                   f"{'评分':<6} | {'学习价值':<12} | {'简介'}")
        else:
            return (f" {'#':<3} | {'仓库名':<45} | {'描述':<40} | "
                   f"{'语言':<12} | {'⭐ 星标'}")

    def _separator(self, header: str) -> str:
        """生成分隔线"""
        return "─" * len(header)

    def _format_repo_row(self, repo: RepositoryWithAI,
                        index: int, show_ai: bool) -> str:
        """格式化单个仓库行"""
        repo_name = repo.repo_name[:40]

        if show_ai and repo.has_ai_analysis:
            # AI 增强显示
            stars = f"{repo.stars:,}"
            if repo.today_stars > 0:
                stars += f" (+{repo.today_stars})"

            score = repo.display_score
            learning = repo.display_learning_value
            summary = (repo.ai_analysis.summary[:50] + "..."
                      if len(repo.ai_analysis.summary) > 50
                      else repo.ai_analysis.summary)

            # 根据评分设置颜色
            score_color = "green" if repo.ai_analysis.score >= 7 else "yellow"

            return (f" {index:<3} | {repo_name:<35} | {stars:<10} | "
                   f"{self._colorize(score, score_color):<6} | {learning:<12} | {summary}")

        else:
            # 基础显示
            desc = repo.description[:35] + "..." if len(repo.description) > 35 else repo.description
            lang = repo.language[:10]
            stars = f"{repo.stars:,}"
            if repo.today_stars > 0:
                stars += f" ↑{repo.today_stars}"

            return (f" {index:<3} | {repo_name:<45} | {desc:<40} | {lang:<12} | {stars}")

    def _format_summary(self, summary: AnalysisSummary) -> str:
        """格式化分析摘要"""
        lines = [
            self._colorize("📊 AI 分析摘要", "cyan"),
            f"  分析项目数: {summary.total_analyzed}",
            f"  高价值推荐: {self._colorize(str(summary.worthwhile_count), 'green')} "
            f"({summary.worthwhile_rate:.1%})",
            f"  平均评分: {self._colorize(f'{summary.avg_score:.1f}', 'yellow')}/10",
            f"  使用模型: {summary.model_used}",
        ]

        if summary.tech_stack_summary:
            lines.append("")
            lines.append("  热门技术栈:")
            for tech, count in list(summary.tech_stack_summary.items())[:5]:
                lines.append(f"    • {tech}: {count}")

        return "\n".join(lines)

    def format_detailed(self, repo: RepositoryWithAI) -> str:
        """
        格式化为详细视图

        Args:
            repo: 仓库对象

        Returns:
            详细视图字符串
        """
        lines = []

        # 标题
        title = f"📦 {repo.repo_name}"
        lines.append(self._colorize(title, "bold"))
        lines.append(self._separator(title))
        lines.append("")

        # 基础信息
        lines.append(f"URL: {repo.url}")
        lines.append(f"语言: {repo.language}")
        lines.append(f"星标: {repo.stars:,} ({repo.today_stars} 今日新增)")
        lines.append(f"Fork: {repo.forks:,}")
        lines.append("")

        # 描述
        if repo.description:
            lines.append(self._colorize("📝 描述", "cyan"))
            lines.append(repo.description)
            lines.append("")

        # AI 分析
        if repo.has_ai_analysis:
            ai = repo.ai_analysis
            lines.append(self._colorize("🤖 AI 分析", "cyan"))
            lines.append(f"  核心价值: {ai.summary}")
            lines.append("")

            if ai.key_features:
                lines.append("  核心功能:")
                for feature in ai.key_features:
                    lines.append(f"    • {feature}")
                lines.append("")

            if ai.tech_stack:
                lines.append(f"  技术栈: {', '.join(ai.tech_stack)}")
                lines.append("")

            if ai.use_cases:
                lines.append("  使用场景:")
                for case in ai.use_cases:
                    lines.append(f"    • {case}")
                lines.append("")

            # 评分
            score_color = "green" if ai.score >= 7 else "yellow" if ai.score >= 5 else "red"
            lines.append(f"  评分: {self._colorize(str(ai.score), score_color)}/10")
            lines.append(f"  学习价值: {repo.display_learning_value}")
            lines.append(f"  评价: {ai.reason}")

        return "\n".join(lines)

    def format_json(self, repos: List[Repository],
                   pretty: bool = True) -> str:
        """
        格式化为 JSON

        Args:
            repos: 仓库列表
            pretty: 是否美化输出

        Returns:
            JSON 字符串
        """
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": len(repos),
            "repositories": [repo.model_dump() for repo in repos],
        }

        if pretty:
            return json.dumps(data, ensure_ascii=False, indent=2,
                            default=str)
        return json.dumps(data, ensure_ascii=False, default=str)

    def format_markdown(self, repos: List[RepositoryWithAI],
                       title: str = "GitHub Trending") -> str:
        """
        格式化为 Markdown

        Args:
            repos: 仓库列表
            title: 标题

        Returns:
            Markdown 字符串
        """
        lines = [
            f"# {title}",
            "",
            f"*抓取时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
            f"*项目数量: {len(repos)}*",
            "",
            "---",
            "",
        ]

        for i, repo in enumerate(repos, 1):
            lines.append(f"## {i}. {repo.repo_name}")
            lines.append("")
            lines.append(f"**⭐ {repo.stars:,}** (+{repo.today_stars} today) | "
                        f"**语言:** {repo.language}")
            lines.append("")
            lines.append(f"{repo.description}")
            lines.append("")

            if repo.has_ai_analysis:
                ai = repo.ai_analysis
                lines.append(f"**AI 评分:** {ai.score:.1f}/10 | "
                           f"**学习价值:** {ai.learning_value}")
                lines.append("")
                lines.append(f"**简介:** {ai.summary}")
                lines.append("")

                if ai.key_features:
                    lines.append("**核心功能:**")
                    for feature in ai.key_features:
                        lines.append(f"- {feature}")
                    lines.append("")

                if ai.tech_stack:
                    lines.append(f"**技术栈:** {', '.join(ai.tech_stack)}")
                    lines.append("")

            lines.append("---")
            lines.append("")

        return "\n".join(lines)

    def format_csv(self, repos: List[Repository]) -> str:
        """
        格式化为 CSV

        Args:
            repos: 仓库列表

        Returns:
            CSV 字符串
        """
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # 表头
        writer.writerow([
            "仓库名", "描述", "语言", "星标", "Fork", "今日星标", "URL"
        ])

        # 数据行
        for repo in repos:
            writer.writerow([
                repo.repo_name,
                repo.description,
                repo.language,
                repo.stars,
                repo.forks,
                repo.today_stars,
                repo.url,
            ])

        return output.getvalue()

    def save_to_file(self, content: str, filepath: Path):
        """
        保存内容到文件

        Args:
            content: 文件内容
            filepath: 文件路径
        """
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def print(self, content: str):
        """打印内容到终端"""
        print(content)
