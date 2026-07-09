# ANZAIDX Minimal Integration Fields

This is the smallest practical integration contract for hosting the OCR agent on `anzaidx.com`.

## Minimal Field Table

| Field | Example | Purpose |
|---|---|---|
| `OCR_HARNESS_BASE_URL` | `http://47.96.7.204:8080` | Upstream FastAPI service base URL |
| `PUBLIC_EMBED_BASE_URL` | `https://anzaidx.com/apps/prism-ocr` | Public frontend entry URL |
| `USER_TOKEN_HEADER` | `Authorization: Bearer <token>` | Preferred runtime user auth transport |
| `USER_TOKEN_QUERY` | optional, empty by default | Only if the host platform must pass token in query string |
| `UPLOAD_ENDPOINT` | `/api/agents/ocr-harness/convert` | PDF upload endpoint |
| `STATUS_ENDPOINT` | `/api/agents/ocr-harness/status/{task_id}` | OCR task status endpoint |
| `RESULT_ENDPOINT` | `/api/agents/ocr-harness/result/{task_id}` | OCR result endpoint |
| `RAG_QUERY_ENDPOINT` | `/api/agents/ocr-harness/rag/query` | RAG query endpoint |
| `HEALTH_ENDPOINT` | `/api/agents/ocr-harness/health` | Health-check endpoint |
| `CORS_ALLOWED_ORIGINS` | `https://anzaidx.com` | Allowed browser origin list |

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
- current recommendation: do not use query transport unless the platform absolutely requires it

`UPLOAD_ENDPOINT`

- backend route in `src/web/app.py`
- platform route mapping in `deploy/zclum/ocr-harness-agent.json`

`STATUS_ENDPOINT`

- backend route in `src/web/app.py`
- platform route mapping in `deploy/zclum/ocr-harness-agent.json`

`RESULT_ENDPOINT`

- backend route in `src/web/app.py`
- platform route mapping in `deploy/zclum/ocr-harness-agent.json`

`RAG_QUERY_ENDPOINT`

- backend route in `src/web/app.py`
- platform route mapping in `deploy/zclum/ocr-harness-agent.json`

`HEALTH_ENDPOINT`

- backend route in `src/web/app.py`
- platform route mapping in `deploy/zclum/ocr-harness-agent.json`

`CORS_ALLOWED_ORIGINS`

- current middleware configuration in `src/web/app.py`
- currently set to `*`
- recommended production narrowing: `https://anzaidx.com`

## Shortest Integration Steps

1. Deploy backend on the source host.

Example:

```text
http://47.96.7.204:8080
```

2. Expose frontend at the public app path.

Example:

```text
https://anzaidx.com/apps/prism-ocr
```

3. Inject runtime values before frontend boot.

```html
<script>
  window.__ANZAIDX_OCR_BASE_URL__ = "/api/agents/ocr-harness";
  window.__ANZAIDX_USER_TOKEN__ = window.ANZAIDX_CURRENT_USER_TOKEN;
</script>
```

4. Configure gateway forwarding.

```text
/api/agents/ocr-harness/* -> http://47.96.7.204:8080/api/*
```

5. Add reverse-proxy support for long OCR requests.

- upload limit: at least `200m`
- upstream timeout: at least `600s`

6. Enable HTTPS on the public domain.

- `https://anzaidx.com`
- optional API subdomain if you split frontend and API

## Notes

- The current app does not require query-based token passing.
- The cleanest production shape is `Authorization: Bearer <token>`.
- Before public rollout, `allow_origins=["*"]` in `src/web/app.py` should be narrowed.

