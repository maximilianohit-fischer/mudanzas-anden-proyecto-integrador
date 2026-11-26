#!/bin/sh
# Resumen de las últimas N ejecuciones: nodos ejecutados, herramientas que llamó el agente, salida y errores.
N=${1:-1}
docker exec n8n-coderhouse sh -c 'cd /usr/local/lib/node_modules/n8n && node -e "
const S=require(\"sqlite3\");const db=new S.Database(\"/home/node/.n8n/database.sqlite\");
db.all(\"select e.id,e.status,d.data from execution_entity e join execution_data d on d.executionId=e.id where e.workflowId=\x27ckp1AgenteLeads1\x27 order by e.id desc limit '$N'\",(e,rows)=>{
if(e) return console.log(e); const {parse}=require(\"flatted\");
for (const r of rows.reverse()) { const x=parse(r.data); const rd=x.resultData.runData||{};
 console.log(\"\n#### exec\",r.id,r.status); for (const k of Object.keys(rd)) { const run=rd[k][rd[k].length-1]; console.log(\"  -\",k,\"x\"+rd[k].length, run.executionStatus||\"\", run.error?(\"ERROR: \"+run.error.message):\"\"); }
 if (x.resultData.error) console.log(\"ERROR:\", x.resultData.error.message);
 (rd[\"registrar_lead\"]||[]).forEach(run=>{console.log(\"  -> registrar_lead in:\", JSON.stringify(run.inputOverride?.ai_tool?.[0]?.[0]?.json).slice(0,500)); console.log(\"     out:\", JSON.stringify(run.data?.ai_tool?.[0]?.[0]?.json).slice(0,300));});
 const ag=Object.keys(rd).find(k=>k.startsWith(\"Andi\")); const o=ag&&rd[ag][0].data?.main; if(o) { const it=(o[0]&&o[0][0])||(o[1]&&o[1][0]); console.log(\"  output:\", JSON.stringify(it?.json?.output||it?.json).slice(0,600)); console.log(\"  pasos:\", (it?.json?.intermediateSteps||[]).length); }
}});"'
