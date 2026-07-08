# Graph Report - test3  (2026-07-08)

## Corpus Check
- 11 files · ~7,666 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 126 nodes · 160 edges · 16 communities (12 shown, 4 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 17 edges (avg confidence: 0.76)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `893fd9cc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Output File Writing|Output File Writing]]
- [[_COMMUNITY_Desktop GUI (Tkinter)|Desktop GUI (Tkinter)]]
- [[_COMMUNITY_Frontend ↔ API Flow|Frontend ↔ API Flow]]
- [[_COMMUNITY_Core MSL Lookup Logic|Core MSL Lookup Logic]]
- [[_COMMUNITY_SQLite Cache & Threaded Lookup|SQLite Cache & Threaded Lookup]]
- [[_COMMUNITY_DigiKey API Integration|DigiKey API Integration]]
- [[_COMMUNITY_Mouser API Integration|Mouser API Integration]]
- [[_COMMUNITY_Flask Web Server|Flask Web Server]]
- [[_COMMUNITY_MSL Domain Concepts|MSL Domain Concepts]]
- [[_COMMUNITY_Claude Permissions Config|Claude Permissions Config]]
- [[_COMMUNITY_Quick Search Feature|Quick Search Feature]]
- [[_COMMUNITY_File Upload Handling|File Upload Handling]]
- [[_COMMUNITY_Results Export|Results Export]]
- [[_COMMUNITY_Python Dependencies|Python Dependencies]]
- [[_COMMUNITY_Community 14|Community 14]]

## God Nodes (most connected - your core abstractions)
1. `MSLGUI` - 12 edges
2. `Project Handoff — MSL Lookup Tool` - 10 edges
3. `find_msl()` - 9 edges
4. `DigiKeyAPIError` - 7 edges
5. `cache_msl()` - 7 edges
6. `get_cached_msl()` - 7 edges
7. `get_access_token()` - 5 edges
8. `search_part()` - 5 edges
9. `search_part_retry()` - 5 edges
10. `get_connection()` - 5 edges

## Surprising Connections (you probably didn't know these)
- `bool` --uses--> `DigiKeyAPIError`  [INFERRED]
  msl_lookup/msl_finder.py → msl_lookup/digikey_api.py
- `MSLGUI` --uses--> `DigiKeyAPIError`  [INFERRED]
  msl_lookup/main.py → msl_lookup/digikey_api.py
- `str` --uses--> `DigiKeyAPIError`  [INFERRED]
  msl_lookup/msl_finder.py → msl_lookup/digikey_api.py
- `find_msl()` --calls--> `cache_msl()`  [INFERRED]
  msl_lookup/msl_finder.py → msl_lookup/local_db.py
- `find_msl()` --calls--> `get_cached_msl()`  [INFERRED]
  msl_lookup/msl_finder.py → msl_lookup/local_db.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Batch MSL Lookup Flow** — msl_lookup_index_handlefile, msl_lookup_index_startlookup, msl_lookup_index_listenprogress, msl_lookup_index_loadresults [INFERRED 0.85]
- **Frontend to Flask API Contract** — concept_api_upload, concept_api_lookup, concept_api_progress, concept_api_results, concept_api_search [INFERRED 0.75]

## Communities (16 total, 4 thin omitted)

### Community 0 - "Output File Writing"
Cohesion: 0.20
Nodes (14): DataFrame, find_mpn_column(), get_msl_for_row(), preview_data(), int, str, Excel/CSV output writer., Find the MPN column in DataFrame. (+6 more)

### Community 2 - "Frontend ↔ API Flow"
Cohesion: 0.20
Nodes (12): /api/lookup Endpoint, /api/progress SSE Endpoint, /api/results Endpoint, filterTable (index.html), listenProgress (index.html), loadResults (index.html), renderTable (index.html), startLookup (index.html) (+4 more)

### Community 3 - "Core MSL Lookup Logic"
Cohesion: 0.27
Nodes (9): bool, find_msl(), find_msl_batch(), normalize_mpn(), str, Core MSL lookup logic combining API and local cache., Normalize MPN for consistent matching., Find MSL for a given MPN.      1. Check local cache first     2. Query DigiKe (+1 more)

### Community 4 - "SQLite Cache & Threaded Lookup"
Cohesion: 0.38
Nodes (9): run_lookup(), search_single(), cache_msl(), get_cached_msl(), get_connection(), init_db(), log_lookup(), str (+1 more)

### Community 5 - "DigiKey API Integration"
Cohesion: 0.33
Nodes (9): DigiKeyAPIError, get_access_token(), float, int, str, DigiKey API v4 integration for MSL lookups., Get OAuth2 access token from DigiKey with caching (tokens valid ~3600s)., search_part() (+1 more)

### Community 6 - "Mouser API Integration"
Cohesion: 0.31
Nodes (8): Exception, MouserAPIError, float, int, str, Mouser API integration for MSL lookups., search_part(), search_part_retry()

### Community 7 - "Flask Web Server"
Cohesion: 0.28
Nodes (4): find_mpn_column(), MSL Lookup Tool - Flask web server., start_lookup(), upload()

### Community 8 - "MSL Domain Concepts"
Cohesion: 0.15
Nodes (13): DigiKey Data Source, Maker Part Number (MPN), Moisture Sensitivity Level (MSL), 1. Get Mouser API Key (free), 2. Install Dependencies, 3. Set API Key, 4. Run, Input File Format (+5 more)

### Community 10 - "Quick Search Feature"
Cohesion: 1.00
Nodes (3): /api/search Endpoint, quickSearch (index.html), quickSearch (templates/index.html)

### Community 11 - "File Upload Handling"
Cohesion: 0.67
Nodes (3): /api/upload Endpoint, handleFile (index.html), handleFile (templates/index.html)

### Community 14 - "Community 14"
Cohesion: 0.18
Nodes (10): Architecture Notes, Completed, graphify Quick Reference, How to Run, Important Files, In Progress / Open, Issues / Risks, Next Actions (suggested) (+2 more)

## Knowledge Gaps
- **31 isolated node(s):** `allow`, `int`, `float`, `int`, `float` (+26 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **4 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `DigiKeyAPIError` connect `DigiKey API Integration` to `Desktop GUI (Tkinter)`, `Core MSL Lookup Logic`, `Mouser API Integration`?**
  _High betweenness centrality (0.118) - this node is a cross-community bridge._
- **Why does `MSLGUI` connect `Desktop GUI (Tkinter)` to `DigiKey API Integration`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `find_msl()` connect `Core MSL Lookup Logic` to `SQLite Cache & Threaded Lookup`?**
  _High betweenness centrality (0.075) - this node is a cross-community bridge._
- **Are the 3 inferred relationships involving `find_msl()` (e.g. with `cache_msl()` and `get_cached_msl()`) actually correct?**
  _`find_msl()` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 3 inferred relationships involving `DigiKeyAPIError` (e.g. with `bool` and `MSLGUI`) actually correct?**
  _`DigiKeyAPIError` has 3 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `cache_msl()` (e.g. with `run_lookup()` and `search_single()`) actually correct?**
  _`cache_msl()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `allow`, `MSL Lookup Tool - Flask web server.`, `int` to the rest of the system?**
  _47 weakly-connected nodes found - possible documentation gaps or missing edges._