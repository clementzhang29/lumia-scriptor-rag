# ECS Deployment Checklist

Target host:

- `47.96.7.204`
- Ubuntu `22.04`
- region: `cn-hangzhou`

Primary target domain:

- `zclum.com`

## Components That Must Run On The Server

- FastAPI backend
- OCR engine runtime environment
- local RAG / knowledge-base storage
- reverse proxy (`nginx`)
- process manager:
  - `docker compose` is already prepared
  - `systemd` is optional only if you do not use Docker

## Components That Do Not Need Separate Server Hosting

- standalone frontend static files do not need a separate site if `zclum.com` already serves the host shell
- the frontend can be embedded into the host platform and use gateway routes
- a separate frontend server process is unnecessary when the built `frontend/dist` is served by the host platform or by nginx as static files

## Required Directories

- app directory: `/opt/zclum-prism-ocr`
- upload data: `/opt/zclum-prism-ocr/deploy/data/uploads`
- rag db: `/opt/zclum-prism-ocr/deploy/data/rag_db`
- knowledge mounts: `/opt/zclum-prism-ocr/deploy/data/kb_mounts`
- provider store: `/opt/zclum-prism-ocr/deploy/data/providers`

## Required Open Ports

- `80` for HTTP
- `443` for HTTPS
- `22` for SSH
- `8080` only if you want direct health/debug access from outside

Recommended:

- public access only through `80/443`
- keep `8080` limited to localhost or security-group restricted access

## Environment Variables

- `APP_PORT=8080`
- `CUDA_VISIBLE_DEVICES=` for CPU mode
- `CUDA_VISIBLE_DEVICES=0` only if GPU runtime is ready
- `SCRIPTOR_RAG_HOST=0.0.0.0`
- `SCRIPTOR_RAG_PORT=8080`
- `SCRIPTOR_RAG_UPLOAD_DIR=/data/uploads`
- `SCRIPTOR_RAG_DB_DIR=/data/rag_db`
- `SCRIPTOR_RAG_KB_MOUNT_DIR=/data/kb_mounts`
- `SCRIPTOR_RAG_PROVIDER_STORE=/data/providers/providers.json`

## Startup Method

Preferred:

```bash
cd /opt/zclum-prism-ocr
cp deploy/.env.example .env
docker compose up -d --build
```

Alternative without Docker:

```bash
python -B -m uvicorn src.web.app:app --host 0.0.0.0 --port 8080
```

## Reverse Proxy Paths

If frontend is hosted by the same server:

- `/` -> `http://127.0.0.1:8080`

If `zclum.com` host shell embeds the OCR app:

- `/apps/prism-ocr` -> frontend static app
- `/api/agents/ocr-harness/*` -> `http://47.96.7.204:8080/api/*`

Nginx requirements:

- `client_max_body_size 200m`
- `proxy_read_timeout 600s`
- `proxy_send_timeout 600s`

## Health Checks

Local:

```text
http://127.0.0.1:8080/api/health
```

Public gateway:

```text
https://zclum.com/api/agents/ocr-harness/health
```

## What Is Still Needed From Platform / Ops

- final GitHub repository URL if it differs from current script default
- final production route:
  - `/apps/prism-ocr` or another path
- `zclum.com` DNS control
- HTTPS certificate method
- security-group permission to open `80/443`
- whether direct `8080` access should stay closed
- runtime user-token injection source
