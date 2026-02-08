"""可视化图表生成模块"""

from typing import List, Dict, Any, Optional
from pathlib import Path

from ..models import RepositoryWithAI, AnalysisSummary


class Visualizer:
    """图表可视化生成器"""

    def __init__(self, output_dir: Optional[Path] = None):
        """
        初始化可视化器

        Args:
            output_dir: 输出目录
        """
        from ..config import Config
        self.output_dir = output_dir or Config.OUTPUT_DIR
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate_language_chart(self, repos: List[RepositoryWithAI],
                               output_file: Optional[str] = None) -> Path:
        """
        生成语言分布饼图

        Args:
            repos: 仓库列表
            output_file: 输出文件名

        Returns:
            输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.font_manager import FontProperties
        except ImportError:
            raise ImportError("请安装 matplotlib: pip install matplotlib")

        # 统计语言分布
        lang_counts = {}
        for repo in repos:
            lang = repo.language or "未知"
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        # 按数量排序，取前10
        sorted_langs = sorted(lang_counts.items(),
                             key=lambda x: x[1], reverse=True)[:10]

        # 中文显示支持
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass

        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))

        languages = [lang for lang, _ in sorted_langs]
        counts = [count for _, count in sorted_langs]

        colors = plt.cm.Set3(range(len(languages)))
        wedges, texts, autotexts = ax.pie(
            counts,
            labels=languages,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90,
        )

        # 设置字体大小
        for text in texts:
            text.set_fontsize(10)
        for autotext in autotexts:
            autotext.set_fontsize(9)
            autotext.set_color('white')

        ax.set_title('GitHub Trending - 编程语言分布', fontsize=14, pad=20)

        # 保存
        if not output_file:
            output_file = "language_distribution.png"
        filepath = self.output_dir / output_file
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_score_chart(self, repos: List[RepositoryWithAI],
                            output_file: Optional[str] = None) -> Path:
        """
        生成评分分布柱状图

        Args:
            repos: 仓库列表
            output_file: 输出文件名

        Returns:
            输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("请安装 matplotlib: pip install matplotlib")

        # 筛选有 AI 分析的仓库
        analyzed_repos = [r for r in repos if r.has_ai_analysis]

        if not analyzed_repos:
            raise ValueError("没有可用的 AI 分析数据")

        # 按评分分组
        score_ranges = {
            "9-10分": 0,
            "7-8分": 0,
            "5-6分": 0,
            "3-4分": 0,
            "1-2分": 0,
        }

        for repo in analyzed_repos:
            score = repo.ai_analysis.score
            if score >= 9:
                score_ranges["9-10分"] += 1
            elif score >= 7:
                score_ranges["7-8分"] += 1
            elif score >= 5:
                score_ranges["5-6分"] += 1
            elif score >= 3:
                score_ranges["3-4分"] += 1
            else:
                score_ranges["1-2分"] += 1

        # 中文显示支持
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass

        # 创建图表
        fig, ax = plt.subplots(figsize=(10, 6))

        ranges = list(score_ranges.keys())
        counts = list(score_ranges.values())

        colors = ['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#95a5a6']

        bars = ax.bar(ranges, counts, color=colors)

        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{int(height)}',
                       ha='center', va='bottom', fontsize=11)

        ax.set_xlabel('评分区间', fontsize=12)
        ax.set_ylabel('项目数量', fontsize=12)
        ax.set_title('GitHub Trending - AI 评分分布', fontsize=14, pad=20)
        ax.set_ylim(0, max(counts) * 1.2 if max(counts) > 0 else 1)

        # 网格
        ax.yaxis.grid(True, linestyle='--', alpha=0.3)
        ax.set_axisbelow(True)

        # 保存
        if not output_file:
            output_file = "score_distribution.png"
        filepath = self.output_dir / output_file
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_tech_stack_chart(self, repos: List[RepositoryWithAI],
                                  output_file: Optional[str] = None) -> Path:
        """
        生成技术栈词云或柱状图

        Args:
            repos: 仓库列表
            output_file: 输出文件名

        Returns:
            输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            raise ImportError("请安装 matplotlib: pip install matplotlib")

        # 统计技术栈
        tech_counts = {}
        for repo in repos:
            if repo.has_ai_analysis and repo.ai_analysis.tech_stack:
                for tech in repo.ai_analysis.tech_stack:
                    tech_counts[tech] = tech_counts.get(tech, 0) + 1

        if not tech_counts:
            raise ValueError("没有可用的技术栈数据")

        # 排序取前15
        sorted_techs = sorted(tech_counts.items(),
                            key=lambda x: x[1], reverse=True)[:15]

        # 中文显示支持
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass

        # 创建水平柱状图
        fig, ax = plt.subplots(figsize=(12, 8))

        techs = [tech for tech, _ in sorted_techs]
        counts = [count for _, count in sorted_techs]

        y_pos = range(len(techs))
        colors = plt.cm.viridis(range(len(techs)))

        bars = ax.barh(y_pos, counts, color=colors)

        # 添加数值标签
        for i, (bar, count) in enumerate(zip(bars, counts)):
            ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{count}', va='center', fontsize=10)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(techs)
        ax.invert_yaxis()
        ax.set_xlabel('出现次数', fontsize=12)
        ax.set_title('GitHub Trending - 热门技术栈 TOP 15', fontsize=14, pad=20)

        # 网格
        ax.xaxis.grid(True, linestyle='--', alpha=0.3)
        ax.set_axisbelow(True)

        plt.tight_layout()

        # 保存
        if not output_file:
            output_file = "tech_stack_distribution.png"
        filepath = self.output_dir / output_file
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        return filepath

    def generate_summary_report(self, repos: List[RepositoryWithAI],
                               summary: AnalysisSummary,
                               output_file: Optional[str] = None) -> Path:
        """
        生成综合分析报告

        Args:
            repos: 仓库列表
            summary: 分析摘要
            output_file: 输出文件名

        Returns:
            输出文件路径
        """
        try:
            import matplotlib.pyplot as plt
            from matplotlib.gridspec import GridSpec
        except ImportError:
            raise ImportError("请安装 matplotlib: pip install matplotlib")

        # 中文显示支持
        try:
            plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass

        # 创建子图
        fig = plt.figure(figsize=(16, 10))
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

        # 1. 评分分布
        ax1 = fig.add_subplot(gs[0, 0])
        self._plot_score_distribution(ax1, repos)

        # 2. 学习价值分布
        ax2 = fig.add_subplot(gs[0, 1])
        self._plot_learning_value(ax2, repos)

        # 3. 语言分布
        ax3 = fig.add_subplot(gs[1, :])
        self._plot_language_distribution(ax3, repos)

        # 总标题
        fig.suptitle('GitHub Trending - AI 分析综合报告', fontsize=16, fontweight='bold')

        # 保存
        if not output_file:
            output_file = "summary_report.png"
        filepath = self.output_dir / output_file
        plt.savefig(filepath, dpi=100, bbox_inches='tight')
        plt.close()

        return filepath

    def _plot_score_distribution(self, ax, repos: List[RepositoryWithAI]):
        """绘制评分分布"""
        analyzed = [r for r in repos if r.has_ai_analysis]
        scores = [r.ai_analysis.score for r in analyzed]

        ax.hist(scores, bins=10, range=(0, 10), color='#3498db', edgecolor='white', alpha=0.7)
        ax.set_xlabel('评分', fontsize=11)
        ax.set_ylabel('项目数量', fontsize=11)
        ax.set_title('评分分布', fontsize=12, fontweight='bold')
        ax.yaxis.grid(True, linestyle='--', alpha=0.3)

        # 添加平均分线
        if scores:
            avg_score = sum(scores) / len(scores)
            ax.axvline(avg_score, color='#e74c3c', linestyle='--', linewidth=2,
                      label=f'平均分: {avg_score:.1f}')
            ax.legend()

    def _plot_learning_value(self, ax, repos: List[RepositoryWithAI]):
        """绘制学习价值分布"""
        analyzed = [r for r in repos if r.has_ai_analysis]

        value_counts = {"high": 0, "medium": 0, "low": 0}
        for repo in analyzed:
            value_counts[repo.ai_analysis.learning_value] += 1

        values = list(value_counts.keys())
        counts = list(value_counts.values())
        colors = ['#2ecc71', '#f39c12', '#e74c3c']

        bars = ax.bar(values, counts, color=colors)

        for bar, count in zip(bars, counts):
            if count > 0:
                ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                       f'{count}', ha='center', va='bottom', fontsize=12)

        ax.set_ylabel('项目数量', fontsize=11)
        ax.set_title('学习价值分布', fontsize=12, fontweight='bold')
        ax.yaxis.grid(True, linestyle='--', alpha=0.3)

    def _plot_language_distribution(self, ax, repos: List[RepositoryWithAI]):
        """绘制语言分布"""
        lang_counts = {}
        for repo in repos:
            lang = repo.language or "未知"
            lang_counts[lang] = lang_counts.get(lang, 0) + 1

        sorted_langs = sorted(lang_counts.items(),
                             key=lambda x: x[1], reverse=True)[:10]

        languages = [lang for lang, _ in sorted_langs]
        counts = [count for _, count in sorted_langs]

        colors = plt.cm.Set3(range(len(languages)))
        bars = ax.bar(languages, counts, color=colors)

        for bar, count in zip(bars, counts):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                   f'{count}', ha='center', va='bottom', fontsize=10)

        ax.set_xlabel('编程语言', fontsize=11)
        ax.set_ylabel('项目数量', fontsize=11)
        ax.set_title('编程语言分布 TOP 10', fontsize=12, fontweight='bold')
        ax.yaxis.grid(True, linestyle='--', alpha=0.3)
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')

    def generate_all_charts(self, repos: List[RepositoryWithAI],
                           summary: AnalysisSummary) -> List[Path]:
        """
        生成所有图表

        Args:
            repos: 仓库列表
            summary: 分析摘要

        Returns:
            生成的文件路径列表
        """
        filepaths = []

        try:
            filepaths.append(self.generate_language_chart(repos))
        except Exception as e:
            print(f"生成语言图表失败: {e}")

        try:
            filepaths.append(self.generate_score_chart(repos))
        except Exception as e:
            print(f"生成评分图表失败: {e}")

        try:
            filepaths.append(self.generate_tech_stack_chart(repos))
        except Exception as e:
            print(f"生成技术栈图表失败: {e}")

        try:
            filepaths.append(self.generate_summary_report(repos, summary))
        except Exception as e:
            print(f"生成综合报告失败: {e}")

        return filepaths
