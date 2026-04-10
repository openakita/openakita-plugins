# 管理 REST API / Management REST API

所有插件管理端点的基础前缀为 `/api/plugins`。插件自身注册的路由前缀为 `/api/plugins/<plugin_id>/`。

All plugin management endpoints share the base prefix `/api/plugins`. Plugin-registered routes use prefix `/api/plugins/<plugin_id>/`.

---

## 插件查询 / Plugin Discovery

### `GET /api/plugins/list`

列出所有已发现的插件及其状态。同时触发磁盘扫描，自动发现新安装的插件。

List all discovered plugins and their states. Also triggers a disk scan to discover newly added plugins.

**响应 / Response:**

```json
{
  "ok": true,
  "plugins": [
    {
      "id": "hello-tool",
      "name": "Hello Tool",
      "version": "1.0.0",
      "type": "python",
      "status": "loaded",
      "enabled": true,
      "has_ui": false,
      "description": "...",
      "permissions": ["tools.register"],
      "granted_permissions": ["tools.register", "config.read", "..."]
    }
  ]
}
```

### `GET /api/plugins/ui-apps`

列出所有带有 UI 界面的插件（`plugin.json` 中含 `ui` 字段）。桌面端侧边栏使用此接口渲染"应用"列表。

List all plugins with a UI entry. The desktop sidebar uses this to render the "Apps" list.

**响应 / Response:**

```json
{
  "ok": true,
  "apps": [
    {
      "plugin_id": "seedance-video",
      "title": "Seedance 视频生成",
      "icon": "",
      "sidebar_group": "apps"
    }
  ]
}
```

### `GET /api/plugins/health`

插件系统健康检查。

Plugin system health check.

**响应 / Response:**

```json
{
  "ok": true,
  "loaded": 5,
  "failed": 0,
  "disabled": 1
}
```

---

## 安装与卸载 / Installation & Uninstallation

### `POST /api/plugins/install`

安装插件。支持多种来源：

Install a plugin from various sources:

**请求体 / Request Body:**

```json
{
  "source": "https://github.com/user/my-plugin",
  "auto_enable": true
}
```

**支持的 `source` 格式 / Supported source formats:**

| 格式 / Format | 说明 / Description |
|----------------|-------------------|
| `https://github.com/user/repo` | Git 仓库克隆 / Git clone |
| `https://github.com/user/repo/tree/branch/path` | Git 子目录 / Git subdirectory |
| `https://example.com/plugin.zip` | HTTP(S) 下载 ZIP / Download ZIP |
| `/local/path/to/plugin/` | 本地目录（含 `plugin.json`）/ Local directory |
| `bundle-name` | 跨生态包名 / Cross-ecosystem bundle name |

**响应 / Response:**

```json
{
  "ok": true,
  "install_id": "uuid",
  "plugin_id": "my-plugin",
  "message": "Installation started"
}
```

### `GET /api/plugins/install/progress/{install_id}`

SSE (Server-Sent Events) 流，实时推送安装进度。

SSE stream for real-time installation progress.

**事件格式 / Event format:**

```
data: {"stage": "downloading", "progress": 0.5, "message": "Cloning repository..."}
data: {"stage": "complete", "progress": 1.0, "plugin_id": "my-plugin"}
```

### `DELETE /api/plugins/{plugin_id}`

卸载并删除插件。

Uninstall and remove a plugin.

**响应 / Response:**

```json
{ "ok": true, "message": "Plugin uninstalled" }
```

---

## 启用与禁用 / Enable & Disable

### `POST /api/plugins/{plugin_id}/enable`

启用插件（加载并运行）。

Enable a plugin (loads and runs it).

### `POST /api/plugins/{plugin_id}/disable`

禁用插件（卸载但保留文件）。

Disable a plugin (unloads but keeps files).

### `POST /api/plugins/{plugin_id}/reload`

热重载插件（先卸载再加载）。

Hot-reload a plugin (unload then load).

---

## 配置管理 / Configuration

### `GET /api/plugins/{plugin_id}/config`

读取插件当前配置。

Read the plugin's current configuration.

**响应 / Response:**

```json
{ "ok": true, "data": { "api_key": "sk-***", "model": "v3" } }
```

### `PUT /api/plugins/{plugin_id}/config`

更新插件配置（合并更新，非覆盖）。

Update plugin config (merge update, not overwrite).

**请求体 / Request Body:** 任意 JSON 对象 / Any JSON object

```json
{ "api_key": "sk-new-key", "timeout": 30 }
```

**JSON Schema 校验 / JSON Schema Validation:**

如果插件目录中存在 `config_schema.json`，配置更新时会用 `jsonschema` 校验。校验失败返回 `422`。

If a `config_schema.json` exists in the plugin directory, config updates are validated against it. Validation failure returns `422`.

**配置变更钩子 / Config Change Hook:**

配置保存成功后，宿主会触发 `on_config_change` 钩子。

After a successful save, the host dispatches the `on_config_change` hook.

### `GET /api/plugins/{plugin_id}/schema`

获取插件的配置 JSON Schema（如果存在）。

Get the plugin's config JSON Schema (if available).

---

## 权限管理 / Permission Management

### `GET /api/plugins/{plugin_id}/permissions`

获取插件的权限状态。

Get the plugin's permission state.

**响应 / Response:**

```json
{
  "ok": true,
  "requested": ["brain.access", "routes.register"],
  "granted": ["brain.access"],
  "pending": ["routes.register"]
}
```

### `POST /api/plugins/{plugin_id}/permissions/grant`

批准插件权限。

Grant permissions to a plugin.

**请求体 / Request Body:**

```json
{ "permissions": ["routes.register", "brain.access"] }
```

### `POST /api/plugins/{plugin_id}/permissions/revoke`

撤销插件权限。

Revoke permissions from a plugin.

**请求体 / Request Body:**

```json
{ "permissions": ["brain.access"] }
```

---

## 信息查询 / Information

### `GET /api/plugins/{plugin_id}/readme`

获取插件 README 内容（Markdown 文本）。

Get the plugin's README content (Markdown text).

### `GET /api/plugins/{plugin_id}/icon`

获取插件图标文件。

Get the plugin's icon file.

### `GET /api/plugins/{plugin_id}/logs`

获取插件最近的日志输出（最后 200 行）。

Get the plugin's recent log output (last 200 lines).

### `GET /api/plugins/{plugin_id}/export`

导出插件为 ZIP 文件。

Export the plugin as a ZIP file.

### `POST /api/plugins/{plugin_id}/open-folder`

在系统文件管理器中打开插件目录。

Open the plugin directory in the system file manager.

---

## 插件市场 / Plugin Hub

### `GET /api/plugins/hub/categories`

获取市场分类列表。

Get marketplace category list.

### `GET /api/plugins/hub/search`

搜索市场插件。

Search marketplace plugins.

**查询参数 / Query params:** `q` (搜索关键词 / search query), `category` (分类 / category)

### `GET /api/plugins/updates`

检查已安装插件的可用更新。

Check for available updates for installed plugins.

### `POST /api/plugins/{plugin_id}/update`

更新插件到最新版本。

Update a plugin to the latest version.

---

## 错误响应 / Error Responses

所有错误使用统一格式：

All errors use a consistent format:

```json
{
  "ok": false,
  "error": {
    "code": "PLUGIN_NOT_FOUND",
    "message": "Plugin 'my-plugin' not found"
  }
}
```

**错误码 / Error Codes:**

| 错误码 / Code | HTTP 状态 / Status | 说明 / Description |
|---------------|--------------------|-------------------|
| `PLUGIN_NOT_FOUND` | 404 | 插件不存在 / Plugin not found |
| `PLUGIN_ALREADY_EXISTS` | 409 | 插件已安装 / Plugin already installed |
| `PLUGIN_LOAD_FAILED` | 500 | 加载失败 / Load failed |
| `PLUGIN_DISABLED` | 409 | 插件已禁用 / Plugin is disabled |
| `MANIFEST_INVALID` | 422 | 清单文件格式错误 / Invalid manifest |
| `PERMISSION_DENIED` | 403 | 权限不足 / Insufficient permissions |
| `INSTALL_FAILED` | 500 | 安装失败 / Installation failed |
| `CONFIG_VALIDATION_FAILED` | 422 | 配置校验失败 / Config validation failed |

---

## 插件自身路由 / Plugin-Registered Routes

插件通过 `api.register_api_routes(router)` 注册的路由统一挂载在：

Plugin routes registered via `api.register_api_routes(router)` are mounted at:

```
/api/plugins/<plugin_id>/<your-route>
```

例如，Seedance 插件注册 `/tasks` 路由，最终可通过 `GET /api/plugins/seedance-video/tasks` 访问。

For example, the Seedance plugin registers `/tasks`, accessible at `GET /api/plugins/seedance-video/tasks`.

---

## 安全限制 / Security Limits

- ZIP 安装时有文件大小和数量上限，防止 zip bomb / ZIP installation has size and count limits
- ZIP 解压有 zip slip 防护（拒绝 `..` 路径遍历）/ Zip slip protection (rejects `..` path traversal)
- Git URL 仅支持 `https://` 协议 / Git URLs only support `https://`
- 安装操作有全局互斥锁，防止并发冲突 / Installation has a global mutex lock

---

## 相关文档 / Related

- [api-reference.md](api-reference.md) — 插件 Python API / Plugin Python API
- [permissions.md](permissions.md) — 权限模型 / Permission model
- [plugin-json.md](plugin-json.md) — 清单文件格式 / Manifest format
- [plugin-ui.md](plugin-ui.md) — UI 插件开发 / UI plugin development
