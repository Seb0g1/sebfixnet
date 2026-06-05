#!/bin/bash
set -euo pipefail

APP_DIR="/opt/sebfixnet"
REPO_URL="https://github.com/Seb0g1/sebfixnet.git"
DOMAIN="fixnet.sebog1.ru"

echo "==> Installing system packages..."
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git python3 python3-venv python3-pip nginx certbot python3-certbot-nginx curl

echo "==> Cloning/updating app..."
if [ -d "$APP_DIR/.git" ]; then
  cd "$APP_DIR"
  git pull origin main
else
  rm -rf "$APP_DIR"
  git clone "$REPO_URL" "$APP_DIR"
  cd "$APP_DIR"
fi

echo "==> Writing .env..."
if [ -n "${DEPLOY_ENV_B64:-}" ]; then
  echo "$DEPLOY_ENV_B64" | base64 -d > "$APP_DIR/.env"
elif [ ! -f "$APP_DIR/.env" ]; then
  echo "ERROR: .env missing. Set DEPLOY_ENV_B64 or create $APP_DIR/.env" >&2
  exit 1
fi
chmod 600 "$APP_DIR/.env"

echo "==> Backend venv..."
cd "$APP_DIR/backend"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
mkdir -p data

echo "==> Bot venv..."
cd "$APP_DIR/bot"
python3 -m venv .venv
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt

echo "==> Systemd services..."
cp "$APP_DIR/server/systemd/fixnet-backend.service" /etc/systemd/system/
cp "$APP_DIR/server/systemd/fixnet-bot.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable fixnet-backend fixnet-bot
systemctl restart fixnet-backend
sleep 2
systemctl restart fixnet-bot

echo "==> Nginx..."
if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  cp "$APP_DIR/server/nginx-fixnet.conf" "/etc/nginx/sites-available/$DOMAIN"
else
  cp "$APP_DIR/server/nginx-fixnet-http.conf" "/etc/nginx/sites-available/$DOMAIN"
fi
ln -sf "/etc/nginx/sites-available/$DOMAIN" "/etc/nginx/sites-enabled/$DOMAIN"
rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
nginx -t
systemctl enable nginx
systemctl restart nginx

echo "==> SSL certificate..."
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
  certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos -m admin@sebog1.ru --redirect || true
  if [ -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    cp "$APP_DIR/server/nginx-fixnet.conf" "/etc/nginx/sites-available/$DOMAIN"
    nginx -t && systemctl reload nginx
  fi
fi

echo "==> Status..."
systemctl is-active fixnet-backend fixnet-bot nginx
curl -sf "http://127.0.0.1:8080/" | head -c 200 || echo "API check pending..."
echo ""
echo "Deploy complete: https://$DOMAIN"
