"""crosscheck_fuse.py — random play in the real Fuse levels, checking the solver's model against the game.

usage: python3 crosscheck_fuse.py GAME.html LEVELS STEPS [SEED] [BUMP_TESTS_PER_STEP] [BIAS]
BIAS (0-1, default 0): chance of preferring a fused piece when one can be pulled, to exercise falls and fusions harder
Loads par_fuse.js's model into the page. At every step of a random game it
  1. tries a few taps the model calls blocked (the game must bump: no pull, bumps+1),
  2. taps a random tap the model calls legal (the game must pull, bumps unchanged) and compares the whole board
     afterwards (cells, pieces, arrow faces) with the model's prediction.
Any disagreement is printed. Zero disagreements over many steps means the model has the game's move set and rules."""
import sys, json, asyncio, os
from playwright.async_api import async_playwright
HTML = sys.argv[1]; LEVELS = [int(x) for x in sys.argv[2].split(',')]; STEPS = int(sys.argv[3])
SEED = int(sys.argv[4]) if len(sys.argv) > 4 else 1; BT = int(sys.argv[5]) if len(sys.argv) > 5 else 3
BIAS = float(sys.argv[6]) if len(sys.argv) > 6 else 0
THREE = open(next(p for p in [os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','tests','vendor','three.min.js'),'/home/claude/three/src/build/three.min.js'] if os.path.exists(p))).read()
SRC = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'par_fuse.js')).read()
if SRC.startswith('#!'): SRC = SRC.split('\n', 1)[1]  # (a shebang line isn't valid inside new Function)
JS = '''async ([lv, src, steps, seed, bt, bias]) => {
 const mod = { exports: {} }; new Function('module', 'require', src)(mod, () => ({}));
 const T = window.__test, sleep = ms => new Promise(r => setTimeout(r, ms));
 const fi = v => T.DIRS.findIndex(f => f[0] === v[0] && f[1] === v[1] && f[2] === v[2]);
 const wait = async () => { await sleep(80); for (let t = 0; t < 150; t++) { if (!T.blocks().some(b => b.busy)) break; await sleep(50) } await sleep(120) };
 let rs = seed >>> 0; const rnd = () => { rs = (Math.imul(rs, 1664525) + 1013904223) >>> 0; return rs / 4294967296 };
 const shuffle = a => { for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(rnd() * (i + 1)); [a[i], a[j]] = [a[j], a[i]] } return a };
 const out = { lv, steps: 0, pulls: 0, bumpTests: 0, playouts: 0, cleared: 0, stuck: 0, mismatches: [], pieceSizes: {} };
 let M = null, level = null;
 const live = () => { const B = T.blocks(), n = B.length, pos = [], gid = [], af = [];
   for (let i = 0; i < n; i++) { const b = B[i]; if (!b.alive) { pos.push(-1); gid.push(i); af.push(0); continue }
     pos.push(b.c[0] * 16 + b.c[1] * 4 + b.c[2]); gid.push(b.group ? Math.min(...b.group.members.filter(m => m.alive).map(m => m.id)) : i); af.push(fi(b.arrowFace)) }
   return { pos, gid, af } };
 while (out.steps < steps) {
   T.load(lv - 1); await sleep(400); out.playouts++;
   if (!M) { level = { cubes: T.blocks().map(b => [b.c.slice(), b.d.slice(), b.arrowFace.slice(), b.fuseIdx]) }; M = mod.exports.makeModel(level) }
   for (;;) {
     const B = T.blocks(), s = live(), alive = B.filter(b => b.alive).map(b => b.id);
     if (!alive.length) { out.cleared++; break }
     const occ = M.occOf(s);
     // taps a player can make: visible arrow (not covered, not floor side)
     const vis = alive.filter(i => { const b = B[i]; if (b.arrowFace[1] === -1) return false; const nb = [b.c[0] + b.arrowFace[0], b.c[1] + b.arrowFace[1], b.c[2] + b.arrowFace[2]]; return !B.some(x => x.alive && x.c[0] === nb[0] && x.c[1] === nb[1] && x.c[2] === nb[2]) });
     const yes = shuffle(vis.filter(i => M.legal(s, occ, i))), no = shuffle(vis.filter(i => !M.legal(s, occ, i)));
     for (const i of no.slice(0, bt)) { // the model says blocked: the game must bump
       const c0 = T.counts(); T.slide(B[i]); const c1 = T.counts(); out.bumpTests++;
       if (!(c1.bumps === c0.bumps + 1 && c1.pulls === c0.pulls)) out.mismatches.push({ kind: 'model blocked, game moved', lv, cube: i, state: s });
       await wait() }
     if (!yes.length) { out.stuck++; break }
     const big = yes.filter(k => s.gid.filter((g, q) => s.pos[q] >= 0 && g === s.gid[k]).length >= 2), i = (big.length && rnd() < bias) ? big[0] : yes[0], c0 = T.counts(); const sz = s.gid.filter((g, k) => s.pos[k] >= 0 && g === s.gid[i]).length; out.pieceSizes[sz] = (out.pieceSizes[sz] || 0) + 1;
     T.slide(B[i]); const c1 = T.counts(); out.steps++; out.pulls++;
     if (!(c1.pulls === c0.pulls + 1 && c1.bumps === c0.bumps)) { out.mismatches.push({ kind: 'model legal, game bumped', lv, cube: i, state: s }); await wait(); break }
     await wait();
     const norm = t => ({ pos: t.pos, gid: t.gid.map((g, k) => t.pos[k] < 0 ? k : g), af: t.af.map((a, k) => t.pos[k] < 0 ? 0 : a) }); // (gone cubes carry no meaning)
     const want = norm(M.apply(s, occ, i)), got = norm(live());
     if (JSON.stringify(want) !== JSON.stringify(got)) { out.mismatches.push({ kind: 'board differs', lv, cube: i, before: s, want, got }); break }
     if (out.mismatches.length > 3 || out.steps >= steps) break;
   }
   if (out.mismatches.length > 3) break;
 }
 return out }'''
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
        for lv in LEVELS:
            r = await pg.evaluate(JS, [lv, SRC, STEPS, SEED + lv, BT, BIAS])
            r['mismatchCount'] = len(r['mismatches']); r['mismatches'] = r['mismatches'][:2]
            print(json.dumps(r), flush=True)
        print('ERRORS', errs)
        await b.close()
asyncio.run(main())
