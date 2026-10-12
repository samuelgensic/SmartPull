#!/usr/bin/env node
// par_fuse.js — exact par search for the Fuse chapter (levels 96-100).
//
// Models the game's fusion rules exactly (index.html: slide, afterRemoval, fallRigid/settleRigid,
// fuseAfterFall/fuseNew, rehomeArrow):
//   - a tap on a cube's visible arrow pulls that cube's whole piece in the cube's direction d,
//     if every member's path is clear (the floor blocks downward);
//   - after a pull the pieces fall rigidly, then same-colored cubes that are NEWLY touching fuse,
//     and any piece of 2+ cubes absorbs every same-colored cube or piece it touches;
//   - a fused cube whose arrow is now buried inside its piece gets its arrow moved to an outside face.
// Fuse levels have no dots, locks, pairs or glass, so par = the fewest pulls (a clean clear never bumps).
//
// Search: A* with a consistent lower bound (see hOf), exact. Usage:
//   node par_fuse.js LEVELS.json LEVEL [stateLimit] [outDir]
// LEVELS.json comes from dump_fuse.js (run through run.py). Writes outDir/fuse-LEVEL.json with the path
// ([["go",cubeIndex],...]) and the predicted state after every move, for validate_fuse.py.
const fs = require('fs');
const DIRS = [[1,0,0],[-1,0,0],[0,1,0],[0,-1,0],[0,0,1],[0,0,-1]];
const DOWN = 3, NEUTRAL = 3, B = 4; // box is 4x4x4; cell = x*16 + y*4 + z
const faceIdx = v => DIRS.findIndex(f => f[0] === v[0] && f[1] === v[1] && f[2] === v[2]);
const cx = c => c >> 4, cy = c => (c >> 2) & 3, cz = c => c & 3;
const cellOf = (x, y, z) => x * 16 + y * 4 + z;
const inBox = (x, y, z) => x >= 0 && x < B && y >= 0 && y < B && z >= 0 && z < B;

function makeModel(level) {
  const cubes = level.cubes, n = cubes.length;
  const col = cubes.map(c => c[3]), dir = cubes.map(c => faceIdx(c[1]));
  const start = { pos: cubes.map(c => cellOf(...c[0])), gid: cubes.map((_, i) => i), af: cubes.map(c => faceIdx(c[2])) };
  const colOf = cubes.map(c => c[0][0] * 4 + c[0][2]); // horizontal column never changes
  // potential-merge graph: same color, same or neighbouring column (fusion needs physical contact)
  const potAdj = cubes.map(() => []);
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    if (col[i] >= NEUTRAL || col[i] !== col[j]) continue;
    const dx = Math.abs(cubes[i][0][0] - cubes[j][0][0]), dz = Math.abs(cubes[i][0][2] - cubes[j][0][2]);
    if (dx + dz <= 1) potAdj[i].push(j);
  }
  // ---- state <-> string (one char per cube: 0 = gone, else pos+1 | af<<7 | gid<<10) ----
  const enc = s => { const a = new Array(n); for (let i = 0; i < n; i++) a[i] = s.pos[i] < 0 ? 0 : (s.pos[i] + 1) | (s.af[i] << 7) | (s.gid[i] << 10); return String.fromCharCode.apply(null, a); };
  const dec = k => { const pos = new Array(n), gid = new Array(n), af = new Array(n);
    for (let i = 0; i < n; i++) { const c = k.charCodeAt(i); if (!c) { pos[i] = -1; gid[i] = i; af[i] = 0 } else { pos[i] = (c & 127) - 1; af[i] = (c >> 7) & 7; gid[i] = c >> 10 } }
    return { pos, gid, af } };
  const memoH = new Map();
  // consistent lower bound on remaining pulls: every neutral cube is its own pull; colored cubes of one color
  // can only end up in one piece if they are linked through same-colored cubes in same/adjacent columns.
  function hOf(s) {
    let h = 0; const par = new Int8Array(n).fill(-1), find = x => { while (par[x] >= 0 && par[x] !== x) x = par[x]; return x };
    let key = '';
    for (let i = 0; i < n; i++) key += s.pos[i] < 0 ? '0' : '1';
    const m = memoH.get(key); if (m !== undefined) return m;
    let comps = 0;
    for (let i = 0; i < n; i++) { if (s.pos[i] < 0) continue; if (col[i] >= NEUTRAL) { h++; continue } par[i] = i; comps++ }
    for (let i = 0; i < n; i++) { if (s.pos[i] < 0 || col[i] >= NEUTRAL) continue;
      for (const j of potAdj[i]) { if (s.pos[j] < 0) continue; const a = find(i), b = find(j); if (a !== b) { par[a] = b; comps-- } } }
    h += comps; memoH.set(key, h); return h;
  }
  const occOf = s => { const o = new Int8Array(64).fill(-1); for (let i = 0; i < n; i++) if (s.pos[i] >= 0) o[s.pos[i]] = i; return o };
  const nbCell = (cell, f) => { const x = cx(cell) + DIRS[f][0], y = cy(cell) + DIRS[f][1], z = cz(cell) + DIRS[f][2]; return inBox(x, y, z) ? cellOf(x, y, z) : -1 };
  let bottomArrow = false;
  // ---- the game's rules ----
  function settleRigid(pos, gid, occ) {
    for (let guard = 0; guard < 400; guard++) {
      const bodies = new Map();
      for (let i = 0; i < n; i++) if (pos[i] >= 0) { if (!bodies.has(gid[i])) bodies.set(gid[i], []); bodies.get(gid[i]).push(i) }
      let moved = false;
      const order = [...bodies.values()].sort((a, b) => Math.min(...a.map(i => cy(pos[i]))) - Math.min(...b.map(i => cy(pos[i]))));
      for (const m of order) {
        const can = m.every(i => { if (cy(pos[i]) <= 0) return false; const o = occ[pos[i] - 4]; return o === -1 || gid[o] === gid[i] });
        if (!can) continue;
        m.forEach(i => occ[pos[i]] = -1); m.forEach(i => { pos[i] -= 4; occ[pos[i]] = i }); moved = true;
      }
      if (!moved) break;
    }
  }
  function touchingPairs(pos, occ) {
    const t = new Uint8Array(n * n);
    for (let i = 0; i < n; i++) { if (pos[i] < 0) continue;
      for (let f = 0; f < 6; f++) { const c = nbCell(pos[i], f); if (c < 0) continue; const j = occ[c]; if (j >= 0) { t[i * n + j] = 1; t[j * n + i] = 1 } } }
    return t;
  }
  function fuseNew(pos, gid, occ, before) {
    const fused = new Set();
    for (let i = 0; i < n; i++) { if (pos[i] < 0) continue;
      for (let f = 0; f < 6; f++) { const c = nbCell(pos[i], f); if (c < 0) continue; const j = occ[c];
        if (j < 0 || col[i] >= NEUTRAL || col[i] !== col[j] || gid[i] === gid[j] || before[i * n + j]) continue;
        const old = gid[j], nw = gid[i];
        for (let k = 0; k < n; k++) if (pos[k] >= 0 && gid[k] === old) gid[k] = nw;
        for (let k = 0; k < n; k++) if (pos[k] >= 0 && gid[k] === nw) fused.add(k);
      } }
    for (let changed = true; changed;) { changed = false;
      const size = new Map(); for (let k = 0; k < n; k++) if (pos[k] >= 0) size.set(gid[k], (size.get(gid[k]) || 0) + 1);
      for (let i = 0; i < n; i++) { if (pos[i] < 0 || size.get(gid[i]) < 2) continue;
        for (let f = 0; f < 6; f++) { const c = nbCell(pos[i], f); if (c < 0) continue; const j = occ[c];
          if (j < 0 || col[i] >= NEUTRAL || col[i] !== col[j] || gid[i] === gid[j]) continue;
          const old = gid[j], nw = gid[i];
          for (let k = 0; k < n; k++) if (pos[k] >= 0 && gid[k] === old) gid[k] = nw;
          for (let k = 0; k < n; k++) if (pos[k] >= 0 && gid[k] === nw) fused.add(k);
          changed = true; } } }
    return fused;
  }
  // rehomeArrow from the game (inPiece/occupied are about the cell the face points at)
  function rehome(i, pos, gid, af, occ) {
    const here = pos[i], inPiece = f => { const c = nbCell(here, f); if (c < 0) return false; const o = occ[c]; return o >= 0 && gid[o] === gid[i] };
    const occupied = f => { const c = nbCell(here, f); return c >= 0 && occ[c] >= 0 };
    const face = af[i];
    if (!inPiece(face)) return face;
    const d = DIRS[dir[i]], sides = [];
    for (let f = 0; f < 6; f++) if (DIRS[f][0] * d[0] + DIRS[f][1] * d[1] + DIRS[f][2] * d[2] === 0 && !inPiece(f)) sides.push(f);
    let best = sides.find(f => f !== DOWN && !occupied(f));
    if (best === undefined) best = sides.find(f => f !== DOWN);
    if (best === undefined) best = sides[0];
    return best === undefined ? face : best;
  }
  // can cube j be tapped right now? (its arrow is visible: not covered, not on the floor side; and its whole piece has a clear path)
  function legal(s, occ, j) {
    if (s.pos[j] < 0) return false;
    const f = s.af[j]; if (f === DOWN) { bottomArrow = true; return false }
    const c = nbCell(s.pos[j], f); if (c >= 0 && occ[c] >= 0) return false;
    const D = DIRS[dir[j]];
    for (let m = 0; m < n; m++) { if (s.pos[m] < 0 || s.gid[m] !== s.gid[j]) continue;
      let x = cx(s.pos[m]), y = cy(s.pos[m]), z = cz(s.pos[m]);
      for (let st = 1; st <= 6; st++) { x += D[0]; y += D[1]; z += D[2]; if (y < 0) return false; if (!inBox(x, y, z)) break; const o = occ[cellOf(x, y, z)]; if (o >= 0 && s.gid[o] !== s.gid[j]) return false } }
    return true;
  }
  function pullable(s, occ) { // one cube per distinct (piece, direction): the same pull, so the same result
    const out = [], seen = new Set();
    for (let j = 0; j < n; j++) { const tag = s.gid[j] * 8 + dir[j]; if (s.pos[j] < 0 || seen.has(tag)) continue; if (legal(s, occ, j)) { seen.add(tag); out.push(j) } }
    return out;
  }
  function apply(s, occ, j) { // pull j's piece, then fall, fuse, rehome
    const pos = s.pos.slice(), gid = s.gid.slice(), af = s.af.slice(), g0 = gid[j];
    for (let i = 0; i < n; i++) if (pos[i] >= 0 && gid[i] === g0) pos[i] = -1;
    const o2 = occOf({ pos });
    const before = touchingPairs(pos, o2);
    settleRigid(pos, gid, o2);
    const fused = fuseNew(pos, gid, o2, before);
    // canonical group label = lowest member id (keeps equal states identical)
    const low = new Map(); for (let i = 0; i < n; i++) if (pos[i] >= 0 && !low.has(gid[i])) low.set(gid[i], i);
    for (let i = 0; i < n; i++) if (pos[i] >= 0) gid[i] = low.get(gid[i]);
    const o3 = occOf({ pos });
    for (const i of fused) if (pos[i] >= 0) af[i] = rehome(i, pos, gid, af, o3);
    return { pos, gid, af };
  }
  start.gid = start.gid.map((g, i) => i);
  return { n, col, dir, start, enc, dec, hOf, occOf, legal, pullable, apply, bottomArrow: () => bottomArrow };
}
function solve(level, limit, onProgress) {
  const M = makeModel(level), { n, start, enc, dec, hOf, occOf, pullable, apply } = M;
  // ---- A* ----
  const k0 = enc(start), ids = new Map([[k0, 0]]), KEYS = [k0], G = [0], H = [hOf(start)], P = [-1], MV = [-1];
  const buckets = []; const push = id => { const f = G[id] + H[id]; (buckets[f] || (buckets[f] = [])).push(id) };
  push(0);
  let expanded = 0, goal = -1, t0 = Date.now(), topF = H[0];
  outer: for (let f = 0; f < buckets.length; f++) {
    const bk = buckets[f]; if (!bk) continue;
    topF = f;
    while (bk.length) {
      const id = bk.pop(); if (G[id] + H[id] !== f) continue; // stale
      const key = KEYS[id], s = dec(key);
      if (H[id] === 0 && s.pos.every(p => p < 0)) { goal = id; break outer }
      if (ids.size > limit) { return { fail: 'limit', states: ids.size, expanded, lowerBound: f, bottomArrow: M.bottomArrow(), ms: Date.now() - t0 } }
      expanded++;
      if (onProgress && expanded % 200000 === 0) onProgress({ expanded, states: ids.size, f, ms: Date.now() - t0 });
      const occ = occOf(s);
      for (const j of pullable(s, occ)) {
        const ns = apply(s, occ, j), nk = enc(ns), g = G[id] + 1, old = ids.get(nk);
        if (old === undefined) { const nid = KEYS.length; ids.set(nk, nid); KEYS.push(nk); G.push(g); H.push(hOf(ns)); P.push(id); MV.push(j); push(nid) }
        else if (G[old] > g) { G[old] = g; P[old] = id; MV[old] = j; push(old) }
      }
    }
  }
  if (goal < 0) return { fail: 'none', states: ids.size, expanded, bottomArrow: M.bottomArrow(), ms: Date.now() - t0 };
  const path = [], trace = []; for (let id = goal; P[id] >= 0; id = P[id]) { path.unshift(['go', MV[id]]); const s = dec(KEYS[id]); trace.unshift(s.pos.map((p, i) => p < 0 ? null : [i, p, s.gid[i], s.af[i]]).filter(Boolean)) }
  return { par: path.length, path, trace, states: ids.size, expanded, bottomArrow: M.bottomArrow(), h0: H[0], ms: Date.now() - t0 };
}

// Same search as solve(), but states live in compact typed arrays (about 140 bytes per state for 64 cubes instead of
// ~1 KB), so level 100's much bigger search fits in memory. Equality is checked on the full state, never on a hash alone.
function solveLean(level, limit, onProgress) {
  const M = makeModel(level), { n, start, hOf, occOf, pullable, apply } = M;
  let capN = 1 << 18, pool = new Uint16Array(capN * n), Gm = new Uint8Array(capN), Hm = new Uint8Array(capN), Pm = new Int32Array(capN), Mm = new Uint8Array(capN), count = 0;
  let tbits = 20, table = new Int32Array(1 << tbits).fill(-1);
  const codes = new Uint16Array(n);
  const encInto = s => { for (let i = 0; i < n; i++) codes[i] = s.pos[i] < 0 ? 0 : (s.pos[i] + 1) | (s.af[i] << 7) | (s.gid[i] << 10) };
  const hashCodes = () => { let h = 2166136261 >>> 0; for (let i = 0; i < n; i++) { h = Math.imul(h ^ codes[i], 16777619) >>> 0; h ^= h >>> 15 } return h };
  const sameAt = id => { const o = id * n; for (let i = 0; i < n; i++) if (pool[o + i] !== codes[i]) return false; return true };
  const grow = () => { capN *= 2; const np = new Uint16Array(capN * n); np.set(pool); pool = np;
    const cp = (A, T) => { const B = new T(capN); B.set(A); return B }; Gm = cp(Gm, Uint8Array); Hm = cp(Hm, Uint8Array); Pm = cp(Pm, Int32Array); Mm = cp(Mm, Uint8Array) };
  const rehash = () => { tbits++; table = new Int32Array(1 << tbits).fill(-1); const mask = (1 << tbits) - 1;
    for (let id = 0; id < count; id++) { for (let i = 0; i < n; i++) codes[i] = pool[id * n + i]; let p = hashCodes() & mask; while (table[p] >= 0) p = (p + 1) & mask; table[p] = id } };
  // find the id of the state in `codes`, or -1 (and the slot to insert at)
  let slot = 0;
  const lookup = () => { const mask = (1 << tbits) - 1; let p = hashCodes() & mask; while (table[p] >= 0) { if (sameAt(table[p])) { slot = p; return table[p] } p = (p + 1) & mask } slot = p; return -1 };
  const insert = (s, g, h, parent, mv) => { // call right after lookup() returned -1 for this state
    if (count >= capN) grow();
    const id = count++; pool.set(codes, id * n); Gm[id] = g; Hm[id] = h; Pm[id] = parent; Mm[id] = mv; table[slot] = id;
    if (count * 2 > (1 << tbits)) rehash();
    return id };
  const decId = id => { const pos = new Array(n), gid = new Array(n), af = new Array(n), o = id * n;
    for (let i = 0; i < n; i++) { const c = pool[o + i]; if (!c) { pos[i] = -1; gid[i] = i; af[i] = 0 } else { pos[i] = (c & 127) - 1; af[i] = (c >> 7) & 7; gid[i] = c >> 10 } }
    return { pos, gid, af } };
  start.gid = start.gid.map((g, i) => i);
  encInto(start); lookup(); insert(start, 0, hOf(start), -1, 255);
  const buckets = []; const push = id => { const f = Gm[id] + Hm[id]; (buckets[f] || (buckets[f] = [])).push(id) };
  push(0);
  let expanded = 0, goal = -1, t0 = Date.now();
  outer: for (let f = 0; f < buckets.length; f++) {
    const bk = buckets[f]; if (!bk) continue;
    while (bk.length) {
      const id = bk.pop(); if (Gm[id] + Hm[id] !== f) continue; // stale
      if (Hm[id] === 0) { goal = id; break outer }
      if (count > limit) return { fail: 'limit', states: count, expanded, lowerBound: f, bottomArrow: M.bottomArrow(), ms: Date.now() - t0 };
      expanded++;
      if (onProgress && expanded % 200000 === 0) onProgress({ expanded, states: count, f, ms: Date.now() - t0 });
      const s = decId(id), occ = occOf(s);
      for (const j of pullable(s, occ)) {
        const ns = apply(s, occ, j); encInto(ns); const old = lookup(), g = Gm[id] + 1;
        if (old < 0) { push(insert(ns, g, hOf(ns), id, j)) }
        else if (Gm[old] > g) { Gm[old] = g; Pm[old] = id; Mm[old] = j; push(old) }
      }
    }
  }
  if (goal < 0) return { fail: 'none', states: count, expanded, bottomArrow: M.bottomArrow(), ms: Date.now() - t0 };
  const path = [], trace = []; for (let id = goal; Pm[id] !== -1 || id !== 0; id = Pm[id]) { if (id === 0) break; path.unshift(['go', Mm[id]]); const s = decId(id); trace.unshift(s.pos.map((p, i) => p < 0 ? null : [i, p, s.gid[i], s.af[i]]).filter(Boolean)) }
  return { par: path.length, path, trace, states: count, expanded, bottomArrow: M.bottomArrow(), h0: Hm[0], ms: Date.now() - t0 };
}
module.exports = { solve, solveLean, makeModel, DIRS };
if (require.main === module) {
  const [, , file, lv, lim, outDir] = process.argv;
  const data = JSON.parse(fs.readFileSync(file, 'utf8'));
  const r = (process.env.LEAN ? solveLean : solve)(data[lv], +(lim || 3e6), p => console.error(JSON.stringify(p)));
  const summary = { level: +lv, ...r }; delete summary.path; delete summary.trace;
  console.log(JSON.stringify(summary));
  if (r.path && outDir) fs.writeFileSync(`${outDir}/fuse-${lv}.json`, JSON.stringify({ level: +lv, par: r.par, path: r.path, trace: r.trace }));
}
