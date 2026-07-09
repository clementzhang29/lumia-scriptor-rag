# ZCLUM Platform Adapter

This document describes how to integrate the OCR agent into a host platform.

Current primary target:

- `zclum.com`

## Agent Identity

- Public name: `ZCLUM Prism OCR`
- Chinese name: `ZCLUM 光棱 OCR`
- Category: document intelligence agent
- Capability: PDF upload, OCR to Markdown, formatting cleanup, quality scoring, RAG retrieval, provider-assisted answer generation

## Frontend Runtime Injection

The frontend supports these runtime variables in priority order.

Base URL:

1. `window.__ZCLUM_OCR_BASE_URL__`
2. `window.__ANZAIDX_OCR_BASE_URL__`
3. `window.__OCR_HARNESS_BASE_URL__`
4. `VITE_ZCLUM_OCR_BASE`
5. `VITE_ANZAIDX_OCR_BASE`
6. `VITE_API_BASE`
7. `/api`

User token:

1. `window.__ZCLUM_USER_TOKEN__`
2. `window.__ZCLUM_TOKEN__`
3. `window.__ANZAIDX_USER_TOKEN__`
4. `window.__ANZAIDX_TOKEN__`
5. `localStorage.zclum_user_token`
6. `localStorage.zclum_token`
7. `sessionStorage.zclum_user_token`
8. `sessionStorage.zclum_token`
9. `localStorage.anzaidx_user_token`
10. `localStorage.anzaidx_token`
11. `sessionStorage.anzaidx_user_token`
12. `sessionStorage.anzaidx_token`

The client automatically attaches:

```http
Authorization: Bearer <token>
X-Agent-App: ocr-harness
```

## Recommended Gateway

Recommended public route:

```text
/api/agents/ocr-harness/*
```

Recommended upstream:

```text
${OCR_HARNESS_BASE_URL}/api/*
```

If `OCR_HARNESS_BASE_URL` is not configured, return:

```json
{
  "error": "ocr_harness_not_configured",
  "message": "OCR-Harness base URL is not configured."
}
```

Recommended status code:

```text
503
```

## Required Platform Fields

- `OCR_HARNESS_BASE_URL`
- user auth strategy
- runtime bearer token injection or gateway auth forwarding
- upload size limit
- OCR timeout limit
- RAG query timeout limit

Optional:

- per-user OCR quota
- admin-only provider management
- file retention policy

## Key Endpoints

- `GET /api/health`
- `GET /api/engines`
- `POST /api/convert`
- `GET /api/status/{task_id}`
- `GET /api/result/{task_id}`
- `GET /api/download/{task_id}`
- `POST /api/format/markdown`
- `GET /api/rag/status`
- `POST /api/rag/rebuild`
- `POST /api/rag/rebuild-mounted`
- `POST /api/rag/query`
- `GET /api/providers`
- `POST /api/providers`
- `POST /api/providers/verify`
- `GET /api/kb-sources`

## Suggested UI Entry Points

- Upload PDF
- OCR result
- Quality score
- Knowledge retrieval
- Export result
- Model settings

