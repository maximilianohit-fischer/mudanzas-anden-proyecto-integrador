#!/bin/sh
# Manda los mensajes de ../pruebas/*.json al Chat Trigger público y guarda las respuestas.
# Cada archivo es una lista de turnos: [{"sessionId": "...", "chatInput": "..."}, ...]
# (los turnos de un mismo archivo comparten sessionId, así se prueba la memoria).
cd "$(dirname "$0")/../pruebas"
URL=${URL:-http://localhost:5678/webhook/ckp1-chat-mudanzas-anden/chat}
OUTDIR=${OUTDIR:-respuestas}
mkdir -p "$OUTDIR"
for f in ${@:-*.json}; do
  echo "== $f"; : > "$OUTDIR/$f.tmp"
  python3 -c "import json,sys; [print(json.dumps(t, ensure_ascii=False)) for t in json.load(open(sys.argv[1]))]" "$f" |
  while IFS= read -r turno; do
    body=$(printf '%s' "$turno" | python3 -c "import json,sys; t=json.load(sys.stdin); t['action']='sendMessage'; print(json.dumps(t, ensure_ascii=False))")
    s=$(date +%s)
    resp=$(curl -s -m 300 -X POST "$URL" -H 'Content-Type: application/json' --data-binary "$body")
    python3 - "$turno" "$resp" "$(( $(date +%s) - s ))" >> "$OUTDIR/$f.tmp" <<'PY'
import json, sys
t = json.loads(sys.argv[1]); raw = sys.argv[2]
try: r = json.loads(raw)
except Exception: r = raw
print(json.dumps({"cliente": t["chatInput"], "respuesta": r, "segundos": int(sys.argv[3])}, ensure_ascii=False))
PY
    tail -1 "$OUTDIR/$f.tmp"
  done
  python3 -c "import json,sys; print(json.dumps([json.loads(l) for l in open(sys.argv[1])], ensure_ascii=False, indent=2))" "$OUTDIR/$f.tmp" > "$OUTDIR/$f"
  rm "$OUTDIR/$f.tmp"
done
