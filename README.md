<p align="center">
  <img src="docs/assets/logo.png" alt="logo" width="150" height="150"/>
</p>

<h1 align="center">V2EX Feed</h1>
<p align="center"><i>一个用于抓取 V2EX 最新帖子并推送到 Telegram 的轻量工具</i></p>

<div align="center">

  <!-- 项目信息 -->
  <img src="https://img.shields.io/github/repo-size/Jv0id/v2ex-feed" alt="Repo size" />
  <img src="https://img.shields.io/github/license/Jv0id/v2ex-feed" alt="License" />
  <img src="https://img.shields.io/badge/python-3.13%2B-blue" alt="Python version" />

  <!-- 社交统计 -->
  <img src="https://img.shields.io/github/stars/Jv0id/v2ex-feed?style=social" alt="Stars" />
  <img src="https://img.shields.io/github/forks/Jv0id/v2ex-feed?style=social" alt="Forks" />
  <img src="https://img.shields.io/github/issues/Jv0id/v2ex-feed" alt="Issues" />

</div>

V2EX Feed 是一个自动同步 V2EX 最新帖子的轻量工具，它会抓取内容并优化展示格式，然后推送到你的 Telegram，让你无需频繁刷新网页，也能第一时间掌握社区动态。

我们关注的不只是速度，还有阅读体验。通过结构化提取帖子中的标题、内容、作者、节点、发布时间等关键信息，V2EX Feed 都能有效剔除干扰内容，让你在 Telegram 上也能看到简洁清爽的内容。

这个项目的目标是做一个简单、直接、高效的 V2EX 阅读及沟通频道。无论你是 V2EX 的重度用户，还是只是不想错过最新的帖子，V2EX Feed 都能帮你更快、更轻松地获取信息。


## 📡 订阅频道

想看看效果？欢迎订阅我们的 Telegram 频道 👉 [@v2exfeed](https://t.me/v2ex_feed) ，及时查看最新的推送内容，赶快马上体验吧！

## 🚀 快速开始

- 项目使用 **Docker + Docker Compose** 进行快速部署，适用于本地开发与服务器运行
- 项目使用 `.env` 管理配置，敏感信息（如 Bot Token）不会硬编码在源码中
- 提供 CLI 启动入口：`v2ex-feed`，支持定制化运行参数

### 1. 克隆仓库

```bash
git clone https://github.com/Jv0id/v2ex-feed.git
cd v2ex-feed
```

### 2. 配置环境变量

复制示例配置文件：

```bash

# 复制编辑
cp .env.example .env
```

编辑 `.env` 文件并填写你的 **Bot Token** 和 **频道 ID** 等信息：

```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=@your_channel
```

> ⚠️ **请勿将包含真实 Bot Token 的 `.env` 文件提交到版本控制系统！**

### 3. 运行方式

#### 🐳 使用 Docker（推荐 ✅）

```bash

docker-compose up -d
```

#### 🐍 本地运行（需 Python 3.13+）

```bash
# 如未安装 uv，可先执行：
curl -Ls https://astral.sh/uv/install.sh | bash
```

```bash

uv venv
source .venv/bin/activate
uv pip install .
uv run v2ex-feed  # 启动 CLI
```

## ⚙️ 技术栈

项目基于 Python 3.13 构建，采用异步编程模型，结合 Telegram Bot 和 RSS 内容处理，通过任务队列与后台异步 worker 实现高效、稳定的信息推送流程。项目内置速率限制与自动重试机制，支持长时间运行和高并发处理，适合部署在服务器或容器环境中。

### 核心依赖与功能模块

| 技术 / 库             | 作用说明                             |
| :-------------------- | :----------------------------------- |
| uv                    | 替代 pip + venv 的极速依赖管理工具   |
| aiohttp               | 异步 HTTP 客户端，抓取 V2EX RSS 数据 |
| aiolimiter            | 异步速率限制器，防止过频发送或被封   |
| feedparser            | RSS 解析库，提取帖子信息             |
| beautifulsoup4 & lxml | 清洗富文本内容，适配 Telegram 展示   |
| tortoise-orm          | 异步 ORM，管理 SQLite 数据持久化     |
| aiosqlite             | 异步数据库驱动，适配 Tortoise ORM    |
| apscheduler           | 定时任务调度器，定期抓取并推送新内容 |
| python-telegram-bot   | 操作 Telegram Bot 接口               |
| pydantic-settings     | 管理配置文件与运行参数               |
| tenacity              | 自动重试机制，提升抓取与推送稳定性   |
| loguru                | 结构化日志输出，方便调试与监控       |
| typer                 | 快速构建命令行工具（CLI）            |

## 🗂️ 项目结构

```bash
src/v2ex_feed/
├── __init__.py                    # 模块初始化
├── cli.py                         # Typer 命令行入口
├── logger_cfg.py                  # 日志配置（基于 Loguru）
├── main.py                        # 程序主入口（可选直接运行）
├── models.py                      # 数据模型定义（用于 ORM）
├── queueing.py                    # 异步消息队列与 Worker 协程
├── rss_tasks.py                   # 抓取任务调度封装
├── settings.py                    # Pydantic 环境变量管理
├── telegram_html_formatter.py     # HTML 转 Telegram 格式清洗
├── telegram_utils.py              # Telegram 消息发送与限速封装
```

## 🤝 贡献指南

欢迎参与贡献！请按照以下流程提交你的修改：

1. 新建功能分支：`git checkout -b feature/your-feature-name`  
2. 提交修改：`git commit -m 'feat: 添加你的功能说明'`  
3. 推送到远程仓库：`git push origin feature/your-feature-name`  
4. 在 GitHub 上发起 Pull Request，我会尽快审核

📌 **提交信息请遵循 [Conventional Commits](https://www.conventionalcommits.org/zh-hans/v1.0.0/) 格式**，例如：

- `feat: 添加新功能`
- `fix: 修复内容解析错误`
- `docs: 更新使用文档`
- ...

这样可以帮助我们更好地管理项目历史与版本变更。

感谢您的贡献 🙌

## 👥 贡献者

<a href="https://github.com/Jv0id/v2ex-feed/graphs/contributors">
    <img src="https://contrib.rocks/image?repo=jackhawks/v2ex-feed" />
</a>


## 🙏 赞助者

无

## ⭐ Star 历史

[![Stargazers over time](https://starchart.cc/Jv0id/v2ex-feed.svg?variant=adaptive)](https://starchart.cc/Jv0id/v2ex-feed)

## 🔒 License

本项目采用 [Apache License 2.0](LICENSE) 开源，允许在遵守许可条款的前提下自由使用、修改、分发和商用。  
请在使用时保留原始版权声明和许可证文件。


---

## 📢 免责声明

> 
> 本项目 v2ex-feed 不是 V2EX 或 Telegram 官方产品，也未与其建立任何合作关系。所有商标和名称归原权利方所有。
> 
> 本项目仅供开发者学习和交流使用，请合理、合法地使用本项目。
