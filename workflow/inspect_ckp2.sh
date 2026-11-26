#!/bin/sh
# Resumen de las últimas N ejecuciones de los workflows del Checkpoint 2 (Manager y Workers).
N=${1:-3}
docker exec n8n-coderhouse sh -c 'cd /usr/local/lib/node_modules/n8n && node -e "
const S=require(\"sqlite3\");const db=new S.Database(\"/home/node/.n8n/database.sqlite\");
db.all(\"select e.id,e.workflowId,e.status,e.mode,e.startedAt,e.stoppedAt,d.data from execution_entity e join execution_data d on d.executionId=e.id where e.workflowId like \x27ckp2%\x27 order by e.id desc limit '$N'\",(e,rows)=>{
if(e) return console.log(e); const {parse}=require(\"flatted\");
for (const r of rows.reverse()) { const x=parse(r.data); const rd=x.resultData.runData||{};
 console.log(\"\n#### exec\",r.id,r.workflowId,r.status,r.mode,(new Date(r.stoppedAt)-new Date(r.startedAt))/1000+\"s\");
 for (const k of Object.keys(rd)) { const run=rd[k][rd[k].length-1]; const o=run.data?.main||[]; const outs=o.map((b,i)=>b&&b.length?i:null).filter(v=>v!==null);
   let j=\"\"; for (const b of o) if (b&&b[0]) { j=JSON.stringify(b[0].json).slice(0,350); break; }
   console.log(\"  -\",k,run.executionStatus||\"\",\"out\"+JSON.stringify(outs), run.error?(\"ERROR: \"+run.error.message):\"\", j); }
 if (x.resultData.error) console.log(\"ERROR:\", x.resultData.error.message);
}});"'
