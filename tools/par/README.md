# Par check tools

Finds and verifies par (fewest moves) for SmartPull levels. See the project doc
`claude/SmartPull-par-handoff.md` for the full workflow.

- `run.py GAME.html SCRIPT.js` — opens the game headless (three.js r128 served locally from
  /home/claude/three/src/build/three.min.js) and prints what SCRIPT.js returns.
- `par_src.js` — par for levels built from hand-made data (Pivot, Echo, Glide, Glass, Order, Relay, Meld),
  using the game's own solvers.
- `par_gen.js` — A* par search for generated levels (dots, pairs, locks, gravity). Set
  `window.__only=[79,83,85]` and `window.__lim` (state cap) by editing the top of the script.
- `validate.py GAME.html [levels]` — plays each solution (from paths.json) through the real game and
  checks it clears with zero bumps in exactly par moves. Only levels that pass go into `PAR`.
