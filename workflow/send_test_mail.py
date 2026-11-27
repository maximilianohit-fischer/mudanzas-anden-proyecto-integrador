"""Manda un correo de prueba a la casilla +andi con la credencial Gmail de M1–M3 (la que puede enviar).
Uso: python3 send_test_mail.py "Asunto" "Cuerpo"   (corre un workflow temporal en el n8n local)"""
import json, subprocess, sys, uuid
from pathlib import Path
HERE = Path(__file__).parent
CFG = json.loads((HERE / "config.json").read_text())
subject, body = sys.argv[1], sys.argv[2]
wf = {"id": "ckp4TestSender01", "name": "Checkpoint 4 · Envío de correo de prueba (herramienta de test)", "active": False,
      "settings": {"executionOrder": "v1"}, "pinData": {}, "connections": {"Manual": {"main": [[{"node": "Enviar", "type": "main", "index": 0}]]}},
      "nodes": [
          {"id": str(uuid.uuid4()), "name": "Manual", "type": "n8n-nodes-base.manualTrigger", "typeVersion": 1, "position": [0, 0], "parameters": {}},
          {"id": str(uuid.uuid4()), "name": "Enviar", "type": "n8n-nodes-base.gmail", "typeVersion": 2.1, "position": [220, 0],
           "parameters": {"resource": "message", "operation": "send", "sendTo": CFG["andi_inbox"], "subject": subject,
                          "emailType": "text", "message": body, "options": {"appendAttribution": False, "senderName": "Prueba Andi"}},
           "credentials": {"gmailOAuth2": CFG["cred_gmail"]}, "webhookId": str(uuid.uuid4())}]}
p = HERE / "build" / "ckp4_test_sender.json"
p.write_text(json.dumps(wf, ensure_ascii=False))
sh = lambda *a: subprocess.run(a, check=True, capture_output=True, text=True)
sh("docker", "cp", str(p), "n8n-coderhouse:/home/node/ckp4_test_sender.json")
sh("docker", "exec", "n8n-coderhouse", "n8n", "import:workflow", "--input=/home/node/ckp4_test_sender.json")
r = subprocess.run(["docker", "exec", "-e", "N8N_RUNNERS_BROKER_PORT=5698", "n8n-coderhouse", "n8n", "execute", "--id=ckp4TestSender01"],
                   capture_output=True, text=True)
print("enviado" if '"labelIds"' in r.stdout or '"id"' in r.stdout else r.stdout[-1500:] + r.stderr[-1500:])
