# Par check tools

Finds and verifies par (fewest moves) for SmartPull levels. The full workflow is in the section
"Par for every level" at the end of this file.

- `run.py GAME.html SCRIPT.js` — opens the game headless (three.js r128 served locally from
  /home/claude/three/src/build/three.min.js) and prints what SCRIPT.js returns.
- `par_src.js` — par for levels built from hand-made data (Pivot, Echo, Glide, Glass, Order, Relay, Meld),
  using the game's own solvers.
- `par_gen.js` — A* par search for generated levels (dots, pairs, locks, gravity). Set
  `window.__only=[79,83,85]` and `window.__lim` (state cap) by editing the top of the script.
- `par_mono.js` — **use this first for any generated level without gravity** (dots, linked pairs, pair dots,
  locks). Exact and takes seconds: with no gravity, removing a cube only ever helps the others, so every
  free cube is pulled at once and only dot taps are searched (par = pulls + fewest dot taps). Cross-checked
  against all 31 stored pars it covers (0 mismatches); solved 79, 83 and 85, which `par_gen.js` could not.
  It does not apply to gravity, fuse, glide, pips, glass, pivot or echo levels.
  Run: `python3 run.py ../../index.html par_mono.js` (set `window.__only=[83,85]` to pick levels).
  Its paths are in the `validate.py` format.
- `par_gen.js` note: its alive mask uses 32-bit `&`, which breaks for levels with more than 32 cubes
  (level 83 has 36). Prefer `par_mono.js`, which tracks alive cubes in an array.
- `validate.py GAME.html [levels]` — plays each solution (from paths.json) through the real game and
  checks it clears with zero bumps in exactly par moves. Only levels that pass go into `PAR`.

### Fuse chapter (levels 96–100): gravity + color fusion
None of the solvers above model fusion, so these do (all exact; par = fewest pulls, since these levels have no
dots, locks or glass and a clean clear never bumps):
- `dump_fuse.js` — run through `run.py`; prints the five levels' starting cubes (cell, direction, arrow face, color).
  `python3 run.py ../../index.html dump_fuse.js` → keep the JSON (drop the trailing `ERRORS` line) as `LEVELS.json`.
- `par_fuse.js` — `node par_fuse.js LEVELS.json 98 6000000 OUTDIR` runs A* over the game's own fusion rules
  (visible arrows only, whole pieces pull and fall rigidly, newly touching same colors fuse and a piece absorbs
  touching same-colored cubes, buried arrows move to an outside face). The lower bound is consistent: each
  white/gray cube is its own pull, and same-colored cubes can only share a piece through a chain of same-colored
  cubes in the same or neighbouring columns (columns never change). Writes `OUTDIR/fuse-LEVEL.json` with the path
  and the board it predicts after each move. Levels 96–99 take under a minute; level 100 (the full 4×4×4 cube) took
  about 16 minutes and 2.9M states with the default solver, so run it in the background. `LEAN=1 node par_fuse.js …`
  keeps states in typed arrays (same answers, a fraction of the memory) for searches that outgrow the default.
- `validate_fuse.py GAME.html OUTDIR [levels]` — plays each solution through the real game one move at a time and
  compares the whole live board (every cube's cell, piece and arrow face) with the prediction after every move.
  Passes only with zero bumps and exactly par moves. Prints each level's `sig`, which goes into `PAR` with the par.
- `crosscheck_fuse.py GAME.html 96,98,100 STEPS [SEED] [BUMP_TESTS] [BIAS]` — random play in the real game that checks
  the solver's model itself: taps the model calls blocked must bump, taps it calls legal must pull, and the board
  afterwards must match. `BIAS` (0–1) favours pulling fused pieces. Run it again after any change to the fusion rules.
- Pars found: 96 = 10, 97 = 16, 98 = 25, 99 = 30, 100 = 50.

## Par for every level

**Status:** par is on all 100 levels (GitHub main, the private workspace and the public copy as of Oct 13).
If a level is ever changed, its par disappears on its own (fingerprint, below), and its solver has to be
re-run for that level.

### How par works in the game (index.html)
- `const PAR={…}` holds entries keyed by level number minus 1: `[fingerprint, par]`. `levelSig()` builds the
  fingerprint from every cube's position, arrow, dot, lock, pair, glide, pips, glass, gear, echo and fuse color.
  On load, `curPar` is set only if the fingerprint matches, so a changed level silently loses its par.
- Moves = pulls + taps + bumps. Dot taps and gear taps are counted by the tap handler (not inside `spin` or
  `pivotTurn`); glass cracks are taps; the last glass tap is a pull.
- Test hooks on `window.__test`: `load, blocks, slide, spin, pivotTurn, glassTap, S4, solveTest, liveSpec,
  solverFor, settle, rayBlocked, levelSig, pullsLeft, par, grav, counts, src, state`.

### Rules for adding par
- Only add a par that has been played through the real game and verified. If a level can't be solved for
  certain, leave it without par. Never guess. Without par, a zero-bump clear still counts as a clean clear.
- Rule changes (gravity, fusion) need `crosscheck_fuse.py` and `validate_fuse.py` re-run, plus `validate.py`
  on a sample of other levels, because a changed rule would silently invalidate stored pars.

### Setup
Clone the repo, then get three.js r128 locally: sparse-clone mrdoob/three.js at tag r128 and copy
`build/three.min.js` to /home/claude/three/src/build/. Install Playwright for Python and run
`python3 -m playwright install chromium` if it isn't already there. The sandbox can't reach cdnjs, so `run.py`
serves three.js locally.

### Workflow
1. Levels without gravity: `par_mono.js` first (see above). Run `python3 run.py ../../index.html par_mono.js`,
   with `window.__only=[79,83,85]` to pick levels.
2. Gravity levels: `par_gen.js` (older A*, only for gravity levels; don't trust it above 32 cubes).
3. Fuse levels: `dump_fuse.js`, then `par_fuse.js`, then `validate_fuse.py` (see the Fuse section above).
4. Put the found paths in `paths.json` (`{"79":[["go",12],["dot",4]]}`, block indices as in `blocks()`), then run
   `python3 validate.py index.html 79`. A level passes only if it clears with 0 bumps in exactly par moves.
   Copy its `sig` and `par` into `PAR`. Playing a level takes about 15 s per 10 moves.

### Shipping a PAR change
- Pull the latest main first (several chats edit index.html). Never assume the level layout.
- Re-run `validate.py` on a sample of existing levels to confirm nothing shifted.
- Push index.html to GitHub. Then publish the same page to the private workspace ("SmartPull · Private") and,
  only when Samuel says "ship it", to the public copy. Publish the page content from `<title>` to the end of the
  script, without the doctype/head line and the closing `</body></html>`, and change only the `PAR` line.
  Read each artifact back and confirm only the new entries differ. Always start from the live page, not an
  older prepared file. Batch par changes into one publish per artifact (200 publishes per day, resets at UTC midnight).
- Tell Samuel in plain words which levels got par.

