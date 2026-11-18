#!/usr/bin/env python3
"""Regenerates tz-wg-install.sh (the single-file installer) from the repo files.

Run:  python3 build.py
"""
import pathlib

here = pathlib.Path(__file__).parent
app = (here / "app.py").read_text().rstrip("\n")
dockerfile = (here / "Dockerfile").read_text()
compose = (here / "docker-compose.yml").read_text()
for name, text in (("app.py", app), ("Dockerfile", dockerfile), ("docker-compose.yml", compose)):
    assert "EOF_TZ" not in text, name + " contains the heredoc marker"

TEMPLATE = r'''#!/usr/bin/env bash
# =====================================================================
#  TZ VPN - WireGuard installer (single file)
#  Upload this file to a fresh Ubuntu/Debian VPS and run:
#      sudo bash tz-wg-install.sh
#  It installs Docker, starts a WireGuard server and an admin panel.
#  Per-user data limit (GB) and expiry are optional.
#
#  Optional: choose your own admin password at install time:
#      sudo TZ_ADMIN_PASSWORD='MyStrongPass' bash tz-wg-install.sh
# =====================================================================
set -euo pipefail

DIR=/opt/tz-wg

if [ "$(id -u)" -ne 0 ]; then
  echo "Please run as root:  sudo bash $0" >&2
  exit 1
fi

echo "=============================="
echo "   TZ VPN  -  WireGuard"
echo "=============================="

if ! command -v curl >/dev/null 2>&1; then
  apt-get update -y && apt-get install -y curl
fi
if ! command -v ss >/dev/null 2>&1; then
  apt-get update -y && apt-get install -y iproute2
fi
if ! command -v docker >/dev/null 2>&1; then
  echo ">> Installing Docker..."
  curl -fsSL https://get.docker.com | sh
fi
if ! docker compose version >/dev/null 2>&1; then
  apt-get update -y && apt-get install -y docker-compose-plugin
fi

mkdir -p "$DIR/data"
cd "$DIR"
chmod 700 "$DIR/data"

cat > Dockerfile <<'EOF_TZ_DOCKERFILE'
@@DOCKERFILE@@EOF_TZ_DOCKERFILE

cat > docker-compose.yml <<'EOF_TZ_COMPOSE'
@@COMPOSE@@EOF_TZ_COMPOSE

cat > app.py <<'EOF_TZ_APP'
@@APP@@
EOF_TZ_APP

# first install only: create .env (an existing .env is never overwritten)
port_in_use() { ss -H -ln"$1" 2>/dev/null | awk '{print $4}' | grep -Eq "[:.]$2\$"; }
free_port() { p="$2"; while port_in_use "$1" "$p"; do p=$((p + 1)); done; echo "$p"; }

if [ ! -f .env ]; then
  IP="$(curl -fsS4 --max-time 10 https://api.ipify.org || true)"
  {
    echo "ADMIN_PASSWORD=${TZ_ADMIN_PASSWORD:-tzalmamun}"
    echo "WG_PORT=$(free_port u 51820)"
    echo "PANEL_PORT=$(free_port t 4444)"
    echo "SERVER_HOST=$IP"
    echo "# PANEL_BIND=127.0.0.1   # uncomment to hide the panel from the internet (use an SSH tunnel)"
  } > .env
  chmod 600 .env
fi

echo ">> Building and starting (first time takes a few minutes)..."
docker compose up -d --build

set -a; . ./.env; set +a
echo ""
echo "=============================================="
echo "  TZ VPN is running"
echo "  Admin panel : https://${SERVER_HOST:-YOUR_SERVER_IP}:${PANEL_PORT}"
echo "  Password    : ${ADMIN_PASSWORD}"
echo "  WireGuard   : UDP ${WG_PORT}"
echo "=============================================="
if [ "${ADMIN_PASSWORD}" = "tzalmamun" ]; then
  echo "!! You are using the DEFAULT password. Change it: edit ADMIN_PASSWORD in $DIR/.env"
  echo "   then run:  cd $DIR && docker compose up -d"
fi
echo "The browser will warn about the certificate (self-signed): choose Advanced > Continue."
echo "Open ${WG_PORT}/udp and ${PANEL_PORT}/tcp in your VPS provider's firewall if one exists."
echo "Logs: cd $DIR && docker compose logs"
'''

out = (TEMPLATE.replace("@@DOCKERFILE@@", dockerfile)
       .replace("@@COMPOSE@@", compose)
       .replace("@@APP@@", app))
target = here / "tz-wg-install.sh"
target.write_text(out)
target.chmod(0o755)
print("wrote", target, len(out), "bytes")
