#!/bin/sh
# Genera los 3 workflows del Checkpoint 3, los importa en el n8n local, los publica y reinicia n8n.
set -e
cd "$(dirname "$0")"
python3 build_checkpoint3.py build >/dev/null
for f in ckp3_worker1 ckp3_worker2 ckp3_manager; do
  docker cp build/$f.json n8n-coderhouse:/home/node/$f.json
  docker exec n8n-coderhouse n8n import:workflow --input=/home/node/$f.json >/dev/null 2>&1
done
wait_up() { for i in $(seq 1 30); do curl -s -m 2 http://localhost:5678/healthz >/dev/null && break; sleep 2; done; sleep 4; }
for _ in 1 2; do   # el primer reinicio a veces deja cargada la versión anterior
  for id in ckp3WorkerLeads1 ckp3WorkerEscal1 ckp3ManagerAnden; do
    docker exec -e N8N_RUNNERS_BROKER_PORT=5699 n8n-coderhouse n8n publish:workflow --id=$id 2>&1 | tail -1
  done
  docker restart n8n-coderhouse >/dev/null; wait_up
done
echo "redeployed checkpoint 3"
