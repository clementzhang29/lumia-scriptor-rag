# Ubuntu 22.04 Deploy Runbook

Target server:

- `47.96.7.204`
- Ubuntu `22.04`
- target domain: `zclum.com`

This runbook assumes:

- you can SSH to the server
- Docker deployment is preferred
- frontend may be hosted by `zclum.com`, while OCR backend stays on ECS

## 1. SSH Login

Replace `root` with your real SSH user if needed.

```bash
ssh root@47.96.7.204
```

## 2. Install Docker and Base Packages

```bash
apt-get update
apt-get install -y ca-certificates curl git nginx

install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

. /etc/os-release
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list

apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

docker --version
docker compose version
```

## 3. Pull Project Code

Replace `REPO_URL` if the final GitHub repository address is different.

```bash
export APP_DIR=/opt/zclum-prism-ocr
export REPO_URL=https://github.com/clementzhang29/zclum-prism-ocr.git

mkdir -p /opt
git clone "$REPO_URL" "$APP_DIR"
cd "$APP_DIR"
```

If the directory already exists:

```bash
cd "$APP_DIR"
git pull --ff-only
```

## 4. Prepare Environment File

```bash
cp deploy/.env.example .env
cat .env
```

Default `.env`:

```dotenv
APP_PORT=8080
CUDA_VISIBLE_DEVICES=
```

CPU mode:

```dotenv
CUDA_VISIBLE_DEVICES=
```

GPU mode only when NVIDIA runtime is ready:

```dotenv
CUDA_VISIBLE_DEVICES=0
```

## 5. Start Backend

```bash
docker compose up -d --build
docker ps
docker compose logs --tail=200
```

## 6. Check Local Health

```bash
curl http://127.0.0.1:8080/api/health
```

Expected:

```json
{"status":"ok","timestamp":"..."}
```

## 7. Minimal Nginx Config

If `zclum.com` directly proxies the OCR app from this server:

```nginx
server {
    listen 80;
    server_name zclum.com www.zclum.com;

    client_max_body_size 200m;

    location /api/agents/ocr-harness/ {
        rewrite ^/api/agents/ocr-harness/(.*)$ /api/$1 break;
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
```

Write config:

```bash
cat > /etc/nginx/sites-available/zclum-prism-ocr <<'NGINX'
server {
    listen 80;
    server_name zclum.com www.zclum.com;

    client_max_body_size 200m;

    location /api/agents/ocr-harness/ {
        rewrite ^/api/agents/ocr-harness/(.*)$ /api/$1 break;
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
NGINX
```

Enable and reload:

```bash
ln -sf /etc/nginx/sites-available/zclum-prism-ocr /etc/nginx/sites-enabled/zclum-prism-ocr
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
systemctl status nginx --no-pager
```

## 8. Deployment Acceptance Order

Local health:

```bash
curl http://127.0.0.1:8080/api/health
```

Public health through reverse proxy:

```bash
curl http://zclum.com/api/agents/ocr-harness/health
curl https://zclum.com/api/agents/ocr-harness/health
```

Upload endpoint:

```bash
curl -X POST "http://zclum.com/api/agents/ocr-harness/convert" \
  -F "file=@tests/test_sample.pdf" \
  -F "strategy=auto" \
  -F "preferred_engine="
```

Status endpoint:

```bash
curl "http://zclum.com/api/agents/ocr-harness/status/<task_id>"
```

Result endpoint:

```bash
curl "http://zclum.com/api/agents/ocr-harness/result/<task_id>"
```

RAG query:

```bash
curl -X POST "http://zclum.com/api/agents/ocr-harness/rag/query" \
  -H "Content-Type: application/json" \
  -d '{"question":"测试问题","top_k":5,"use_llm":false}'
```

## 9. Manual Values That Must Be Supplied

- final GitHub repository URL
- final DNS for `zclum.com`
- whether OCR frontend lives at `/apps/prism-ocr`
- HTTPS certificate method
- token injection source:
  - `window.__ZCLUM_USER_TOKEN__`
  - or gateway-added `Authorization` header
- security-group settings for `80/443`
- whether port `8080` should remain private

## 10. Optional HTTPS

If DNS is already pointing at this server:

```bash
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d zclum.com -d www.zclum.com
```
