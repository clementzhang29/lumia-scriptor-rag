#!/usr/bin/env bash
set -euo pipefail

APP_DIR="${APP_DIR:-/opt/zclum-prism-ocr}"
REPO_URL="${REPO_URL:-https://github.com/clementzhang29/zclum-prism-ocr.git}"
DOMAIN="${DOMAIN:-zclum.com}"
EMAIL="${EMAIL:-}"
ENABLE_HTTPS="${ENABLE_HTTPS:-0}"

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root."
  exit 1
fi

echo "[1/8] Installing base packages"
apt-get update
apt-get install -y ca-certificates curl git nginx

echo "[2/8] Installing Docker if missing"
if ! command -v docker >/dev/null 2>&1; then
  install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
  chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${VERSION_CODENAME} stable" > /etc/apt/sources.list.d/docker.list
  apt-get update
  apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi

echo "[3/8] Preparing app directory"
mkdir -p "$(dirname "$APP_DIR")"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
else
  git -C "$APP_DIR" pull --ff-only
fi

echo "[4/8] Preparing environment"
cd "$APP_DIR"
if [ ! -f .env ]; then
  cp deploy/.env.example .env
fi

echo "[5/8] Starting application"
docker compose up -d --build

echo "[6/8] Writing nginx config"
cat > /etc/nginx/sites-available/zclum-prism-ocr <<NGINX
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};

    client_max_body_size 200m;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 600s;
        proxy_send_timeout 600s;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/zclum-prism-ocr /etc/nginx/sites-enabled/zclum-prism-ocr
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [ "$ENABLE_HTTPS" = "1" ]; then
  echo "[7/8] Enabling HTTPS"
  apt-get install -y certbot python3-certbot-nginx
  if [ -n "$EMAIL" ]; then
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
  else
    certbot --nginx -d "$DOMAIN" -d "www.$DOMAIN"
  fi
else
  echo "[7/8] Skipping HTTPS. Set ENABLE_HTTPS=1 to enable certbot."
fi

echo "[8/8] Health check"
curl -fsS http://127.0.0.1:8080/api/health
echo
echo "Done. Public site target: http://${DOMAIN}"
echo "Local health: http://127.0.0.1:8080/api/health"
