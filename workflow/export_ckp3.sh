#!/bin/sh
# Exporta los 3 workflows del Checkpoint 3 desde n8n (destinatario del mail reemplazado por uno de ejemplo).
set -e
cd "$(dirname "$0")/.."
mkdir -p checkpoint3
for pair in ckp3ManagerAnden:manager ckp3WorkerLeads1:worker1 ckp3WorkerEscal1:worker2; do
  id=${pair%%:*}; out=checkpoint3/${pair##*:}_modulo3_herr_maximiliano.json
  docker exec n8n-coderhouse n8n export:workflow --id=$id --pretty --output=/home/node/$id.json >/dev/null
  docker cp n8n-coderhouse:/home/node/$id.json "$out"
  python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d=d[0] if isinstance(d,list) else d; d={k: d[k] for k in ('name','nodes','pinData','connections','active','settings','versionId','meta','id','tags') if k in d}; d['pinData']={}
[n['parameters'].update(sendTo='supervisor@ejemplo.com') for n in d['nodes'] if n['type']=='n8n-nodes-base.gmail']
json.dump(d, open(sys.argv[1],'w'), ensure_ascii=False, indent=2)" "$out"
  echo "exportado: $out"
done
