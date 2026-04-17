# Discord Channel Plugin / Discord 通道插件

[中文](#中文) | [English](#english)

<a id="中文"></a>

## 中文

将 OpenAkita 接入 Discord，通过 Discord Bot API 实现消息收发。

### 功能特性

- **服务器频道 + 私聊**：支持 Guild 文本频道和 DM 私聊
- **@提及触发**：在服务器中仅在被 @mention 时回复（可配置）
- **消息流式输出**：利用 Discord 的消息编辑功能实现打字机效果（edit-in-place）
- **多媒体支持**：图片、文件、视频的收发
- **帖子/线程支持**：自动识别 Thread 消息
- **消息管理**：删除、编辑已发送的消息
- **Markdown 格式**：原生 Discord Markdown 渲染
- **灵活过滤**：按 Guild ID、Channel ID 过滤监听范围
- **长消息自动拆分**：超过 2000 字符自动拆分发送

### 前置准备

1. 前往 [Discord Developer Portal](https://discord.com/developers/applications) 创建应用
2. 在 **Bot** 页面创建 Bot，获取 **Bot Token**
3. 开启以下 **Privileged Gateway Intents**：
   - `MESSAGE CONTENT INTENT` — 必需，用于读取消息内容
   - `SERVER MEMBERS INTENT` — 推荐，用于获取成员信息
4. 使用 OAuth2 URL 将 Bot 邀请到你的服务器（需要 `bot` 和 `applications.commands` scope）
5. Bot 权限建议：`Send Messages`、`Read Message History`、`Attach Files`、`Embed Links`、`Manage Messages`

### 安装

```bash
# 安装依赖
pip install discord.py>=2.3.0

# 将插件目录复制到 OpenAkita 的 data/plugins/ 下
# 或在设置中心添加插件路径
```

### 配置

在 OpenAkita 的 IM 通道配置中添加：

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "credentials": {
        "bot_token": "your-bot-token-here",
        "allowed_guild_ids": ["123456789"],
        "respond_to_mentions_only": true,
        "respond_to_dms": true,
        "status_message": "Powered by OpenAkita"
      }
    }
  }
}
```

也可通过环境变量设置：

```bash
export DISCORD_BOT_TOKEN="your-bot-token-here"
```

### 配置项说明

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `bot_token` | string | (必填) | Discord Bot Token |
| `application_id` | string | — | Discord Application ID |
| `allowed_guild_ids` | string[] | [] | 允许响应的服务器 ID 列表，空 = 全部 |
| `allowed_channel_ids` | string[] | [] | 允许监听的频道 ID 列表，空 = 全部 |
| `respond_to_dms` | bool | true | 是否响应私聊消息 |
| `respond_to_mentions_only` | bool | true | 在服务器中是否仅在 @mention 时回复 |
| `command_prefix` | string | "" | 传统命令前缀（如 `!`），留空禁用 |
| `streaming_throttle_ms` | int | 1500 | 流式编辑最小间隔（毫秒） |
| `max_message_length` | int | 2000 | 单条消息最大长度（Discord 限制 2000） |
| `status_message` | string | "Powered by OpenAkita" | Bot 活动状态消息 |

### 使用方式

- **私聊**：直接给 Bot 发消息即可
- **服务器**：@Bot 发消息，或回复 Bot 的消息
- **命令**：如设置了 command_prefix，可用 `!ask 问题` 形式

---

<a id="english"></a>

## English

Connect OpenAkita to Discord via the official Bot API.

### Features

- **Guild channels + DMs**: text channels, threads, and direct messages
- **@mention trigger**: only responds when mentioned in guild channels (configurable)
- **Streaming output**: edit-in-place typewriter effect using Discord's message editing
- **Media support**: send and receive images, files, and videos
- **Thread support**: automatic thread detection and routing
- **Message management**: delete and edit sent messages
- **Markdown rendering**: native Discord Markdown
- **Flexible filtering**: filter by Guild ID or Channel ID
- **Auto-split long messages**: automatically splits messages exceeding 2000 characters

### Prerequisites

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications) and create an application
2. Create a Bot in the **Bot** section and copy the **Bot Token**
3. Enable the following **Privileged Gateway Intents**:
   - `MESSAGE CONTENT INTENT` — required for reading message content
   - `SERVER MEMBERS INTENT` — recommended for member info
4. Invite the Bot to your server using the OAuth2 URL (scopes: `bot`, `applications.commands`)
5. Recommended bot permissions: `Send Messages`, `Read Message History`, `Attach Files`, `Embed Links`, `Manage Messages`

### Installation

```bash
# Install dependencies
pip install discord.py>=2.3.0

# Copy the plugin directory to OpenAkita's data/plugins/
# Or add the plugin path in the Setup Center
```

### Configuration

Add to your OpenAkita IM channel configuration:

```json
{
  "channels": {
    "discord": {
      "enabled": true,
      "credentials": {
        "bot_token": "your-bot-token-here",
        "allowed_guild_ids": ["123456789"],
        "respond_to_mentions_only": true,
        "respond_to_dms": true,
        "status_message": "Powered by OpenAkita"
      }
    }
  }
}
```

Or set via environment variable:

```bash
export DISCORD_BOT_TOKEN="your-bot-token-here"
```

### Configuration Reference

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `bot_token` | string | (required) | Discord Bot Token |
| `application_id` | string | — | Discord Application ID |
| `allowed_guild_ids` | string[] | [] | Guild IDs to respond in. Empty = all |
| `allowed_channel_ids` | string[] | [] | Channel IDs to listen to. Empty = all |
| `respond_to_dms` | bool | true | Whether to respond to direct messages |
| `respond_to_mentions_only` | bool | true | Only respond when @mentioned in guilds |
| `command_prefix` | string | "" | Legacy command prefix (e.g. `!`). Empty = disabled |
| `streaming_throttle_ms` | int | 1500 | Min interval (ms) between streaming edits |
| `max_message_length` | int | 2000 | Max chars per message (Discord limit: 2000) |
| `status_message` | string | "Powered by OpenAkita" | Bot activity status |

### Usage

- **DMs**: Simply send a message to the Bot
- **Guild channels**: @mention the Bot, or reply to one of its messages
- **Commands**: If `command_prefix` is set, use `!ask question` format

## License

MIT
