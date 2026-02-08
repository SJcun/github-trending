# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 提供在此代码库中工作的指导。

## 项目概述

GitHub Trending 是一个 Python CLI 工具，用于获取和分析 GitHub Trending 仓库并提供 AI 智能解读。它抓取 GitHub Trending 页面，使用 LLM 分析项目 README，将结果存储在 SQLite 中，并提供多种输出格式包括可视化图表。

## 常用命令

### 运行应用

```bash
# 基础趋势获取
python main.py trending

# 带语言筛选和 AI 分析
python main.py trending --language python --ai

# 不同输出格式
python main.py trending -o json
python main.py trending -o markdown
python main.py trending -o csv

# 保存到数据库
python main.py trending --save

# 单个仓库分析
python main.py repo microsoft/semantic-kernel --ai

# 数据库操作
python main.py stats
python main.py high-score --min-score 7.0
python main.py cleanup --days 30

# 缓存管理
python main.py cache-clear --all
```

### Windows 快速启动

项目包含批处理文件，用于处理 Windows 上的 UTF-8 编码问题：
- `run.bat` - 通用命令包装器
- `trending.bat` - 快速趋势命令

### 安装

```bash
pip install -r requirements.txt
# 或作为包安装
pip install -e .
```

### 测试

`tests/` 目录当前为空。测试应使用以下命令运行：
```bash
pytest tests/
```

## 架构

项目采用**分层架构**，模块化组件设计：

```
main.py (CLI/Click)
    |
    +-- scraper/      # HTML 抓取和解析
    +-- ai/           # LLM 集成和分析
    +-- storage/      # SQLite 和文件缓存
    +-- output/       # 格式化和可视化
    +-- models/       # Pydantic 数据模型
```

### 核心架构模式

**策略模式（AI 提供商）**：`src/ai/client.py` 定义了 `LLMProvider` 抽象基类，实现了 Claude、OpenAI、DeepSeek 和 Ollama 的具体类。`AIClient` 提供统一接口并处理提供商初始化。

**多级缓存**：
- `FileCache` (`src/storage/cache.py`) - JSON 文件缓存趋势结果
- `AICache` (`src/ai/cache.py`) - 基于内容哈希的 AI 分析缓存，支持 TTL
- `Database` (`src/storage/database.py`) - SQLite 持久化存储仓库和分析数据

**速率限制**：`src/scraper/limiter.py` 中的令牌桶算法控制对 GitHub 的请求速率。

**配置管理**：
- `src/config.py` - `Config` 类管理全局设置，`AIModelConfig` 管理 LLM 设置
- `config/ai_config.yaml` - AI 模型配置文件

### 模块详解

**Scraper 模块** (`src/scraper/`):
- `HttpClient` - HTTP 请求，支持重试、代理、随机 User-Agent
- `TrendingParser` - 基于 BeautifulSoup 的 GitHub Trending 页面 HTML 解析
- `ReadmeFetcher` - 多源 README 获取（raw.githubusercontent.com、GitHub API、HTML 抓取）
- `RateLimiter` - 令牌桶速率限制

**AI 模块** (`src/ai/`):
- `AIClient` - 支持多个 LLM 提供商的统一接口
- `PromptManager` - 基于模板的提示词生成
- `AIResultParser` - 解析和验证 LLM JSON 响应
- `AICache` - 基于内容哈希的缓存，支持 TTL

**Storage 模块** (`src/storage/`):
- `Database` - SQLite 操作，管理仓库、快照、AI 分析
- `FileCache` - JSON 文件缓存趋势结果

**Output 模块** (`src/output/`):
- `OutputFormatter` - 表格、JSON、Markdown、CSV 格式化，支持彩色输出
- `Visualizer` - Matplotlib 图表（语言分布、评分、技术栈）

**Models** (`src/models/`):
- Pydantic 模型：`Repository`、`AIAnalysis`、`RepositoryWithAI`、`TrendingResult`、`AnalysisSummary`

## 配置

### AI 模型

AI 提供商通过环境变量或 `config/ai_config.yaml` 配置：

- Claude: `ANTHROPIC_API_KEY`
- OpenAI: `OPENAI_API_KEY`
- DeepSeek: `DEEPSEEK_API_KEY`
- Ollama: 无需密钥（本地 `http://localhost:11434`）

### 数据路径

- 数据库：`data/github_trending.db`
- 缓存：`data/cache/`
- 输出：`outputs/`
- 配置：`config/ai_config.yaml`

## 重要实现说明

### Windows 编码处理

项目通过以下方式处理 Windows 上的 UTF-8 编码问题：
- `main.py` 和 `setup.py` 中使用 `io.TextIOWrapper` 包装 stdout/stderr
- 批处理文件（`run.bat`、`trending.bat`）用于 UTF-8 执行

### AI 分析流程

1. 获取仓库 README（长度根据 detail_level 限制）
2. 对 README 内容进行哈希作为缓存键
3. 检查缓存（除非使用 `--ai-force`）
4. 如有缓存：返回缓存的分析结果
5. 如无缓存：发送到 LLM 并附带元数据，解析 JSON 响应，保存到缓存

### 已知问题

来自 `TESTING.md`：
- 描述字段有时为空，由于 GitHub 页面结构变化（`src/scraper/parser.py` 中的解析器选择器问题）
- Pydantic V2 兼容性已处理

### 添加新的 AI 提供商

1. 在 `src/ai/client.py` 中创建继承自 `LLMProvider` 的新类
2. 实现 `call()`、`is_available()` 和 `model_name` 属性
3. 在 `AIClient._initialize_provider()` 中添加工厂方法
4. 在 `config/ai_config.yaml` 中添加配置
5. 更新 `src/config.py` 中的 `AIModelConfig`

## 数据流示例

**趋势抓取**：`CLI → HttpClient → GitHub Trending → HTML → TrendingParser → Repository[] → Output`

**AI 分析**：`Repository → ReadmeFetcher → README → AIClient → LLM → AIResultParser → AIAnalysis → 缓存/数据库`

**可视化**：`RepositoryWithAI[] → Visualizer → Matplotlib → PNG 文件`
