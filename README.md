# ZCLUM Prism OCR

Open-source document intelligence agent for `PDF -> Markdown -> RAG`.

[![License: MIT](https://img.shields.io/badge/License-MIT-20e7d7.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-78a8ff)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-20e7d7)](https://fastapi.tiangolo.com/)
[![Vue 3](https://img.shields.io/badge/UI-Vue%203-75f0a2)](https://vuejs.org/)

Primary web integration target: [zclum.com](https://zclum.com)

![ZCLUM Prism OCR UI](docs/assets/zclum-prism-ocr-home.png)

## Overview

ZCLUM Prism OCR is built for teams and individuals who need a full document workflow, not just OCR output.

```text
PDF / Scan / Book
  -> OCR routing
  -> quality scoring
  -> Markdown cleanup
  -> knowledge indexing
  -> citation-aware RAG answers
```

It works as:

- a local OCR workbench
- a document cleanup pipeline
- a private RAG knowledge-base builder
- an embeddable web agent for host platforms

## 中文简介

`ZCLUM 光棱 OCR` 是一个开源文档智能体，目标是把 PDF、扫描件、书籍和研究资料转化为可阅读、可排版、可检索、可引用的知识资产。

它不是单纯的 OCR 工具，而是一条完整链路：

- 上传 PDF 或扫描文档
- 自动路由 OCR 引擎
- 转换为 Markdown
- 进行排版清理与质量评分
- 进入 RAG 知识库
- 在网页端完成检索、问答与导出

## Features

- multi-engine OCR orchestration
- single-file and batch OCR for multiple PDFs or folders
- Markdown cleanup and formatting
- quality scoring and fallback routing
- mounted knowledge-source management
- local RAG retrieval with references
- provider-assisted answer generation
- standalone frontend and embedded platform frontend

## Architecture

- `src/web` - FastAPI endpoints
- `src/engines` - OCR engine adapters
- `src/orchestrator` - routing and pipeline logic
- `src/correctors` - OCR correction logic
- `src/formatter` - Markdown cleanup
- `src/rag` - persistent local retrieval engine
- `src/llm` - provider abstraction
- `frontend` - Vue 3 web UI
- `deploy/zclum` - agent manifest and gateway package

## Usage

### English

1. Start the FastAPI backend.
2. Open the web UI and upload one PDF, multiple PDFs, or an entire folder.
3. Let the pipeline route OCR, score quality, and generate Markdown.
4. Optionally clean the Markdown and rebuild the RAG index.
5. Query the indexed corpus with source-aware references.

### 中文

1. 启动 FastAPI 后端服务。
2. 打开网页工作台，上传单个 PDF、多个 PDF，或整个文件夹。
3. 系统会自动路由 OCR、质量评分并生成 Markdown。
4. 可继续做 Markdown 清洗，并重建 RAG 索引。
5. 在文枢 RAG 中基于引用来源进行检索与问答。

## Quick Start

Backend:

```powershell
cd C:\Users\35160\Documents\Codex\zclum-ocr-harness-agent
python -m pip install -r requirements-web.txt
python -m pip install -r requirements-rag.txt
python -B -m uvicorn src.web.app:app --host 127.0.0.1 --port 8080
```

Frontend:

```powershell
cd frontend
npm install
npm run build
npm run preview -- --host 127.0.0.1 --port 5174
```

Open:

```text
http://127.0.0.1:5174/
```

## API Highlights

- `GET /api/health`
- `GET /api/engines`
- `POST /api/convert`
- `POST /api/convert/batch`
- `GET /api/status/{task_id}`
- `GET /api/batch/{batch_id}`
- `GET /api/result/{task_id}`
- `GET /api/download/{task_id}`
- `POST /api/format/markdown`
- `GET /api/rag/status`
- `POST /api/rag/query`
- `GET /api/providers`
- `POST /api/providers`

## Platform Integration

The frontend supports runtime injection for embedded usage.

Supported base-url variables:

- `window.__ZCLUM_OCR_BASE_URL__`
- `window.__ANZAIDX_OCR_BASE_URL__`
- `window.__OCR_HARNESS_BASE_URL__`
- `VITE_ZCLUM_OCR_BASE`
- `VITE_ANZAIDX_OCR_BASE`

Supported token variables:

- `window.__ZCLUM_USER_TOKEN__`
- `window.__ANZAIDX_USER_TOKEN__`
- `localStorage.zclum_user_token`
- `localStorage.anzaidx_user_token`

Recommended public gateway path:

```text
/api/agents/ocr-harness/*
```

Integration docs:

- [zclum-agent-integration](docs/zclum-agent-integration.md)
- [platform-batch-ocr-reuse](docs/platform-batch-ocr-reuse.md)
- [zclum-platform-adapter](docs/zclum-platform-adapter.md)
- [zclum-online-launch](docs/zclum-online-launch.md)
- [ocr-harness-agent manifest](deploy/zclum/ocr-harness-agent.json)

## Open Source

Community files included:

- `LICENSE`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `.github/ISSUE_TEMPLATE/*`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/workflows/ci.yml`

## License

MIT License.

Author: `Zhang Chun`
