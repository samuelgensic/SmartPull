import os
import sys, json, asyncio
from playwright.async_api import async_playwright
HTML=sys.argv[1]; P=json.load(open('paths.json')); only=[int(x) for x in sys.argv[2].split(',')] if len(sys.argv)>2 else None
THREE=open(next(p for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','tests','vendor','three.min.js'),'/home/claude/three/src/build/three.min.js'] if os.path.exists(p))).read()
JS='''async ([i,path])=>{const T=window.__test;T.load(i-1);await new Promise(r=>setTimeout(r,300));let manual=0;
 const wait=async()=>{await new Promise(r=>setTimeout(r,120));for(let t=0;t<80;t++){if(!T.blocks().some(b=>b.busy))break;await new Promise(r=>setTimeout(r,60))}await new Promise(r=>setTimeout(r,250))};
 const sig=T.levelSig();
 for(const mv of path){const b=T.blocks()[ (window.__map||null) ? 0 : 0 ];
   const [k,j]=mv;const bl=T.alive?null:null;
   const blocks=T.blocks();
   // solver indices: src levels index alive blocks at start (= all blocks); gen levels index blocks directly
   const c=blocks[j];
   if(k==='dot'){manual++;T.spin(c)}else if(k==='pivot'){manual++;T.pivotTurn(c)}else if(k==='glass'){T.glassTap(c)}else T.slide(c);
   await wait()}
 await new Promise(r=>setTimeout(r,800));const c=T.counts();
 return {sig,left:T.blocks().filter(b=>b.alive).length,moves:c.pulls+c.taps+c.bumps+manual,bumps:c.bumps,cleared:T.state().clearing}}'''
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader'])
        pg=await b.new_page(viewport={'width':390,'height':844})
        await pg.add_init_script("try{localStorage.setItem('pa2_dev','1');localStorage.setItem('pa2_tier','full');localStorage.setItem('pa3_unlocked','100');localStorage.setItem('pa4_layout','100');localStorage.setItem('pa2_sound','0')}catch(e){}")
        await pg.route('**/three.min.js', lambda r: r.fulfill(body=THREE, content_type='application/javascript'))
        await pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        await pg.route('http://game.local/', lambda r: r.fulfill(body=open(HTML).read(), content_type='text/html'))
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://game.local/'); await pg.wait_for_timeout(1500)
        for k in sorted(P,key=int):
            i=int(k)
            if only and i not in only: continue
            r=await pg.evaluate(JS,[i,P[k]])
            ok=r['left']==0 and r['bumps']==0 and r['moves']==len(P[k])
            print(json.dumps({'lv':i,'par':len(P[k]),'ok':ok,**r}),flush=True)
        print('ERRORS',errs)
        await b.close()
asyncio.run(main())
