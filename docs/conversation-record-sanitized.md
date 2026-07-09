# OCR-Harness conversation record, sanitized

Generated at: 2026-07-09

This file is a sanitized handoff record created from the visible project history and Codex prompt history. It intentionally removes raw API keys, tokens, and private credentials.

## Project origin

The project began as **OCR-Harness**, a multi-engine PDF to Markdown conversion system. The initial target was:

- FastAPI backend
- Vue 3 frontend
- OCR engines: Surya, MinerU, Marker, Docling, PaddleOCR, Nougat
- GPU-first execution with CPU fallback
- LLM-assisted correction
- document classification and engine routing

The early verification target was:

```text
python -B test_e2e.py
```

Expected behavior:

```text
Engine: Surya
MD chars > 0
```

## Major implementation stages

### 1. OCR engine stabilization

The work first focused on fixing runtime dependencies and making the OCR route usable locally.

Key points:

- Surya was confirmed as the most reliable local OCR engine.
- MinerU required extra dependencies such as `doclayout_yolo` and `ultralytics`.
- GPU DLL and CUDA issues were handled by allowing CPU fallback with `CUDA_VISIBLE_DEVICES=""`.
- Marker and Docling installation paths were prepared.

### 2. Frontend productization

The project evolved from an API harness into a web application.

Key changes:

- Vue 3 + Vite frontend was built.
- UI was polished into the product identity **Lumia ScriptorRAG**.
- Navigation included OCR, guide, formatter, RAG, knowledge sources, provider settings, and help.
- Multiple UI polish passes were requested, including better visual hierarchy, interaction states, empty/error/loading states, and removing template-like AI styling.

### 3. OCR plus RAG integration

The project was expanded from OCR-only into a complete document intelligence workflow:

```text
PDF / scan
  -> OCR routing
  -> correction
  -> quality scoring
  -> Markdown formatting
  -> RAG indexing
  -> cited query answering
```

The RAG system was tuned toward:

- at least several sources per answer
- preference for older/classical source material where relevant
- exported results
- Markdown/HTML output
- knowledge source mounting

### 4. Knowledge source mounting

External knowledge source support was added:

- local directory
- WebDAV
- AList

Related files:

- `src/kb_mounts/manager.py`
- `frontend/src/views/KnowledgeSources.vue`
- `docs/knowledge_mounts.md`

### 5. Provider and model center

The model provider system was expanded:

- persistent provider storage
- provider routing groups
- preferred scenario routing
- catalog / model list reading
- supplier identity and base URL hidden in UI

Sensitive model provider keys were discussed during development and are intentionally omitted from this record.

### 6. Formatter module upgrade

The formatter was upgraded into an independently usable **字炉排版** workbench.

Capabilities:

- heading/list cleanup
- paragraph merging
- OCR noise cleanup
- punctuation normalization
- statistics report
- before/after preview
- Markdown and HTML export

Related files:

- `src/formatter/markdown_cleaner.py`
- `frontend/src/views/Formatter.vue`
- `src/web/app.py`

### 7. Open-source and deployment packaging

The repository was prepared for public open source release:

- bilingual README
- MIT license
- GitHub description and topics
- deployment docs
- Dockerfile
- docker-compose
- Nginx configs
- Aliyun ECS checklist
- 1Panel / BT Panel / Docker Compose deployment paths

### 8. zclum platform integration

The latest stage focused on turning OCR-Harness into a zclum / 来客有方 intelligent agent application.

Added integration files:

- `docs/zclum-agent-integration.md`
- `deploy/zclum/ocr-harness-agent.json`
- `deploy/zclum/validate_agent_manifest.py`

Gateway rule:

If `OCR_HARNESS_BASE_URL` is not configured, the zclum API Gateway should return:

```json
{
  "error": "ocr_harness_not_configured",
  "message": "OCR-Harness base URL is not configured."
}
```

## Current local status before zclum-specific fork

Current repository path:

```text
C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0
```

Current local app:

```text
http://127.0.0.1:8080
```

Recent checks:

- `/api/health`: ok
- `/api/engines`: six engines reported available locally
- `/api/rag/status`: ok, local index present
- provider list hides `base_url`
- zclum manifest validates against FastAPI routes

## Open items

The next requested direction is:

- back up the current code and project record
- create a separate zclum-specific engineering project
- adapt API routes, gateway token behavior, and UI style to match `zclum.com`
- make OCR-Harness available as a zclum intelligent agent web application

## Redaction note

This record intentionally excludes:

- raw API keys
- provider tokens
- private passwords
- session cookies
- browser login information

