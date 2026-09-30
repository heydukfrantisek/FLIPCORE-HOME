# AGENTS.md

## What this repo is

A Home Assistant HACS repository (`FLIPCORE-HOME`) whose only content is one custom
integration: `custom_components/kilo_ai`, a client for the Kilo AI Gateway
(OpenAI-compatible API, default base URL `https://api.kilo.ai/api/gateway`).
There is no app, no package manager, and no runtime process here — the deliverable is
files that get copied into `/config/custom_components/` on a HAOS VM.

## Verification: there is almost none

No `pyproject.toml`, no `requirements*.txt`, no test suite, no linter config.
`.github/workflows/blank.yml` is the untouched GitHub placeholder and runs only
`echo` — it does not build or check anything. Do not claim CI validates a change.

The checks that actually work in this container:

```bash
python3 -m py_compile custom_components/kilo_ai/*.py
python3 -c "import json;json.load(open('custom_components/kilo_ai/manifest.json'))"
```

`pyflakes`/`flake8` are not installed and `pip install` has no network access, so
unused-import and unused-variable bugs are caught by reading, not tooling. The local
Python is 3.10 while Home Assistant runs 3.12+, so `py_compile` success is not proof
the code runs on HA.

Manual smoke test: the only real check of the API path is running HA and calling
`kilo_ai.list_models` / `kilo_ai.ask`.

## Release / packaging

- `hacs.json` sets `content_in_root: false`, so `custom_components/kilo_ai/` must stay
  exactly at that path — HACS maps the repo root to the integration root.
- `hacs.json` has `zip_release: false` and the release zip is built by hand. Bump
  `version` in `custom_components/kilo_ai/manifest.json` on every change; HACS uses it
  to detect updates.
- Build the HACS/release zip without leaving scratch files in the repo root:
  ```bash
  rm -rf build && mkdir -p build && cp -r custom_components build/ \
    && rm -rf build/custom_components/kilo_ai/__pycache__ \
    && (cd build && zip -r ../kilo_ai-0.1.0.zip custom_components -x '*__pycache__*') \
    && rm -rf build
  ```
  The zip must contain `custom_components/kilo_ai/...` at the top level. Release zips
  and `build/` are gitignored — never commit them.

## Version constraints that constrain code style

- `manifest.json` declares `homeassistant: 2024.11.0`. That floor exists because the
  code uses `ConfigEntry.runtime_data` (2024.6+) and `self.config_entry` inside
  `OptionsFlow` (2024.11+). If you use another recent-only helper, raise the floor in
  **both** `manifest.json` and `hacs.json`.
- `hacs.json` still says `"homeassistant": "2024.6.0"` while `manifest.json` says
  `2024.11.0`. Keep the real minimum in the manifest; HACS only uses its copy as an
  install hint, so this mismatch is known and not a bug to "fix" casually.

## Integration conventions

- API calls go through `custom_components/kilo_ai/api.py`; services in `__init__.py`
  and the config flow must not build their own HTTP requests. Reuse the HA shared
  session via `async_get_clientsession`, never a bare `aiohttp.ClientSession`.
- Gateway errors become `KiloGatewayError`; the config flow turns them into
  `errors["base"] = "cannot_connect"` and `__init__` into `ConfigEntryNotReady`. Keep
  that mapping rather than surfacing raw HTTP status codes in the UI.
- The config flow validates credentials by calling `/models` before creating the
  entry, and stores the fetched model list in `entry.options` for the options flow
  model picker. Changing entry data must keep both in sync.
- Any new user-visible string needs an entry in `strings.json` **and**
  `translations/cs.json` (Czech is the primary UI language for this user). `services.yaml`
  fields and the `ATTR_*` keys in `__init__.py` must stay aligned by name.
- The API key is stored in `config_entry.data` and persisted in `.storage`; never log it
  and never commit a real key. Prefer only adding new secrets to `entry.data` on
  reconfigure, not renaming existing keys, which would orphan saved entries.
