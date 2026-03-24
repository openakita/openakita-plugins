# 贡献指南 / Contributing Guide

[中文](#中文) | [English](#english)

<a id="中文"></a>

## 中文

感谢你有兴趣为 OpenAkita 插件生态做贡献！

### 提交插件

1. Fork 本仓库
2. 在 `plugins/` 下创建你的插件目录
3. 确保包含以下文件：
   - `plugin.json` — 清单文件（必需）
   - `plugin.py` — 入口代码（Python 插件必需）
   - `README.md` — 中英文文档
   - `config_schema.json` — 配置 schema（如有可配置项）
   - `icon.png` 或 `icon.svg` — 图标（建议 128x128px）
4. 提交 Pull Request

### 插件规范

#### plugin.json 必要字段

```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "description": "What this plugin does",
  "author": "Your Name",
  "license": "MIT",
  "type": "python",
  "entry": "plugin.py",
  "permissions": ["tools.register"],
  "requires": {
    "openakita": ">=1.5.0",
    "plugin_api": "~1",
    "python": ">=3.11"
  },
  "category": "tool",
  "tags": ["keyword1", "keyword2"]
}
```

#### 权限级别

- **Basic**（无需审批）：`tools.register`, `log`, `data.own`, `hooks.basic`, `config.read`, `config.write`, `skill`
- **Advanced**（需用户授权）：`channel.register`, `channel.send`, `memory.read`, `memory.write`, `llm.register`, `hooks.message`, `hooks.retrieve`, `retrieval.register`, `search.register`, `routes.register`, `brain.access`, `vector.access`, `settings.read`
- **System**（需用户授权）：`memory.replace`, `hooks.all`, `system.config.write`

#### 质量要求

- [ ] `plugin.json` 格式正确，`id` 全局唯一
- [ ] 所有权限在 `permissions` 中声明
- [ ] 包含中英文 `README.md`
- [ ] 异常处理完善，不会导致宿主崩溃
- [ ] 无硬编码密钥/凭证

---

<a id="english"></a>

## English

Thanks for your interest in contributing to the OpenAkita plugin ecosystem!

### Submitting a Plugin

1. Fork this repository
2. Create your plugin directory under `plugins/`
3. Ensure it includes:
   - `plugin.json` — Manifest (required)
   - `plugin.py` — Entry point (required for Python plugins)
   - `README.md` — Bilingual documentation
   - `config_schema.json` — Config schema (if configurable)
   - `icon.png` or `icon.svg` — Icon (128x128px recommended)
4. Submit a Pull Request

### Quality Checklist

- [ ] Valid `plugin.json` with globally unique `id`
- [ ] All permissions declared in `permissions` array
- [ ] Bilingual `README.md` included
- [ ] Proper error handling (must not crash the host)
- [ ] No hardcoded secrets or credentials
