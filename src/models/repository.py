"""仓库数据模型"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class AIAnalysis(BaseModel):
    """AI 分析结果"""

    summary: str = Field(description="项目核心价值一句话概括")
    key_features: List[str] = Field(default_factory=list, description="核心功能列表")
    tech_stack: List[str] = Field(default_factory=list, description="技术栈列表")
    use_cases: List[str] = Field(default_factory=list, description="使用场景列表")
    learning_value: str = Field(default="medium", description="学习价值评级: high/medium/low")
    score: float = Field(default=5.0, ge=0, le=10, description="综合评分 0-10")
    is_worthwhile: bool = Field(default=False, description="是否值得深入了解")
    reason: str = Field(default="", description="评价理由")

    # 元数据
    analyzed_at: Optional[datetime] = Field(default=None, description="分析时间")
    model_used: Optional[str] = Field(default=None, description="使用的模型")
    analysis_status: str = Field(default="pending", description="分析状态: pending/analyzing/completed/failed")
    error_message: Optional[str] = Field(default=None, description="错误信息")


class Repository(BaseModel):
    """GitHub 仓库基础信息"""

    # 基础信息
    repo_name: str = Field(description="仓库名，格式: owner/repo")
    description: str = Field(default="", description="项目描述")
    language: str = Field(default="", description="主要编程语言")

    # 统计数据
    stars: int = Field(default=0, description="当前星标数")
    forks: int = Field(default=0, description="Fork 数量")
    today_stars: int = Field(default=0, description="今日新增星标")

    # 其他信息
    contributors: List[str] = Field(default_factory=list, description="贡献者头像 URL 列表")
    period: str = Field(default="daily", description="时间周期: daily/weekly/monthly")

    # 元数据
    timestamp: datetime = Field(default_factory=datetime.now, description="抓取时间")
    url: str = Field(default="", description="仓库 URL")

    def __post_init__(self):
        """初始化后处理"""
        if not self.url and self.repo_name:
            self.url = f"https://github.com/{self.repo_name}"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RepositoryWithAI(Repository):
    """带 AI 分析的仓库信息"""

    ai_analysis: Optional[AIAnalysis] = Field(default=None, description="AI 分析结果")

    @property
    def has_ai_analysis(self) -> bool:
        """是否有 AI 分析结果"""
        return self.ai_analysis is not None and self.ai_analysis.analysis_status == "completed"

    @property
    def display_score(self) -> str:
        """格式化显示评分"""
        if self.ai_analysis and self.ai_analysis.analysis_status == "completed":
            score = self.ai_analysis.score
            return f"{score:.1f}/10"
        return "N/A"

    @property
    def display_learning_value(self) -> str:
        """格式化显示学习价值"""
        if self.ai_analysis and self.ai_analysis.analysis_status == "completed":
            value_map = {"high": "高 ⭐⭐⭐", "medium": "中 ⭐⭐", "low": "低 ⭐"}
            return value_map.get(self.ai_analysis.learning_value, "未知")
        return "未知"


class TrendingResult(BaseModel):
    """趋势抓取结果"""

    repositories: List[Repository] = Field(default_factory=list, description="仓库列表")
    period: str = Field(default="daily", description="时间周期")
    language: str = Field(default="", description="筛选语言")
    total_count: int = Field(default=0, description="总数")
    timestamp: datetime = Field(default_factory=datetime.now, description="抓取时间")

    def __init__(self, **data):
        super().__init__(**data)
        self.total_count = len(self.repositories)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AnalysisSummary(BaseModel):
    """分析摘要"""

    total_analyzed: int = Field(default=0, description="分析项目总数")
    worthwhile_count: int = Field(default=0, description="高价值推荐数量")
    worthwhile_rate: float = Field(default=0.0, description="高价值占比")
    tech_stack_summary: dict = Field(default_factory=dict, description="技术栈统计")
    avg_score: float = Field(default=0.0, description="平均评分")
    model_used: str = Field(default="", description="使用的 AI 模型")

    def calculate_from_repositories(self, repos: List[RepositoryWithAI]) -> None:
        """从仓库列表计算摘要"""
        self.total_analyzed = len(repos)

        worthwhile = [r for r in repos if r.ai_analysis and r.ai_analysis.is_worthwhile]
        self.worthwhile_count = len(worthwhile)
        self.worthwhile_rate = self.worthwhile_count / self.total_analyzed if self.total_analyzed > 0 else 0

        # 统计技术栈
        tech_counts = {}
        for repo in repos:
            if repo.ai_analysis and repo.ai_analysis.tech_stack:
                for tech in repo.ai_analysis.tech_stack:
                    tech_counts[tech] = tech_counts.get(tech, 0) + 1

        self.tech_stack_summary = dict(sorted(tech_counts.items(), key=lambda x: x[1], reverse=True)[:10])

        # 计算平均分
        scores = [r.ai_analysis.score for r in repos if r.ai_analysis and r.ai_analysis.score > 0]
        self.avg_score = sum(scores) / len(scores) if scores else 0

        # 获取使用的模型
        if repos:
            self.model_used = next((r.ai_analysis.model_used for r in repos
                                   if r.ai_analysis and r.ai_analysis.model_used), "unknown")
