#!/bin/sh
# Genera el workflow, lo importa en el n8n local (contenedor n8n-coderhouse), lo publica y reinicia n8n.
# Ojo: el reinicio borra la Simple Memory (las charlas en curso).
set -e
cd "$(dirname "$0")"
WF_ID=ckp1AgenteLeads1
python3 build_workflow.py build/checkpoint1.json >/dev/null
docker cp build/checkpoint1.json n8n-coderhouse:/home/node/ckp1.json
docker exec n8n-coderhouse n8n import:workflow --input=/home/node/ckp1.json >/dev/null 2>&1
wait_up() { for i in $(seq 1 30); do curl -s -m 2 http://localhost:5678/healthz >/dev/null && break; sleep 2; done; sleep 4; }
for _ in 1 2; do   # el primer reinicio a veces deja cargada la versión anterior
  docker exec -e N8N_RUNNERS_BROKER_PORT=5699 n8n-coderhouse n8n publish:workflow --id=$WF_ID >/dev/null 2>&1
  docker restart n8n-coderhouse >/dev/null; wait_up
done
echo "redeployed $WF_ID"
