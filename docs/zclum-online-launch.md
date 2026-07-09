# ZCLUM Online Launch Guide

Primary deployment target:

- `zclum.com`

## Recommended Entry

Suggested application URL:

```text
https://zclum.com/apps/prism-ocr
```

Alternative:

```text
https://zclum.com/agents/ocr-harness
```

## Frontend Delivery

Build the frontend:

```powershell
cd frontend
npm install
npm run build
```

Publish `frontend/dist` to the host platform static-app directory, or let the application center serve it.

Recommended runtime injection:

```html
<script>
  window.__ZCLUM_OCR_BASE_URL__ = "/api/agents/ocr-harness";
  window.__ZCLUM_USER_TOKEN__ = window.ZCLUM_CURRENT_USER_TOKEN;
</script>
```

## Gateway Mapping

Recommended gateway rule:

```text
/api/agents/ocr-harness/* -> ${OCR_HARNESS_BASE_URL}/api/*
```

Required environment fields:

```text
OCR_HARNESS_BASE_URL=http://127.0.0.1:8080
OCR_HARNESS_MAX_UPLOAD_MB=200
OCR_HARNESS_TIMEOUT_SECONDS=600
```

If the backend is not configured:

```json
{
  "error": "ocr_harness_not_configured",
  "message": "OCR-Harness base URL is not configured."
}
```

## App Card Copy

Title:

```text
Prism OCR
```

Subtitle:

```text
PDF to Markdown and RAG agent
```

Description:

```text
Upload PDFs or scanned documents, run OCR, clean Markdown, score quality, and search the resulting knowledge base.
```

CTA:

```text
Open Agent
```

## Platform Fields Still Needed

- public app URL
- gateway host/domain
- runtime user token source
- admin auth rule for provider endpoints
- max upload size
- OCR timeout
- log retention and file retention policy

