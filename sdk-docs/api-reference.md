# PluginAPI 参考 / PluginAPI Reference

`PluginAPI` 是插件与宿主系统交互的唯一接口。SDK 提供抽象定义用于类型提示，运行时由宿主注入具体实现。

`PluginAPI` is the sole interface for plugins to interact with the host. The SDK provides the abstract definition for typing; the runtime injects the concrete implementation.

```python
from openakita_plugin_sdk import PluginAPI
```

方法按**权限级别**分组。未声明权限的调用会被宿主**静默跳过**（记录 warning 日志，注册类方法不执行注册，`get_*` 类方法返回 `None`），插件继续运行。

Methods are grouped by **permission tier**. Calls without the required permission are **silently skipped** (warning logged, register methods do nothing, `get_*` methods return `None`), and the plugin continues running.

---

## Basic 级 / Basic Tier

安装即有，无需用户确认。

Auto-granted on install, no user approval needed.

### 日志 / Logging

```python
api.log("消息内容")                          # info 级别
api.log("warning message", "warning")        # warning 级别
api.log_error("错误描述", exception)          # error 级别，附带异常堆栈
api.log_debug("调试信息")                     # debug 级别
```

> **最佳实践 / Best Practice:** 始终使用 `api.log()` 而不是 `print()` 或 `logging.getLogger()`。插件日志会写入独立的日志文件 `<plugin_dir>/logs/<plugin_id>.log`，支持日志轮转。
>
> Always use `api.log()` instead of `print()` or `logging.getLogger()`. Plugin logs go to a dedicated rotated log file.

### 配置 / Configuration

```python
# 读取插件配置 / Read plugin config
cfg = api.get_config()        # 返回 dict / returns dict
token = cfg.get("api_key")

# 写入插件配置（合并更新）/ Write plugin config (merge update)
api.set_config({"api_key": "sk-xxx", "last_sync": "2026-03-22"})
```

权限 / Permission: `config.read`, `config.write`

### 数据目录 / Data Directory

```python
data_dir = api.get_data_dir()  # 返回 pathlib.Path / returns pathlib.Path
db_path = data_dir / "cache.sqlite"
```

权限 / Permission: `data.own`

### 工具注册 / Tool Registration

```python
from openakita_plugin_sdk.tools import tool_definition

TOOLS = [
    tool_definition(
        name="search_notes",
        description="搜索用户笔记 / Search user notes",
        parameters={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词 / Search keyword"},
            },
            "required": ["query"],
        },
    ),
]

async def handler(tool_name: str, arguments: dict) -> str:
    """处理函数签名：(tool_name, arguments) -> str"""
    if tool_name == "search_notes":
        return f"Results for: {arguments['query']}"
    return ""

api.register_tools(TOOLS, handler)
```

权限 / Permission: `tools.register`

**注意 / Notes:**
- 工具定义使用 OpenAI 格式（`type: "function"` + `function.name`）
- Tool definitions use OpenAI format (`type: "function"` + `function.name`)
- 没有 `name` 字段的定义会被静默跳过 / Definitions without a `name` field are silently skipped
- `handler` 接收所有工具调用，通过 `tool_name` 分发 / `handler` receives all tool calls, dispatch by `tool_name`

### 基础钩子注册 / Basic Hook Registration

```python
async def on_init(**kwargs):
    api.log("插件初始化完成 / Plugin initialized")

api.register_hook("on_init", on_init)
api.register_hook("on_shutdown", on_shutdown_fn)
```

权限 / Permission: `hooks.basic`（仅限 `on_init`、`on_shutdown`、`on_schedule` / only for these three hooks）

---

## Advanced 级 / Advanced Tier

需要用户确认授权。

Requires user approval.

### 通道注册 / Channel Registration

```python
from openakita_plugin_sdk.channel import ChannelAdapter

class WhatsAppAdapter(ChannelAdapter):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def send_message(self, message) -> str: ...
    async def send_text(self, chat_id: str, text: str, **kwargs) -> str: ...

def factory(creds, *, channel_name, bot_id, agent_profile_id):
    return WhatsAppAdapter(creds)

api.register_channel("whatsapp", factory)
```

权限 / Permission: `channel.register`

### 消息发送 / Send Message

```python
api.send_message("telegram", "chat_12345", "来自插件的消息 / Message from plugin")
```

权限 / Permission: `channel.send`

> 内部使用 fire-and-forget 模式，发送失败会记录日志但不抛出异常。
>
> Uses fire-and-forget internally; failures are logged but do not raise exceptions.

### 检索源注册 / Retrieval Source Registration

```python
class ObsidianRetriever:
    source_name = "obsidian"

    async def retrieve(self, query: str, limit: int = 5) -> list[dict]:
        return [{"content": "...", "score": 0.9, "source": "vault/note.md"}]

api.register_retrieval_source(ObsidianRetriever())
```

权限 / Permission: `retrieval.register`

### 搜索后端注册 / Search Backend Registration

```python
api.register_search_backend("pinecone", PineconeBackend())
```

权限 / Permission: `search.register`

### API 路由注册 / API Route Registration

```python
from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def status():
    return {"healthy": True}

api.register_api_routes(router)
# 挂载到 /api/plugins/<plugin_id>/status
# Mounted at /api/plugins/<plugin_id>/status
```

权限 / Permission: `routes.register`

### 消息/检索钩子注册 / Message & Retrieval Hook Registration

```python
async def on_message_received(**kwargs):
    text = kwargs.get("text", "")
    channel = kwargs.get("channel", "")
    api.log(f"收到消息 / Got message from {channel}: {text[:50]}")

api.register_hook("on_message_received", on_message_received)
```

权限 / Permission: `hooks.message`（消息类钩子）或 `hooks.retrieve`（检索类钩子）

详见 [hooks.md](hooks.md)。See [hooks.md](hooks.md) for full hook reference.

### LLM 提供商注册 / LLM Provider Registration

双重注册机制：协议类 + 厂商目录。

Dual registration: protocol class + vendor catalog.

```python
from openakita_plugin_sdk.llm import LLMProvider, ProviderRegistry, ProviderRegistryInfo

class OllamaProvider(LLMProvider):
    def __init__(self, config) -> None:
        self.base_url = config.base_url

    async def chat(self, messages: list[dict], **kwargs):
        ...

    async def chat_stream(self, messages: list[dict], **kwargs):
        ...

class OllamaRegistry(ProviderRegistry):
    def list_models(self) -> list[dict]:
        return [{"id": "llama3", "name": "Llama 3"}]

api.register_llm_provider("ollama_native", OllamaProvider)
api.register_llm_registry("ollama", OllamaRegistry(ProviderRegistryInfo(
    slug="ollama",
    name="Ollama",
    api_type="ollama_native",
    default_base_url="http://localhost:11434",
    api_key_env="OLLAMA_API_KEY",
)))
```

权限 / Permission: `llm.register`

### 宿主服务访问 / Host Service Access

```python
brain = api.get_brain()              # 权限 / perm: brain.access
memory = api.get_memory_manager()    # 权限 / perm: memory.read
vector = api.get_vector_store()      # 权限 / perm: vector.access
settings = api.get_settings()        # 权限 / perm: settings.read
```

> 返回宿主内部对象的引用。请仅使用宿主文档中记录的公开 API，不要访问私有属性。
>
> Returns references to host internal objects. Only use publicly documented APIs; do not access private attributes.

---

## System 级 / System Tier

需要明确的手动确认，通常仅限内置插件或高度受信任的第三方插件。

Requires explicit manual approval; typically for built-in or highly trusted plugins.

### 记忆后端替换 / Memory Backend Replacement

```python
api.register_memory_backend(QdrantMemoryBackend())
```

权限 / Permission: `memory.replace`

当使用 `memory.replace` 权限时，插件提供的记忆后端将**替换**内置记忆系统。如果只使用 `memory.write` 权限，则为**附加**模式。

With `memory.replace` permission, the plugin's memory backend **replaces** the built-in system. With `memory.write`, it's **additive**.

### 全钩子访问 / Full Hook Access

```python
api.register_hook("on_schedule", scheduled_task)  # hooks.basic 权限
```

权限 / Permission: `hooks.all`

---

## 相关类型 / Related Types

| 名称 / Name | 模块 / Module | 用途 / Purpose |
|-------------|--------------|----------------|
| `PluginBase` | `openakita_plugin_sdk` | 插件入口基类 / Plugin entry class |
| `PluginManifest` | `openakita_plugin_sdk` | 清单数据类 / Manifest dataclass |
| `tool_definition()` | `openakita_plugin_sdk.tools` | 工具定义构建器 / Tool definition builder |
| `ToolHandler` | `openakita_plugin_sdk.tools` | 工具处理基类 / Tool handler base |
| `ChannelAdapter` | `openakita_plugin_sdk.channel` | 通道适配器基类 / Channel adapter base |
| `LLMProvider` | `openakita_plugin_sdk.llm` | LLM 提供商基类 / LLM provider base |
| `MemoryBackendProtocol` | `openakita_plugin_sdk.protocols` | 记忆后端协议 / Memory backend protocol |
| `RetrievalSource` | `openakita_plugin_sdk.protocols` | 检索源协议 / Retrieval source protocol |
| `SearchBackend` | `openakita_plugin_sdk.protocols` | 搜索后端协议 / Search backend protocol |
| `MockPluginAPI` | `openakita_plugin_sdk.testing` | 测试用模拟 / Test mock |
| `HOOK_NAMES` | `openakita_plugin_sdk.hooks` | 有效钩子名集合 / Valid hook names |
| `HOOK_SIGNATURES` | `openakita_plugin_sdk.hooks` | 钩子回调签名参考 / Hook callback signature reference |
| `UnifiedMessage` | `openakita_plugin_sdk.types` | 统一消息类型 / Unified message type |
