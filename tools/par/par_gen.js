(()=>{const T=window.__test,K=T.K,turn=T.turn,out={};
const only=window.__only||null;
for(let i=0;i<100;i++){if(only&&!only.includes(i+1))continue;T.load(i);if(T.src())continue;const B=T.blocks();if(B.some(b=>b.fuseIdx!=null))continue;
 const n=B.length,grav=T.grav(),span=16,t0=performance.now();
 const pairOf=B.map(b=>b.partner?b.partner.id:-1),lockOf=B.map(b=>b.lockKey?b.lockKey.id:-1);
 const dotted=B.map((b,j)=>b.axis?j:-1).filter(j=>j>=0);
 const start={m:2**n-1,pos:B.map(b=>b.c.slice()),d:B.map(b=>b.d.slice()),f:B.map(b=>b.arrowFace.slice())};
 const key=s=>s.m+'|'+dotted.map(j=>s.d[j].join(',')+s.f[j].join(',')).join(';')+(grav?'|'+s.pos.map((p,j)=>(s.m&2**j)?p[1]:'').join(','):'');
 const alive=(s,j)=>(s.m&2**j)!==0;
 function moves(s){const occ=new Map();for(let j=0;j<n;j++)if(alive(s,j))occ.set(K(...s.pos[j]),j);const res=[];
  const cov=(j,f)=>(grav&&f[1]===-1)||occ.has(K(s.pos[j][0]+f[0],s.pos[j][1]+f[1],s.pos[j][2]+f[2]));
  for(let j=0;j<n;j++){if(!alive(s,j))continue;const b=B[j];
   const unit=pairOf[j]>=0&&alive(s,pairOf[j])?[j,pairOf[j]]:[j];
   if(b.axis&&!cov(j,b.dotFace)){const tu=b.pairDot&&unit.length>1?unit:[j];const d=s.d.slice(),f=s.f.slice();tu.forEach(u=>{d[u]=turn(s.d[u],B[u].axis||b.axis);f[u]=turn(s.f[u],B[u].axis||b.axis)});res.push([{m:s.m,pos:s.pos,d,f},['dot',j]])}
   if(cov(j,s.f[j]))continue;
   if(lockOf[j]>=0&&alive(s,lockOf[j]))continue;
   const D=s.d[j];if(unit.some(u=>T.rayBlocked(s.pos[u],D,occ,unit,span,grav)))continue;
   let m=s.m;unit.forEach(u=>m-=2**u);let pos=s.pos;
   if(grav){pos=s.pos.map(p=>p.slice());const gone=new Set();for(let u=0;u<n;u++)if(!(m&2**u))gone.add(u);T.settle(pos,new Map(),gone)}
   res.push([{m,pos,d:s.d,f:s.f},['go',j]])}
  return res}
 const hU=s=>{let c=0;const sn=new Set();for(let j=0;j<n;j++)if(alive(s,j)){const p=pairOf[j]>=0&&alive(s,pairOf[j])?Math.min(j,pairOf[j]):j;if(!sn.has(p)){sn.add(p);c++}}return c};
 const seen=new Map([[key(start),[null,null,0]]]),buckets=[];const push=(st,g)=>{const f=g+hU(st);(buckets[f]||(buckets[f]=[])).push([st,g])};push(start,0);
 let found=null,lim=window.__lim||1500000,fi=0;
 outer:for(;fi<buckets.length;fi++){const bk=buckets[fi];if(!bk)continue;while(bk.length){const [s,g]=bk.pop();const ks=key(s);if(seen.get(ks)[2]<g)continue;
   if(s.m===0){found=s;break outer}if(seen.size>lim)break outer;
   for(const [ns,mv] of moves(s)){const k=key(ns),o=seen.get(k);if(!o||o[2]>g+1){seen.set(k,[ks,mv,g+1]);push(ns,g+1)}}}}
 if(!found){console.log("@@"+(i+1)+" fail "+seen.size);out[i+1]={fail:seen.size>lim?'limit':'none',states:seen.size,ms:Math.round(performance.now()-t0)};continue}
 const path=[];let k=key(found);while(seen.get(k)[0]!==null){const [pk,mv]=seen.get(k);path.unshift(mv);k=pk}
 console.log("@@"+(i+1)+" "+path.length+" "+seen.size);out[i+1]={par:path.length,path,states:seen.size,ms:Math.round(performance.now()-t0),grav,locks:lockOf.some(x=>x>=0),pairs:pairOf.some(x=>x>=0)}}
return out})()
