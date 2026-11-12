#!/usr/bin/env bash
# Instalación en un servidor Debian/Ubuntu (o Raspberry Pi OS) en /opt/netpanel.
# Uso:  sudo bash deploy/instalar_linux.sh
set -euo pipefail

DESTINO=/opt/netpanel
ORIGEN="$(cd "$(dirname "$0")/.." && pwd)"

apt-get update
apt-get install -y python3 python3-venv iputils-ping

id netpanel >/dev/null 2>&1 || useradd -r -s /usr/sbin/nologin netpanel
mkdir -p "$DESTINO"
cp -r "$ORIGEN"/{panel,run.py,wsgi.py,herramientas.py,requirements.txt,ejemplos} "$DESTINO"/
python3 -m venv "$DESTINO/.venv"
"$DESTINO/.venv/bin/pip" install -r "$DESTINO/requirements.txt"

if [ ! -f "$DESTINO/.env" ]; then
  cp "$ORIGEN/.env.example" "$DESTINO/.env"
  CLAVE=$(python3 -c "import secrets; print(secrets.token_hex(32))")
  PASS=$(python3 -c "import secrets; print(secrets.token_urlsafe(12))")
  sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$CLAVE|; s|^MONITOR_ADMIN_PASSWORD=.*|MONITOR_ADMIN_PASSWORD=$PASS|" "$DESTINO/.env"
  echo ">>> Contraseña de admin generada: $PASS  (guárdala; está en $DESTINO/.env)"
fi
mkdir -p "$DESTINO/instance"
chown -R netpanel:netpanel "$DESTINO"
chmod 600 "$DESTINO/.env"

cp "$ORIGEN/deploy/netpanel.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now netpanel
echo ">>> Listo. Comprueba con: systemctl status netpanel   y   curl http://127.0.0.1:5000/api/estado"
