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
