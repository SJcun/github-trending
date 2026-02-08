# GitHub Trending

> 获取并解读 GitHub Trending 界面，支持 AI 智能分析项目

## 功能特性

- 🚀 **Trending 抓取**: 获取 GitHub Trending 列表，支持语言和时间范围筛选
- 🤖 **AI 智能分析**: 集成 LLM 解读项目功能，自动分析 README 文档
- 📊 **数据可视化**: 生成语言分布、评分统计等图表
- 💾 **数据持久化**: SQLite 存储历史数据，支持趋势对比
- 🎨 **多种输出格式**: 表格、JSON、Markdown、CSV

## 安装

### 克隆仓库

```bash
git clone https://github.com/yourusername/github-trending.git
cd github-trending
```

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 AI 模型（可选）

复制 `.env.example` 为 `.env` 并配置 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件，至少配置一个 AI 提供商：

```bash
# Claude API Key（推荐）
ANTHROPIC_API_KEY=your_api_key_here

# 或使用 OpenAI
OPENAI_API_KEY=your_api_key_here

# 或使用 DeepSeek
DEEPSEEK_API_KEY=your_api_key_here

# 或使用本地 Ollama（无需 API Key）
# 确保已安装并启动 Ollama
```

## 使用方法

### 基本用法

```bash
# 获取今日 Trending（基础模式）
python src/cli.py trending

# 指定编程语言
python src/cli.py trending --language python

# 指定时间范围
python src/cli.py trending --since weekly

# 组合使用
python src/cli.py trending -l python -s weekly -n 10
```

### AI 分析模式

```bash
# 启用 AI 分析
python src/cli.py trending --ai

# 指定 AI 模型
python src/cli.py trending --ai --ai-model claude

# 强制重新分析（忽略缓存）
python src/cli.py trending --ai --ai-force

# 设置分析深度
python src/cli.py trending --ai --detail-level deep
```

### 输出格式

```bash
# JSON 输出
python src/cli.py trending -o json

# Markdown 输出（保存到文件）
python src/cli.py trending -o markdown

# CSV 输出
python src/cli.py trending -o csv
```

### 可视化图表

```bash
# 生成所有图表
python src/cli.py trending --ai --visualize
```

生成的图表保存在 `outputs/` 目录。

### 其他命令

```bash
# 查看单个仓库详情（含 AI 分析）
python src/cli.py repo microsoft/semantic-kernel

# 查看高评分项目
python src/cli.py high-score --min-score 8.0

# 数据库统计
python src/cli.py stats

# 清理旧数据
python src/cli.py cleanup --days 30

# 清理缓存
python src/cli.py cache-clear

# 查看支持的语言列表
python src/cli.py languages
```

## 命令行参数

### trending 命令

| 参数 | 说明 |
|------|------|
| `-l, --language TEXT` | 筛选编程语言 |
| `-s, --since` | 时间周期 (daily/weekly/monthly) |
| `-n, --limit INTEGER` | 返回数量限制 |
| `-o, --output` | 输出格式 (table/json/markdown/csv) |
| `--save` | 保存到数据库 |
| `--ai/--no-ai` | 是否启用 AI 分析 |
| `--ai-model` | AI 模型 (claude/openai/deepseek/ollama) |
| `--ai-cache/--no-ai-cache` | 是否使用缓存 |
| `--ai-force` | 强制重新分析 |
| `--detail-level` | 分析深度 (brief/standard/deep) |
| `--visualize` | 生成可视化图表 |
| `--proxy TEXT` | 代理地址 |

## 项目结构

```
github-trending/
├── src/
│   ├── ai/              # AI 模块
│   ├── analyzer/        # 分析器
│   ├── cli.py           # 命令行入口
│   ├── config.py        # 配置管理
│   ├── models/          # 数据模型
│   ├── output/          # 输出格式化
│   ├── scraper/         # 爬虫模块
│   ├── storage/         # 数据存储
│   └── utils/           # 工具函数
├── config/              # 配置文件
├── data/                # 数据目录
│   ├── cache/           # 缓存文件
│   └── github_trending.db  # SQLite 数据库
├── outputs/             # 输出文件
├── tests/               # 测试文件
├── requirements.txt     # 依赖列表
├── setup.py            # 安装配置
├── .env.example        # 环境变量模板
└── README.md           # 项目说明
```

## AI 分析能力

AI 可以分析项目的以下维度：

- **项目简介**: 一句话概括核心价值
- **核心功能**: 提炼 3-5 个主要功能点
- **技术栈**: 识别使用的技术、框架、语言
- **使用场景**: 适用的问题域和业务场景
- **学习价值**: 评级 (high/medium/low)
- **综合评分**: 0-10 分评分
- **推荐建议**: 是否值得深入了解

## 支持的 AI 模型

| 模型 | 说明 | 需要配置 |
|------|------|----------|
| Claude | Anthropic 官方，分析质量高 | `ANTHROPIC_API_KEY` |
| OpenAI | GPT-4，通用能力强 | `OPENAI_API_KEY` |
| DeepSeek | 国内可用，性价比高 | `DEEPSEEK_API_KEY` |
| Ollama | 本地部署，零成本 | 无需配置 |

## 配置文件

### AI 配置 (config/ai_config.yaml)

```yaml
# 默认使用的 AI 提供商
default_provider: claude

# 是否启用缓存
enable_cache: true
cache_ttl_hours: 24

# 模型参数
max_tokens: 4096
temperature: 0.7
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black src/
```

## 许可证

MIT License
