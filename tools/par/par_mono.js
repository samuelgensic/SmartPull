// Exact par for generated levels WITHOUT gravity (dots, linked pairs, pair dots, locks).
//
// Why this is exact and tiny: with no gravity, cube positions never change and removing a cube can only
// help every other cube (rays clear, arrow faces uncovered, keys gone, dot faces uncovered). So pulling a
// cube the moment it is free is never worse (the pull is mandatory anyway, and it only ever removes
// obstacles). Every plan therefore costs  pulls (= units, fixed)  +  dot taps, and an optimal plan can be
// rearranged to "pull everything that is free, then tap a dot, repeat". The search is a BFS over dot taps
// only; each state is closed under free pulls. par = units + fewest dot taps.
//
// Note: alive flags are an array, NOT a 32-bit mask (par_gen.js's `m&2**j` breaks for 32+ cubes).
// Edit window.__only to pick levels. Set window.__check=true to also report states explored.
(()=>{const T=window.__test,K=T.K,turn=T.turn,out={};
const only=window.__only||null,span=16;
for(let i=0;i<100;i++){if(only&&!only.includes(i+1))continue;T.load(i);if(T.src())continue;const B=T.blocks();
 if(B.some(b=>b.fuseIdx!=null)){out[i+1]={skip:'fuse'};continue}
 if(T.grav()){out[i+1]={skip:'gravity'};continue}
 if(B.some(b=>b.glide||b.num||b.glass||b.pivot||b.echo!=null)){out[i+1]={skip:'other rule'};continue}
 const t0=performance.now(),n=B.length;
 const pairOf=B.map(b=>b.partner?b.partner.id:-1),lockOf=B.map(b=>b.lockKey?b.lockKey.id:-1);
 const pos=B.map(b=>b.c.slice());
 const start={alive:new Uint8Array(n).fill(1),d:B.map(b=>b.d.slice()),f:B.map(b=>b.arrowFace.slice())};
 const key=s=>{let k='';for(let j=0;j<n;j++){if(!s.alive[j]){k+='x';continue}k+=(s.d[j].join(',')+'/'+s.f[j].join(',')+';')}return k};
 const occOf=s=>{const o=new Map();for(let j=0;j<n;j++)if(s.alive[j])o.set(K(...pos[j]),j);return o};
 const unitOf=(s,j)=>pairOf[j]>=0&&s.alive[pairOf[j]]?[j,pairOf[j]]:[j];
 // the game's own rules, same as par_gen.js
 const covered=(occ,j,f)=>occ.has(K(pos[j][0]+f[0],pos[j][1]+f[1],pos[j][2]+f[2]));
 const canPull=(s,occ,j)=>{if(covered(occ,j,s.f[j]))return null;if(lockOf[j]>=0&&s.alive[lockOf[j]])return null;
   const unit=unitOf(s,j);if(unit.some(u=>T.rayBlocked(pos[u],s.d[j],occ,unit,span,false)))return null;return unit};
 // close a state under free pulls; returns the list of pulls made
 const close=s=>{const gos=[];let changed=true;while(changed){changed=false;const occ=occOf(s);
   for(let j=0;j<n;j++){if(!s.alive[j])continue;const unit=canPull(s,occ,j);if(!unit)continue;
     unit.forEach(u=>{s.alive[u]=0;occ.delete(K(...pos[u]))});gos.push(['go',j]);changed=true}}
   return gos};
 const taps=s=>{const occ=occOf(s),res=[];
  for(let j=0;j<n;j++){if(!s.alive[j])continue;const b=B[j];if(!b.axis||covered(occ,j,b.dotFace))continue;
   const unit=unitOf(s,j),tu=b.pairDot&&unit.length>1?unit:[j];
   const ns={alive:s.alive.slice(),d:s.d.slice(),f:s.f.slice()};
   tu.forEach(u=>{ns.d[u]=turn(s.d[u],B[u].axis||b.axis);ns.f[u]=turn(s.f[u],B[u].axis||b.axis)});
   res.push([ns,['dot',j]])}
  return res};
 const s0=start;const g0=close(s0);const seen=new Map([[key(s0),{p:null,mv:g0}]]);let layer=[s0],tapCount=0,found=null;
 const done=s=>!s.alive.some(x=>x);
 if(done(s0))found=s0;
 while(!found&&layer.length){const next=[];tapCount++;
  for(const s of layer){const ks=key(s);
   for(const [ns,mv] of taps(s)){const gos=close(ns);const k=key(ns);if(seen.has(k))continue;seen.set(k,{p:ks,mv:[mv,...gos]});next.push(ns);if(!found&&done(ns))found=ns}}
  layer=next}
 if(!found){out[i+1]={fail:'none',states:seen.size};console.log('@@'+(i+1)+' fail '+seen.size);continue}
 const path=[];let k=key(found);while(seen.get(k).p!==null){const e=seen.get(k);path.unshift(...e.mv);k=e.p}path.unshift(...g0);
 out[i+1]={par:path.length,taps:path.filter(m=>m[0]==='dot').length,path,states:seen.size,ms:Math.round(performance.now()-t0),pairs:pairOf.some(x=>x>=0),locks:lockOf.some(x=>x>=0)};
 console.log('@@'+(i+1)+' par '+path.length+' states '+seen.size)}
return out})()
