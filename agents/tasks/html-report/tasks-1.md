# Tasks: HTML report

**Spec:** `agents/specs/html-report/spec.md`
**Created:** 2026-11-11
**Version:** 1

This list builds step 16 of the implementation order: HTML report spec 2.0 and the new GraphQL API spec 1.0 (`agents/specs/graphql-api/spec.md`), with the amendments made with them: web app spec 2.0, reports spec 1.16 and user guide spec 1.1. The choices are in `agents/specs/html-report/review-1.md`, every one approved on 2026-11-11. Nothing in it is built yet: `src/wambatic/reports/api.py`, `jobs.py` and `assets.py` do not exist, and none of `assets_hash`, `page_assets`, `write_assets`, `graphql_router`, `ApiContext` or `SyncNeeded` is in `src/wambatic` (checked 2026-11-11).

The report page starts with the summary tiles, puts each section in a tab, wraps every table in a collapsible block, and adds sorting, filtering and CSV and Excel export to each table; its scripts and stylesheet move to a `wambatic-assets-HASH/` folder written beside it. The web app serves that folder at `/assets/HASH/`, and its REST routes give way to one GraphQL endpoint, `/graphql`, built with Strawberry.

The project has no affected-tests tool: each task names its test files. Every `pytest` and `mkdocs` command runs after `source bin/activate.sh`; `mkdocs` needs `uv sync --group docs` first. Browser tests (marker `browser`) run when Playwright's Chromium can be launched and are skipped otherwise; a task whose acceptance rests on them runs them locally and stops as `blocked` if Chromium cannot be launched. Never list environment variables or print a token: test one with `[ -n "${GITHUB_TOKEN:-}" ]` and print only yes or no.

The spec gives `html_document` an `assets_url` parameter the code does not have yet, so its API block carries a `# auditme: accept[spec-api-signature-drift]` line (added 2026-11-11 so the specs could be pushed); Task 2 builds the parameter and removes that line, and every task must leave `bin/audit-check.sh` passing.

---

## Task 1: Check that Strawberry works under Python 3.14

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** GraphQL API 1.1, External dependencies; review-1 item 17

**Technical Goal:** strawberry-graphql 0.338.0 does not list Python 3.14 on PyPI (checked 2026-11-11). Prove it installs and serves a query under the project's Python before anything is built on it.

**Subtasks:**

- [x] Starting-point check: `grep -rnwE 'assets_hash|page_assets|write_assets|graphql_router|ApiContext|SyncNeeded' src/wambatic` finds nothing, and `src/wambatic/reports/api.py`, `jobs.py` and `assets.py` do not exist; if any does, stop the task as `blocked` naming what was found
- [x] Add `strawberry-graphql[fastapi]==0.338.0` to the runtime dependencies in `pyproject.toml` (an exact pin, as the GraphQL API spec says) and run `uv lock` and `uv sync`
- [x] Add `openpyxl` to the development dependencies (for Task 6's browser test) and lock it
- [x] Write `src/tests/reports/test_api.py` with one test: a throwaway `strawberry.Schema` with a `hello: String!` query, mounted on a `fastapi.FastAPI` with `strawberry.fastapi.GraphQLRouter`, answers `POST /graphql {"query": "{ hello }"}` over `httpx.ASGITransport` with `{"data": {"hello": "world"}}`
- [x] If the install or the test fails under Python 3.14, stop the task as `blocked` with the error; do not try another version or library

**Acceptance Criteria:**

- [x] `uv run python -c 'import importlib.metadata, strawberry.fastapi; print(importlib.metadata.version("strawberry-graphql"))'` prints `0.338.0` under Python 3.14, with `exclude-newer` unchanged
- [x] The throwaway query test passes, and mypy accepts the test file

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/reports/test_api.py src/tests/test_package.py` passes

**Notes:**

- Key files: `pyproject.toml`, `uv.lock`, `src/tests/reports/test_api.py`
- Task 8 replaces the throwaway test with the real schema's tests
- Was blocked (2026-11-11): `uv lock` cannot resolve `strawberry-graphql[fastapi]==0.341.2`. The project's `[tool.uv] exclude-newer = "14 days"` quarantine hides it: it was published 2026-11-07, so it only becomes eligible on 2026-11-21. Needs the operator to choose: wait until it passes the quarantine, or add `exclude-newer-package = { strawberry-graphql = "2026-11-08" }` (or similar) to `pyproject.toml`, which relaxes the supply-chain measure for this one package. The `pyproject.toml` edits were reverted; nothing else in the subtasks has been done.
- Unblocked (2026-11-11, operator session): pin `strawberry-graphql[fastapi]==0.338.0` (released 2026-10-26), the newest release outside the 14-day window, and leave `exclude-newer` unchanged. Checked in the operator session: `uv lock` resolves it with `graphql-core` 3.3.1, and it imports and answers `{ hello }` through `GraphQLRouter` under Python 3.14.7. GraphQL API spec 1.1 records the new pin.

---

## Task 2: Write the assets folder beside the page

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** HTML report 2.0, Module location, API (`Asset`, `page_assets`, `assets_hash`, `assets_folder_name`, `write_assets`, `html_document`, `render_html`), Error handling, Implementation (Offline, with an assets folder), External dependencies; web app 2.0 (`/assets/HASH/NAME`)

**Technical Goal:** The page loads plotly.js, its script and its stylesheet from a hashed folder beside it instead of inlining them, so the new libraries do not swell every report, and the web app serves the same files.

**Subtasks:**

- [x] Vendor `bundle/write-excel-file.min.js` of write-excel-file 4.1.1 (from the npm tarball `https://registry.npmjs.org/write-excel-file/-/write-excel-file-4.1.1.tgz`) as `src/wambatic/reports/vendor/write-excel-file.min.js`, with its `LICENSE` beside it
- [x] Create `src/wambatic/reports/assets.py` with `Asset`, `page_assets()` (cached; `plotly.min.js` from `plotly.offline.get_plotlyjs()`, `write-excel-file.min.js`, `tables.js`, `report.js`, `report.css` with the palette tokens filled), `assets_hash()`, `assets_folder_name()` and `write_assets(directory)`, writing a temporary sibling directory renamed into place, keeping an existing folder, and raising `OutputError` (`cannot write PATH: REASON`) on failure. Record `WRITE_EXCEL_FILE_VERSION = '4.1.1'` and its SHA-256 in the module
- [x] Add an empty `templates/tables.js` placeholder (Tasks 5 and 6 fill it), and check that `uv_build` ships `vendor/` and every template in the wheel
- [x] Change `html_document(report, theme, assets_url)` so `report.html` links `report.css` and loads the scripts with `<script defer src=...>` under `assets_url`, in the order `plotly.min.js`, `write-excel-file.min.js`, `tables.js`, `report.js`; the page data stays inline
- [x] Remove the `# auditme: accept[spec-api-signature-drift]` line above `def html_document(` in `agents/specs/html-report/spec.md`: with `assets_url` built, spec and code agree and `bin/audit-check.sh` must pass without it
- [x] Change `render_html` to call `write_assets(out.parent)` first and pass `assets_folder_name() + '/'`; the page is not written if the folder fails
- [x] Add the `/assets/{hash}/{name}` route to `web.py` with each asset's media type and `Cache-Control: public, max-age=31536000, immutable`, a 404 for another hash or name, and build `/report` with `assets_url='/assets/' + assets_hash() + '/'`
- [x] Add `<p class="assets-missing">` after the header, `This report's files (wambatic-assets-HASH) did not load; keep the page beside that folder.`, shown by default and hidden by `report.css`
- [x] Tests in `src/tests/reports/test_html.py`: the hash changes when an asset's content changes; `write_assets` keeps an existing folder and leaves no folder after a failed write; a failed folder write leaves no page; the vendored file's SHA-256 equals the recorded one; the page names only files under `assets_url`. In `src/tests/reports/test_web.py`: `/assets/HASH/report.js` answers with its media type and cache header, another hash is a 404, and `/report` points at `/assets/HASH/`. In `src/tests/reports/test_html_browser.py`: the existing checks pass with requests to the page and its folder allowed and every other request still refused, and a page opened without its folder shows the notice

**Acceptance Criteria:**

- [x] `report --format html` writes the page and `wambatic-assets-HASH/` beside it, and the page opens offline from disk with every chart drawn
- [x] A second report in the same directory reuses the folder; a changed asset makes a second folder and leaves the first unchanged
- [x] `bin/audit-check.sh` reports no `spec-api-signature-drift` for `html_document`, with the acceptance line removed

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/reports/test_html.py src/tests/reports/test_html_browser.py src/tests/reports/test_web.py src/tests/reports/test_web_browser.py src/tests/test_cli.py src/tests/test_package.py` passes
- [x] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Task 1 (the dependency changes in `pyproject.toml`)
- Key files: `src/wambatic/reports/html.py` (`read_plotlyjs`, `stylesheet`, `render_html`), `src/wambatic/reports/templates/report.html`, `src/wambatic/reports/web.py`
- Scripts are classic, not modules, because Chromium and Firefox refuse module scripts from `file://`

---

## Task 3: Give every table cell its type and raw value

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** HTML report 2.0, Tables (Values)

**Technical Goal:** Sorting, filtering and export read numbers, not formatted text, so each header cell says its column's type and each numeric cell carries the value its text was formatted from.

**Subtasks:**

- [x] Change `cell` and `table_html` in `src/wambatic/reports/html.py` to take, per column, `data-type="number"` or `data-type="text"` on the header cell, and per numeric body and footer cell a `data-value`: `repr` of a float, `str` of an int, or empty for `None`
- [x] Pass the raw values from `period_table_html` (from `PeriodTable.rows` and `total`) and from the breakdown, contributors, languages and popularity-now builders, which format numbers they already hold; ratios keep the 0 to 100 percentage they show
- [x] Mark the text columns (the first column, and Login, Name, Language, Repository, Metric and Reason) `text`
- [x] Tests in `src/tests/reports/test_html.py`: for every table of a report built from the stats fixtures, each numeric cell's `data-value` parsed as a number formats to its text through the same formatter, and each `-` cell has an empty `data-value`; a hypothesis property test in `src/tests/reports/test_properties.py` for arbitrary values of each metric kind

**Acceptance Criteria:**

- [x] A cell showing `1,234` carries `data-value="1234"`, `+56` carries `56`, `12.5%` carries `12.5`
- [x] The page's visible text is unchanged

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/reports/test_html.py src/tests/reports/test_properties.py src/tests/reports/test_rows.py` passes
- [x] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Task 2
- `rows.py` is shared with the terminal; change it only to expose a raw value it already computes, never its rows' formatted text

---

## Task 4: Put each section in a tab

**Status:** todo
**Priority:** high
**Complexity:** large
**Spec Reference:** HTML report 2.0, Implementation (Layout items 1 to 5, Tabs, Granularity switch), Error handling (assets missing)

**User Story:** As a reader of a report, I want the summary tiles first and each section in its own tab, so that I can reach the part I want without scrolling past the rest.

**Subtasks:**

- [ ] Change the layout in `html.py` to the header, the missing-assets notice, the tiles, the tab bar, then the panels `tab-commits`, `tab-contributors`, `tab-lines`, `tab-flow`, `tab-delivery` and `tab-popularity` holding the charts and tables the spec lists for each, then Unavailable and the footer outside every panel; a tab and its panel appear only when the panel has content
- [ ] Write the tab bar as a `role="tablist"` of `role="tab"` buttons with `aria-controls`, and each panel as `<section role="tabpanel">` with its heading; the tab bar is hidden and every panel shows without script
- [ ] In `report.js`: show the first present tab, or the panel named by the URL fragment; set the fragment with `history.replaceState` on a choice; Left, Right, Home and End move between tabs
- [ ] Draw a panel's charts with `Plotly.newPlot` the first time it shows; on a granularity change redraw the shown panel's charts and mark the others to be redrawn when they next show
- [ ] Tests in `src/tests/reports/test_html.py`: the panel order and contents for an `activity`, `flow`, `delivery` and `popularity` report; a report without `flow` has no Flow tab; Unavailable sits outside the panels. In `src/tests/reports/test_html_browser.py`: every chart in every tab has a non-zero width once its tab shows; a granularity switch then a tab first opened after it shows the new granularity's buckets; arrow keys, Home and End move the selection; `#tab-flow` opens on Flow; with script disabled every panel shows

**Acceptance Criteria:**

- [ ] The page opens on the tiles and the first tab, and every chart and table of 1.3 is in exactly one panel
- [ ] No console error and no page error in the browser test

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_html.py src/tests/reports/test_html_browser.py src/tests/reports/test_web_browser.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Task 2
- Key files: `src/wambatic/reports/html.py`, `templates/report.html`, `templates/report.js`, `templates/report.css`
- The figures are built once per page (the Built once paragraph); the tabs only move where their elements go

---

## Task 5: Collapse, sort and filter the tables

**Status:** todo
**Priority:** high
**Complexity:** medium
**Spec Reference:** HTML report 2.0, Tables (Collapsible, Sortable, Filterable)

**User Story:** As a reader, I want long tables folded away, and columns I can sort and filter, so that I can find the rows I care about in a table of hundreds.

**Subtasks:**

- [ ] In `html.py`, wrap each data table, or the four tables of one period kind, in `<details class="table-block">` whose `<summary>` gives the title and the shown table's row count; it is `open` when that table (the `initial` granularity's, for a period group) has at most `TABLE_OPEN_ROWS = 10` body rows. Unavailable stays a plain table
- [ ] In `templates/tables.js`: a sort button in each header cell (ascending, descending, original order; `aria-sort` and an arrow; numbers by `data-value` with empty values last both ways; text with `Intl.Collator(undefined, {numeric: true, sensitivity: 'base'})`; stable; the total row stays last; each table keeps its own sort)
- [ ] A filter row of inputs inserted under each header: text contains, ignoring case; numbers `N`, `=N`, `>N`, `>=N`, `<N`, `<=N`, `A..B` with `,` and `%` allowed; an unreadable input gets `aria-invalid="true"` and filters nothing; AND across columns; 150 ms after the last keystroke; a `role="status"` line `Showing X of Y rows`; the total row reads `Total (all rows)` while a filter is on
- [ ] Update the summary's count when the granularity switch shows another period table
- [ ] Tests in `src/tests/reports/test_html.py`: which blocks are open for tables of 10 and 11 rows. In `src/tests/reports/test_html_browser.py`: sorting a numeric column orders by value with `-` last both ways and the third click restores the order; a text filter and each number form narrow the rows and update the count; an unreadable filter is marked and filters nothing; the total row keeps its place and its new label

**Acceptance Criteria:**

- [ ] A table of 11 body rows starts closed and one of 10 starts open
- [ ] Without script every table shows, unsorted and unfiltered, inside its `<details>`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_html.py src/tests/reports/test_html_browser.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Tasks 3 and 4
- No table library is added (External dependencies)

---

## Task 6: Export tables to CSV and Excel

**Status:** todo
**Priority:** high
**Complexity:** medium
**Spec Reference:** HTML report 2.0, Tables (Export), Error handling (failed export), Layout item 5 (footer version), External dependencies

**User Story:** As a reader, I want to save a table as CSV or Excel, so that I can work with the numbers in a spreadsheet.

**Subtasks:**

- [ ] In `templates/tables.js`, add `CSV` and `Excel` buttons beside each data table, exporting the shown rows in the shown order with the header and without the total row
- [ ] Name files `<page stem>-<slugified table title>[-<granularity>].csv|.xlsx`, the page stem passed in the page data from `report_filename`
- [ ] CSV: RFC 4180, CRLF, UTF-8 with a byte order mark, numbers from `data-value` without separators, empty values as empty fields, and a leading `'` on a text cell starting with `=`, `+`, `-` or `@`
- [ ] Excel: `writeXlsxFile` with one sheet named after the table (at most 31 characters, without `[]:*?/\`), a bold header row, numbers as numbers and text as text
- [ ] Download through a `Blob` URL and an `<a download>` click, revoking the URL afterwards; a failure shows one line beside the buttons and writes nothing
- [ ] Add the write-excel-file version to the provenance footer
- [ ] Tests in `src/tests/reports/test_html_browser.py`: after a filter and a sort, both buttons download (Playwright's download event) files whose rows match the shown rows; the CSV starts with the byte order mark and guards a login planted as `=cmd`; the `.xlsx` read with `openpyxl` has numeric cells for number columns and the sheet name rule; with the Excel library removed from the folder, the Excel button shows its failure line. In `src/tests/reports/test_html.py`: the footer names the version

**Acceptance Criteria:**

- [ ] Both exports open in a spreadsheet with the rows and order shown on the page
- [ ] No exported cell is a formula

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_html.py src/tests/reports/test_html_browser.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Task 5; `openpyxl` was added in Task 1

---

## Task 7: Move the sync jobs to `jobs.py`

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** GraphQL API 1.0, Module location; web app 2.0, Module location and API

**Technical Goal:** The GraphQL API and the web pages share the sync jobs without importing each other.

**Subtasks:**

- [ ] Move `SyncJob`, `Jobs`, `progress_json` and the sync-or-compute step `results_or_job` from `src/wambatic/reports/web.py` to `src/wambatic/reports/jobs.py` unchanged; `results_or_job` takes what it reads from `make_app`'s closure (settings, cache, jobs, clock and the job's run function) as arguments
- [ ] Update `web.py` to import them, and move their tests from `src/tests/reports/test_web.py` to `src/tests/reports/test_jobs.py`
- [ ] Update `src/tests/test_layering.py` and `src/tests/test_package.py` if they list the reports modules

**Acceptance Criteria:**

- [ ] Every web app behaviour is unchanged: the existing web tests pass with no other edit than their imports
- [ ] `jobs.py` imports nothing from `web.py`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_jobs.py src/tests/reports/test_web.py src/tests/reports/test_service.py src/tests/test_layering.py src/tests/test_package.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Can run in parallel with Tasks 2 to 6; it touches only the web app

---

## Task 8: Serve the GraphQL API at `/graphql`

**Status:** todo
**Priority:** high
**Complexity:** large
**Spec Reference:** GraphQL API 1.0, API, Error handling, Implementation (Stats, Sync, Transport, Cross-site requests, GraphiQL, Schema size, Testing)

**User Story:** As a script author, I want to ask the local server for exactly the stats I need, and to start and follow a sync, through one GraphQL endpoint.

**Subtasks:**

- [ ] Create `src/wambatic/reports/api.py` with the Strawberry types of the spec's SDL (`Granularity`, `CommitTimezone`, `JobState`, `StatsInput`, `Query`, `Mutation`, `StatsOutcome`, `SyncNeeded`, `Stats`, `Subject`, `RequestInfo`, `Series`, `Point`, `SyncJob`), `ApiContext`, `schema` and `graphql_router(context)`
- [ ] Resolvers: `stats` computes through `jobs.results_or_job` and builds `Stats` from `result_to_dict`, returns `SyncNeeded` on stale data and never starts a sync; `series(metrics:, by:)` filters; `job(id)` is `null` for an unknown job and forgets a failed job once reported; `sync` calls `Jobs.start` with `context.run_sync`; `version` is wambatic's version. Inputs go through `service.parse_target` and `service.make_request`
- [ ] The `WambaticErrors` schema extension: `extensions.code` and `extensions.status` per the spec's mapping, `BAD_QUERY` for syntax and validation errors, redacted messages, `internal error; see the server log` for anything else with `loguru.logger.exception`, and no traceback
- [ ] A check before Strawberry reads a POST: a `Content-Type` other than `application/json` gets 415 `{"error": "POST /graphql needs Content-Type: application/json"}`
- [ ] Mount the router in `make_app` at `/graphql` with `graphql_ide='graphiql'`, `allow_queries_via_get=True` and `multipart_uploads_enabled=False`; the loopback `Host` check and the request log apply
- [ ] Replace the throwaway test in `src/tests/reports/test_api.py` with the spec's Testing list: `stats` on fresh data equals `result_to_dict` for each granularity; the `series` filters; `SyncNeeded` on stale data with no job started; `sync`, `job` polling to `DONE`, then `stats(job:)`; two `sync` calls share a job; each error's code and status; a planted exception gives `INTERNAL` with no traceback and no token (set in the environment for the test); a mutation over GET refused; `text/plain` and `application/x-www-form-urlencoded` POSTs get 415; and `strawberry export-schema wambatic.reports.api:schema` equals the SDL in `agents/specs/graphql-api/spec.md`

**Acceptance Criteria:**

- [ ] `curl -s -H 'Content-Type: application/json' -d '{"query": "{ version }"}' http://127.0.0.1:PORT/graphql` answers `{"data": {"version": ...}}` from a running `wambatic serve`
- [ ] The exported schema matches the spec's SDL exactly

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_api.py src/tests/reports/test_jobs.py src/tests/reports/test_web.py src/tests/test_layering.py src/tests/test_package.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Tasks 1 and 7
- The test client and fixtures are those of `test_web.py`: `httpx.AsyncClient` over `httpx.ASGITransport` under `asyncio.run`, the stats fixtures' cache, and the `Upstream` fake GitHub
- If the SDL Strawberry prints differs from the spec only in formatting (ordering, line breaks), compare the parsed schemas with `graphql.build_schema` and `graphql.utilities.find_breaking_changes` both ways; any other difference stops the task as `blocked`, naming it

---

## Task 9: Remove the REST routes and poll GraphQL from the progress page

**Status:** todo
**Priority:** high
**Complexity:** medium
**Spec Reference:** GraphQL API 1.0, Implementation (Removed); web app 2.0, Implementation (routes, Sync jobs, Error handling)

**Technical Goal:** One API remains: the progress page follows a sync through `/graphql`, and `/api/stats`, `/api/progress`, `/openapi.json` and `/docs` answer 404.

**Subtasks:**

- [ ] Remove the `/api/stats` and `/api/progress` routes from `web.py`, and build the app with `openapi_url=None, docs_url=None, redoc_url=None`
- [ ] Change `templates/progress.js` to `POST /graphql` with `Content-Type: application/json` and the `job` query of the web app spec, once a second, and load the report with `&job=ID` when the state is `DONE`, or show the error when `FAILED`
- [ ] Update `src/tests/reports/test_web.py`: drop the REST tests the GraphQL tests now cover, assert the four removed paths answer 404, and keep the `/report` and progress-page tests; update `src/tests/reports/test_web_browser.py` so the progress page becomes the report through GraphQL polling with no request outside the server

**Acceptance Criteria:**

- [ ] A `/report` request that needs a sync shows the progress page, which becomes the report with every chart drawn
- [ ] `GET /api/stats`, `GET /api/progress`, `GET /openapi.json` and `GET /docs` answer 404

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_web.py src/tests/reports/test_web_browser.py src/tests/reports/test_api.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Task 8

---

## Task 10: Update the user guide and its screenshots

**Status:** todo
**Priority:** medium
**Complexity:** medium
**Spec Reference:** user guide 1.1 (`guide/html.md`, `guide/web.md`, the screenshot script); reports 1.16

**User Story:** As a user, I want the guide to show the tabbed report, the table controls and the GraphQL API, so that I can use them without reading the code.

**Subtasks:**

- [ ] `docs/guide/html.md`: the page and its assets folder (names, sharing them together, the missing-files notice), the tabs and links to a tab, collapsible tables, sorting, filtering with every number form, CSV and Excel export
- [ ] `docs/guide/web.md`: replace the JSON routes and `/docs` with the GraphQL API (a `stats` query, the `sync` mutation and `job` polling, each with a `curl` example), GraphiQL and its network need, the JSON content type a POST needs and why; replace the sequence diagram with `stats` answering `SyncNeeded`, `sync`, `job` polling, then `stats` with `job`
- [ ] `docs/guide/json.md` and every other page: replace each mention of `/api/stats` or `/api/progress` (`grep -rn 'api/stats\|api/progress\|/docs' docs README.md`)
- [ ] `bin/screenshots.py`: capture GraphiQL in place of `/docs`, the tab bar, and an open table with a filter applied and its export buttons; update `WANTED` and the selectors
- [ ] Run `bin/screenshots.sh` and commit the new images; it needs a GitHub token because it syncs `pallets/click` and `org:pallets` from GitHub, and GraphiQL needs the network for its CDN script. If `[ -n "${GITHUB_TOKEN:-}" ]` is false and `gh auth token` fails, stop the task as `blocked` saying so

**Acceptance Criteria:**

- [ ] No page of the guide or the README mentions `/api/stats`, `/api/progress` or `/docs`
- [ ] Every image the guide includes exists and shows the 2.0 page

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] `uv sync --group docs` succeeds
- [ ] `mkdocs build --strict` exits 0
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/test_docs.py src/tests/test_screenshots.py` passes
- [ ] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Tasks 6 and 9
- The screenshot cache `~/.cache/wambatic/docs.sqlite3` is the script's own, never the user's

---

## Task 11: Close the list

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** implementation order 1.14, step 16; every spec section above (closing)

**Technical Goal:** Mark the work done and run every check across the whole tree once before the branch merges.

**Subtasks:**

- [ ] Mark step 16 `done` in `agents/specs/implementation-order.md`, linking this list, and set its `**Status:**` to `implemented`
- [ ] Set the spec's `**Status:**` to `implemented` in `agents/specs/html-report/spec.md`, `agents/specs/graphql-api/spec.md`, `agents/specs/web-app/spec.md`, `agents/specs/reports/spec.md` and `agents/specs/user-guide/spec.md`
- [ ] Add the list to `agents/tasks/index.md` if it is not there

**Acceptance Criteria:**

- [ ] Every spec this list builds says `implemented`, and step 16 says `done`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] `uv sync --group docs` succeeds
- [ ] `mkdocs build --strict` exits 0
- [ ] `pre-commit run --all-files` exits 0
- [ ] `bin/audit-check.sh` exits 0
- [ ] `pytest src/tests/reports src/tests/test_cli.py src/tests/test_docs.py src/tests/test_layering.py src/tests/test_package.py src/tests/test_screenshots.py` passes: every test that reaches `reports`, the package this list changes

**Notes:**

- Depends on Tasks 1 to 10
- `browser` and `live` tests run in CI's `browser` and `live` jobs; the local run above skips the browser tests only when Chromium cannot be launched
