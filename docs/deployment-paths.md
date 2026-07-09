# Lumia ScriptorRAG deployment paths

This document gives three practical ways to deploy Lumia ScriptorRAG on an Aliyun ECS server.

## Path A: Docker Compose

Use this path when you have SSH access and want the cleanest deployment.

### Requirements

- Ubuntu 22.04 or 24.04
- SSH access
- Security group allows `22`, `80`, `443`
- Docker and Docker Compose plugin

### Commands

```bash
git clone https://github.com/clementzhang29/lumia-scriptor-rag.git
cd lumia-scriptor-rag
cp deploy/.env.example .env
docker compose up -d --build
curl http://127.0.0.1:8080/api/health
```

### Nginx

```bash
cp deploy/nginx/zclum.con.conf /etc/nginx/sites-available/lumia-scriptor-rag
ln -sf /etc/nginx/sites-available/lumia-scriptor-rag /etc/nginx/sites-enabled/lumia-scriptor-rag
nginx -t
systemctl reload nginx
```

### Best for

- Developers
- Production-like deployment
- Easy upgrades with `git pull` and `docker compose up -d --build`

## Path B: 1Panel

Use this path when the server has 1Panel installed.

### 1Panel steps

1. Open 1Panel.
2. Go to `App Store` and install `Docker` if it is not installed.
3. Go to `Website` and create a reverse proxy website.
4. Set domain to `zclum.com` or `api.zclum.com`.
5. Proxy target:

```text
http://127.0.0.1:8080
```

6. Go to `Terminal` or SSH and run:

```bash
cd /opt
git clone https://github.com/clementzhang29/lumia-scriptor-rag.git
cd lumia-scriptor-rag
cp deploy/.env.example .env
docker compose up -d --build
```

7. In 1Panel, enable HTTPS for the website.

### 1Panel reverse proxy notes

Recommended upload limit:

```text
200 MB
```

Recommended proxy timeout:

```text
600 seconds
```

### Best for

- Visual server management
- Easier SSL setup
- Users who prefer panel operations

## Path C: BT Panel

Use this path when the server uses BaoTa / BT Panel.

### BT Panel steps

1. Open BT Panel.
2. Install Nginx and Docker Manager.
3. Add a website:

```text
Domain: zclum.com
Root: any empty directory, for example /www/wwwroot/zclum.com
```

4. Open website settings and configure reverse proxy:

```text
Name: lumia-scriptor-rag
Target URL: http://127.0.0.1:8080
```

5. SSH into the server and run:

```bash
cd /opt
git clone https://github.com/clementzhang29/lumia-scriptor-rag.git
cd lumia-scriptor-rag
cp deploy/.env.example .env
docker compose up -d --build
```

6. In BT Panel, apply SSL certificate for `zclum.com`.

### BT Panel Nginx tuning

Add or verify:

```nginx
client_max_body_size 200m;
proxy_read_timeout 600s;
proxy_send_timeout 600s;
```

### Best for

- Existing BT Panel servers
- Fast domain binding
- Non-command-line server operations

## Which path to choose

Recommended order:

1. Docker Compose if you are comfortable with SSH.
2. 1Panel if you want cleaner visual operations.
3. BT Panel if the ECS already has BT installed.

For the first public version, use Docker Compose plus Nginx. It is easier to debug and easier to migrate later.

