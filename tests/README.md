# SmartPull tests

`python3 tests/test_game.py [GAME.html] [--shots DIR] [--quick]` runs the whole suite headless (Playwright + Chromium, SwiftShader WebGL). Exit code is non-zero if any check fails.

- Checks: clean load (no page/console errors), every level builds and loads, 5 levels and a name per chapter, `<title>` starts with "SmartPull", a positive par for every level, sound effects render (live and OfflineAudioContext), brand colors (#FF6C10 #007C92 #B2BB1E present; old #F17B31 #007493 #C0B50A gone), no "theme" wording in UI text.
- `--shots DIR` saves 393x852 shots of the first level of every chapter in Classic, SmartPull and Neon, plus a 1280x800 desktop shot. `--quick` skips par, sound, wording and shots (about 10 s).
- GAME.html defaults to `../index.html`. three.js r128 is vendored in `tests/vendor/` (the `tools/par` scripts use it too); Google Fonts are stubbed, `tv/*.mp3` served from the repo.
- Private artifact copy: read it with the Artifact tool (action "read"), which saves the page to a local file; then run `python3 tests/test_game.py /path/to/saved.html`.
- `tools/par/validate.py` is the deeper par check: it plays every par solution through the real game.
