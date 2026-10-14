import os
import sys, json, asyncio
from playwright.async_api import async_playwright
HTML=sys.argv[1]; JS=sys.argv[2]
THREE=open(next(p for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','tests','vendor','three.min.js'),'/home/claude/three/src/build/three.min.js'] if os.path.exists(p))).read()
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(args=['--use-gl=swiftshader','--enable-unsafe-swiftshader'])
        pg=await b.new_page(viewport={'width':390,'height':844})
        await pg.add_init_script("try{localStorage.setItem('pa2_dev','1');localStorage.setItem('pa2_tier','full');localStorage.setItem('pa3_unlocked','100');localStorage.setItem('pa4_layout','100')}catch(e){}")
        await pg.route('**/three.min.js', lambda r: r.fulfill(body=THREE, content_type='application/javascript'))
        await pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        await pg.route('http://game.local/', lambda r: r.fulfill(body=open(HTML).read(), content_type='text/html'))
        errs=[]; pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('console', lambda m: print('LOG', m.text, flush=True) if m.text.startswith('@@') else None)
        await pg.goto('http://game.local/'); await pg.wait_for_timeout(1500)
        out=await pg.evaluate(open(JS).read())
        print(json.dumps(out,indent=0) if not isinstance(out,str) else out)
        print('ERRORS',errs)
        await b.close()
asyncio.run(main())
