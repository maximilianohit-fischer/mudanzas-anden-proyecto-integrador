"""Genera el workflow del Checkpoint 1 (M1 · Agente base) del Proyecto Integrador.

[Chat Trigger] -> [AI Agent (Tools Agent, máx. 6 iteraciones) + Gemini + Simple Memory
                   + Tool Google Sheets "registrar_lead"] -> [Respuesta en el chat]
               -> [Gmail · Log de observabilidad "Tarea completada"]
Si el agente falla: [Respuesta de contingencia] -> [Gmail · Alerta de falla]

Uso: python3 build_workflow.py [salida.json]
La configuración local (credenciales y destinatario del log) se lee de config.json
(ver config.example.json). Sin config.json se generan valores de ejemplo.
"""
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).parent
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "build" / "checkpoint1.json"
CFG_FILE = HERE / "config.json"
CFG = json.loads((CFG_FILE if CFG_FILE.exists() else HERE / "config.example.json").read_text())

SYSTEM_PROMPT = (HERE / "system_prompt.md").read_text(encoding="utf-8").strip()
TOOL_DESCRIPTION = (HERE / "tool_description.md").read_text(encoding="utf-8").strip()

WF_ID = "ckp1AgenteLeads1"
WF_NAME = "Checkpoint 1 · Agente de calificación de leads (Mudanzas Andén)"
MAX_ITER = 6
MODEL_NODE = "Google Gemini Chat Model"

TRIGGER = "Chat del cliente"
AGENT = "Andi · AI Agent (Tools Agent)"
TRG = f"$('{TRIGGER}').first().json"
AG = f"$('{AGENT}').first().json"

CRED_SHEETS = {"googleSheetsOAuth2Api": CFG["cred_sheets"]}
CRED_GMAIL = {"gmailOAuth2": CFG["cred_gmail"]}
CRED_LLM = {"googlePalmApi": CFG["cred_gemini"]}

COLUMNS = ["fecha_registro", "sesion", "nombre", "telefono", "origen", "destino", "ambientes",
           "fecha_mudanza", "pisos_por_escalera", "objetos_especiales", "calificacion", "resumen"]


def uid():
    return str(uuid.uuid4())


def node(name, ntype, version, pos, params, **extra):
    n = {"id": uid(), "name": name, "type": ntype, "typeVersion": version, "position": pos, "parameters": params}
    n.update(extra)
    return n


def fa(key, desc, typ="string"):
    return f"={{{{ $fromAI('{key}', `{desc}`, '{typ}') }}}}"


def sticky(name, pos, w, h, text, color=None):
    p = {"content": text, "width": w, "height": h}
    if color:
        p["color"] = color
    return node(name, "n8n-nodes-base.stickyNote", 1, pos, p)


# ---------- Expresiones del log ----------
STEPS = f"({AG}.intermediateSteps || [])"
TOOLS_HTML = (
    f"{{{{ {STEPS}.length ? {STEPS}.map((s, i) => '<li><b>' + (i + 1) + '. ' + s.action.tool + '</b><br>"
    "Argumentos: <code>' + JSON.stringify(s.action.toolInput) + '</code><br>Resultado: <code>' + "
    "String(typeof s.observation === 'string' ? s.observation : JSON.stringify(s.observation)).slice(0, 400)"
    " + '</code></li>').join('') : '<li>Ninguna: el agente respondió sin activar herramientas "
    "(consulta incompleta, escalamiento o fuera de ámbito).</li>' }}"
)
LOG_HTML = f"""=<h2>✅ Tarea completada · Agente de leads Mudanzas Andén</h2>
<p><b>Fecha:</b> {{{{ $now.setZone('America/Argentina/Buenos_Aires').toFormat('dd/LL/yyyy HH:mm:ss') }}}}<br>
<b>Ejecución n8n:</b> #{{{{ $execution.id }}}} · <b>Sesión:</b> {{{{ {TRG}.sessionId }}}}<br>
<b>Pasos con herramientas:</b> {{{{ {STEPS}.length }}}} · <b>Límite de iteraciones:</b> {MAX_ITER}<br>
<b>Lead registrado en la planilla:</b> {{{{ {STEPS}.some(s => s.action.tool === 'registrar_lead') ? 'SÍ' : 'NO' }}}}</p>
<h3>Mensaje del cliente</h3>
<blockquote>{{{{ {TRG}.chatInput }}}}</blockquote>
<h3>Herramientas ejecutadas (Execution Log)</h3>
<ol>{TOOLS_HTML}</ol>
<h3>Respuesta del agente</h3>
<blockquote>{{{{ {AG}.output }}}}</blockquote>
<p style="color:#888">Reporte automático de supervisión humana · workflow "{WF_NAME}"</p>"""

ERR_HTML = f"""=<h2>⚠️ Falla del agente de leads Mudanzas Andén</h2>
<p><b>Fecha:</b> {{{{ $now.setZone('America/Argentina/Buenos_Aires').toFormat('dd/LL/yyyy HH:mm:ss') }}}}<br>
<b>Ejecución n8n:</b> #{{{{ $execution.id }}}} · <b>Sesión:</b> {{{{ {TRG}.sessionId }}}}</p>
<h3>Mensaje del cliente</h3><blockquote>{{{{ {TRG}.chatInput }}}}</blockquote>
<h3>Error</h3><pre>{{{{ JSON.stringify($('{AGENT}').first().json.error || $('{AGENT}').first().json, null, 2).slice(0, 1500) }}}}</pre>
<p>El cliente recibió el mensaje de contingencia. Revisar la ejecución en n8n y contactarlo a mano.</p>"""

FALLBACK = ("Gracias por escribirnos. En este momento no puedo procesar tu consulta; "
            "una persona del equipo te va a escribir a la brevedad.")


def gmail(name, pos, subject, html):
    return node(name, "n8n-nodes-base.gmail", 2.2, pos, {
        "resource": "message", "operation": "send",
        "sendTo": CFG["log_email"],
        "subject": subject,
        "emailType": "html",
        "message": html,
        "options": {"appendAttribution": False},
    }, credentials=CRED_GMAIL, webhookId=uid(), onError="continueRegularOutput")


def chat_reply(name, pos, message):
    """Set node que deja {output} para el Chat Trigger (responseMode = lastNode)."""
    return node(name, "n8n-nodes-base.set", 3.4, pos, {
        "assignments": {"assignments": [{"id": uid(), "name": "output", "value": message, "type": "string"}]},
        "options": {},
    })


Y = 300
nodes = [
    node(TRIGGER, "@n8n/n8n-nodes-langchain.chatTrigger", 1.4, [0, Y], {
        "public": True,
        "mode": "hostedChat",
        "initialMessages": "¡Hola! Soy Andi, de Mudanzas Andén. Contame qué mudanza o flete necesitás.",
        "options": {"responseMode": "lastNode", "title": "Mudanzas Andén",
                    "subtitle": "Asistente de pedidos de mudanza"},
    }, webhookId="ckp1-chat-mudanzas-anden"),

    node(AGENT, "@n8n/n8n-nodes-langchain.agent", 1.7, [320, Y], {
        "agent": "toolsAgent",
        "promptType": "auto",
        "options": {
            "systemMessage": "=" + SYSTEM_PROMPT
            + "\n\n# CONTEXTO\nFecha y hora actual: {{ $now.setZone('America/Argentina/Buenos_Aires')"
              ".setLocale('es').toFormat(\"cccc d 'de' LLLL 'de' yyyy, HH:mm\") }}",
            "maxIterations": MAX_ITER,
            "returnIntermediateSteps": True,
        },
    }, onError="continueErrorOutput"),

    node(MODEL_NODE, "@n8n/n8n-nodes-langchain.lmChatGoogleGemini", 1.2, [180, Y + 260], {
        "modelName": CFG["gemini_model"],
        "options": {"temperature": 0.2, "maxOutputTokens": 1024},
    }, credentials=CRED_LLM, retryOnFail=True, maxTries=3, waitBetweenTries=3000),

    node("Memoria de la charla", "@n8n/n8n-nodes-langchain.memoryBufferWindow", 1.3, [360, Y + 260], {
        "sessionIdType": "fromInput", "contextWindowLength": 10,
    }),

    node("registrar_lead", "n8n-nodes-base.googleSheetsTool", 4.7, [560, Y + 260], {
        "descriptionType": "manual",
        "toolDescription": TOOL_DESCRIPTION,
        "operation": "append",
        "documentId": {"__rl": True, "value": CFG["sheet_id"], "mode": "id"},
        "sheetName": {"__rl": True, "value": "Leads", "mode": "name"},
        "columns": {
            "mappingMode": "defineBelow",
            "value": {
                "fecha_registro": "={{ $now.setZone('America/Argentina/Buenos_Aires').toFormat('yyyy-LL-dd HH:mm') }}",
                "sesion": f"={{{{ {TRG}.sessionId }}}}",
                "nombre": fa("nombre", "Nombre de la persona tal como lo escribió"),
                "telefono": fa("telefono", "Teléfono de contacto tal como lo escribió la persona"),
                "origen": fa("origen", "Localidad de origen (un barrio de Neuquén capital es 'Neuquén')"),
                "destino": fa("destino", "Localidad de destino"),
                "ambientes": fa("ambientes", "Cantidad de ambientes contando el living; 0 si es un flete de pocos bultos", "number"),
                "fecha_mudanza": fa("fecha_mudanza", "Fecha estimada en formato AAAA-MM-DD, o el texto que dijo la persona, o 'no informado'"),
                "pisos_por_escalera": fa("pisos_por_escalera", "Pisos que se suben o bajan por escalera, o 'no informado'"),
                "objetos_especiales": fa("objetos_especiales", "Objetos especiales separados por coma (heladera, lavarropas, piano, caja fuerte, cama box, aire acondicionado) o 'ninguno' o 'no informado'"),
                "calificacion": fa("calificacion", "caliente, tibio o frio según la fecha, con las reglas del system prompt"),
                "resumen": fa("resumen", "Una oración con el pedido y cualquier detalle útil para el área de presupuestos"),
            },
            "matchingColumns": [],
            "schema": [{"id": c, "displayName": c, "required": False, "defaultMatch": False, "display": True,
                        "type": "string", "canBeUsedToMatch": True} for c in COLUMNS],
            "attemptToConvertTypes": False,
            "convertFieldsToString": False,
        },
        "options": {},
    }, credentials=CRED_SHEETS),

    # Las dos ramas salen en paralelo del agente. Con executionOrder v1 se ejecuta primero la de
    # arriba (Gmail) y al final la respuesta, que es lo que el Chat Trigger devuelve (lastNode).
    gmail("Gmail · Log de observabilidad", [760, Y - 300],
          f"=✅ Tarea completada · Agente Mudanzas Andén · sesión {{{{ {TRG}.sessionId }}}}"
          f"{{{{ {STEPS}.some(s => s.action.tool === 'registrar_lead') ? ' · lead registrado' : '' }}}}",
          LOG_HTML),
    chat_reply("Respuesta al cliente", [760, Y - 140], f"={{{{ {AG}.output }}}}"),

    gmail("Gmail · Alerta de falla", [760, Y + 20],
          f"=⚠️ Falla del agente · Mudanzas Andén · sesión {{{{ {TRG}.sessionId }}}}", ERR_HTML),
    chat_reply("Respuesta de contingencia", [760, Y + 160], FALLBACK),

    sticky("Nota · Arquitectura", [-60, -340], 1100, 240,
           "## Checkpoint 1 · Agente base (M1)\n"
           "**Trigger** (Chat) → **AI Agent en modo Tools Agent** → en paralelo: **Gmail: log de observabilidad** (nodo final de notificación) y la respuesta al cliente en el chat.\n\n"
           f"- **Guardrail:** máximo {MAX_ITER} iteraciones del ciclo ReAct (Options → Max Iterations).\n"
           "- **System Prompt modular:** Rol → Ámbito → Objetivo → Reglas de la herramienta → Escalamiento → Prohibiciones.\n"
           "- **Tool lateral:** `registrar_lead` (Google Sheets, append) con descripción de negocio extensa; el agente decide cuándo usarla.\n"
           "- **Observabilidad:** cada ejecución manda un mail \"✅ Tarea completada\" con el mensaje, las herramientas usadas (intermediate steps) y la respuesta. Si el agente falla, sale una alerta.\n"
           "- **Memoria:** Simple Memory por sesión (en M3 se reemplaza por Airtable)."),
    sticky("Nota · Extensiones del agente", [140, Y + 200], 560, 240,
           "### Extensiones (sub-nodos) del agente\nModelo · Memoria · **Tool** acoplada al costado, no en el lienzo secuencial.", color=5),
]

# Rama de error: la salida 1 del agente (onError = continueErrorOutput)
link = lambda n, t="main", i=0: {"node": n, "type": t, "index": i}
connections = {
    TRIGGER: {"main": [[link(AGENT)]]},
    AGENT: {"main": [[link("Gmail · Log de observabilidad"), link("Respuesta al cliente")],
                     [link("Gmail · Alerta de falla"), link("Respuesta de contingencia")]]},
    MODEL_NODE: {"ai_languageModel": [[link(AGENT, "ai_languageModel")]]},
    "Memoria de la charla": {"ai_memory": [[link(AGENT, "ai_memory")]]},
    "registrar_lead": {"ai_tool": [[link(AGENT, "ai_tool")]]},
}

wf = {
    "id": WF_ID,
    "name": WF_NAME,
    "nodes": nodes,
    "connections": connections,
    "active": False,
    "settings": {"executionOrder": "v1", "timezone": "America/Argentina/Buenos_Aires",
                 "saveManualExecutions": True, "saveDataSuccessExecution": "all"},
    "pinData": {},
    "tags": [],
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(wf, ensure_ascii=False, indent=2), encoding="utf-8")
print(OUT)
