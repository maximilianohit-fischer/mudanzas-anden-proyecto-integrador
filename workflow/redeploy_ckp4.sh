#!/bin/sh
# Genera el workflow del Checkpoint 4, lo importa en el n8n local (conservando el staticData del
# Gmail Trigger para no reprocesar correos viejos), opcionalmente lo publica y reinicia n8n.
set -e
cd "$(dirname "$0")"
python3 build_checkpoint4.py >/dev/null
if docker exec n8n-coderhouse n8n export:workflow --id=ckp4AndiIntegra1 --output=/home/node/ckp4_prev.json >/dev/null 2>&1; then
  docker cp n8n-coderhouse:/home/node/ckp4_prev.json build/ckp4_prev.json
  python3 -c "import json; p=json.load(open('build/ckp4_prev.json')); p=p[0] if isinstance(p,list) else p; n=json.load(open('build/ckp4_andi.json')); n['staticData']=p.get('staticData'); json.dump(n, open('build/ckp4_andi.json','w'), ensure_ascii=False, indent=2)"
fi
docker cp build/ckp4_andi.json n8n-coderhouse:/home/node/ckp4_andi.json
docker exec n8n-coderhouse n8n import:workflow --input=/home/node/ckp4_andi.json >/dev/null 2>&1
if [ "${1:-}" = "--publish" ]; then
  docker exec -e N8N_RUNNERS_BROKER_PORT=5699 n8n-coderhouse n8n publish:workflow --id=ckp4AndiIntegra1 2>&1 | tail -1
fi
docker restart n8n-coderhouse >/dev/null
for i in $(seq 1 30); do curl -s -m 2 http://localhost:5678/healthz >/dev/null && break; sleep 2; done; sleep 4
echo "redeployed checkpoint 4"
