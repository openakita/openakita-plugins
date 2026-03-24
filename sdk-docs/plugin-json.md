# plugin.json 参考 / plugin.json Reference

每个插件目录必须包含一个 `plugin.json` 清单文件。宿主在启动时扫描此文件以发现和加载插件。

Every plugin directory must contain a `plugin.json` manifest file. The host scans for this file at startup to discover and load plugins.

---

## 必需字段 / Required Fields

| 字段 / Field | 类型 / Type | 说明 / Description |
|-------------|------------|-------------------|
| `id` | `string` | 唯一标识符，使用 kebab-case / Unique identifier, kebab-case |
| `name` | `string` | 用户可见的显示名称 / Human-readable display name |
| `version` | `string` | 语义化版本号 / SemVer version string |
| `type` | `string` | 运行时类型 / Runtime type: `python`, `mcp`, `skill` |

## 可选字段 / Optional Fields

| 字段 / Field | 类型 / Type | 默认值 / Default | 说明 / Description |
|-------------|------------|------------------|-------------------|
| `entry` | `string` | 按 type 而定 / varies | 入口文件 / Entry point file |
| `description` | `string` | `""` | 简短描述 / Short description |
| `author` | `string` | `""` | 作者 / Author name |
| `license` | `string` | `""` | 许可证 / License (e.g., `"MIT"`) |
| `homepage` | `string` | `""` | 项目主页 URL / Project homepage URL |
| `permissions` | `string[]` | `[]` | 所需权限列表 / Required permissions (see [permissions.md](permissions.md)) |
| `requires` | `object` | `{}` | 依赖声明 / Dependencies |
| `provides` | `object` | `{}` | 能力声明 / Provided capabilities |
| `replaces` | `string[]` | `[]` | 替换的内置模块 / Built-in modules this replaces |
| `conflicts` | `string[]` | `[]` | 冲突的插件 ID / Conflicting plugin IDs |
| `category` | `string` | `""` | 市场分类 / Marketplace category |
| `tags` | `string[]` | `[]` | 搜索标签 / Search tags |
| `icon` | `string` | `""` | 图标名称 (Tabler Icons) / Icon name |
| `load_timeout` | `number` | `10` | `on_load()` 最大秒数 / Max seconds for `on_load()` |
| `hook_timeout` | `number` | `5` | 每个钩子回调最大秒数 / Max seconds per hook callback |
| `retrieve_timeout` | `number` | `3` | 检索源调用最大秒数 / Max seconds for retrieval calls |

## 默认入口文件 / Default Entry Points

| `type` | 默认 `entry` / Default `entry` |
|--------|-------------------------------|
| `python` | `plugin.py` |
| `mcp` | `mcp_config.json` |
| `skill` | `SKILL.md` |

---

## `provides` 对象 / `provides` Object

声明插件提供的能力，用于市场展示和依赖检查。

Declares what the plugin provides. Used for marketplace display and dependency checking.

```json
{
  "provides": {
    "channels": ["whatsapp"],
    "tools": ["search_notes", "create_note"],
    "memory_backend": "qdrant",
    "llm_provider": {
      "api_type": "ollama_native",
      "registry_slug": "ollama"
    },
    "retrieval_sources": ["obsidian"],
    "hooks": ["on_message_received", "on_retrieve"],
    "api_routes": "routes.py",
    "skill": "SKILL.md",
    "config_schema": "config_schema.json"
  }
}
```

## `requires` 对象 / `requires` Object

声明依赖关系。宿主在加载前检查版本兼容性。

Declares dependencies. The host checks version compatibility before loading.

```json
{
  "requires": {
    "openakita": ">=1.5.0",
    "plugin_api": "~1",
    "sdk": ">=0.1.0",
    "python": ">=3.11",
    "pip": ["qdrant-client>=1.7.0", "httpx"],
    "npm": [],
    "system": []
  }
}
```

| 字段 / Field | 运行时校验 / Validated | 说明 / Description |
|-------------|:---:|-------------------|
| `openakita` | 是 (error) | 最低 OpenAkita 版本，格式 `>=X.Y.Z` / Minimum OpenAkita version |
| `plugin_api` | 是 (error) | 兼容的 API 主版本，格式 `~N` 或 `>=X.Y.Z` / Compatible API major version |
| `sdk` | 是 (warn) | 最低 SDK 版本（仅警告）/ Minimum SDK version (warn only) |
| `python` | 是 (error) | 最低 Python 版本，格式 `>=3.11` / Minimum Python version |
| `pip` | 否 (stored) | Python 包依赖 / Python package dependencies |
| `npm` | 否 (stored) | Node.js 包依赖（MCP 类型用）/ Node.js dependencies (for MCP type) |
| `system` | 否 (stored) | 系统级依赖 / System-level dependencies |

---

## 完整示例 / Complete Example

### 工具插件 / Tool Plugin

```json
{
  "id": "hello-tool",
  "name": "Hello Tool",
  "version": "1.0.0",
  "description": "一个简单的问候工具 / A simple greeting tool",
  "author": "OpenAkita Team",
  "license": "MIT",
  "type": "python",
  "entry": "plugin.py",
  "permissions": ["tools.register"],
  "provides": { "tools": ["hello_world"] },
  "category": "tool",
  "tags": ["demo", "greeting"]
}
```

### RAG 知识库插件 / RAG Knowledge Base Plugin

```json
{
  "id": "obsidian-kb",
  "name": "Obsidian Knowledge Base",
  "version": "1.0.0",
  "description": "从 Obsidian 知识库检索内容 / RAG retrieval from Obsidian vault",
  "author": "Community",
  "license": "MIT",
  "homepage": "https://github.com/openakita/plugin-obsidian-kb",
  "type": "python",
  "entry": "plugin.py",
  "permissions": [
    "tools.register",
    "hooks.retrieve",
    "retrieval.register",
    "config.read",
    "config.write"
  ],
  "requires": {
    "openakita": ">=1.5.0",
    "pip": ["markdown-it-py"]
  },
  "provides": {
    "tools": ["search_obsidian"],
    "retrieval_sources": ["obsidian"],
    "hooks": ["on_retrieve"],
    "config_schema": "config_schema.json"
  },
  "category": "productivity",
  "tags": ["obsidian", "knowledge-base", "rag", "markdown"],
  "icon": "notebook",
  "load_timeout": 15,
  "retrieve_timeout": 5
}
```

### 记忆后端插件 / Memory Backend Plugin

```json
{
  "id": "qdrant-memory",
  "name": "Qdrant Memory Backend",
  "version": "1.0.0",
  "description": "使用 Qdrant 向量数据库替换内置记忆系统 / Replace built-in memory with Qdrant",
  "type": "python",
  "permissions": ["memory.replace", "config.read", "config.write"],
  "requires": { "pip": ["qdrant-client>=1.7.0"] },
  "provides": { "memory_backend": "qdrant" },
  "replaces": ["builtin-memory"],
  "category": "memory"
}
```

### MCP 包装插件 / MCP Wrapper Plugin

```json
{
  "id": "github-mcp",
  "name": "GitHub MCP",
  "version": "1.0.0",
  "description": "通过 MCP 协议接入 GitHub API / GitHub API via MCP protocol",
  "type": "mcp",
  "entry": "mcp_config.json",
  "permissions": ["tools.register"],
  "category": "tool",
  "tags": ["github", "mcp", "git"]
}
```

---

## 校验 / Validation

宿主在加载时会校验清单文件：

The host validates the manifest at load time:

- 缺少必需字段 → 跳过并记录错误 / Missing required fields → skip with error
- `type` 不是 `python`/`mcp`/`skill` → 跳过 / Invalid `type` → skip
- `requires.openakita` 版本不兼容 → 跳过 / Incompatible version → skip
- `conflicts` 中的插件已加载 → 跳过 / Conflicting plugin loaded → skip

---

## 相关文档 / Related

- [getting-started.md](getting-started.md) — 最小 plugin.json 示例 / Minimal manifest example
- [permissions.md](permissions.md) — 权限字符串完整列表 / Full permission string catalog
