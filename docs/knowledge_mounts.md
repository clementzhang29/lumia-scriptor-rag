# Lumia ScriptorRAG 外部知识源挂载说明

生成时间：2026-07-08  
作者：张春  
说明：AI 根据当前项目代码与新增模块整理生成。

## 功能目标

“知识源挂载”用于把外部资料库接入当前产品，让 OCR 智能体之后的 RAG 不再只依赖单一本地目录，而是支持持续维护、多来源扩展与跨设备迁移。

核心链路：

```text
外部目录 / WebDAV / AList
  → 挂载源注册
  → 同步到本地缓存
  → DocumentParser 统一解析
  → UniversalRAGEngine 建立索引
  → 问答 / 引用 / 导出
```

## 当前支持的挂载类型

### 1. `local_dir`

- 适合本机已整理好的资料目录
- 配置字段：`root_path`
- 优点：简单、稳定、最快

### 2. `webdav`

- 兼容坚果云、Nextcloud、群晖、S3 网关等标准 WebDAV
- 配置字段：`base_url`、`root_path`、`username`、`password`
- 当前实现：`PROPFIND` 遍历目录，Basic Auth 鉴权

### 3. `alist`

- 兼容 AList 聚合云盘
- 配置字段：`base_url`、`root_path`、`token`、`password`
- 当前实现：`/api/fs/list` 列目录，`/d/...` 直接下载

## 支持的文档格式

- `.md`
- `.txt`
- `.html`
- `.htm`
- `.pdf`
- `.epub`
- `.docx`

## 后端实现位置

- 挂载管理器：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\src\kb_mounts\manager.py`
- API 接入：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\src\web\app.py`
- 文档解析：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\src\ingest\document_parser.py`
- RAG 索引：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\src\rag\engine.py`

## 前端实现位置

- 知识源页面：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\frontend\src\views\KnowledgeSources.vue`
- API 客户端：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\frontend\src\api.js`
- 路由：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\frontend\src\router.js`
- 顶部导航：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0\frontend\src\App.vue`

## API 一览

### 列出知识源

```http
GET /api/kb-sources
```

### 新建知识源

```http
POST /api/kb-sources
Content-Type: application/json

{
  "name": "中医古籍本地库",
  "type": "local_dir",
  "enabled": true,
  "config": {
    "root_path": "C:\\Users\\35160\\Desktop\\中医RAG系统\\data\\books"
  }
}
```

### 同步单个知识源

```http
POST /api/kb-sources/{id}/sync
```

### 同步所有启用的知识源

```http
POST /api/kb-sources/sync-all
```

### 从挂载缓存重建 RAG

```http
POST /api/rag/rebuild-mounted
Content-Type: application/json

{
  "source_ids": [],
  "sync_first": true
}
```

说明：

- `source_ids` 为空时，默认对所有已启用知识源生效
- `sync_first=true` 时，会先同步再建库

## 本地缓存机制

- 注册表：`%LOCALAPPDATA%\Lumia ScriptorRAG\kb_mounts\kb_sources.json`
- 缓存目录：`%LOCALAPPDATA%\Lumia ScriptorRAG\kb_mounts\mounts\<source-name>`
- 每个知识源单独维护 `.manifest.json`

缓存设计目的：

- 避免每次问答都直接访问远程云盘
- 降低网络波动对问答与建库的影响
- 允许离线重建索引

## 安全说明

- API 返回时会对 `password`、`token`、`api_key` 等字段做脱敏显示
- 编辑知识源时，若密码 / Token 留空，后端会保留原有密钥，不会被空值覆盖
- 当前配置仍以本地 JSON 形式维护，生产化建议进一步加密落盘
- 不建议把真实密钥提交进 Git

## 推荐使用方式

### 普通用户

1. 在“知识源”页面新增一个本地目录
2. 点击“同步”
3. 点击“从挂载知识源重建 RAG”
4. 在“文枢 RAG”中提问

### 面向云盘用户

1. 先用 WebDAV 或 AList 挂载远程资料
2. 让系统同步到本地缓存
3. 统一走本地缓存建库

### 面向二次开发

如果要扩展到更多商业云盘，例如 ima 或带开放接口的商用盘，建议沿用当前 provider 抽象：

- 在 `manager.py` 中新增一个 `BaseMountProvider` 子类
- 实现 `list_files()` 与 `download()`
- 把 provider 注册到 `KnowledgeMountManager.PROVIDERS`
- 前端只需补充类型说明与配置字段

## 已知边界

- 当前 WebDAV 仅实现 Basic Auth
- 当前同步逻辑为同步 API 调用，尚未做任务队列
- 大规模远程知识库建议先做分批同步和索引分层
- 后续如升级到万册级知识库，应进一步接入向量索引、章节图谱与 rerank

## 后续演进建议

1. 增加后台异步同步队列
2. 增加挂载健康检查与计划任务
3. 引入更细粒度的知识源权限与用户隔离
4. 挂载层直接产出章节级元数据，为 Graph-RAG 做准备
5. 扩展到对象存储、SMB/NAS、商业知识库 API

## 当前验证情况

- 已通过接口级冒烟：创建知识源 → 同步 → 挂载建库
- 已新增自动化测试：`tests/test_kb_mounts.py`
- 已验证本地目录挂载的缓存与索引链路可运行
