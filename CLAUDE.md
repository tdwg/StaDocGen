# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

StaDocGen generates static HTML documentation websites for TDWG data standards from tabular source data (CSV/TSV, SSSOM mappings) plus markdown content, using Flask + Jinja2 and Frozen-Flask. There is no test suite, linter, or CI; "testing" means running the dev server and viewing pages.

## Instances

Each top-level folder named after a standard namespace is an independent **instance** — its own Flask app, templates, static assets, data, and build. Instances share no code (copying patterns between them is expected; importing between them is not). `instances.md` lists them and their status.

- `ltc/` — Latimer Core (maintenance; has French translation routes/templates under `fr/`)
- `mids/` — Minimum Information about a Digital Specimen (most active; has public review pages and static JSON "API")
- `minext/` — Mineralogy Extension to Darwin Core
- `tdwg-metadata/` — metadata field spreadsheets/reference, not a Flask instance
- `docs/` — markdown docs exported from a legacy Writerside project (`docs/md/*.md` covers building, templates, utilities)
- `globals.py` (repo root) — `get_project_root()` etc.; utility scripts insert the repo root into `sys.path` to import it

## Instance structure (`<ns>/app/`)

- `freeze.py` — **the actual application**: defines all routes, reads `meta.yml`, renders markdown (`markdown2`) and TSVs (`pandas`) into Jinja templates, and freezes to `build/`. `routes.py` is deprecated/absent.
- `meta.yml` — standard metadata (title, links, source file URLs) passed to templates
- `md/` — page content markdown, copied from the standard's own GitHub repo (e.g. `tdwg/mids/source/md`)
- `data/source(s)/` — verbatim source files copied from the standard's repo; never hand-edit, change them upstream and re-copy
- `data/output/` — transformed TSVs that `freeze.py` actually reads
- `utils/` — copy-source scripts and transformers (source → output)
- `templates/` (`base.html` + `includes/<page>/` partials), `static/assets/` (shared theme, do not change), `static/custom/` (per-instance CSS/JS overrides), `static/.../images`
- `build/` — Frozen-Flask output, committed; this is what gets published

## Commands

Setup (Python 3.11, pip + venv; conda is known to break Frozen-Flask):
```
python -m venv .stadocgen-venv
.\.stadocgen-venv\Scripts\activate      # Windows
pip install -r requirements.txt          # note: requirements.txt is UTF-16 encoded
```

`freeze.py` opens `meta.yml`, `md/...`, and `data/...` with paths relative to the **app directory**, so run it from there:
```
cd mids/app
python freeze.py          # dev server on http://127.0.0.1:8001
python freeze.py build    # freeze static site into app/build/
```
`ltc` also supports `flask run` from `ltc/` (its `app/__init__.py` chdirs into `app/` and imports `freeze.app`). The `mids` and `minext` `__init__.py`/`main.py` files are stale (no routes / import a nonexistent `routes` module), so use `python freeze.py` for them.

Data refresh pipeline (per instance, before building):
- MIDS: `python mids/app/utils/copy-source-files.py` (downloads from tdwg/mids), then run `process_files.py` from `mids/app/utils/transformers/` (it derives the instance path from the CWD as `cwd.parent.parent.parent`), and `write_filters_json.py` to regenerate `api/filters.json` / `api/data.json`.
- MinExt: `copy_source_files.py` then `utils/transformations/terms_transformations.py` (column header requirements in `minext/README.md`).
- LtC: scripts in `ltc/app/utils/file-utils/` and `ltc/app/utils/transformations/`. The translation workflow requires manual cleanup (see `ltc/app/Translations-README.md`).

Publishing: copy the contents of `<ns>/app/build/` into the `docs/` folder of the standard's own repo (e.g. `robocopy <ns>\app\build <target>\docs /mir`), then PR there.

## Conventions and gotchas

- In `freeze.py`, every route must have leading **and** trailing slashes (e.g. `/terms/`) so Frozen-Flask emits `terms/index.html`. `FREEZER_RELATIVE_URLS = True`, so templates must build links/static paths that work relative to page depth.
- GitHub Pages can't serve dynamic endpoints: MIDS's `/api/*.json` routes exist so they get frozen into static JSON files that the mappings page JS fetches (see `mids/app/README.md`).
- TSV reads are inconsistent about `lineterminator` (`'\n'` vs `'\r'`) per file; match the existing call for a given file rather than "fixing" it.
- File naming (from README): html and csv use hyphens (`quick-reference.html`); py, md, and folders use underscores. Existing files don't all follow this.
- New standards: copy an existing instance folder and rename it to the standard's namespace.
