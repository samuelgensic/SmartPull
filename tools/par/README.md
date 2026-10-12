# Par check tools

Finds and verifies par (fewest moves) for SmartPull levels. See the project doc
`claude/SmartPull-par-handoff.md` for the full workflow.

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
