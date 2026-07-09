# Lumia 技术融合评估与落地方案

生成时间：2026-07-06  
来源：`C:\Users\35160\Desktop\lumiasystem.htm` 与当前 `Lumia ScriptorRAG` 项目代码对照。

## 结论

Lumia 文档描述的是一个“多工具 AI Agent 操作系统”架构：以 LLM Function Calling 为调度入口，通过 ToolRouter 统一调度文档、网页、生成、股票、记忆等工具。

Lumia ScriptorRAG 当前已经具备“文档智能处理产品”的主链路：

```text
PDF/文档输入 -> 光棱 OCR 路由 -> 字炉 Markdown 排版 -> 文枢 RAG 建库/问答 -> WebUI/API 导出
```

两者可以融合，但不建议把 Lumia ScriptorRAG 改成泛聊天机器人。更合适的定位是：

```text
Lumia ScriptorRAG = 序光品牌下的文档智能体与文枢 RAG 产品底座
Lumia ToolRouter = 产品中的 Agent 调度层 / 工具编排层
```

## 已经落地的能力

| Lumia 模块 | Lumia ScriptorRAG 当前状态 | 对应位置 |
|---|---|---|
| RESTful API | 已实现 | `src/web/app.py` |
| LLM Provider 抽象 | 已实现基础版 | `src/llm/` |
| 文档处理 | 已实现 OCR + 多格式解析 | `src/orchestrator/`, `src/engines/`, `src/ingest/` |
| Markdown 整理 | 已实现 | `src/formatter/markdown_cleaner.py` |
| RAG 检索 | 已实现 BM25 版 | `src/rag/engine.py` |
| WebUI | 已实现 Vue3 页面 | `frontend/src/views/` |
| 工具分模块 | 已有模块边界，但未统一 ToolRouter | `src/*` |

## 尚未落地或只部分落地

| Lumia 模块 | 当前缺口 | 建议 |
|---|---|---|
| ToolRouter / Function Calling | 没有统一工具注册、JSON Schema、tool_call 执行闭环 | 新增 `src/agent/tool_router.py` |
| MemoryEngine 五层记忆 | 暂无用户/项目/偏好/经验记忆系统 | 新增 `src/memory/`，先 SQLite/JSON，后续向量化 |
| Agent Documents | 当前是文件解析/RAG，不是可编辑文档库 | 新增 `src/documents/`，支持 CRUD 与节点级编辑 |
| Web Browsing | 暂无网页搜索/爬取 API | 新增 `src/tools/web_browsing.py`，先单页抓取，搜索后接入可配置 provider |
| 图片/视频/音乐生成 | 项目已有 gpt-image skill 使用痕迹，但产品后端未统一封装 | 作为可选工具模块，不影响 OCR 主线 |
| 股票查询 | 与 Lumia ScriptorRAG 主产品弱相关 | 建议插件化，不作为第一阶段 |
| Artifacts/HTML 可视化组件 | 已有 HTML 项目介绍和 Vue UI，但无统一 Artifact 生成接口 | 可在导出中心扩展 |

## 推荐融合架构

```text
用户 / WebUI / API
      |
      v
AgentController
      |
      +-- ToolRouter
             |
             +-- OCR Tools: convert_pdf, list_engines, get_result
             +-- Format Tools: clean_markdown
             +-- RAG Tools: rebuild_index, query_knowledge
             +-- Document Tools: create/read/update/list documents
             +-- Provider Tools: add/list/verify providers
             +-- Memory Tools: remember/search/update preferences
             +-- Web Tools: crawl_url/search_web
```

## 第一阶段落地范围

优先做与当前产品强相关的 Agent 化改造：

1. 新增 `src/agent/tool_router.py`：统一工具注册、参数校验、执行、错误返回。
2. 新增 `src/agent/tools.py`：把现有 OCR、Formatter、RAG、Provider 包装成工具。
3. 新增 `POST /api/agent/tools`：列出可用工具与 JSON Schema。
4. 新增 `POST /api/agent/run`：支持自然语言意图或显式 tool 调用。
5. 新增 `src/memory/engine.py`：先做项目记忆、用户偏好、经验沉淀三类记忆。
6. 前端新增 “Agent 工作台”：展示光棱 OCR、文枢 RAG、字炉排版、星轨模型工具按钮、执行流、结果卡片。

## 第二阶段落地范围

1. Agent Documents 文档库：文档 CRUD、版本、节点级编辑。
2. Web Browsing：网页抓取、网页转 Markdown、网页资料加入 RAG。
3. Artifacts 导出：检索结果导出为 HTML/MD/PNG，OCR 报告导出为 HTML。
4. Tool Calling 与 LLM 深度集成：OpenAI compatible / Z.ai / GLM / Claude 工具调用适配。

## 第三阶段落地范围

1. 图片/视频/音乐生成作为插件市场能力。
2. 股票查询等垂直工具作为可选插件。
3. 向量数据库替换或增强 BM25：Hybrid Search = BM25 + Embedding + rerank。
4. 多 Agent 流水线：OCR Agent、Formatter Agent、Knowledge Agent、Research Agent。

## 注意事项

- Lumia ScriptorRAG 的核心定位仍应是“文档智能体”，Lumia 能力应作为工具调度层增强，而不是替换光棱 OCR / 字炉排版 / 文枢 RAG 主流程。
- 当前 `src/rag/engine.py` 中存在中文 mojibake 常量和 fallback 文案，需要优先修复编码，否则 RAG 回答会乱码。
- ToolRouter 应避免直接持久化 API Key；Provider 密钥仍由现有 `LLMRouter/APIKeyManager` 管理。
- Web Browsing 涉及网络和版权边界，应保留来源 URL、抓取时间、摘要长度限制。
