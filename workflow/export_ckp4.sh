#!/bin/sh
# Exporta el workflow del Checkpoint 4 desde n8n (casilla real reemplazada por una de ejemplo, sin staticData).
set -e
cd "$(dirname "$0")/.."
out=checkpoint4_maximiliano_herr.json
docker exec n8n-coderhouse n8n export:workflow --id=ckp4AndiIntegra1 --pretty --output=/home/node/ckp4_export.json >/dev/null
docker cp n8n-coderhouse:/home/node/ckp4_export.json "$out"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d=d[0] if isinstance(d,list) else d; d={k: d[k] for k in ('name','nodes','pinData','connections','active','settings','versionId','meta','id','tags') if k in d}; d['pinData']={}; d['active']=False
for n in d['nodes']:
    if n['type']=='n8n-nodes-base.gmailTrigger': n['parameters']['filters']['q']='to:casilla+andi@ejemplo.com'
json.dump(d, open(sys.argv[1],'w'), ensure_ascii=False, indent=2)" "$out"
echo "exportado: $out"
