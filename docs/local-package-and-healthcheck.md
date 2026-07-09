# Local package and health check

Use this document when GitHub is temporarily unreachable or when you want to upload the project to an ECS server manually.

## Create a local deployment package on Windows

Run from PowerShell:

```powershell
cd C:\Users\35160\Documents\Codex\ocr-harness-v0.1.0
.\deploy\server\package_local.ps1
```

Default output:

```text
C:\Users\35160\Desktop\lumia-scriptor-rag-deploy.zip
```

The package excludes:

- `.git`
- `node_modules`
- build artifacts
- logs
- runtime uploads
- local deployment data

## Upload package to ECS

Example:

```powershell
scp C:\Users\35160\Desktop\lumia-scriptor-rag-deploy.zip root@<ECS_PUBLIC_IP>:/opt/
```

On the server:

```bash
cd /opt
apt-get update
apt-get install -y unzip
unzip lumia-scriptor-rag-deploy.zip -d lumia-scriptor-rag
cd lumia-scriptor-rag
cp deploy/.env.example .env
docker compose up -d --build
```

## Server health check

If the repository is already on the server:

```bash
cd /opt/lumia-scriptor-rag
DOMAIN=zclum.com ./deploy/server/check_server.sh
```

If you only need a quick app check:

```bash
curl http://127.0.0.1:8080/api/health
docker compose ps
docker compose logs --tail=100
```

## Browser checks

After Nginx is configured:

```bash
curl -I http://zclum.com
curl -I https://zclum.com
```

Expected:

- HTTP returns `200`, `301`, or `308`
- HTTPS returns `200`
- `/api/health` returns JSON with `status: ok`

## Rollback

If a new deployment fails:

```bash
cd /opt/lumia-scriptor-rag
docker compose down
```

Restore the previous backup described in `docs/operations-checklist.md`, then:

```bash
docker compose up -d
```

