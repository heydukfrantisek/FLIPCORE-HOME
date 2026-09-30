# AGENTS.md

## Current state — verify before trusting anything

- This repository is a **placeholder**. The only tracked file is `README.md`
  (2 lines: `# FLIPCORE-HOME` / `FLIPCORE HOMEASISTENT`).
- There is **no source code, no dependency manifest, no CI, and no
  lint / test / typecheck / build config** anywhere in the tree. Do not invent
  commands (`npm test`, `pytest`, `docker build`, …) — nothing defines them, and
  a guessed command will look plausible but be wrong.
- Git: one commit (`7a8e229 Initial commit`). Default branch is `main`
  (`origin/HEAD -> origin/main`). Work happens on `kilo/*` topic branches
  (current: `kilo/calm-copper-2xt`), not on `main` directly.

## Intended domain

- Target is **Home Assistant**, per the README — but the repo does *not* decide
  the integration mechanism (custom component vs. add-on vs. plain container).
  Confirm the layout with the maintainer before scaffolding directories; do not
  assume one.

## Working rules until code lands

- When the first real source files appear, **replace this file** with verified
  project conventions: real setup/run commands, how to run a single test, and
  the required check order. Delete this placeholder section at that point.
- Keep entries backed by an executable source (config file, script, CI workflow).
  If you cannot point to one, leave the claim out.