"""Prompt 模板管理模块"""

from typing import Optional


class PromptManager:
    """Prompt 模板管理器"""

    def __init__(self):
        self._system_prompt = self._default_system_prompt()
        self._analysis_template = self._default_analysis_template()

    def _default_system_prompt(self) -> str:
        """默认系统提示"""
        return """你是一个经验丰富的技术专家，擅长分析和解读开源项目。

你的任务是阅读 GitHub 项目的 README 内容，对其进行分析和评估。

分析要求：
1. 准确理解项目的核心价值和功能
2. 识别项目使用的技术栈
3. 评估项目对开发者的学习价值
4. 给出客观的评分和判断

输出格式：必须严格按照 JSON 格式输出，不要包含任何额外的文字说明。"""

    def _default_analysis_template(self) -> str:
        """默认分析模板"""
        return """请分析以下 GitHub 项目，并按照 JSON 格式输出分析结果。

【项目信息】
- 仓库名: {repo_name}
- 描述: {description}
- 编程语言: {language}
- 星标数: {stars}
- 今日新增: {today_stars}

【README 内容】
{readme_content}

请按以下 JSON 格式输出（不要添加任何其他文字）：
{{
  "summary": "项目核心价值的一句话概括",
  "key_features": ["功能1", "功能2", "功能3"],
  "tech_stack": ["技术1", "技术2", "技术3"],
  "use_cases": ["使用场景1", "使用场景2"],
  "learning_value": "high/medium/low",
  "score": 8.5,
  "is_worthwhile": true,
  "reason": "值得/不值得深入了解的原因"
}}

评分标准：
- 9-10分: 革命性项目，强烈推荐关注
- 7-8分: 优秀项目，值得学习
- 5-6分: 有一定价值，可选择性关注
- 3-4分: 普通项目，价值有限
- 1-2分: 不推荐关注"""

    def build_analysis_prompt(self, repo_name: str, description: str,
                             language: str, stars: int, today_stars: int,
                             readme_content: str,
                             max_length: int = 15000) -> str:
        """
        构建分析 Prompt

        Args:
            repo_name: 仓库名
            description: 项目描述
            language: 编程语言
            stars: 星标数
            today_stars: 今日星标
            readme_content: README 内容
            max_length: 内容最大长度

        Returns:
            完整的 Prompt
        """
        # 截断过长的 README
        if len(readme_content) > max_length:
            readme_content = readme_content[:max_length] + "\n\n... (内容已截断)"

        return self._analysis_template.format(
            repo_name=repo_name,
            description=description or "无描述",
            language=language or "未知",
            stars=stars,
            today_stars=today_stars,
            readme_content=readme_content or "无 README 内容"
        )

    def build_batch_analysis_prompt(self, repos: list) -> str:
        """
        构建批量分析 Prompt

        Args:
            repos: 仓库信息列表

        Returns:
            批量分析的 Prompt
        """
        repos_text = ""
        for i, repo in enumerate(repos, 1):
            repos_text += f"\n【项目 {i}】\n"
            repos_text += f"- 仓库名: {repo.get('repo_name', '')}\n"
            repos_text += f"- 描述: {repo.get('description', '')}\n"
            repos_text += f"- 语言: {repo.get('language', '')}\n"
            repos_text += f"- 星标: {repo.get('stars', 0)}\n"
            readme = repo.get('readme', '')[:1000]
            if readme:
                repos_text += f"- README: {readme}...\n"

        return f"""请批量分析以下 {len(repos)} 个 GitHub 项目，对每个项目给出简洁的评价。

{repos_text}

请按以下 JSON 格式输出：
{{
  "analyses": [
    {{
      "repo_name": "项目1仓库名",
      "summary": "一句话概括",
      "is_worthwhile": true
    }},
    ...
  ]
}}"""

    def get_system_prompt(self) -> str:
        """获取系统提示"""
        return self._system_prompt

    def set_system_prompt(self, prompt: str):
        """设置系统提示"""
        self._system_prompt = prompt

    def set_analysis_template(self, template: str):
        """设置分析模板"""
        self._analysis_template = template

    @staticmethod
    def create_brief_prompt(repo_name: str, description: str,
                           language: str) -> str:
        """
        创建简短分析 Prompt（快速模式）

        Args:
            repo_name: 仓库名
            description: 项目描述
            language: 编程语言

        Returns:
            简短 Prompt
        """
        return f"""请简要分析以下 GitHub 项目：

仓库名: {repo_name}
描述: {description}
语言: {language}

请用一句话概括该项目的主要价值。"""

    @staticmethod
    def create_comparison_prompt(repo1: dict, repo2: dict) -> str:
        """
        创建对比分析 Prompt

        Args:
            repo1: 项目1信息
            repo2: 项目2信息

        Returns:
            对比分析 Prompt
        """
        return f"""请对比分析以下两个 GitHub 项目：

【项目 A】
- 仓库名: {repo1.get('repo_name', '')}
- 描述: {repo1.get('description', '')}
- 星标: {repo1.get('stars', 0)}

【项目 B】
- 仓库名: {repo2.get('repo_name', '')}
- 描述: {repo2.get('description', '')}
- 星标: {repo2.get('stars', 0)}

请分析：
1. 两个项目的定位差异
2. 各自的优势和特点
3. 对于不同场景的推荐建议

请以 JSON 格式输出：
{{
  "positioning_diff": "定位差异描述",
  "a_advantages": ["A的优势1", "A的优势2"],
  "b_advantages": ["B的优势1", "B的优势2"],
  "recommendation": "场景建议"
}}"""
