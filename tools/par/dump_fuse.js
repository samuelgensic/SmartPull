// dump_fuse.js — run through run.py. Prints the starting cubes of the Fuse chapter (levels 96-100):
// [cell [x,y,z], direction vector, arrow-face vector, fusion color (0-2 colors, 3-4 white/gray)].
(()=>{const T=window.__test,out={};
for(let i=95;i<100;i++){T.load(i);const B=T.blocks();out[i+1]={sig:T.levelSig(),cubes:B.map(b=>[b.c.slice(),b.d.slice(),b.arrowFace.slice(),b.fuseIdx])}}
return out})()
