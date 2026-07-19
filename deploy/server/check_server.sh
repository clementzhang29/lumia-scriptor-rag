#!/usr/bin/env bash
set -u

DOMAIN="${DOMAIN:-zclum.com}"

echo "== OS =="
uname -a
if [ -f /etc/os-release ]; then
  cat /etc/os-release
fi

echo
echo "== Network =="
hostname -I || true
curl -fsS ifconfig.me || true
echo

echo
echo "== DNS =="
getent hosts "$DOMAIN" || true
getent hosts "www.$DOMAIN" || true

echo
echo "== Ports =="
ss -tulpn | grep -E ':80|:443|:8080' || true

echo
echo "== Docker =="
docker --version || true
docker compose version || true
docker ps || true

echo
echo "== Nginx =="
nginx -v || true
nginx -t || true
systemctl status nginx --no-pager -l || true

echo
echo "== App Health =="
curl -fsS http://127.0.0.1:8080/api/health || true
echo
