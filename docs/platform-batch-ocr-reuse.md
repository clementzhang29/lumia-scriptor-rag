# Batch OCR Reuse Contract

This note defines the smallest stable batch OCR contract that both `zclum` and `来客有方` can reuse without forking backend behavior.

## Recommended shared routes

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

## Shared request fields

- `strategy`
- `preferred_engine`
- `file`
- `files`

## Shared response fields

Single task:

- `task_id`
- `status`

Batch task:

- `batch_id`
- `task_ids`
- `count`
- `status`

Per-file status:

- `id`
- `batch_id`
- `filename`
- `status`
- `progress`
- `created_at`

Per-batch status:

- `batch_id`
- `count`
- `counts`
- `tasks`

Completed OCR result:

- `markdown`
- `quality_score`
- `quality_details`
- `engine_used`
- `corrections`
- `attempts`

## Recommended host-side behavior

- Use `convert` when the user selects a single PDF.
- Use `convert/batch` when the user selects multiple PDFs or a folder.
- Poll `batch/{batch_id}` for overview cards and progress bars.
- Poll `status/{task_id}` for each file detail row.
- Open `result/{task_id}` only after `status=completed`.

## Common error payloads

- `{"detail":"No files uploaded"}`
- `{"detail":"Task not found"}`
- `{"detail":"Batch not found"}`
- `{"detail":"Task not completed, current status: converting"}`
- `{"error":"ocr_harness_not_configured","message":"OCR-Harness base URL is not configured."}`

## Safe reuse boundaries

These routes and fields are suitable for both websites because they do not expose provider secrets or internal storage details as required host inputs.

Provider administration routes should remain admin-only:

- `GET /api/agents/ocr-harness/providers`
- `POST /api/agents/ocr-harness/providers`
- `POST /api/agents/ocr-harness/providers/verify`
