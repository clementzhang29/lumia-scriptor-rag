# Two-Site Shared Backend Setup

This document explains the most stable way to connect the same OCR + RAG agent to two websites.

## Recommended topology

Use one public backend deployment and let both websites proxy to it.

```text
Website A (zclum.com) --------\
                               -> shared OCR/RAG backend -> 47.96.7.204:8080
Website B (来客有方 / other) --/
```

## When one backend is enough

Use one backend instance when both websites can share:

- the same OCR engines
- the same RAG corpus
- the same provider configuration
- the same admin operations

## When you should deploy two instances

Use separate backend instances when the two websites need:

- isolated knowledge bases
- isolated provider keys
- isolated file retention rules
- isolated admin permissions
- isolated billing or quotas

## Shared route contract

Both websites should proxy these routes to the same backend:

- `GET /api/agents/ocr-harness/health`
- `GET /api/agents/ocr-harness/engines`
- `POST /api/agents/ocr-harness/convert`
- `POST /api/agents/ocr-harness/convert/batch`
- `GET /api/agents/ocr-harness/status/{task_id}`
- `GET /api/agents/ocr-harness/batch/{batch_id}`
- `GET /api/agents/ocr-harness/result/{task_id}`
- `GET /api/agents/ocr-harness/download/{task_id}`
- `POST /api/agents/ocr-harness/format/markdown`
- `GET /api/agents/ocr-harness/rag/status`
- `POST /api/agents/ocr-harness/rag/query`

Admin-only routes should not be public on both websites unless needed:

- `GET /api/agents/ocr-harness/providers`
- `POST /api/agents/ocr-harness/providers`
- `POST /api/agents/ocr-harness/providers/verify`
- `GET /api/agents/ocr-harness/kb-sources`

## Backend environment

Recommended server-side environment:

```dotenv
APP_PORT=8080
CUDA_VISIBLE_DEVICES=
OCR_HARNESS_CORS_ALLOWED_ORIGINS=https://zclum.com,https://your-second-site.com
```

If the second website is still not final, keep temporary permissive CORS during testing:

```dotenv
OCR_HARNESS_CORS_ALLOWED_ORIGINS=*
```

## Frontend runtime injection

Website A can inject:

```html
<script>
  window.__ZCLUM_OCR_BASE_URL__ = "/api/agents/ocr-harness";
  window.__ZCLUM_USER_TOKEN__ = window.ZCLUM_CURRENT_USER_TOKEN;
</script>
```

Website B can inject:

```html
<script>
  window.__HOST_OCR_BASE_URL__ = "/api/agents/ocr-harness";
  window.__HOST_USER_TOKEN__ = window.HOST_CURRENT_USER_TOKEN;
</script>
```

Generic fallback is also supported:

```html
<script>
  window.__OCR_HARNESS_BASE_URL__ = "/api/agents/ocr-harness";
  window.__OCR_HARNESS_USER_TOKEN__ = window.CURRENT_USER_TOKEN;
</script>
```

## Reverse proxy rule

Both websites should map:

```text
/api/agents/ocr-harness/* -> http://47.96.7.204:8080/api/*
```

## Why two websites may still fail to connect

Most common causes:

- the backend is not yet deployed publicly
- `OCR_HARNESS_BASE_URL` is missing on the website gateway
- reverse proxy is not forwarding `/api/agents/ocr-harness/*`
- website runtime token is not injected
- CORS does not include the real website origin
- DNS or HTTPS still points elsewhere

## Acceptance checklist

From each website environment, verify in this order:

1. `GET /api/agents/ocr-harness/health`
2. `GET /api/agents/ocr-harness/engines`
3. `POST /api/agents/ocr-harness/convert`
4. `POST /api/agents/ocr-harness/convert/batch`
5. `GET /api/agents/ocr-harness/status/{task_id}`
6. `GET /api/agents/ocr-harness/batch/{batch_id}`
7. `POST /api/agents/ocr-harness/rag/query`

## Practical recommendation

For your current stage, the best path is:

1. deploy one backend to `47.96.7.204`
2. expose one stable public domain such as `api.zclum.com`
3. let both websites proxy to that same backend
4. only split into dual instances later if data isolation becomes necessary
