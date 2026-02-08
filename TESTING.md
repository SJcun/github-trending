# GitHub Trending - 测试与使用文档

## 一、项目概述

GitHub Trending 是一个用于获取和解读 GitHub Trending 页面的 Python 工具，支持 AI 智能分析项目。

### 核心功能
- 获取 GitHub Trending 列表（支持语言/时间筛选）
- AI 智能分析项目 README 文档
- 数据持久化（SQLite）
- 可视化图表生成
- 多种输出格式

## 二、项目结构

```
github-trending/
├── main.py                 # 主入口文件
├── run.bat                 # Windows 启动脚本
├── trending.bat            # 快捷启动脚本
├── requirements.txt        # 依赖列表
├── config/
│   └── ai_config.yaml      # AI 配置
├── src/
│   ├── ai/                 # AI 模块
│   ├── config.py           # 全局配置
│   ├── models/             # 数据模型
│   ├── output/             # 输出格式化
│   ├── scraper/            # 爬虫模块
│   ├── storage/            # 数据存储
│   └── utils/              # 工具函数
├── data/                   # 数据目录
│   ├── cache/              # 缓存文件
│   └── github_trending.db  # SQLite 数据库
└── outputs/                # 输出文件
```

## 三、功能测试清单

### 3.1 基础功能测试

| 功能 | 测试命令 | 预期结果 | 状态 |
|------|----------|----------|------|
| 获取全部 Trending | `python main.py trending` | 显示 25 个仓库列表 | ✅ 已测试 |
| 按语言筛选 | `python main.py trending -l python` | 显示 Python 项目 | ✅ 已测试 |
| 限制数量 | `python main.py trending -n 5` | 只显示 5 个项目 | ✅ 已测试 |
| 周 Trending | `python main.py trending -s weekly` | 显示周趋势 | 待测试 |
| 月 Trending | `python main.py trending -s monthly` | 显示月趋势 | 待测试 |

### 3.2 输出格式测试

| 格式 | 测试命令 | 预期结果 | 状态 |
|------|----------|----------|------|
| 表格输出 | `python main.py trending -o table` | 终端表格显示 | ✅ 已测试 |
| JSON 输出 | `python main.py trending -o json` | JSON 格式输出 | 待测试 |
| Markdown | `python main.py trending -o markdown` | 生成 .md 文件 | 待测试 |
| CSV 输出 | `python main.py trending -o csv` | 生成 .csv 文件 | 待测试 |

### 3.3 AI 分析测试

| 功能 | 测试命令 | 前置条件 | 预期结果 | 状态 |
|------|----------|----------|----------|------|
| 基础 AI 分析 | `python main.py trending --ai` | 配置 API Key | 显示 AI 分析结果 | 待测试 |
| Claude 模型 | `python main.py trending --ai --ai-model claude` | Claude API Key | 使用 Claude 分析 | 待测试 |
| OpenAI 模型 | `python main.py trending --ai --ai-model openai` | OpenAI API Key | 使用 GPT 分析 | 待测试 |
| 强制重新分析 | `python main.py trending --ai --ai-force` | 配置 API Key | 忽略缓存重新分析 | 待测试 |
| 简洁模式 | `python main.py trending --ai --detail-level brief` | 配置 API Key | 快速分析 | 待测试 |
| 深度模式 | `python main.py trending --ai --detail-level deep` | 配置 API Key | 详细分析 | 待测试 |

### 3.4 数据库测试

| 功能 | 测试命令 | 预期结果 | 状态 |
|------|----------|----------|------|
| 保存数据 | `python main.py trending --save` | 数据保存到数据库 | 待测试 |
| 查看统计 | `python main.py stats` | 显示数据库统计 | 待测试 |
| 高分项目 | `python main.py high-score` | 显示高评分项目 | 待测试 |
| 清理数据 | `python main.py cleanup --days 30` | 清理旧数据 | 待测试 |

### 3.5 单仓库测试

| 功能 | 测试命令 | 预期结果 | 状态 |
|------|----------|----------|------|
| 查看仓库 | `python main.py repo openai/gpt` | 显示仓库详情 | 待测试 |
| AI 分析仓库 | `python main.py repo microsoft/semantic-kernel --ai` | AI 分析结果 | 待测试 |

### 3.6 可视化测试

| 功能 | 测试命令 | 前置条件 | 预期结果 | 状态 |
|------|----------|----------|----------|------|
| 生成图表 | `python main.py trending --ai --visualize` | AI 分析完成 | 生成图表文件 | 待测试 |

### 3.7 缓存测试

| 功能 | 测试命令 | 预期结果 | 状态 |
|------|----------|----------|------|
| 清空缓存 | `python main.py cache-clear --all` | 清空所有缓存 | 待测试 |
| 清理过期 | `python main.py cache-clear` | 清理过期缓存 | 待测试 |

## 四、已知问题

### 4.1 已确认问题

| 问题描述 | 严重程度 | 影响 | 状态 |
|----------|----------|------|------|
| 描述字段为空 | 中 | 爬取数据不完整 | 需修复解析器 |
| Windows 编码问题 | 低 | 已通过脚本解决 | ✅ 已解决 |
| Pydantic V2 兼容性 | 中 | dict() 方法已弃用 | ✅ 已修复 |

### 4.2 待修复问题

1. **爬虫解析器问题**
   - 问题：项目描述字段为空
   - 原因：GitHub 页面结构变化
   - 解决方案：更新 `src/scraper/parser.py` 中的选择器

2. **贡献者头像获取**
   - 问题：可能无法正确获取
   - 需要验证并修复

## 五、AI 配置指南

### 5.1 Claude 配置（推荐）

1. 获取 API Key: https://console.anthropic.com/
2. 配置环境变量：
   ```bash
   set ANTHROPIC_API_KEY=your_key_here
   ```
3. 或在 `.env` 文件中配置

### 5.2 OpenAI 配置

1. 获取 API Key: https://platform.openai.com/
2. 配置环境变量：
   ```bash
   set OPENAI_API_KEY=your_key_here
   ```

### 5.3 DeepSeek 配置

1. 获取 API Key: https://platform.deepseek.com/
2. 配置环境变量：
   ```bash
   set DEEPSEEK_API_KEY=your_key_here
   ```

### 5.4 Ollama 配置（本地）

1. 安装 Ollama: https://ollama.ai/
2. 拉取模型：`ollama pull llama3`
3. 无需配置 API Key，直接使用

## 六、测试步骤

### 6.1 环境准备

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置 AI（可选）
copy .env.example .env
# 编辑 .env 文件，添加 API Key

# 3. 测试基础功能
python main.py trending --language python -n 3
```

### 6.2 基础功能测试

```bash
# 测试 1: 获取 Trending
python main.py trending

# 测试 2: 不同语言
python main.py trending -l rust
python main.py trending -l go

# 测试 3: 不同时间范围
python main.py trending -s weekly
python main.py trending -s monthly

# 测试 4: 输出格式
python main.py trending -o json
python main.py trending -o markdown
python main.py trending -o csv
```

### 6.3 AI 功能测试

```bash
# 测试 5: AI 分析（需要配置 API Key）
python main.py trending --ai -n 3

# 测试 6: 不同模型
python main.py trending --ai --ai-model claude -n 2
python main.py trending --ai --ai-model openai -n 2

# 测试 7: 不同分析深度
python main.py trending --ai --detail-level brief -n 2
python main.py trending --ai --detail-level deep -n 1
```

### 6.4 数据功能测试

```bash
# 测试 8: 保存到数据库
python main.py trending --save

# 测试 9: 查看统计
python main.py stats

# 测试 10: 高分项目
python main.py high-score --min-score 7.0
```

### 6.5 单仓库测试

```bash
# 测试 11: 查看单个仓库
python main.py repo openai/gpt

# 测试 12: AI 分析单仓库
python main.py repo microsoft/semantic-kernel --ai
```

### 6.6 可视化测试

```bash
# 测试 13: 生成图表
python main.py trending --ai --visualize -n 5
# 检查 outputs/ 目录下的图片文件
```

## 七、命令速查表

| 命令 | 说明 |
|------|------|
| `python main.py trending` | 获取今日 Trending |
| `python main.py trending -l <lang>` | 按语言筛选 |
| `python main.py trending -s <period>` | 时间范围 (daily/weekly/monthly) |
| `python main.py trending -n <num>` | 限制数量 |
| `python main.py trending -o <format>` | 输出格式 (table/json/markdown/csv) |
| `python main.py trending --save` | 保存到数据库 |
| `python main.py trending --ai` | 启用 AI 分析 |
| `python main.py trending --ai-model <model>` | 指定 AI 模型 |
| `python main.py trending --visualize` | 生成图表 |
| `python main.py repo <owner/repo>` | 查看单个仓库 |
| `python main.py stats` | 数据库统计 |
| `python main.py high-score` | 高分项目 |
| `python main.py languages` | 支持的语言列表 |
| `python main.py cache-clear` | 清理缓存 |
| `python main.py cleanup` | 清理旧数据 |

## 八、快速开始示例

```bash
# 示例 1: 查看 Python 今日热门前 10
python main.py trending -l python -n 10

# 示例 2: AI 分析 Rust 周趋势
python main.py trending -l rust -s weekly --ai -n 5

# 示例 3: 生成报告并保存
python main.py trending -o markdown --save

# 示例 4: 查看某个热门项目
python main.py repo openai/gpt --ai
```

## 九、下一步计划

### 9.1 优先级高
- [ ] 修复爬虫解析器（描述字段为空）
- [ ] 完善错误处理和重试机制
- [ ] 添加单元测试

### 9.2 优先级中
- [ ] 优化 AI Prompt 效果
- [ ] 添加更多可视化图表
- [ ] 支持配置文件

### 9.3 优先级低
- [ ] Web 界面
- [ ] 定时任务支持
- [ ] Docker 部署

## 十、常见问题

### Q1: 如何配置 AI 模型？
A: 复制 `.env.example` 为 `.env`，添加对应的 API Key。

### Q2: 编码错误怎么解决？
A: 使用 `run.bat` 或 `trending.bat` 脚本运行，已处理编码问题。

### Q3: 如何只爬取不分析？
A: 不加 `--ai` 参数即可：`python main.py trending`

### Q4: 数据存储在哪里？
A: 数据存储在 `data/github_trending.db`，缓存在 `data/cache/`

### Q5: 如何更新依赖？
A: 运行 `pip install -r requirements.txt --upgrade`

---

## 更新日志

| 日期 | 版本 | 更新内容 |
|------|------|----------|
| 2025-02-08 | 0.1.0 | 初始版本，基础功能实现 |
