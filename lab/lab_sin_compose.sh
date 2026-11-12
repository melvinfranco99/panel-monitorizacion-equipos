#!/usr/bin/env bash
# Mismo laboratorio que docker-compose.yml, pero solo con "docker" (por si no tienes compose).
#   bash lab/lab_sin_compose.sh arrancar   -> http://localhost:5000  (admin / laboratorio)
#   docker stop lab-pc-contabilidad        -> simula una caída
#   docker start lab-pc-contabilidad       -> recuperación
#   bash lab/lab_sin_compose.sh borrar
set -euo pipefail
cd "$(dirname "$0")/.."
RED=netpanel-lab-red
EQUIPOS=("lab-router 172.30.0.2" "lab-servidor-ficheros 172.30.0.21" "lab-pc-recepcion 172.30.0.50"
         "lab-pc-contabilidad 172.30.0.51" "lab-impresora 172.30.0.100")

case "${1:-}" in
  arrancar)
    docker build -t netpanel-lab .
    docker network inspect $RED >/dev/null 2>&1 || docker network create --subnet 172.30.0.0/24 $RED
    for e in "${EQUIPOS[@]}"; do
      read -r nombre ip <<< "$e"
      docker run -d --name "$nombre" --network $RED --ip "$ip" alpine:3.20 sleep infinity
    done
    docker run -d --name lab-servidor-web --network $RED --ip 172.30.0.20 nginx:alpine
    docker run -d --name netpanel --network $RED --ip 172.30.0.10 -p 5000:5000 \
      -e TZ=Europe/Madrid -e MONITOR_INTERVALO=10 -e MONITOR_ADMIN_PASSWORD=laboratorio \
      -e SECRET_KEY=solo-para-el-laboratorio netpanel-lab \
      sh -c "python herramientas.py importar lab/equipos_lab.csv && gunicorn -w 1 --threads 8 -b 0.0.0.0:5000 wsgi:app"
    echo ">>> Abre http://localhost:5000  (admin / laboratorio)"
    ;;
  borrar)
    docker rm -f netpanel lab-servidor-web $(for e in "${EQUIPOS[@]}"; do echo "${e%% *}"; done) 2>/dev/null || true
    docker network rm $RED 2>/dev/null || true
    echo ">>> Laboratorio borrado"
    ;;
  *) echo "Uso: bash lab/lab_sin_compose.sh arrancar|borrar"; exit 1 ;;
esac
