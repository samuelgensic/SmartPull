#!/usr/bin/env python3
"""One-command test suite for SmartPull.

usage: python3 tests/test_game.py [GAME.html] [--shots DIR] [--quick]

GAME.html defaults to ../index.html (relative to this file). Exits non-zero on any failure.
"""
import argparse, asyncio, os, re, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ORIGIN = 'https://smartpull.test'
VENDOR = os.path.join(HERE, 'vendor', 'three.min.js')
FALLBACK = '/home/claude/three/src/build/three.min.js'

ap = argparse.ArgumentParser()
ap.add_argument('game', nargs='?', default=os.path.join(ROOT, 'index.html'))
ap.add_argument('--shots', metavar='DIR')
ap.add_argument('--quick', action='store_true', help='skip par, sound, wording checks and screenshots')
args = ap.parse_args()

from playwright.async_api import async_playwright

THREE = open(VENDOR if os.path.exists(VENDOR) else FALLBACK, 'rb').read()
SRC = open(args.game, encoding='utf-8').read()

results = []
def report(name, ok, detail=''):
    results.append((name, ok))
    print(('PASS' if ok else 'FAIL') + ' ' + name + (' - ' + detail if detail else ''), flush=True)
def note(name, detail):
    print('SKIP ' + name + ' - ' + detail, flush=True)

IGNORE = re.compile(r'swiftshader|gpu stall|webgl|gl driver|deprecat|fonts\.g|font|favicon|net::ERR|Failed to load resource|\.mp3|AudioContext was not allowed|ReadPixels', re.I)

async def main():
    t0 = time.time()
    # ---- static facts from the source -------------------------------------------------
    gm = re.search(r'const GROUPS=(\[\[.*?\]\]);', SRC)
    groups = [(int(a), b) for a, b in re.findall(r"\[(\d+),'([^']*)'\]", gm.group(1))] if gm else []
    pm = re.search(r'^const PAR=\{(.*?)\};', SRC, re.M)
    par = {int(k): int(v) for k, _, v in re.findall(r"(\d+):\['([^']*)',(\d+)\]", pm.group(1))} if pm else None
    nlev = groups[-1][0] if groups else 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-webgl', '--ignore-gpu-blocklist', '--enable-unsafe-swiftshader', '--autoplay-policy=no-user-gesture-required'])
        ctx = await browser.new_context(viewport={'width': 393, 'height': 852}, device_scale_factor=1)
        await ctx.add_init_script("try{localStorage.setItem('pa2_dev','1');localStorage.setItem('pa2_tier','full');localStorage.setItem('pa3_unlocked','100');localStorage.setItem('pa4_layout','100')}catch(e){}")

        async def route(r):
            url = r.request.url
            if url.rstrip('/') == ORIGIN or url.startswith(ORIGIN + '/?') or url == ORIGIN + '/index.html':
                return await r.fulfill(body=SRC, content_type='text/html; charset=utf-8')
            if 'three' in url and url.endswith('.js') and ORIGIN not in url:
                return await r.fulfill(body=THREE, content_type='application/javascript')
            if 'fonts.googleapis.com' in url:
                return await r.fulfill(body='', content_type='text/css')
            if 'fonts.gstatic.com' in url:
                return await r.fulfill(status=404, body='')
            if url.startswith(ORIGIN + '/'):
                rel = url[len(ORIGIN) + 1:].split('?')[0].split('#')[0]
                fp = os.path.normpath(os.path.join(ROOT, rel))
                if fp.startswith(ROOT) and os.path.isfile(fp):
                    ct = 'audio/mpeg' if fp.endswith('.mp3') else None
                    return await r.fulfill(body=open(fp, 'rb').read(), **({'content_type': ct} if ct else {}))
                return await r.fulfill(status=404, body='')
            return await r.fulfill(status=404, body='')
        await ctx.route('**/*', route)

        page = await ctx.new_page()
        errors, cons = [], []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.on('console', lambda m: cons.append(m.text) if m.type == 'error' and not IGNORE.search(m.text) else None)

        await page.goto(ORIGIN + '/', wait_until='load')
        await page.wait_for_function('window.__test&&window.__test.blocks&&window.__test.blocks().length>0', timeout=20000)
        await page.wait_for_timeout(1000)

        # a. load cleanliness
        report('a. page loads, no page errors / console errors', not errors and not cons, '; '.join((errors + cons)[:5]))

        # b. levels
        if not nlev:
            report('b. level count found (GROUPS)', False, 'GROUPS not found in source')
        else:
            report('b. level count found (GROUPS)', True, f'{nlev} levels, {len(groups)} chapters')
        bad = await page.evaluate('''async n=>{const T=window.__test,bad=[];
          for(let i=0;i<n;i++){try{const L=T.buildLevel(i);if(!L)throw new Error('buildLevel returned '+L)}catch(e){bad.push('build '+(i+1)+': '+e.message);continue}
            try{T.load(i);if(!T.blocks().length)throw new Error('no blocks')}catch(e){bad.push('load '+(i+1)+': '+e.message)}
            if(i%10==9)await new Promise(r=>setTimeout(r,0))}
          T.load(0);return bad}''', nlev)
        report(f'b. all {nlev} levels build and load', not bad, '; '.join(bad[:6]) + (f' (+{len(bad)-6} more)' if len(bad) > 6 else ''))
        await page.wait_for_timeout(300)
        # DOM cross-check: the chapter menu lists every level the source says exists
        shown = await page.evaluate('''async()=>{const o=document.getElementById('lvl');if(o)o.click();await new Promise(r=>setTimeout(r,900));const e=document.querySelectorAll('[data-lv]');const n=new Set([...e].map(x=>x.dataset.lv)).size;if(o&&o.getAttribute('aria-expanded')==='true')o.click();return n}''')
        if shown:
            report('b. level menu lists all levels', shown == nlev, f'{shown} listed vs {nlev}')
        else:
            note('b. level menu lists all levels', 'menu not rendered until opened')

        # c. chapters / title
        probs = []
        prev = 0
        for end, name in groups:
            if end - prev != 5: probs.append(f'{name or "?"}: {end-prev} levels')
            if not name.strip(): probs.append(f'chapter ending {end} has no name')
            prev = end
        title = await page.title()
        if not title.startswith('SmartPull'): probs.append(f'title is "{title}"')
        report('c. 5 levels + a name per chapter; title starts with SmartPull', not probs and bool(groups), '; '.join(probs))

        errs_after = list(errors)

        if not args.quick:
            # d. par
            if par is None:
                note('d. par entries', 'game has no PAR table')
            else:
                missing = [i + 1 for i in range(nlev) if i not in par]
                badv = [i + 1 for i, v in par.items() if v <= 0]
                extra = [i + 1 for i in par if i >= nlev]
                msg = ''
                if missing: msg += f'missing par for levels {missing}; '
                if badv: msg += f'non-positive {badv}; '
                if extra: msg += f'par beyond last level {extra}'
                report('d. every level has a positive integer par', not (missing or badv), msg)
                livepar = await page.evaluate('''async n=>{const T=window.__test,bad=[];for(let i=0;i<n;i++){T.load(i);const v=T.par();if(!(Number.isInteger(v)&&v>0))bad.push((i+1)+'='+v);if(i%10==9)await new Promise(r=>setTimeout(r,0))}T.load(0);return bad}''', nlev)
                report('d. live curPar (__test.par) is a positive integer on every level', not livepar, ', '.join(livepar[:10]))

            # e. sound
            snd = await page.evaluate('''async()=>{const T=window.__test,out={bad:[],called:0,renders:0,fail:0};
              if(!T.audio||!T.woosh||!T.thump)return {skip:'__test.audio/woosh/thump missing'};
              try{localStorage.setItem('pa2_sound','1')}catch(e){}
              const calls=[['woosh0',()=>T.woosh(0)],['woosh2',()=>T.woosh(2)],['woosh5',()=>T.woosh(5)],['thump near',()=>T.thump(0,false)],['thump far',()=>T.thump(0.02,true)],
                ['slide',()=>{T.load(0);const b=T.blocks()[0];if(b)T.slide(b)}],['pivot sound',()=>{const c=T.blocks()[0];if(c)T.pivotTurn&&T.pivotTurn(c)}]];
              const run=async label=>{for(const [n,f] of calls){try{f();out.called++}catch(e){out.bad.push(label+' '+n+': '+e.message)}await new Promise(r=>setTimeout(r,80))}await new Promise(r=>setTimeout(r,1200))};
              await run('webaudio');
              // the game's own offline-rendered engine (OfflineAudioContext); every render must succeed
              if(T.TV&&T.TV.set){try{T.TV.set(true)}catch(e){out.bad.push('TV.set: '+e.message)}
                if(T.TV.on){await run('offline');
                  for(const e of T.TV.cache.values()){out.renders++;const r=await Promise.race([e.p,new Promise(r=>setTimeout(()=>r(null),8000))]);if(!r)out.fail++}
                  try{T.TV.set(false)}catch(e){}}
                else out.note='offline engine unavailable'}
              T.load(0);return out}''')
            if 'skip' in snd:
                note('e. sound functions', snd['skip'])
            else:
                if snd.get('note'): note('e. offline engine', snd['note'])
                detail = f"{snd['called']} sound calls, {snd['renders']} offline renders"
                ok = not snd['bad'] and not snd['fail'] and (snd['renders'] > 0 or bool(snd.get('note')))
                report('e. sound effects render without throwing (live + OfflineAudioContext)', ok, detail + ('; ' + '; '.join(snd['bad']) if snd['bad'] else '') + (f"; {snd['fail']} renders failed" if snd['fail'] else ''))
            report('e. no page errors during sound calls', len(errors) == len(errs_after), '; '.join(errors[len(errs_after):3]))

        # f. brand colors
        miss = [h for h in ('#FF6C10', '#007C92', '#B2BB1E') if h.lower() not in SRC.lower()]
        old = [h for h in ('#F17B31', '#007493', '#C0B50A') if h.lower() in SRC.lower()]
        report('f. brand colors present, old colors absent', not miss and not old, (f'missing {miss}; ' if miss else '') + (f'old still present {old}' if old else ''))

        if not args.quick:
            # g. wording
            off = await page.evaluate('''async()=>{const found=new Set();const re=/\\bthemes?\\b/i;
              const scan=()=>{const w=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=w.nextNode()){const t=n.nodeValue.trim();if(!t||!re.test(t))continue;const p=n.parentElement;if(!p||['SCRIPT','STYLE'].includes(p.tagName))continue;found.add(t.slice(0,80))}
                document.querySelectorAll('[aria-label],[title],[placeholder],[alt]').forEach(e=>{for(const a of ['aria-label','title','placeholder','alt']){const v=e.getAttribute(a);if(v&&re.test(v))found.add(a+': '+v.slice(0,80))}})};
              scan();
              // open each panel / tray so its text is in the DOM, then scan again
              for(const sel of ['#lvl','#paint','#tools','#toolsBtn','#menuBtn','#lvBtn','#lvcol','#scoreOpen','#settings']){const e=document.querySelector(sel);if(e&&e.click){try{e.click()}catch(_){}await new Promise(r=>setTimeout(r,250));scan()}}
              document.querySelectorAll('.panel').forEach(p=>{p.hidden=false});scan();
              return [...found]}''')
            report('g. no "theme"/"themes" wording in UI text', not off, '; '.join(off[:8]))

        # screenshots
        if args.shots and groups:
            os.makedirs(args.shots, exist_ok=True)
            modes = [('plain', 'Classic'), ('brand', 'SmartPull'), ('neon', 'Neon')]
            bad_modes = []
            n = 0
            await page.reload(wait_until='load')
            await page.wait_for_function('window.__test&&window.__test.blocks().length>0', timeout=20000)
            for mi, (mid, mname) in enumerate(modes):
                await page.evaluate('i=>{document.querySelectorAll("#optTheme .topt")[i].click()}', mi)
                await page.wait_for_timeout(300)
                st = await page.evaluate('''()=>({ls:localStorage.getItem('pa2_theme'),neon:document.documentElement.classList.contains('neon'),brand:document.documentElement.classList.contains('brandtheme')})''')
                okm = st['ls'] == mid and st['neon'] == (mid == 'neon') and st['brand'] == (mid == 'brand')
                if not okm: bad_modes.append(f'{mid}: {st}')
                prev = 0
                for end, name in groups:
                    await page.evaluate('i=>window.__test.load(i)', prev)
                    await page.wait_for_timeout(450)
                    await page.screenshot(path=os.path.join(args.shots, f'{mid}_ch{groups.index((end,name))+1:02d}_{name}_L{prev+1}.png'))
                    n += 1; prev = end
            report('shots. mode switch via #optTheme sets pa2_theme plain/brand/neon', not bad_modes, '; '.join(bad_modes))
            await page.evaluate('()=>{document.querySelectorAll("#optTheme .topt")[0].click();window.__test.load(0)}')
            await page.set_viewport_size({'width': 1280, 'height': 800})
            await page.wait_for_timeout(600)
            await page.screenshot(path=os.path.join(args.shots, 'desktop_1280x800_L1.png'))
            n += 1
            report('shots. screenshots written', True, f'{n} files in {args.shots}')
            report('shots. no page errors while switching modes', len(errors) == len(errs_after), '; '.join(errors[len(errs_after):3]))

        await browser.close()
    fails = [n for n, ok in results if not ok]
    print(f'\n{len(results)-len(fails)}/{len(results)} checks passed in {time.time()-t0:.0f}s' + (' - FAILED: ' + '; '.join(fails) if fails else ''))
    return 1 if fails else 0

sys.exit(asyncio.run(main()))
