# ZCLUM Minimal Integration Fields

This is the smallest practical integration contract for hosting the OCR agent on `zclum.com`.

## Minimal Field Table

| Field | Example | Purpose |
|---|---|---|
| `OCR_HARNESS_BASE_URL` | `http://47.96.7.204:8080` | Upstream FastAPI service base URL |
| `PUBLIC_EMBED_BASE_URL` | `https://zclum.com/apps/prism-ocr` | Public frontend entry URL |
| `USER_TOKEN_HEADER` | `Authorization: Bearer <token>` | Preferred runtime user auth transport |
| `USER_TOKEN_QUERY` | optional, empty by default | Only if the host platform must pass token in query string |
| `UPLOAD_ENDPOINT` | `/api/agents/ocr-harness/convert` | PDF upload endpoint |
| `STATUS_ENDPOINT` | `/api/agents/ocr-harness/status/{task_id}` | OCR task status endpoint |
| `RESULT_ENDPOINT` | `/api/agents/ocr-harness/result/{task_id}` | OCR result endpoint |
| `RAG_QUERY_ENDPOINT` | `/api/agents/ocr-harness/rag/query` | RAG query endpoint |
| `HEALTH_ENDPOINT` | `/api/agents/ocr-harness/health` | Health-check endpoint |
| `CORS_ALLOWED_ORIGINS` | `https://zclum.com` | Allowed browser origin list |

## Runtime Injection

```html
<script>
  window.__ZCLUM_OCR_BASE_URL__ = "/api/agents/ocr-harness";
  window.__ZCLUM_USER_TOKEN__ = window.ZCLUM_CURRENT_USER_TOKEN;
</script>
```

## Gateway Forwarding

```text
/api/agents/ocr-harness/* -> http://47.96.7.204:8080/api/*
```

## Code Locations

`OCR_HARNESS_BASE_URL`

- `deploy/zclum/ocr-harness-agent.json`
- `docs/zclum-platform-adapter.md`
- `docs/zclum-online-launch.md`

`PUBLIC_EMBED_BASE_URL`

- documented in `docs/zclum-online-launch.md`
- public-facing description in `README.md`

`USER_TOKEN_HEADER`

- runtime injection and `Authorization` forwarding in `frontend/src/api.js`
- documented in `docs/zclum-platform-adapter.md`

`USER_TOKEN_QUERY`

- not implemented in current frontend or backend
- recommendation: use header-based token transport

`UPLOAD_ENDPOINT`, `STATUS_ENDPOINT`, `RESULT_ENDPOINT`, `RAG_QUERY_ENDPOINT`, `HEALTH_ENDPOINT`

- backend routes in `src/web/app.py`
- platform route mapping in `deploy/zclum/ocr-harness-agent.json`

`CORS_ALLOWED_ORIGINS`

- current middleware configuration in `src/web/app.py`
- currently set to `*`
- recommended production narrowing: `https://zclum.com`

