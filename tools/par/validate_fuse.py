"""validate_fuse.py — play Fuse-chapter solutions through the real game, move by move.

usage: python3 validate_fuse.py GAME.html SOLUTION_DIR [levels]
SOLUTION_DIR holds fuse-LEVEL.json files written by par_fuse.js (path + the board it predicts after every move).
For every move it checks, in the live game: the tapped arrow is really visible (not covered, not on the floor side),
the pull is a clean pull (pulls +1, bumps unchanged), and the whole board afterwards (every cube's cell, its piece,
its arrow face) equals what the solver predicted. A level passes only if it also clears in exactly `par` moves
with 0 bumps. Prints one JSON line per level, with its levelSig, ready to copy into PAR."""
import sys, json, asyncio, os
from playwright.async_api import async_playwright
HTML = sys.argv[1]; DIR = sys.argv[2]
only = [int(x) for x in sys.argv[3].split(',')] if len(sys.argv) > 3 else None
THREE = open(next(p for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','tests','vendor','three.min.js'),'/home/claude/three/src/build/three.min.js'] if os.path.exists(p))).read()
JS = '''async ([lv, path, trace]) => {
 const T = window.__test, sleep = ms => new Promise(r => setTimeout(r, ms));
 T.load(lv - 1); await sleep(400);
 const fi = v => T.DIRS.findIndex(f => f[0] === v[0] && f[1] === v[1] && f[2] === v[2]);
 const snap = () => T.blocks().map((b, id) => b.alive ? [id, b.c[0] * 16 + b.c[1] * 4 + b.c[2],
   b.group ? Math.min(...b.group.members.filter(m => m.alive).map(m => m.id)) : id, fi(b.arrowFace)] : null).filter(Boolean);
 const wait = async () => { await sleep(120); for (let t = 0; t < 120; t++) { if (!T.blocks().some(b => b.busy)) break; await sleep(60) } await sleep(250) };
 const sig = T.levelSig(), problems = [];
 for (let s = 0; s < path.length; s++) {
   const B = T.blocks(), b = B[path[s][1]];
   if (!b.alive) { problems.push('step ' + s + ': cube ' + path[s][1] + ' already gone'); break }
   const nb = [b.c[0] + b.arrowFace[0], b.c[1] + b.arrowFace[1], b.c[2] + b.arrowFace[2]];
   if (b.arrowFace[1] === -1) problems.push('step ' + s + ': arrow on the floor side');
   if (B.some(x => x.alive && x.c[0] === nb[0] && x.c[1] === nb[1] && x.c[2] === nb[2])) problems.push('step ' + s + ': arrow covered');
   const c0 = T.counts(); T.slide(b); const c1 = T.counts(); await wait();
   if (c1.pulls !== c0.pulls + 1 || c1.bumps !== c0.bumps) problems.push('step ' + s + ': not a clean pull');
   const live = JSON.stringify(snap()), want = JSON.stringify(trace[s]);
   if (live !== want) { problems.push('step ' + s + ': board differs from prediction'); if (problems.length < 6) problems.push({ live: snap(), want: trace[s] }); break }
 }
 await sleep(800); const c = T.counts();
 return { sig, left: T.blocks().filter(b => b.alive).length, moves: c.pulls + c.taps + c.bumps, bumps: c.bumps, problems }
}'''
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
        pg = await b.new_page(viewport={'width': 390, 'height': 844})
        await pg.add_init_script("try{localStorage.setItem('pa2_dev','1');localStorage.setItem('pa2_tier','full');localStorage.setItem('pa3_unlocked','100');localStorage.setItem('pa4_layout','100');localStorage.setItem('pa2_sound','0')}catch(e){}")
        await pg.route('**/three.min.js', lambda r: r.fulfill(body=THREE, content_type='application/javascript'))
        await pg.route('**/fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
        await pg.route('http://game.local/', lambda r: r.fulfill(body=open(HTML).read(), content_type='text/html'))
        errs = []; pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://game.local/'); await pg.wait_for_timeout(1500)
        for f in sorted(os.listdir(DIR)):
            if not (f.startswith('fuse-') and f.endswith('.json')): continue
            S = json.load(open(os.path.join(DIR, f))); lv = S['level']
            if only and lv not in only: continue
            r = await pg.evaluate(JS, [lv, S['path'], S['trace']])
            ok = r['left'] == 0 and r['bumps'] == 0 and r['moves'] == S['par'] and not r['problems']
            print(json.dumps({'lv': lv, 'par': S['par'], 'ok': ok, **r}), flush=True)
        print('ERRORS', errs)
        await b.close()
asyncio.run(main())
