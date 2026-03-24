# WhatsApp 通道插件 / WhatsApp Channel Plugin

将 WhatsApp 接入 OpenAkita 作为 IM 通道。支持两种模式：

## 模式 A: Cloud API（企业版）

使用 Meta 官方 WhatsApp Cloud API，通过 HTTP REST + Webhook 收发消息。

**适用场景**：企业账号、正式商用  
**优点**：稳定、合规、无需 QR 扫码  
**配置**：在 Meta Developer Portal 创建应用，获取 Phone Number ID 和 Access Token

### 必填配置

| 参数 | 说明 |
|------|------|
| `mode` | 设为 `cloud_api` |
| `phone_number_id` | WhatsApp Business 手机号 ID |
| `access_token` | Graph API 永久访问令牌 |
| `verify_token` | Webhook 验证令牌（自定义字符串） |

## 模式 B: WhatsApp Web（个人版）

通过 Baileys（Node.js）连接 WhatsApp Web 协议，支持 QR 扫码链接个人账号。

**适用场景**：个人账号、测试环境  
**优点**：免费、支持 QR 扫码  
**要求**：需要安装 Node.js

### 配置

| 参数 | 说明 |
|------|------|
| `mode` | 设为 `web` |
| `node_path` | Node.js 可执行文件路径（默认 `node`） |
| `bridge_port` | Baileys bridge HTTP 端口（默认 9882） |

### 首次使用

1. 设置 `mode` 为 `web`
2. 启动 bot 后，在 IM 配置界面点击"扫码连接"
3. 用手机 WhatsApp 扫描 QR 码完成配对

## 功能

- 文本消息收发
- 图片、文件、语音、视频消息
- 群聊 / 私聊
- @提及检测
- 流式输出（累积后发送）
- 输入状态指示器

## 权限

- `channel.register` — 注册 WhatsApp 通道适配器
- `routes.register` — 注册 onboard API 端点（QR 扫码流程）
- `config.read/write` — 读写插件配置

---

# WhatsApp Channel Plugin

Connect WhatsApp to OpenAkita as an IM channel. Two modes are supported:

## Mode A: Cloud API (Business)

Uses Meta's official WhatsApp Cloud API via HTTP REST + Webhook.

**Use case**: Business accounts, production  
**Setup**: Create an app in Meta Developer Portal, get Phone Number ID and Access Token

## Mode B: WhatsApp Web (Personal)

Uses Baileys (Node.js) to connect via WhatsApp Web protocol with QR code pairing.

**Use case**: Personal accounts, testing  
**Requirements**: Node.js installed

## Features

- Text, image, file, voice, and video messages
- Group chat / DM support
- @mention detection
- Streaming output (accumulated batch send)
- Typing indicators
- QR code pairing (Web mode)
