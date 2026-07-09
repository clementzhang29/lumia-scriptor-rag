# Platform Handoff

Project path:

`C:\Users\35160\Documents\Codex\zclum-ocr-harness-agent`

## Current Status

- Backend OCR, formatting, RAG, provider, and knowledge-source APIs are present.
- Frontend supports standalone mode and embedded platform mode.
- Runtime host variables now support `zclum` first, with `anzaidx` kept only as a compatibility fallback.
- Provider UI hides supplier URLs by default.
- Open-source packaging files are present: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`, `.github/*`.

## Verified

- `npm run build` passes.
- zclum adapter manifest is valid JSON.
- frontend runtime configuration file exists.
- Docker compose file exists.
- Windows start/stop/tool scripts exist.
- obvious secret scan passes.

## Website Integration Status

Status:

`Partially complete`

What is done:

- frontend runtime injection support
- gateway route design
- agent manifest
- online launch guide
- platform adapter documentation

What still depends on the host platform:

- actual `zclum.com` route mounting
- gateway environment injection
- bearer token source
- upload and timeout policy
- production domain and HTTPS

## Required Platform Fields

- `OCR_HARNESS_BASE_URL`
- public app path such as `/apps/prism-ocr`
- user token injection field
- admin auth policy for provider management
- upload limit in MB
- OCR timeout in seconds
- file retention policy

