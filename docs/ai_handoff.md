# Lumia ScriptorRAG AI / 开发者交接文档

生成时间：2026-07-06
作者：张春
说明：AI 根据项目文件、运行状态和迭代过程整理生成。

## 项目定位

Lumia ScriptorRAG｜序光文枢 RAG 不是单纯的 RAG 聊天页，也不是单引擎 OCR 工具，而是一条面向本地文档数字化的完整流水线：先做 OCR 智能体路由，再做 Markdown 排版清洗，最后进入可追溯的通用 RAG。

```text
输入资料 → 光棱 OCR → 字炉排版 → 文枢 RAG → 问答 / 导出 / API
```

## 当前运行状态

- 后端：FastAPI，默认 `http://127.0.0.1:8080/`。
- 前端：Vue3 + Vite + Naive UI，生产构建位于 `frontend/dist`。
- 本地启动脚本：`start.bat`、`stop.bat`、`tool.bat`。
- GitHub 私有仓库：`https://github.com/clementzhang29/lumia-scriptor-rag`。
- 本地目录：`C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0`，目录名暂不修改，避免破坏路径与缓存。

## 模块边界

| 模块 | 路径 | 说明 |
|---|---|---|
| 光棱 OCR 调度 | `src/orchestrator/` | 文档分析、引擎选择、Pipeline 编排、质量回退 |
| OCR 引擎适配 | `src/engines/` | Surya / MinerU / Docling / Marker / PaddleOCR / Nougat |
| 校正器 | `src/correctors/` | 表格、公式、阅读顺序校正，可接入 LLM |
| 质量评分 | `src/qa/` | 对 OCR Markdown 结果打分，低分触发回退 |
| 字炉排版 | `src/formatter/` | Markdown 清洗、标题/列表/空行/代码块规范化 |
| 文档导入 | `src/ingest/` | 解析 md/txt/html/pdf/epub/docx 为统一文档对象 |
| 知识源挂载 | `src/kb_mounts/` | 本地目录 / WebDAV / AList 挂载、同步、本地缓存 |
| 文枢 RAG | `src/rag/` | BM25 检索、来源去重、原典权重、fallback answer |
| LLM Provider | `src/llm/` | OpenAI 兼容、Anthropic、base_url 自动识别 |
| Web API | `src/web/app.py` | OCR、排版、RAG、Provider、SPA 静态页面 |
| Vue 前端 | `frontend/src/` | OCR、导览、排版、RAG、模型、帮助说明入口 |

## 已实现能力

- 六大 OCR 引擎封装：Surya、MinerU、Docling、Marker、PaddleOCR、Nougat。
- OCR API 工作流：上传 PDF → 后台任务 → 状态查询 → 质量评分 → Markdown 下载。
- Markdown 排版清洗接口：`POST /api/format/markdown`。
- RAG 建库与检索接口：`GET /api/rag/status`、`POST /api/rag/rebuild`、`POST /api/rag/query`。
- 外部知识源挂载接口：`GET /api/kb-sources`、`POST /api/kb-sources`、`POST /api/kb-sources/{id}/sync`、`POST /api/rag/rebuild-mounted`。
- LLM Provider 管理：注册、列表、删除、验证。
- LLM 模型中心：支持 Provider 持久化、模型目录读取、价格倍率展示、供应商名称隐藏。
- 前端产品化：精简顶部导航、服务状态、OCR 工作台、RAG 检索导出、Provider 配置、帮助说明。
- 知识源前端：新增“知识源”页面，可维护外部目录与云盘挂载，支持一键同步和挂载建库。
- 静态资源修复：FastAPI 已挂载 `/assets`，避免 JS 被 SPA fallback 返回 HTML 导致白屏。

## 运行命令

```powershell
py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info
cd frontend
npm run build
cd ..
py -3 -B -m compileall src
py -3 -B test_e2e.py
```

## 注意事项

- 不要把产品改成纯 RAG 聊天页；OCR 智能体是入口，RAG 是下游知识应用。
- 不要提交 API Key、模型文件、上传文件、日志、构建缓存或大型临时下载文件。
- 修改前端后必须执行 `npm run build`，后端默认服务 `frontend/dist`。
- 当前 LLM Provider 主要保存在内存中，生产化应增加加密落盘。
- Windows 上 MinerU / torch / GPU DLL 可能存在依赖冲突，必要时使用 CPU 降级。
- 挂载配置当前保存在本地 JSON，虽然 API 返回已做脱敏，但生产化仍建议引入加密存储和后台任务队列。
- 当前已接入两个默认模型入口：`gpt-main` 与 `omni-catalog`。其中 `omni-catalog` 可稳定读取 `/v1/models` 与 `/api/pricing`；`gpt-main` 可读取模型列表，但聊天调用受 Cloudflare / 源站稳定性影响，已配置自动回退到次入口。
