# 权限模型 / Permission Model

OpenAkita 插件使用**三级权限模型**控制对系统资源的访问。插件必须在 `plugin.json` 的 `permissions` 数组中声明所需权限。

OpenAkita plugins use a **three-tier permission model** to control access to system resources. Plugins must declare required permissions in the `permissions` array of `plugin.json`.

---

## 总览 / Overview

| 级别 / Tier | 授权方式 / Approval | 能力范围 / Scope |
|-------------|---------------------|-----------------|
| **Basic** | 安装即有 / Auto-granted | 日志、自有配置/数据、工具注册、基础钩子 / Logging, own config/data, tools, basic hooks |
| **Advanced** | 用户确认 / User consent | 通道、记忆读写、检索源、路由、消息发送、宿主服务访问、消息/检索钩子 / Channels, memory R/W, retrieval, routes, messaging, host access, message/retrieve hooks |
| **System** | 手动确认 / Manual approval | LLM 注册、记忆替换、全钩子、系统配置写入 / LLM registration, memory replacement, all hooks, system config |

---

## 权限清单 / Permission Catalog

### Basic 级

| 权限 ID / Permission | API 方法 / API Method | 风险 / Risk |
|---------------------|----------------------|------------|
| `log` | `log()`, `log_error()`, `log_debug()` | 低 / Low — 写日志 |
| `config.read` | `get_config()` | 低 / Low — 读取本插件配置 |
| `config.write` | `set_config()` | 低 / Low — 写入本插件配置 |
| `data.own` | `get_data_dir()` | 低 / Low — 本插件数据目录 |
| `tools.register` | `register_tools()` | 中 / Medium — 新工具影响 AI 行为 |
| `hooks.basic` | `register_hook("on_init" / "on_shutdown" / "on_schedule")` | 低 / Low — 生命周期钩子 |

### Advanced 级

安装时会向用户显示风险提示。

Risk prompts are shown to users during installation.

| 权限 ID / Permission | API 方法 / API Method | 用户提示 / User Prompt |
|---------------------|----------------------|----------------------|
| `channel.register` | `register_channel()` | "此插件将添加新的消息通道 / This plugin will add a new messaging channel" |
| `channel.send` | `send_message()` | "此插件可以通过 IM 发送消息 / This plugin can send messages via IM" |
| `memory.read` | `get_memory_manager()` 只读 / read-only | "此插件可以读取对话记忆 / This plugin can read conversation memory" |
| `memory.write` | `get_memory_manager()` 写入 / write | "此插件可以修改记忆数据 / This plugin can modify memory data" |
| `vector.access` | `get_vector_store()` | "此插件可以访问向量数据库 / This plugin can access the vector database" |
| `brain.access` | `get_brain()` | "此插件可以直接调用 AI 模型 / This plugin can directly invoke AI models" |
| `settings.read` | `get_settings()` | "此插件可以读取系统配置 / This plugin can read system settings" |
| `search.register` | `register_search_backend()` | "此插件将添加搜索引擎后端 / This plugin will add a search backend" |
| `retrieval.register` | `register_retrieval_source()` | "此插件将添加知识检索来源 / This plugin will add a retrieval source" |
| `routes.register` | `register_api_routes()` | "此插件将添加网络接口 / This plugin will add HTTP endpoints" |
| `hooks.message` | `on_message_received`, `on_message_sending`, `on_session_start`, `on_session_end` | "此插件可以拦截和观察消息 / This plugin can intercept and observe messages" |
| `hooks.retrieve` | `on_retrieve`, `on_tool_result`, `on_prompt_build` | "此插件可以向 AI 注入上下文 / This plugin can inject context into AI prompts" |

### System 级

| 权限 ID / Permission | API 方法 / API Method | 说明 / Description |
|---------------------|----------------------|-------------------|
| `llm.register` | `register_llm_provider()`, `register_llm_registry()` | 注册新的 LLM 提供商 / Register new LLM providers |
| `hooks.all` | 所有 10 个钩子 / all 10 hooks | 完整钩子访问权 / Full hook access |
| `memory.replace` | `register_memory_backend()` 替换模式 / replace mode | 替换内置记忆系统 / Replace built-in memory |
| `system.config.write` | — | 写入全局系统配置 / Write global system config |

---

## 声明权限 / Declaring Permissions

在 `plugin.json` 中声明最小必要权限集：

Declare the minimal required permission set in `plugin.json`:

```json
{
  "id": "my-plugin",
  "permissions": [
    "tools.register",
    "hooks.basic",
    "config.read",
    "channel.send"
  ]
}
```

**最佳实践 / Best Practices:**
- 只声明实际需要的权限 / Only declare what you actually need
- 权限越少，用户信任越高 / Fewer permissions = higher user trust
- Basic 权限无需用户确认，优先使用 / Basic permissions need no approval, prefer them

---

## 授权流程 / Approval Flow

```
1. 读取 plugin.json 的 permissions 列表
   Read permissions list from plugin.json
       ↓
2. Basic 权限自动授予
   Basic permissions auto-granted
       ↓
3. Advanced 权限：弹窗/CLI 提示用户确认
   Advanced permissions: UI/CLI prompt for user consent
       ↓
4. System 权限：需要手动在设置中确认
   System permissions: require manual approval in settings
       ↓
5. 已授权权限持久化到 data/plugin_state.json
   Granted permissions persisted to data/plugin_state.json
       ↓
6. 运行时每次 API 调用检查权限
   Runtime permission check on every API call
```

---

## 权限不足时的行为 / Behavior When Permission Denied

```python
# 如果未声明 channel.send，调用 send_message 会抛出：
# If channel.send is not declared, calling send_message raises:
# PluginPermissionError: Plugin 'my-plugin' requires permission 'channel.send'
#                        which was not granted. Add it to plugin.json permissions.
```

**建议 / Recommendation:** 插件应优雅降级 — 如果某个功能的权限被拒绝，记录日志并禁用该功能，而不是让整个插件崩溃。

Plugins should degrade gracefully — if a feature's permission is denied, log it and disable that feature rather than crashing the entire plugin.

---

## 相关文档 / Related

- [api-reference.md](api-reference.md) — 每个方法对应的权限 / Permission for each method
- [hooks.md](hooks.md) — 每个钩子对应的权限 / Permission for each hook
- [plugin-json.md](plugin-json.md) — `permissions` 字段格式 / permissions field format
