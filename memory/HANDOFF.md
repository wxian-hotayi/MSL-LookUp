# Project Handoff — MSL Lookup Tool

_Last updated: 2026-07-08_

## Project Summary
`test3` is an **MSL (Moisture Sensitivity Level) Lookup Tool** for electronic
components. Given Maker Part Numbers (MPNs), it resolves each part's MSL rating
via the DigiKey API (primary) with a Mouser fallback, caching results in a local
SQLite DB. It ships **two frontends**: a Flask web app and a Tkinter desktop GUI.
DigiKey OAuth2 credentials are hardcoded in `digikey_api.py`, so no API-key setup
is needed to run the tool.

## Completed
- Core MSL lookup logic (cache-first, then DigiKey API) — `msl_finder.py`
- DigiKey API v4 integration with OAuth2 token caching — `digikey_api.py`
- Mouser API integration (fallback supplier) — `mouser_api.py`
- SQLite cache + lookup logging — `local_db.py` (`msl_cache.db`)
- Flask web server with SSE progress streaming — `app.py`
- Tkinter desktop GUI with threaded lookup — `main.py`
- Excel/CSV input reading + output writing — `output_writer.py`
- **Double-click launcher `Run-MSL-Tool.bat`** (project root) — detects Python,
  auto-installs deps if missing, starts the Flask web app, auto-opens the browser
  at http://localhost:5000. Verified end-to-end (HTTP 200, title "MSL Lookup Tool").
- graphify knowledge graph → `graphify-out/` (graph.html, graph.json, GRAPH_REPORT.md)

## In Progress / Open
- Nothing actively mid-edit. Project is feature-complete per git log.

## Issues / Risks
1. **Duplicate frontends**: `msl_lookup/index.html` and
   `msl_lookup/templates/index.html` are near-duplicates. Flask serves the
   `templates/` version (canonical, newer). The root `index.html` is stale —
   safe to delete to avoid drift.
2. **Uncommitted change**: `msl_lookup/msl_cache.db` shows as modified — runtime
   cache churn; should be gitignored rather than committed.
3. **`.bat` requires Python on the target PC** — accepted trade-off. For a
   Python-free portable build, add a PyInstaller `.exe` (not yet done).
4. **graphify caveat**: high-betweenness "bridge" nodes (`DigiKeyAPIError`, plus
   generic `str`/`bool`/`int`) are partly artifacts. `DigiKeyAPIError`↔`MouserAPIError`
   is a FALSE bridge (shared `Exception` base collapsed into one node), not real coupling.

## Important Files
| File | Role |
|------|------|
| `Run-MSL-Tool.bat` | Double-click launcher → starts web app + opens browser |
| `msl_lookup/app.py` | Flask web server (entry: `python app.py` → localhost:5000) |
| `msl_lookup/main.py` | Tkinter desktop GUI (`MSLGUI`, threaded lookup) |
| `msl_lookup/msl_finder.py` | Core logic: `find_msl()`, `find_msl_batch()`, `normalize_mpn()` |
| `msl_lookup/digikey_api.py` | DigiKey v4: `get_access_token()`, `search_part()`, `search_part_retry()`, `DigiKeyAPIError` |
| `msl_lookup/mouser_api.py` | Mouser fallback: `search_part()`, `MouserAPIError` |
| `msl_lookup/local_db.py` | SQLite cache: `init_db()`, `cache_msl()`, `get_cached_msl()`, `log_lookup()` |
| `msl_lookup/output_writer.py` | `read_input_file()`, `find_mpn_column()`, write to Excel/CSV |
| `msl_lookup/templates/index.html` | Canonical web UI |
| `graphify-out/` | Knowledge graph outputs (graph.html, graph.json, GRAPH_REPORT.md) |

## Architecture Notes
- **Lookup flow** (the app's spine): MPN → normalize → check SQLite cache →
  on miss, query DigiKey → on `DigiKeyAPIError`/no result, fall back to Mouser →
  cache result → return.
- **Two independent entry points** (web `app.py`, desktop `main.py`) share the
  same core modules (`msl_finder`, `*_api`, `local_db`).
- **Graph snapshot (2026-07-08, commit 893fd9cc): 126 nodes · 160 edges · 16 communities.**
- **God nodes** (most connected): `MSLGUI` (12), `find_msl()` (9),
  `DigiKeyAPIError` (7), `cache_msl()` (7), `get_cached_msl()` (7),
  `get_access_token()` / `search_part()` / `search_part_retry()` / `get_connection()` (5).
- **Communities**: Output File Writing, Frontend↔API Flow, Core MSL Logic,
  SQLite Cache & Threaded Lookup, DigiKey API, Mouser API, Flask Web Server,
  MSL Domain Concepts, Quick Search, File Upload, Results Export, Claude
  Permissions Config, Python Dependencies (+ thin communities incl. one covering
  this HANDOFF's own sections, now indexed as graph nodes).
- No import cycles detected.

## Next Actions (suggested)
1. Resolve the duplicate `index.html` (keep `templates/` version, delete root).
2. Add `msl_lookup/msl_cache.db` to `.gitignore`.
3. Optional: PyInstaller `.exe` for a Python-free double-click distribution.
4. Optional: add tests for `find_msl()` cache-hit vs API-miss paths.

## How to Run
```
# Easiest: double-click Run-MSL-Tool.bat  (project root)

# Or manually:
cd msl_lookup
python app.py        # web UI at http://localhost:5000 (auto-opens browser)
# or
python main.py       # desktop GUI
```

## graphify Quick Reference
- Graph already built. Ask codebase questions and they'll be answered from
  `graphify-out/graph.json`.
- **This environment has NO LLM API key**, so full semantic rebuild (`graphify .`)
  fails. Use `graphify update .` — re-extracts code and refreshes graph.json /
  graph.html / GRAPH_REPORT.md with **no LLM/API cost**. Last run did this.
- Each update backs up the prior curated graph to `graphify-out/<date>/`
  (e.g. `graphify-out/2026-07-08/`).
- To enable semantic extraction later: set `GEMINI_API_KEY` / `GOOGLE_API_KEY`
  (or another supported backend key) before running `graphify .`.
