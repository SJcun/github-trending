# -*- coding: utf-8 -*-
"""命令行接口模块"""

import sys
import os
import click
from pathlib import Path
from typing import Optional

# Windows 编码处理
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config, AIModelConfig
from src.models import Repository, RepositoryWithAI, TrendingResult, AnalysisSummary
from src.scraper import HttpClient, TrendingParser, RateLimiter, ReadmeFetcher
from src.ai import AIClient, AICache
from src.storage import Database, FileCache
from src.output import OutputFormatter, Visualizer


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GitHub Trending - 解读 GitHub Trending 界面"""
    pass


@cli.command()
@click.option("-l", "--language", default="", help="筛选编程语言")
@click.option("-s", "--since", type=click.Choice(["daily", "weekly", "monthly"]),
              default="daily", help="时间周期")
@click.option("-n", "--limit", default=25, help="返回数量限制")
@click.option("-o", "--output", type=click.Choice(["table", "json", "markdown", "csv"]),
              default="table", help="输出格式")
@click.option("--save", is_flag=True, help="保存到数据库")
@click.option("--ai/--no-ai", default=False, help="是否启用 AI 分析")
@click.option("--ai-model", type=click.Choice(["claude", "openai", "deepseek", "ollama"], case_sensitive=False),
              default=None, help="使用的 AI 模型")
@click.option("--ai-cache/--no-ai-cache", default=True, help="是否使用 AI 缓存")
@click.option("--ai-force", is_flag=True, help="强制重新分析，忽略缓存")
@click.option("--detail-level", type=click.Choice(["brief", "standard", "deep"]),
              default="standard", help="分析深度")
@click.option("--visualize", is_flag=True, help="生成可视化图表")
@click.option("--proxy", default="", help="代理地址")
def trending(language: str, since: str, limit: int, output: str,
            save: bool, ai: bool, ai_model: str, ai_cache: bool,
            ai_force: bool, detail_level: str, visualize: bool, proxy: str):
    """获取 GitHub Trending 列表"""
    # 初始化组件
    formatter = OutputFormatter(use_color=True)
    limiter = RateLimiter()

    try:
        # 显示加载提示
        click.echo(f"🔍 正在获取 {language or '全部'} 语言的 {since} Trending...", nl=False)

        # 获取 Trending 数据
        with HttpClient(proxy=proxy or None) as client:
            limiter.wait()
            html = client.fetch_trending_page(language, since)
            parser = TrendingParser(html, since)
            repositories = parser.parse()

        # 限制数量
        repositories = repositories[:limit]

        click.echo(f"\r✅ 找到 {len(repositories)} 个仓库", nl=True)

        if not repositories:
            click.echo(click.style("没有找到任何仓库", fg="yellow"))
            return

        # AI 分析
        repos_with_ai = []
        if ai:
            repos_with_ai = _run_ai_analysis(
                repositories, ai_model, ai_cache, ai_force,
                detail_level, proxy, formatter, limiter
            )
        else:
            repos_with_ai = [RepositoryWithAI(**repo.model_dump()) for repo in repositories]

        # 保存到数据库
        if save:
            db = Database()
            result = TrendingResult(
                repositories=[Repository(**repo.model_dump()) for repo in repos_with_ai],
                period=since,
                language=language,
            )
            db.save_trending_snapshot(result)
            click.echo(f"💾 已保存到数据库: {Config.DB_PATH}")

        # 生成可视化图表
        if visualize and ai:
            try:
                viz = Visualizer()
                summary = AnalysisSummary()
                summary.calculate_from_repositories(repos_with_ai)
                filepaths = viz.generate_all_charts(repos_with_ai, summary)
                click.echo(f"📊 图表已保存到:")
                for filepath in filepaths:
                    click.echo(f"   {filepath}")
            except Exception as e:
                click.echo(click.style(f"⚠️  图表生成失败: {e}", fg="yellow"))

        # 输出结果
        _output_results(repos_with_ai, output, formatter, ai, language, since)

    except Exception as e:
        import traceback
        click.echo(click.style(f"\n错误: {e}", fg="red"), err=True)
        click.echo(traceback.format_exc(), err=True)
        sys.exit(1)


def _run_ai_analysis(repositories, ai_model, ai_cache, ai_force,
                    detail_level, proxy, formatter, limiter):
    """运行 AI 分析"""
    # 初始化 AI 客户端
    ai_client = AIClient(ai_model) if ai_model else AIClient()

    if not ai_client.is_available():
        click.echo(click.style("\n⚠️  AI 客户端不可用，请检查 API Key 配置", fg="yellow"))
        click.echo("提示: 使用 --ai-model 指定模型，或设置环境变量")
        return [RepositoryWithAI(**repo.model_dump()) for repo in repositories]

    click.echo(f"🤖 使用 AI 模型: {ai_client.get_model_name()}")

    # 初始化缓存和 README 获取器
    cache = AICache() if ai_cache else None
    if proxy:
        http_client = HttpClient(proxy=proxy)
        readme_fetcher = ReadmeFetcher(http_client)
    else:
        readme_fetcher = ReadmeFetcher()
    ai_config = AIModelConfig()

    repos_with_ai = []
    max_length = {
        "brief": 2000,
        "standard": 8000,
        "deep": 20000,
    }.get(detail_level, 8000)

    for i, repo in enumerate(repositories, 1):
        repo_name = repo.repo_name

        # 检查缓存
        readme = ""
        if cache and not ai_force:
            cached_analysis = cache.get(repo_name, "")
            if cached_analysis and cached_analysis.analysis_status == "completed":
                click.echo(f"\r  [{i}/{len(repositories)}] {repo_name} (缓存) ", nl=False)
                repos_with_ai.append(RepositoryWithAI(**repo.model_dump(), ai_analysis=cached_analysis))
                continue

        # 获取 README
        click.echo(f"\r  [{i}/{len(repositories)}] {repo_name} 正在分析... ", nl=False)

        try:
            limiter.wait()
            readme = readme_fetcher.fetch_readme(repo_name, max_length=max_length)

            # AI 分析
            limiter.wait()
            analysis = ai_client.analyze_repository(
                repo_name=repo_name,
                description=repo.description,
                language=repo.language,
                stars=repo.stars,
                today_stars=repo.today_stars,
                readme_content=readme or "无 README 内容",
            )

            # 保存缓存
            if cache:
                cache.set(repo_name, readme, analysis)

            repos_with_ai.append(RepositoryWithAI(**repo.model_dump(), ai_analysis=analysis))

        except Exception as e:
            click.echo(click.style(f"\n  分析失败: {e}", fg="red"))
            repos_with_ai.append(RepositoryWithAI(**repo.model_dump()))

    click.echo("")  # 换行
    return repos_with_ai


def _output_results(repos, output_format, formatter, with_ai, language, period):
    """输出结果"""
    if output_format == "table":
        result = formatter.format_table(repos, show_ai=with_ai)
        formatter.print(result)

    elif output_format == "json":
        result = formatter.format_json(repos)
        formatter.print(result)

    elif output_format == "markdown":
        title = f"GitHub Trending - {language or '全部语言'} ({period})"
        result = formatter.format_markdown(repos, title=title)

        output_file = Config.OUTPUT_DIR / f"trending_{language}_{period}.md"
        formatter.save_to_file(result, output_file)
        click.echo(f"📄 Markdown 已保存到: {output_file}")

    elif output_format == "csv":
        result = formatter.format_csv([Repository(**repo.model_dump()) for repo in repos])

        output_file = Config.OUTPUT_DIR / f"trending_{language}_{period}.csv"
        formatter.save_to_file(result, output_file)
        click.echo(f"📄 CSV 已保存到: {output_file}")


@cli.command()
@click.argument("repo_name")
@click.option("--ai/--no-ai", default=True, help="是否启用 AI 分析")
@click.option("--ai-model", type=click.Choice(["claude", "openai", "deepseek", "ollama"], case_sensitive=False),
              default=None, help="使用的 AI 模型")
@click.option("--output", type=click.Choice(["table", "json"]),
              default="table", help="输出格式")
def repo(repo_name: str, ai: bool, ai_model: str, output: str):
    """查看单个仓库详情"""
    formatter = OutputFormatter(use_color=True)

    try:
        # 获取仓库信息
        with HttpClient() as client:
            limiter = RateLimiter()

            click.echo(f"🔍 正在获取仓库 {repo_name} 的信息...", nl=False)

            limiter.wait()

            # 获取 README
            readme_fetcher = ReadmeFetcher(client)
            readme = readme_fetcher.fetch_readme(repo_name)

            # 获取基础信息（从 Trending 页面或 API）
            metadata = readme_fetcher.get_readme_metadata(repo_name)

            click.echo(f"\r✅ 获取成功", nl=True)

            # 构建仓库对象
            from models import Repository
            repo = Repository(
                repo_name=repo_name,
                description="",  # 需要从其他地方获取
                language="",
                url=f"https://github.com/{repo_name}",
            )

            # AI 分析
            if ai:
                ai_client = AIClient(ai_model) if ai_model else AIClient()

                if ai_client.is_available() and readme:
                    click.echo("🤖 正在分析...")

                    analysis = ai_client.analyze_repository(
                        repo_name=repo_name,
                        description="",
                        language="",
                        stars=0,
                        today_stars=0,
                        readme_content=readme,
                    )

                    repo_with_ai = RepositoryWithAI(**repo.model_dump(), ai_analysis=analysis)

                    if output == "table":
                        formatter.print(formatter.format_detailed(repo_with_ai))
                    else:
                        formatter.print(formatter.format_json([repo_with_ai]))
                    return

            # 无 AI 分析
            if output == "table":
                formatter.print(f"URL: {repo.url}\nREADME 长度: {len(readme) if readme else 0} 字符")
                if readme:
                    formatter.print("\nREADME 内容:")
                    formatter.print(readme[:1000] + "..." if len(readme) > 1000 else readme)

    except Exception as e:
        click.echo(click.style(f"❌ 错误: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--limit", default=50, help="返回数量")
@click.option("--min-score", default=7.0, help="最低评分")
def high_score(limit: int, min_score: float):
    """查看高评分项目"""
    formatter = OutputFormatter(use_color=True)
    db = Database()

    try:
        results = db.get_high_score_repos(min_score=min_score, limit=limit)

        if not results:
            click.echo(click.style("没有找到符合条件的仓库", fg="yellow"))
            return

        click.echo(f"🏆 评分 >= {min_score} 的 TOP {len(results)} 项目:\n")

        for i, item in enumerate(results, 1):
            score_color = "green" if item["score"] >= 8 else "yellow"
            score_str = f"{item['score']:.1f}"
            click.echo(f"{i} {click.style(item['repo_name'], fg='blue')}")
            click.echo(f"   评分: {click.style(score_str, fg=score_color)}/10")
            click.echo(f"   简介: {item['summary']}")
            if item["tech_stack"]:
                tech_str = ', '.join(item['tech_stack'][:5])
                click.echo(f"   技术栈: {tech_str}")
            click.echo()

    except Exception as e:
        click.echo(click.style(f"❌ 错误: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def stats():
    """显示数据库统计信息"""
    formatter = OutputFormatter(use_color=True)

    try:
        db = Database()
        stats = db.get_stats()

        click.echo(click.style("📊 数据库统计", fg="cyan", bold=True))
        click.echo()
        click.echo(f"  仓库总数: {stats['total_repositories']}")
        click.echo(f"  语言数量: {stats['total_languages']}")
        click.echo()
        click.echo(f"  AI 分析总数: {stats['total_analyses']}")
        click.echo(f"  平均评分: {stats['average_score']}/10")
        click.echo(f"  高价值推荐: {stats['worthwhile_count']}")
        click.echo()
        click.echo(f"  快照总数: {stats['total_snapshots']}")
        click.echo(f"  数据库大小: {stats['db_size_mb']} MB")

    except Exception as e:
        click.echo(click.style(f"❌ 错误: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--days", default=30, help="保留天数")
def cleanup(days: int):
    """清理旧数据"""
    formatter = OutputFormatter(use_color=True)

    try:
        db = Database()
        db.clear_old_data(days=days)
        click.echo(click.style(f"✅ 已清理 {days} 天前的数据", fg="green"))

    except Exception as e:
        click.echo(click.style(f"❌ 错误: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
@click.option("--all", "clear_all", is_flag=True, help="清空所有缓存")
def cache_clear(clear_all: bool):
    """清理缓存"""
    formatter = OutputFormatter(use_color=True)

    try:
        from ai import AICache
        from storage import FileCache

        if clear_all:
            ai_cache = AICache()
            ai_cache.clear_all()

            file_cache = FileCache()
            file_cache.clear_all()

            click.echo(click.style("✅ 已清空所有缓存", fg="green"))
        else:
            ai_cache = AICache()
            ai_cache.clear_expired()

            click.echo(click.style("✅ 已清理过期缓存", fg="green"))

    except Exception as e:
        click.echo(click.style(f"❌ 错误: {e}", fg="red"), err=True)
        sys.exit(1)


@cli.command()
def languages():
    """显示支持的编程语言列表"""
    formatter = OutputFormatter(use_color=True)

    click.echo(click.style("📚 支持的编程语言", fg="cyan", bold=True))
    click.echo()

    languages = Config.POPULAR_LANGUAGES
    for i, lang in enumerate(languages, 1):
        click.echo(f"  {lang}", nl=False)
        if i % 5 == 0:
            click.echo()
        else:
            click.echo("  ", nl=False)

    if len(languages) % 5 != 0:
        click.echo()

    click.echo()
    click.echo("提示: 使用 --language 参数指定语言，如:")
    click.echo("  github-trending trending --language python")


if __name__ == "__main__":
    cli()
