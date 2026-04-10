# OpenAkita Plugins

[English](#english) | [中文](#中文)

<a id="中文"></a>

## 中文

OpenAkita 官方插件仓库 — 即装即用的扩展能力。

### 快速开始

```bash
# 1. 安装 SDK（开发插件时使用）
pip install openakita-plugin-sdk

# 2. 在 OpenAkita 中安装插件
#    方式一：设置中心 → 插件管理 → 输入路径或 Git URL → 安装
#    方式二：将插件目录复制到 data/plugins/
#    方式三：告诉 Akita "帮我安装 xxx 插件"
```

### 插件目录

| 插件 | 类别 | 说明 |
|------|------|------|
| [hello-tool](plugins/hello-tool/) | 🔧 工具 | 最简工具示例 |
| [echo-channel](plugins/echo-channel/) | 📡 通道 | 消息回声通道 |
| [sqlite-memory](plugins/sqlite-memory/) | 🧠 记忆 | SQLite 轻量记忆后端 |
| [echo-llm](plugins/echo-llm/) | 🤖 LLM | Echo 模型提供商（测试用） |
| [obsidian-kb](plugins/obsidian-kb/) | 📚 知识库 | Obsidian 笔记检索 |
| [message-logger](plugins/message-logger/) | 🪝 钩子 | 消息日志记录 |
| [translate-skill](plugins/translate-skill/) | 🎯 技能 | 翻译技能包 |
| [github-mcp](plugins/github-mcp/) | 🔌 MCP | GitHub MCP 服务封装 |
| [whatsapp-channel](plugins/whatsapp-channel/) | 📡 通道 | WhatsApp IM 接入 |
| [qdrant-memory](plugins/qdrant-memory/) | 🧠 记忆 | Qdrant 向量记忆后端 |
| [ollama-provider](plugins/ollama-provider/) | 🤖 LLM | Ollama 本地大模型接入 |

### 插件类别

OpenAkita 支持 **9 种插件类别**：

| 类别 | 说明 | 权限级别 |
|------|------|---------|
| Tool | 注册自定义工具 | Basic |
| Channel | 添加 IM 通道适配器 | Advanced |
| Memory | 替换/扩展记忆后端 | Advanced / System |
| LLM | 添加 LLM 提供商 | Advanced |
| Knowledge/RAG | 接入知识源 | Advanced |
| Hook | 拦截生命周期事件 | Basic / Advanced |
| Skill | 捆绑 SKILL.md 技能文件 | Basic |
| MCP | 封装 MCP 服务 | Basic |
| **Full-Stack UI** | 带独立前端页面的全栈插件 (Plugin 2.0) | Advanced |

### 开发你自己的插件

```bash
# 脚手架创建
python -m openakita_plugin_sdk.scaffold --id my-plugin --type tool --dir ./my-plugin

# 目录结构
my-plugin/
├── plugin.json          # 清单文件
├── plugin.py            # 入口代码
├── config_schema.json   # 配置 schema（可选）
├── README.md            # 文档
└── icon.png/svg         # 图标（可选）
```

详细文档见 [SDK 文档](sdk-docs/) 和 [插件开发指南](CONTRIBUTING.md)。

---

<a id="english"></a>

## English

Official plugin repository for [OpenAkita](https://github.com/openakita/openakita) — drop-in extensions for your AI team.

### Quick Start

```bash
# 1. Install the SDK (for plugin development)
pip install openakita-plugin-sdk

# 2. Install a plugin in OpenAkita
#    Option A: Setup Center → Plugin Manager → enter path or Git URL → Install
#    Option B: Copy plugin directory to data/plugins/
#    Option C: Tell Akita "install the xxx plugin for me"
```

### Plugin Catalog

| Plugin | Category | Description |
|--------|----------|-------------|
| [hello-tool](plugins/hello-tool/) | 🔧 Tool | Minimal tool example |
| [echo-channel](plugins/echo-channel/) | 📡 Channel | Message echo adapter |
| [sqlite-memory](plugins/sqlite-memory/) | 🧠 Memory | Lightweight SQLite memory backend |
| [echo-llm](plugins/echo-llm/) | 🤖 LLM | Echo model provider (for testing) |
| [obsidian-kb](plugins/obsidian-kb/) | 📚 Knowledge | Obsidian vault retrieval |
| [message-logger](plugins/message-logger/) | 🪝 Hook | Message logging |
| [translate-skill](plugins/translate-skill/) | 🎯 Skill | Translation skill pack |
| [github-mcp](plugins/github-mcp/) | 🔌 MCP | GitHub MCP server wrapper |
| [whatsapp-channel](plugins/whatsapp-channel/) | 📡 Channel | WhatsApp IM integration |
| [qdrant-memory](plugins/qdrant-memory/) | 🧠 Memory | Qdrant vector memory backend |
| [ollama-provider](plugins/ollama-provider/) | 🤖 LLM | Ollama local LLM provider |

### Plugin Categories

OpenAkita supports **9 plugin categories**:

| Category | Description | Permission Level |
|----------|-------------|-----------------|
| Tool | Register custom tools | Basic |
| Channel | Add IM channel adapters | Advanced |
| Memory | Replace / extend memory backends | Advanced / System |
| LLM | Add LLM providers | Advanced |
| Knowledge/RAG | Connect knowledge sources | Advanced |
| Hook | Intercept lifecycle events | Basic / Advanced |
| Skill | Bundle SKILL.md files | Basic |
| MCP | Wrap MCP servers | Basic |
| **Full-Stack UI** | Plugin with dedicated frontend page (Plugin 2.0) | Advanced |

### Develop Your Own Plugin

```bash
# Scaffold a new plugin
python -m openakita_plugin_sdk.scaffold --id my-plugin --type tool --dir ./my-plugin

# Directory structure
my-plugin/
├── plugin.json          # Manifest
├── plugin.py            # Entry point
├── config_schema.json   # Config schema (optional)
├── README.md            # Documentation
└── icon.png/svg         # Icon (optional)
```

See [SDK Documentation](sdk-docs/) and [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT — see individual plugin directories for their respective licenses.
