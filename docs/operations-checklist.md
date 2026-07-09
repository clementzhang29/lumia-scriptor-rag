# Lumia ScriptorRAG operations checklist

This checklist covers DNS, Aliyun security groups, HTTPS, backup, restore, logs, and troubleshooting.

## DNS

### Full domain deployment

Use this when Lumia ScriptorRAG should own the main domain.

```text
A     zclum.com        <ECS_PUBLIC_IP>
A     www.zclum.com    <ECS_PUBLIC_IP>
```

### API subdomain deployment

Use this when `zclum.com` stays on Vercel and Aliyun only hosts the backend.

```text
A     api.zclum.com    <ECS_PUBLIC_IP>
```

### DNS checks

```bash
dig zclum.com
dig www.zclum.com
dig api.zclum.com
curl -I http://zclum.com
```

## Aliyun security group

Required inbound rules:

```text
22/tcp     0.0.0.0/0      SSH
80/tcp     0.0.0.0/0      HTTP
443/tcp    0.0.0.0/0      HTTPS
```

Optional test-only rule:

```text
8080/tcp   your_ip/32     Direct app test
```

Do not keep `8080` open to the whole internet in production unless there is a specific reason.

## HTTPS

Use Certbot on Ubuntu:

```bash
apt-get update
apt-get install -y certbot python3-certbot-nginx
certbot --nginx -d zclum.com -d www.zclum.com
```

For API subdomain:

```bash
certbot --nginx -d api.zclum.com
```

Renewal check:

```bash
certbot renew --dry-run
```

## Backup

Runtime data is stored under:

```text
deploy/data/uploads
deploy/data/rag_db
deploy/data/kb_mounts
deploy/data/providers
```

Create backup:

```bash
cd /opt/lumia-scriptor-rag
tar -czf /opt/lumia-backup-$(date +%Y%m%d-%H%M%S).tar.gz deploy/data .env
```

Recommended backup schedule:

```text
Daily for active knowledge bases
Weekly for low-traffic demo deployments
Before every major upgrade
```

## Restore

Stop app:

```bash
cd /opt/lumia-scriptor-rag
docker compose down
```

Restore backup:

```bash
tar -xzf /opt/lumia-backup-YYYYMMDD-HHMMSS.tar.gz -C /opt/lumia-scriptor-rag
```

Start app:

```bash
docker compose up -d
curl http://127.0.0.1:8080/api/health
```

## Logs

Application logs:

```bash
cd /opt/lumia-scriptor-rag
docker compose logs -f --tail=200
```

Nginx logs:

```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

Container status:

```bash
docker ps
docker compose ps
```

## Common troubleshooting

### Domain does not open

Check:

```bash
dig zclum.com
curl -I http://127.0.0.1:8080
curl -I http://zclum.com
nginx -t
systemctl status nginx --no-pager -l
```

Likely causes:

- DNS points to the wrong IP
- Security group does not allow `80` or `443`
- Nginx is not running
- App container is not running

### Upload fails

Check Nginx upload size:

```nginx
client_max_body_size 200m;
```

Check logs:

```bash
docker compose logs -f --tail=200
tail -f /var/log/nginx/error.log
```

### OCR is slow

Likely causes:

- CPU-only server
- Large PDF
- OCR engine dependency not installed in the container

For a public lightweight deployment, start with OCR demo workloads and keep large OCR jobs private or move them to a GPU worker.

### RAG query has no results

Check:

```bash
curl http://127.0.0.1:8080/api/rag/status
```

Then rebuild the knowledge base from the UI or mounted sources page.

### Provider model calls fail

Check:

- API key validity
- Provider base URL
- Model name
- Outbound network from ECS
- Logs in `docker compose logs`

## Health check command

```bash
curl http://127.0.0.1:8080/api/health
```

Expected:

```json
{"status":"ok"}
```

