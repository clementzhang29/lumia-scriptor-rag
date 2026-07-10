# zclum agent integration: OCR-Harness

This document describes how zclum / 来客有方 can integrate OCR-Harness, currently published as Lumia ScriptorRAG, as an intelligent document agent.

## Positioning

OCR-Harness is a document intelligence agent for:

- PDF upload
- OCR to Markdown
- quality scoring
- Markdown cleanup
- knowledge base indexing
- RAG query
- LLM provider configuration

Recommended zclum product name:

```text
OCR-Harness 文档智能体
```

Recommended role:

```text
Document OCR, Markdown refinement, and RAG retrieval agent.
```

## Base URL

The FastAPI service should be deployed behind a zclum API Gateway.

Environment variable:

```text
OCR_HARNESS_BASE_URL=https://api.zclum.com/ocr-harness
```

Local development example:

```text
OCR_HARNESS_BASE_URL=http://127.0.0.1:8080
```

Gateway route suggestion:

```text
/api/agents/ocr-harness/* -> ${OCR_HARNESS_BASE_URL}/api/*
```

If `OCR_HARNESS_BASE_URL` is not configured, the gateway must not proxy blindly. Return:

```json
{
  "error": "ocr_harness_not_configured",
  "message": "OCR-Harness base URL is not configured."
}
```

Suggested HTTP status:

```text
503 Service Unavailable
```

## Health check

### Request

```http
GET /api/health
```

### Response

```json
{
  "status": "ok",
  "timestamp": "2026-07-09T00:00:00"
}
```

Gateway public route:

```http
GET /api/agents/ocr-harness/health
```

## Engine list

### Request

```http
GET /api/engines
```

### Purpose

Shows available OCR engines and availability state.

### Response shape

```json
{
  "engines": [
    {
      "name": "surya",
      "available": true
    }
  ]
}
```

## Upload PDF and start OCR

### Request

```http
POST /api/convert
Content-Type: multipart/form-data
```

### Form fields

```text
file              required PDF file
strategy          optional, default auto
preferred_engine  optional, for example surya, mineru, docling
```

### Response

```json
{
  "task_id": "uuid",
  "status": "queued"
}
```

Gateway public route:

```http
POST /api/agents/ocr-harness/convert
```

Common error responses:

```json
{
  "detail": "Task not found"
}
```

## Batch OCR for multiple files or folders

This endpoint is the recommended integration target for both zclum and 来客有方 when the host UI supports:

- multiple PDF selection
- folder selection from the browser
- drag-and-drop bulk upload

### Request

```http
POST /api/convert/batch
Content-Type: multipart/form-data
```

### Form fields

```text
files             required, one or more PDF files
strategy          optional, default auto
preferred_engine  optional, for example surya, mineru, docling
```

### Notes

- the frontend may send plain filenames such as `book-a.pdf`
- when the browser supports folder upload, each file can carry a relative path such as `books/classic/book-a.pdf`
- the backend preserves the relative structure inside the batch staging directory

### Response

```json
{
  "batch_id": "uuid",
  "task_ids": ["uuid-1", "uuid-2", "uuid-3"],
  "count": 3,
  "status": "queued"
}
```

### Error responses

If no file is uploaded:

```json
{
  "detail": "No files uploaded"
}
```

Suggested gateway public route:

```http
POST /api/agents/ocr-harness/convert/batch
```

## Batch status

### Request

```http
GET /api/batch/{batch_id}
```

### Response shape

```json
{
  "batch_id": "uuid",
  "count": 3,
  "counts": {
    "queued": 1,
    "analyzing": 0,
    "converting": 1,
    "completed": 1,
    "failed": 0
  },
  "tasks": [
    {
      "id": "task-uuid",
      "batch_id": "uuid",
      "filename": "books/classic/book-a.pdf",
      "stored_path": "C:/.../uploads/batches/uuid/books/classic/book-a.pdf",
      "status": "queued",
      "progress": 0,
      "created_at": "2026-07-10T00:00:00"
    }
  ]
}
```

### Error responses

If the batch does not exist:

```json
{
  "detail": "Batch not found"
}
```

Suggested gateway public route:

```http
GET /api/agents/ocr-harness/batch/{batch_id}
```

## Task status

### Request

```http
GET /api/status/{task_id}
```

### Response shape

```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "status": "converting",
  "progress": 40,
  "created_at": "2026-07-09T00:00:00"
}
```

Status values can include:

```text
queued
analyzing
converting
completed
failed
```

Gateway public route:

```http
GET /api/agents/ocr-harness/status/{task_id}
```

This route remains the canonical way to inspect each file inside a batch. Host platforms can:

- show a batch overview through `GET /api/batch/{batch_id}`
- drill into per-file progress through `GET /api/status/{task_id}`

## OCR result and quality score

### Request

```http
GET /api/result/{task_id}
```

### Response shape

```json
{
  "id": "uuid",
  "filename": "document.pdf",
  "status": "completed",
  "progress": 100,
  "markdown": "# Extracted Markdown",
  "quality_score": 0.91,
  "quality_details": {},
  "engine_used": "surya",
  "corrections": [
    "table_correction",
    "formula_correction",
    "ordering_correction"
  ],
  "attempts": []
}
```

If the task is not complete, the API returns `400`.

If the task id is unknown, the API returns `404`.

Gateway public route:

```http
GET /api/agents/ocr-harness/result/{task_id}
```

## Download Markdown

### Request

```http
GET /api/download/{task_id}
```

### Response

Returns a Markdown file.

Gateway public route:

```http
GET /api/agents/ocr-harness/download/{task_id}
```

## Markdown formatter

### Request

```http
POST /api/format/markdown
Content-Type: application/json
```

### Body

```json
{
  "markdown": "#Title\ncontent",
  "fix_headings": true,
  "fix_lists": true,
  "merge_paragraphs": true,
  "remove_noise": true,
  "normalize_punctuation": true,
  "preserve_tables": true
}
```

### Response

```json
{
  "markdown": "# Title\n\ncontent\n",
  "stats": {
    "source_chars": 15,
    "result_chars": 17,
    "changed": true
  }
}
```

Gateway public route:

```http
POST /api/agents/ocr-harness/format/markdown
```

## RAG status

### Request

```http
GET /api/rag/status
```

### Response

```json
{
  "status": "ok",
  "documents": 100,
  "chunks": 1200
}
```

Gateway public route:

```http
GET /api/agents/ocr-harness/rag/status
```

## RAG rebuild from local corpus

### Request

```http
POST /api/rag/rebuild
Content-Type: application/json
```

### Body

```json
{
  "corpus_dir": "/data/books"
}
```

The server parses supported documents under the directory and rebuilds the local index.

Gateway public route:

```http
POST /api/agents/ocr-harness/rag/rebuild
```

## RAG rebuild from mounted knowledge sources

### Request

```http
POST /api/rag/rebuild-mounted
Content-Type: application/json
```

### Body

```json
{
  "source_ids": [],
  "sync_first": true
}
```

Gateway public route:

```http
POST /api/agents/ocr-harness/rag/rebuild-mounted
```

## RAG query

### Request

```http
POST /api/rag/query
Content-Type: application/json
```

### Body

```json
{
  "question": "What does this corpus say about ...?",
  "top_k": 8,
  "use_llm": true
}
```

### Response

```json
{
  "answer": "Answer text",
  "references": [
    {
      "title": "source document",
      "content": "matched excerpt",
      "score": 0.88
    }
  ],
  "stats": {}
}
```

Gateway public route:

```http
POST /api/agents/ocr-harness/rag/query
```

## Provider configuration

Provider APIs are administrative. They should be protected in zclum / 来客有方 with admin permissions.

### Register provider

```http
POST /api/providers
```

Body:

```json
{
  "name": "my-provider",
  "base_url": "https://api.example.com/v1",
  "api_key": "sk-...",
  "model": "gpt-4o-mini",
  "route_group": "default",
  "visible_provider": false,
  "preferred_for": ["ocr_correction", "rag_answer"]
}
```

### List providers

```http
GET /api/providers
```

The current backend masks provider base URLs in the list response.

### Verify providers

```http
POST /api/providers/verify
```

### Model catalog

```http
GET /api/providers/catalog/{name}
```

## Knowledge source APIs

These APIs let zclum attach local or external knowledge sources.

```http
GET    /api/kb-sources
POST   /api/kb-sources
PUT    /api/kb-sources/{source_id}
DELETE /api/kb-sources/{source_id}
POST   /api/kb-sources/{source_id}/sync
POST   /api/kb-sources/sync-all
```

Supported source types:

```text
local_dir
webdav
alist
```

## 来客有方 API Gateway behavior

Recommended gateway pseudo-code:

```js
const baseUrl = process.env.OCR_HARNESS_BASE_URL;

if (!baseUrl) {
  return json(
    {
      error: "ocr_harness_not_configured",
      message: "OCR-Harness base URL is not configured."
    },
    { status: 503 }
  );
}

return proxyRequest(request, {
  target: baseUrl,
  stripPrefix: "/api/agents/ocr-harness",
  addPrefix: "/api"
});
```

For file upload routes, keep request body streaming enabled and set upload limit to at least:

```text
200 MB
```

Recommended gateway timeout:

```text
600 seconds
```

## zclum UI entry suggestions

Recommended cards:

- Upload PDF
- OCR Task Status
- Markdown Result
- Quality Score
- Knowledge Retrieval
- Export Markdown
- Provider Settings

Recommended user flow:

```text
Upload PDF -> Poll task status -> Show Markdown -> Show quality score -> Export or send to RAG
```

Recommended RAG flow:

```text
Configure knowledge source -> Sync source -> Rebuild index -> Query -> Show answer and references
```

## Required fields for zclum deployment

The zclum platform only needs these fields from deployment:

```text
OCR_HARNESS_BASE_URL
OCR_HARNESS_PUBLIC_NAME
OCR_HARNESS_MAX_UPLOAD_MB
OCR_HARNESS_TIMEOUT_SECONDS
```

Recommended defaults:

```text
OCR_HARNESS_PUBLIC_NAME=OCR-Harness
OCR_HARNESS_MAX_UPLOAD_MB=200
OCR_HARNESS_TIMEOUT_SECONDS=600
```
