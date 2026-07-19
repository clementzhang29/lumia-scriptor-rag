# Lumia ScriptorRAG｜序光文枢 RAG 详细项目介绍

生成时间：2026-07-07  
作者：张春  
整理说明：本文档由 AI 根据项目源码、运行状态、前端界面、构建记录与迭代过程整理生成，用于项目交接、作品集展示、简历扩展说明和后续产品发布准备。

## 一、项目概述

Lumia ScriptorRAG｜序光文枢 RAG 是一个面向本地文档数字化、OCR 提取、Markdown 排版清洗与通用 RAG 问答的综合型智能体系统。项目最初来自 OCR-Harness 的多模型 PDF → Markdown 转换目标，后续融合了文档排版优化、知识库检索、LLM Provider 管理、前端工作台和本地发布能力，最终形成一条完整的文档智能流水线。

项目并不是单纯的 RAG 聊天页面，也不是只调用一个 OCR 引擎的工具。它的核心价值在于把“不可用的 PDF / 扫描件 / 本地资料”变成“可阅读、可检索、可追溯引用、可继续开发”的结构化知识资产。

核心链路如下：

```text
PDF / 扫描件 / 本地资料
  → 光棱 OCR：自动文档分析、多引擎路由、OCR 识别、质量评分、失败回退
  → 字炉排版：Markdown 清洗、标题与段落修复、噪声字符移除、导出
  → 文枢 RAG：多格式建库、来源去重、原典优先、可追溯问答
  → 星轨模型：多厂商 LLM Provider 配置，用于校正与综合回答
  → WebUI / API：前端操作、结果复制、文件下载、二次开发入口
```

## 二、产品命名与品牌含义

产品名称：**Lumia ScriptorRAG**  
中文名称：**序光文枢 RAG**

命名含义：

- **Lumia**：象征微光、照明与知识被重新照见。
- **Scriptor**：来自“书写者、转写者、抄录者”的含义，对应 OCR 和文献整理。
- **RAG**：检索增强生成，表示项目最终服务于可追溯问答和知识应用。
- **序光文枢**：表达“让旧纸重见微光，让文献进入知识中枢”。

前端栏目命名保持产品感和功能感统一：

- **OCR**：光棱 OCR 的工作入口。
- **导览**：完整流程说明。
- **排版**：字炉排版，处理 Markdown 清洗。
- **RAG**：文枢 RAG，负责建库和问答。
- **模型**：星轨模型，负责 LLM Provider 配置。
- **帮助**：使用说明、迁移说明和二次开发入口。

## 三、技术架构

### 1. 后端架构

后端使用 FastAPI，主入口位于：

```text
src/web/app.py
```

核心 API 包括：

- `GET /api/health`：健康检查。
- `GET /api/engines`：查看 OCR 引擎状态。
- `POST /api/convert`：上传 PDF 并启动 OCR 转换任务。
- `GET /api/status/{task_id}`：查询任务状态。
- `GET /api/result/{task_id}`：读取 OCR 结果。
- `GET /api/download/{task_id}`：下载 Markdown。
- `POST /api/format/markdown`：独立 Markdown 清洗接口。
- `POST /api/rag/rebuild`：从资料目录重建 RAG 索引。
- `POST /api/rag/query`：执行 RAG 检索问答。
- `POST /api/providers`：注册 LLM Provider。
- `GET /api/providers`：查看 Provider。
- `POST /api/providers/verify`：验证 Provider 可用性。

FastAPI 同时托管 Vue 构建产物：

```text
frontend/dist
```

为避免前端白屏，已显式挂载：

```python
app.mount("/assets", StaticFiles(directory=str(assets_path)), name="assets")
```

这样 `/assets/*.js` 会正确返回 JavaScript，而不会被 SPA fallback 错误返回成 HTML。

### 2. OCR 智能体架构

OCR 调度模块位于：

```text
src/orchestrator/
src/engines/
src/qa/
src/correctors/
```

设计目标是让系统根据文档情况选择合适 OCR 引擎，而不是固定走单一路径。

已封装或规划接入的 OCR 引擎：

- Surya
- MinerU
- Docling
- Marker
- PaddleOCR
- Nougat

引擎优先策略可按实际可用性调整，当前产品层面保留多引擎统一封装能力。Surya 已作为稳定 OCR 方案被验证过，MinerU / Docling 作为可扩展方案保留。

### 3. Markdown 排版清洗

排版模块位于：

```text
src/formatter/
frontend/src/views/Formatter.vue
```

目标是把 OCR 输出中常见的噪声进行结构化处理：

- 修复标题层级。
- 整理空行与段落。
- 减少无意义符号。
- 保留正常断句和原文语义。
- 输出可继续进入 RAG 的 Markdown。
- 支持导出 Markdown 与单文件 HTML。

### 4. RAG 架构

RAG 模块位于：

```text
src/ingest/
src/rag/
frontend/src/views/Rag.vue
```

支持多格式资料导入：

- Markdown
- TXT
- HTML
- PDF
- EPUB
- DOCX

当前 RAG 检索强调：

- 尽量返回不同文档来源。
- 至少提供多条可追溯引用。
- 古籍原典权重高于近现代补充资料。
- LLM 不可用时仍可返回本地 fallback answer。
- 支持复制结果、导出 Markdown、导出 HTML、导出 PNG。

### 5. LLM Provider 抽象

LLM 模块位于：

```text
src/llm/
frontend/src/views/Providers.vue
```

支持 OpenAI 兼容风格的 Provider 配置，并可识别多种服务商：

- OpenAI
- DeepSeek
- 智谱 GLM
- Kimi
- 通义千问
- Anthropic Claude
- 自定义 OpenAI 兼容接口

当前 Provider 主要保存在后端运行环境中，生产化建议增加加密落盘和密钥管理。

## 四、前端设计系统

前端使用：

```text
Vue3 + Vite + Naive UI
```

本次前端优化参考了 Claude Design / Claude Code design skill 的公开工作流思想，并按以下阶段执行：

1. `design-system-extract`
2. `frontend-aesthetic-direction`
3. `hierarchy-rhythm-review`
4. `interaction-states-pass`
5. `ai-slop-check`
6. `polish-pass`

### 1. 设计系统提取

当前 UI 的视觉语言是“温润的本地知识工作台”：

- 背景：暖纸色，避免冷冰冰的纯白 SaaS 风格。
- 主色：深青绿色，代表文档、知识、可信赖。
- 字体：中文优先，保证 Windows 本地可读。
- 圆角：整体圆润，但不做过度卡通化。
- 阴影：低对比柔和阴影，像纸面浮层。
- 密度：中低密度，适合 OCR / RAG 这种长任务工作台。
- 动效：轻微 hover、focus、active，不做炫技动画。

### 2. 审美方向

最终审美方向定义为：

> 像一张整理文献的书桌，清晰、可信、克制、可持续操作。

明确避免：

- 紫粉蓝 AI 套壳渐变。
- 无意义装饰图形。
- 过度营销式大标题。
- 乱码和无效占位。
- 为了“看起来高级”而降低工具可用性。

### 3. 层级与节奏优化

已优化内容：

- 顶部导航改为 `OCR / 导览 / 排版 / RAG / 模型 / 帮助`。
- 避免长中文导航竖排和越界。
- 首页明确呈现“引擎状态、质量阈值、模型 Provider”三项关键指标。
- 排版页采用左右工作区：原始 Markdown / 优化结果。
- RAG 页采用左右工作区：提问检索 / 回答结果。
- 移动端使用单列布局。

### 4. 交互状态补齐

已补齐：

- hover
- focus-visible
- active
- disabled
- loading
- empty
- error

具体包括：

- 导航交互状态。
- 上传区 ready 状态。
- 按钮禁用状态。
- 排版结果空状态。
- RAG 回答空状态。
- Provider 保存 loading。
- API 异常 message / alert。

## 五、实现过程

### 阶段 1：OCR 工作流验证

先跑通端到端 API 工作流：

```text
上传 PDF → OCR → 质量评分 → 返回 Markdown
```

Surya OCR 被验证为稳定可用方案。MinerU、Docling 等引擎保留在架构中，用于后续扩展。

### 阶段 2：前后端联通

通过 FastAPI 提供 API，Vue 前端调用接口，实现：

- 文件上传。
- 任务轮询。
- 结果查看。
- Markdown 下载。
- Provider 配置。
- RAG 建库与问答。

### 阶段 3：排版与 RAG 融合

项目不再停留在 OCR 输出，而是加入：

- OCR Markdown 清洗。
- 文档资料目录建库。
- 多来源检索。
- 引用导出。

这使项目从“转换工具”升级为“文档智能体底座”。

### 阶段 4：产品化与品牌化

完成：

- 产品命名统一。
- 前端 UI 统一。
- 文档体系补齐。
- 本地启动脚本。
- GitHub 私有仓库同步。
- 最终源码压缩包。

## 六、遇到的问题与解决方案

### 1. Windows 无法识别 python

问题：PowerShell 提示 `python` 不是可识别命令。  
解决：优先使用 Windows Python Launcher：

```powershell
py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info
```

### 2. 前端白屏

问题：页面返回 200，但 Vue 未挂载。  
根因：`/assets/*.js` 被 SPA fallback 返回为 HTML。  
解决：在 FastAPI 中挂载 Vite 静态资源目录。

### 3. 顶部导航拥挤

问题：中文导航太长，在较窄屏幕中竖排和越界。  
解决：改为短标签与图标：

```text
OCR / 导览 / 排版 / RAG / 模型 / 帮助
```

### 4. 乱码问题

问题：历史文档和前端页面中出现 mojibake。  
解决：重写主要真实页面的中文文案，并新增干净 UTF-8 文档。

### 5. GitHub 推送不稳定

问题：网络连接 GitHub 时出现 reset / timeout。  
解决：本地已提交，网络恢复后继续执行：

```powershell
git push
```

## 七、当前最终状态

### 已完成

- FastAPI 后端可运行。
- Vue 前端构建通过。
- 首页、排版页、RAG 页、模型页、帮助页可打开。
- 桌面端浏览器检查无控制台错误。
- 前端主页面已清理乱码。
- 已新增设计系统审查文档。
- 已生成桌面源码压缩包。

### 本地访问

```powershell
cd C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0
py -3 -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080 --log-level info
```

浏览器访问：

```text
http://127.0.0.1:8080/
```

### 重要文档

- `docs/detailed_project_introduction.md`：本详细项目介绍。
- `docs/project-introduction.html`：单文件 HTML 项目介绍。
- `docs/frontend_design_system_review.md`：前端设计系统审查记录。
- `docs/ai_handoff.md`：AI / 开发者交接文档。
- `docs/final_delivery_note.md`：最终交付说明。
- `docs/resume_project_blurb.md`：简历用项目介绍。

## 八、简历扩展版介绍

Lumia ScriptorRAG（序光文枢 RAG）是一个多模型智能编排的本地文档数字化与知识库系统，围绕“光棱 OCR → 字炉排版 → 文枢 RAG”的完整链路设计。项目集成 Surya、MinerU、Docling、Marker、PaddleOCR、Nougat 等 OCR 引擎，支持文档类型分析、自动路由、质量评分、失败回退、LLM 增强校正和 Markdown 导出；同时扩展通用 RAG 能力，支持多格式建库、来源去重、原典权重提升和可追溯问答。本人负责整体架构设计、FastAPI 后端接口、OCR Pipeline 编排、LLM Provider 抽象、多格式文档导入、BM25 检索模块、Vue3 + Naive UI 前端产品化、本地启动脚本、前端设计系统优化和项目交付文档建设。实现过程中解决了 Windows 本地启动兼容、OCR 引擎依赖冲突、前端白屏、静态资源挂载、导航拥挤、RAG 检索宽度、乱码清理和 GitHub 私有仓库交付等问题。

## 九、后续建议

后续如果继续产品化，建议优先做：

1. Provider Key 加密落盘。
2. RAG 检索升级为 BM25 + embedding + rerank。
3. OCR 引擎能力做可视化健康检查。
4. 增加批量文档处理队列。
5. 增加打包安装器和自动更新机制。
6. 增加项目内置示例数据与演示流程。
