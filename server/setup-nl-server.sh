#!/usr/bin/env bash
set -euo pipefail

# InetFix NL server bootstrap (Ubuntu 22/24)
# Usage: sudo bash setup-nl-server.sh

INETFIX_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${INETFIX_DIR}/.env"

echo "=== InetFix Server Setup ==="

if [[ $EUID -ne 0 ]]; then
  echo "Run as root: sudo bash $0"
  exit 1
fi

apt-get update -qq
apt-get install -y curl docker.io docker-compose-plugin python3 python3-pip openssl

systemctl enable --now docker

if [[ ! -f "$ENV_FILE" ]]; then
  cp "${INETFIX_DIR}/.env.example" "$ENV_FILE"
  echo "Created .env from example — edit before continuing!"
fi

# Generate Xray REALITY keys if placeholders remain
XRAY_CFG="${INETFIX_DIR}/server/xray/config.json"
if grep -q "REPLACE_WITH_PRIVATE_KEY" "$XRAY_CFG"; then
  KEYS=$(docker run --rm teddysun/xray:latest xray x25519)
  PRIVATE_KEY=$(echo "$KEYS" | awk '/PrivateKey/ {print $2}')
  PUBLIC_KEY=$(echo "$KEYS" | awk '/Password/ {print $2}')
  sed -i "s/REPLACE_WITH_PRIVATE_KEY/${PRIVATE_KEY}/" "$XRAY_CFG"
  sed -i "s|XRAY_PUBLIC_KEY=.*|XRAY_PUBLIC_KEY=${PUBLIC_KEY}|" "$ENV_FILE" 2>/dev/null || \
    echo "XRAY_PUBLIC_KEY=${PUBLIC_KEY}" >> "$ENV_FILE"
  echo "Generated REALITY keys. Public key saved to .env"
fi

mkdir -p "${INETFIX_DIR}/server/releases"
mkdir -p "${INETFIX_DIR}/backend/data"

cd "${INETFIX_DIR}/server"
docker compose build
docker compose up -d

echo ""
echo "=== Done ==="
echo "API:    http://$(curl -s ifconfig.me):8080/docs"
echo "Edit:   ${ENV_FILE}"
echo "Logs:   docker compose -f ${INETFIX_DIR}/server/docker-compose.yml logs -f"
