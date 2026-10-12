(()=>{const T=window.__test,r={};for(let i=0;i<100;i++){T.load(i);if(!T.src())continue;
 const t0=performance.now();const res=T.solverFor()(T.liveSpec(),{limit:1500000});
 r[i+1]=res.path?{par:res.path.length,ms:Math.round(performance.now()-t0),states:res.states,path:res.path}:{fail:res.fail,ms:Math.round(performance.now()-t0)}}
 return r})()
