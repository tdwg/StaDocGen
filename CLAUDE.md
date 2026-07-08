# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

StaDocGen is a Python Flask + Frozen-Flask static-site generator that turns TSV/CSV data files and markdown content into HTML documentation websites for TDWG biodiversity data standards.

The repo is organized as independent top-level **instances**, one per standard: `ltc/` (Latimer Core), `mids/` (Minimum Information about a Digital Specimen), `minext/` (MinExt). Instances do not share code or resources — a fix in one instance must be replicated manually in the others. The only shared code is repo-root `globals.py` (path helpers imported by utility scripts).

## Environment and commands

- Python 3.11 with a pip venv at the repo root: `.venv-stadocgen` (activate via `init.bat` or `.\.venv-stadocgen\Scripts\activate`). Do **not** use conda — Frozen-Flask breaks under it.
- Install deps: `pip install -r requirements.txt` (note: the file is UTF-16 encoded).
- **Dev server (mids)**: `cd mids/app && python freeze.py` → http://localhost:8001. The `main.py` at the instance root runs the bare app from `app/__init__.py`, which has no routes — the real app lives in `freeze.py`.
- **Dev server (ltc)**: `flask run` from the instance root (localhost:5000).
- **Build static site**: from `<instance>/app`, run `python freeze.py build` → output written to `<instance>/app/build/` (committed to this repo).
- **Publish**: copy the contents of `app/build/` into the `docs/` folder of the standard's own repo (e.g. tdwg/mids), e.g. `robocopy ...\app\build ...\mids\docs /mir`, then branch/PR/merge in that repo. GitHub Pages serves it there.
- There are no tests or linters.

## Architecture

Each instance follows the same pipeline (mids is the current reference implementation):

1. **Import sources**: `app/utils/copy-source-files.py` downloads TSVs and markdown from the standard's GitHub repo into `app/data/source/`. Source files are kept verbatim — content fixes belong in the standard's repo, then re-import; never hand-edit `data/source/`.
2. **Transform**: scripts in `app/utils/transformers/` run in sequence — `source_yaml_validator.py` → `process_files.py` → `merge_source_files.py` → `write_filters_json.py` — producing the TSVs in `app/data/output/`. These scripts do `from globals import ...` (repo-root globals.py), so the repo root must be on PYTHONPATH, and their relative paths assume they are run from the script's own directory (PyCharm-style run configs).
3. **Render**: `app/freeze.py` holds all Flask routes AND the Freezer. Routes read `data/output/*.tsv` with pandas, markdown content from `app/md/` (rendered with markdown2), and standard metadata (title, acronym, links) from `app/meta.yml`, then render Jinja templates in `app/templates/`.
4. **Freeze**: `python freeze.py build` writes static HTML to `build/` with relative URLs. The "API" endpoints (`/api/data.json`, `/api/filters.json`) are frozen to static JSON files consumed client-side by the interactive mappings table — there is no dynamic backend on GitHub Pages, so both JSON files must end up in the build.

Constraints inherited from Frozen-Flask (documented in the README):
- Every route in `freeze.py` must be bound with both leading and trailing slashes (e.g. `@app.route('/mappings/')`).
- File references in `freeze.py` are relative to the `app/` dir — no leading `app/` prefix (unlike the deprecated `routes.py` pattern in older instances).

Instance-specific notes:
- `ltc` is bilingual (English/French): parallel templates and a `build/fr/` tree; see `ltc/app/Translations-README.md`.
- In mids, MIDS Levels correspond to classes and Information Elements to properties in the merged termlist; mappings are SSSOM TSVs, one per (target standard, discipline) pair.

## Conventions

- File naming: hyphens for `.html`/`.csv`/`.tsv` (`quick-reference.html`), underscores for `.py`/`.md`/folders (`quick_reference.py`).
- `app/static/assets/` is the standardized shared theme (do not change); instance customizations go in `app/static/custom/` and `app/static/images/`.
