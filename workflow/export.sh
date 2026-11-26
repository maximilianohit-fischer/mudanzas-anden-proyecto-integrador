#!/bin/sh
# Exporta el workflow tal cual quedó en n8n (después de probarlo) al entregable del checkpoint.
set -e
cd "$(dirname "$0")/.."
OUT=${1:-checkpoint1_maximiliano_herr.json}
docker exec n8n-coderhouse n8n export:workflow --id=ckp1AgenteLeads1 --pretty --output=/home/node/ckp1_export.json >/dev/null
docker cp n8n-coderhouse:/home/node/ckp1_export.json "$OUT"
# n8n exporta una lista con metadatos de la instancia: se deja solo lo que trae el botón Download de la UI
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); d=d[0] if isinstance(d,list) else d; d={k: d[k] for k in ('name','nodes','pinData','connections','active','settings','versionId','meta','id','tags') if k in d}; d['pinData']={}
[n['parameters'].update(sendTo='supervisor@ejemplo.com') for n in d['nodes'] if n['type']=='n8n-nodes-base.gmail']
json.dump(d, open(sys.argv[1],'w'), ensure_ascii=False, indent=2)" "$OUT"
echo "exportado: $OUT"
