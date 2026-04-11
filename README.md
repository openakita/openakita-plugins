# OpenAkita Plugins

[English](#english) | [中文](#中文)

<a id="中文"></a>

## 中文

OpenAkita 官方插件仓库 — 示例插件 + SDK 开发文档。

### 这个仓库是什么？

本仓库包含两部分内容：

1. **`plugins/`** — 各类型插件的**参考实现**和示例，覆盖所有 9 种插件类型
2. **`sdk-docs/`** — 插件开发 SDK 文档，插件开发者的完整指南

> **安装插件**不需要克隆本仓库。在 OpenAkita 中直接输入 Git URL 或本地路径即可安装。

### 快速开始

```bash
# 1. 安装 SDK（开发插件时使用）
pip install openakita-plugin-sdk

# 2. 脚手架创建新插件
python -m openakita_plugin_sdk.scaffold --id my-plugin --type tool --dir ./my-plugin

# 3. 在 OpenAkita 中安装插件
#    方式一：设置中心 → 插件管理 → 输入路径或 Git URL → 安装
#    方式二：将插件目录复制到 data/plugins/
#    方式三：告诉 Akita "帮我安装 xxx 插件"
```

### 示例插件

| 插件 | 类型 | 说明 | 适合学习 |
|------|------|------|---------|
| [hello-tool](plugins/hello-tool/) | Tool | 最简工具注册示例 | 入门必看 |
| [echo-channel](plugins/echo-channel/) | Channel | 消息回声通道（IM 适配器示例） | Channel 开发 |
| [sqlite-memory](plugins/sqlite-memory/) | Memory | SQLite 轻量记忆后端，零外部依赖 | Memory 后端 |
| [echo-llm](plugins/echo-llm/) | LLM | Echo 模型提供商（测试用） | LLM 接入 |
| [ollama-provider](plugins/ollama-provider/) | LLM | Ollama 本地大模型接入（双注册示例） | LLM 高级用法 |
| [obsidian-kb](plugins/obsidian-kb/) | RAG | Obsidian 笔记库检索，支持全文搜索和标签过滤 | RAG/知识库 |
| [message-logger](plugins/message-logger/) | Hook | 消息日志记录（钩子示例） | Hook 开发 |
| [translate-skill](plugins/translate-skill/) | Skill | 翻译技能包（SKILL.md 示例） | Skill 开发 |
| [github-mcp](plugins/github-mcp/) | MCP | GitHub MCP 服务封装 | MCP 集成 |
| [whatsapp-channel](plugins/whatsapp-channel/) | Channel | WhatsApp IM 接入（Cloud API + Web） | 生产级 Channel |
| [qdrant-memory](plugins/qdrant-memory/) | Memory | Qdrant 向量记忆后端 | 向量存储 |

### 插件类型

OpenAkita 支持 **9 种插件类型**：

| 类型 | 说明 | 权限级别 | 需要 Python？ |
|------|------|---------|:---:|
| Tool | 注册 AI 可调用的自定义工具 | Basic | 是 |
| Channel | 添加 IM 通道适配器 | Advanced | 是 |
| Memory | 替换/扩展记忆后端 | Advanced / System | 是 |
| LLM | 添加 LLM 提供商 | Advanced | 是 |
| Knowledge/RAG | 接入知识源 | Advanced | 是 |
| Hook | 拦截生命周期事件 | Basic / Advanced | 是 |
| Skill | 捆绑 SKILL.md 技能文件 | Basic | **否** |
| MCP | 封装 MCP 服务 | Basic | **否** |
| **Full-Stack UI** | 带独立前端页面的全栈插件 (Plugin 2.0) | Advanced | 是 |

### 开发你自己的插件

```bash
# Python 插件目录结构
my-plugin/
├── plugin.json          # 清单文件（必需）
├── plugin.py            # 入口代码（Python 类型必需）
├── config_schema.json   # 配置 schema（可选）
├── README.md            # 文档
└── icon.png/svg         # 图标（可选）
```

**关键约定：**
- Python 插件的入口文件必须导出名为 `Plugin` 的类，继承 `PluginBase`
- MCP 类型只需 `plugin.json` + `mcp_config.json`，无需 Python 代码
- Skill 类型只需 `plugin.json` + `SKILL.md`，无需 Python 代码
- 默认插件安装目录：`{project_root}/data/plugins/`

详细文档见 [SDK 文档](sdk-docs/) 和 [插件开发指南](CONTRIBUTING.md)。

---

<a id="english"></a>

## English

Official plugin repository for [OpenAkita](https://github.com/openakita/openakita) — reference plugins + SDK documentation.

### What Is This Repository?

This repository contains two parts:

1. **`plugins/`** — **Reference implementations** and examples covering all 9 plugin types
2. **`sdk-docs/`** — Plugin development SDK documentation, a complete guide for plugin developers

> You don't need to clone this repo to **install plugins**. Just provide a Git URL or local path in OpenAkita.

### Quick Start

```bash
# 1. Install the SDK (for plugin development)
pip install openakita-plugin-sdk

# 2. Scaffold a new plugin
python -m openakita_plugin_sdk.scaffold --id my-plugin --type tool --dir ./my-plugin

# 3. Install a plugin in OpenAkita
#    Option A: Setup Center → Plugin Manager → enter path or Git URL → Install
#    Option B: Copy plugin directory to data/plugins/
#    Option C: Tell Akita "install the xxx plugin for me"
```

### Example Plugins

| Plugin | Type | Description | Good For Learning |
|--------|------|-------------|-------------------|
| [hello-tool](plugins/hello-tool/) | Tool | Minimal tool registration example | Getting started |
| [echo-channel](plugins/echo-channel/) | Channel | Message echo adapter (IM adapter demo) | Channel dev |
| [sqlite-memory](plugins/sqlite-memory/) | Memory | SQLite memory backend, zero deps | Memory backends |
| [echo-llm](plugins/echo-llm/) | LLM | Echo model provider (for testing) | LLM integration |
| [ollama-provider](plugins/ollama-provider/) | LLM | Ollama local LLM (dual-registration demo) | Advanced LLM |
| [obsidian-kb](plugins/obsidian-kb/) | RAG | Obsidian vault retrieval with full-text search | RAG/Knowledge |
| [message-logger](plugins/message-logger/) | Hook | Message logging (hook demo) | Hook dev |
| [translate-skill](plugins/translate-skill/) | Skill | Translation skill pack (SKILL.md demo) | Skill dev |
| [github-mcp](plugins/github-mcp/) | MCP | GitHub MCP server wrapper | MCP integration |
| [whatsapp-channel](plugins/whatsapp-channel/) | Channel | WhatsApp IM (Cloud API + Web) | Production channel |
| [qdrant-memory](plugins/qdrant-memory/) | Memory | Qdrant vector memory backend | Vector storage |

### Plugin Types

OpenAkita supports **9 plugin types**:

| Type | Description | Permission Level | Python Required? |
|------|-------------|-----------------|:---:|
| Tool | Register custom AI-callable tools | Basic | Yes |
| Channel | Add IM channel adapters | Advanced | Yes |
| Memory | Replace / extend memory backends | Advanced / System | Yes |
| LLM | Add LLM providers | Advanced | Yes |
| Knowledge/RAG | Connect knowledge sources | Advanced | Yes |
| Hook | Intercept lifecycle events | Basic / Advanced | Yes |
| Skill | Bundle SKILL.md files | Basic | **No** |
| MCP | Wrap MCP servers | Basic | **No** |
| **Full-Stack UI** | Plugin with dedicated frontend page (Plugin 2.0) | Advanced | Yes |

### Develop Your Own Plugin

```bash
# Python plugin directory structure
my-plugin/
├── plugin.json          # Manifest (required)
├── plugin.py            # Entry point (required for Python type)
├── config_schema.json   # Config schema (optional)
├── README.md            # Documentation
└── icon.png/svg         # Icon (optional)
```

**Key conventions:**
- Python plugin entry file must export a class named `Plugin` inheriting from `PluginBase`
- MCP type only needs `plugin.json` + `mcp_config.json`, no Python code
- Skill type only needs `plugin.json` + `SKILL.md`, no Python code
- Default plugin install directory: `{project_root}/data/plugins/`

See [SDK Documentation](sdk-docs/) and [Contributing Guide](CONTRIBUTING.md) for details.

## License

MIT — see individual plugin directories for their respective licenses.
