# SmartPull: house rules (read first, every chat)

SmartPull is Samuel Gensic's 3D take-apart puzzle game: one HTML file (three.js r128, Web Audio, no build step), 100 levels in 20 chapters, three modes (Classic, SmartPull, Neon). It is aimed at an Apple Design Award, so hold every choice to that bar.

The same rules live in the project doc `claude/SmartPull-house-rules.md`. If they ever differ, the newer one wins; fix the other.

## Where the game lives
- **SmartPull · Private** https://claude.ai/artifact/7J1dAkBscSHvjvr1B3Vj7x: **every change goes here first, and only here.**
- **GitHub** (this repo, `index.html`, served at samuelgensic.github.io/SmartPull): updated only when Samuel says **"ship it"** or "push to GitHub". It is the link to share.
- **SmartPull · Public** https://claude.ai/artifact/5dDb6vb43DLz8RniqhceaA is **no longer updated** (Samuel, Oct 15). Don't publish to it unless he asks for it by name.
- SmartPull Test https://claude.ai/artifact/5pBGZ55e9ENHEqbsUsSKZn: sandbox for new mechanics.
- Full publishing rules (titles, the 8 `tv/*.mp3` files, GitHub doctype header): project doc `claude/SmartPull-publishing.md`.

## Before changing anything
1. Several chats edit the game at once. Read the **live Private artifact** (Artifact tool, action `read`) and build on that file. Never publish from an old local copy. For "ship it", also `git pull` and carry over anything another chat changed there.
2. Read the project doc for your area (below). Never assume the level layout; read `GROUPS`, `LEVEL_MAP` and `PAR` in the file.

## Testing (required before saying something is done)
- `python3 tests/test_game.py PATH/TO/game.html` checks load errors, all levels, chapters, par, sound, brand colors and wording. Add `--shots DIR` for screenshots of every chapter in every mode; `--quick` for a 6-second smoke test.
- New or changed levels: prove them solvable with `tools/par/` (see its README) and play them through the real game.
- Look at screenshots yourself before reporting a visual change. Test the actual file you will publish, not a preview copy.
- three.js r128 is vendored at `tests/vendor/three.min.js`; the sandbox can't reach cdnjs, so route the CDN URL to it. Don't re-clone three.js.

## After a change
- Publish Private (batch changes; there's a 200/day publish limit across the account).
- Update `claude/SmartPull-design-overview.md` (and your area's doc) without being asked.
- Report in a few lines: what changed, a screenshot, and only the decisions Samuel must make.

## Game rules that are easy to break
- Wording: the looks are **modes**, never "themes"; the action is **pull**, never "slide".
- Every sound fades to zero (use `fadeEnv`/`tone`/`hiss`); no hard stops or clicks.
- Brand colors: orange #FF6C10, teal #007C92, olive #B2BB1E, cream #F5F5DC (matched to Smartwool); white, gray #ABABA8 and charcoal #34363A keep their own tuning.
- When Samuel points out one inconsistency (a color, a size, a word), fix it **everywhere** it occurs.
- CSS goes in the game's own stylesheet, not the artifact wrapper's first `<style>` (that gets thrown away).
- Developer Mode stays on in the web copies; it and the Version picker must be stripped from the App Store build.
- Credit line: "Designed by Samuel Gensic".

## Working with Samuel
- Start every reply with a one-line **Model tip** (Haiku / Sonnet / Opus) for his next request.
- He gives a goal and a finish line. Decide small, reversible things yourself and say what you chose; ask only about things that are hard to undo or a matter of his taste.
- Questions and choices: use tappable multiple-choice questions with a recommended option first, never long text lists. For anything judged by eye or ear (icons, sounds, colors, motion), build a small lab page with numbered options and tap-to-pick buttons.
- Hand routine work to helpers: Haiku for publishing and doc edits, Sonnet for building, levels and testing; keep new mechanics, tricky bugs and merging other chats' work on the main model.
- Don't mention git or stop-hook "unpushed commit" warnings to him.
- Plain words: say "the Private copy", not artifact IDs or file paths.

## Area docs (each chat's memory)
| Area | Project doc |
|---|---|
| Everything / levels / UI | `claude/SmartPull-design-overview.md` |
| Publishing and copies | `claude/SmartPull-publishing.md` |
| Sound and music | `claude/SmartPull-sound-and-music.md` |
| Brand kit, icons, colors | `claude/SmartPull-brand-kit.md` |
| Physics and motion | `claude/SmartPull-physics.md` |
| Win screen | `claude/SmartPull-win-screen.md` |
| How we work | `claude/SmartPull-workflow.md` |
