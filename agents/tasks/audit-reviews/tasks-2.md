# Tasks: Audit review 2

**Source:** `agents/audit-reviews/review-2.md`
**Created:** 2026-10-31
**Version:** 2

This list fixes what the second audit found and the user approved on 2026-10-31: findings G1-G16 of [review-2.md](../../audit-reviews/review-2.md), with option A for both of its decisions (keep the web server's two error-boundary handlers and record why; split the fetch-and-cache spec now, the others when they next change). It also closes what [tasks-1.md](tasks-1.md) left open, Task 15, whose zero-hit check the newer checker broke, and the `TODO.md` item "The auditme checker's 2026-10-31 rules report hits here", which is the same work as G2.

Task 1 comes first because the pre-push hook refuses every push until the 16 `raises-section-drift` hits are gone. Line numbers below are from review-2 (2026-10-31); earlier tasks move lines, so each task finds its sites by their code and works from a fresh `bin/audit-check.sh` run. A task that meets a case review-2 and its Answers do not settle stops for the user.

## Coverage

| Finding or decision | Covered by |
|---|---|
| G2 (`raises-section-drift`, A4), the `TODO.md` item | Task 1 |
| G1, G3 | Task 2 |
| G15 | Task 3 |
| G16 / Decision 2 (split the fetch-and-cache spec) | Task 4 |
| G16 (the rest) | Task 5 |
| G4, G5 | Task 6 |
| G6 | Task 7 |
| G7, G9 | Task 8 |
| G8 / Decision 1, G10, G11, G14 | Task 9 |
| G12 | Task 10 |
| G13 (no change), tasks-1 Task 15, the `TODO.md` item, closing the audit | Task 11 |

---

## Task 1: Make every Raises section match what reaches the caller

**Status:** done
**Priority:** high
**Complexity:** medium
**Source Reference:** G2 (A4, `raises-section-drift`); `TODO.md` item "The auditme checker's 2026-10-31 rules report hits here"

**Technical Goal:** Clear the 16 `raises-section-drift` hits and the 14 A4 rows, so the pre-push hook passes and every `Raises:` section says what a caller must handle.

**Subtasks:**

- [x] For each hit of `bin/audit-check.sh --rule raises-section-drift` and each A4 row of review-2 (`fetch/client.py` `graphql_dated`, `rest_get`; `fetch/cache.py` `write_rows`; `fetch/base.py` `owner_kind`, `list_repos`, `provenance`, `line_counts`; `reports/service.py` `sync_and_compute`; `stats/engine.py` `read_records`, `compute`, `compute_all`; `reports/web.py` `parse_query`, `results_or_job`, `serve`; `stats/buckets.py` and `stats/engine.py:235` as the script names them), make the `Raises:` section list exactly the domain errors that reach the caller: add each one a same-package callee raises and the function does not catch; drop each one its own `except` always catches
- [x] Where a callee in another package raises (for example `CacheError` reaching `stats/engine.py` through the fetcher), list it as A4 asks (the script follows same-package callees only)
- [x] Where the rule is wrong for a site, add `# auditme: accept[raises-section-drift] <reason>` on the `def` line and stop for the user to raise the pattern in the auditme skill's `requests.md` (that is a change to the agents repository, not this one)
- [x] Re-check the `TODO.md` item's other hit: `stats/delivery.py` `UNITS` is `types.MappingProxyType` since tasks-1 Task 7, so `bin/audit-check.sh --rule mutable-module-level-exported` reports nothing; note that in the item's closing line in Task 11

**Acceptance Criteria:**

- [x] `bin/audit-check.sh --rule raises-section-drift` exits 0
- [x] `bin/audit-check.sh` exits 0, so `git push` passes the pre-push hook

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pre-commit run --hook-stage pre-push --all-files` passes
- [x] `pytest src/tests/test_package.py` passes (docstrings only; no behaviour changes)

**Notes:**

- Key files: `src/wambatic/fetch/client.py`, `fetch/cache.py`, `fetch/base.py`, `stats/engine.py`, `stats/buckets.py`, `reports/service.py`, `reports/web.py`
- Docstrings only: if a hit needs a behaviour change to be true, stop for the user

---
- Operator session, 2026-10-31: the 16 script hits are fixed. Two were false (`stats/buckets.py` `bucket_range` and `stats/engine.py` `aggregate`: `bucket_start` cannot raise for TOTAL there) and carry scoped `accept[raises-section-drift]` markers; the checker does not see the TOTAL guard, which is a refinement to raise in the auditme skill's `requests.md`. Second session, 2026-10-31: the A4 rows the script does not check are fixed too (`owner_kind`, `list_repos`, `provenance`, `line_counts`, `read_records`, `compute`, `compute_all`, `results_or_job`, `serve`, `sync_and_compute`). The `TODO.md` item's `UNITS` hit is for Task 11 to note.

---

## Task 2: Translate the remaining stdlib errors

**Status:** done
**Priority:** high
**Complexity:** small
**Source Reference:** G1 (A1-A3, review-1 F2/F5), G3

**User Story:** As a CLI user, I want a malformed GitHub response or a broken install to give one line saying what failed, so that I never see a traceback for them.

**Subtasks:**

- [x] `fetch/client.py:254-257`: on a `ValueError` from `raw.json()` for an OK response, raise `FetchError` naming the endpoint (`GitHub sent a response that is not JSON for ...`), chained from the `ValueError`; add a test with the fake upstream answering `200` with a non-JSON body, and check it fails on the old code
- [x] `version.py:10-11`: catch `OSError` and `UnicodeDecodeError` too, with the same `'0+unknown'` fallback; test each
- [x] `bin/audit-check.py:97`: an `OSError` from running the checker exits 2 with a one-line message naming the command; test it
- [x] `bin/record-fixtures.py:131`, `:140`, `:150`: raise `RecordingError` instead of `RuntimeError`; update the tests that expect `RuntimeError`
- [x] Add each new error to the function's `Raises:` section

**Acceptance Criteria:**

- [x] `grep -rn "raise RuntimeError\|^\s*raise$" src/wambatic bin` finds no re-raise of a stdlib error out of a translating function
- [x] `wambatic report` against a fake upstream returning non-JSON exits 1 with one error line and no traceback

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `bin/audit-check.sh --path src/wambatic/fetch/client.py --path src/wambatic/version.py --path bin` exits 0
- [x] `pytest src/tests/fetch/test_client.py src/tests/test_version.py src/tests/test_audit_check.py src/tests/test_record_fixtures.py src/tests/test_cli.py` passes

**Notes:**

- Depends on Task 1

---

## Task 3: Bring the spec text in line with the code

**Status:** done
**Priority:** medium
**Complexity:** small
**Source Reference:** G15 (Doc4)

**Technical Goal:** Every Doc4 row of review-2 is fixed in the spec, so a reader of a spec meets the behaviour the code has.

**Subtasks:**

- [x] `fetch-and-cache/spec.md:409-410`: exhausted retries raise `FetchError` (with the cause chained) for connection errors, timeouts and 500/502/503/504; any other non-2xx raises `FetchError` naming the status; other `aiohttp.ClientError`s become `FetchError`; add the non-JSON 200 of Task 2
- [x] `system/spec.md:48`: `cli` opens the `Cache`; `reports/service.py` builds the `Fetcher`, syncs and calls `compute_all`
- [x] `system/spec.md:88`: the runtime libraries are declared (drop "proposals pending a maintenance check")
- [x] `stats/spec.md:19-28`: add `percentile.py` to the module table; `:215`: the workflow file name strips a trailing `@ref` first; `:257`, `:261`: write the defaults as tuples
- [x] `reports/spec.md:221`: `inspect_cache`, not `Cache.inspect`; `:234` and `:315`: `OutputError` for `--out` and `ServeError` for binding, exit 1 through `ReportsError`; `:200-201`: the 2008-01-01 floor, the tomorrow ceiling and the empty `--groups` refusal; `:27`: `redact_error` in the `service.py` row
- [x] Bump each changed spec's minor version, citing review-2 G15

**Acceptance Criteria:**

- [x] Each Doc4 row of review-2 is fixed, checked one by one against the code

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Depends on Task 2 (the fetch spec describes its non-JSON error)
- Key files: `agents/specs/fetch-and-cache/spec.md`, `system/spec.md`, `stats/spec.md`, `reports/spec.md`

---

## Task 4: Split the fetch-and-cache spec into a fetch spec and a cache spec

**Status:** done
**Priority:** medium
**Complexity:** medium
**Source Reference:** G16, Decision 2 (A)

**Technical Goal:** No spec a planning step loads is more than twice the specdev size guide; fetch and cache each get their own spec.

**Subtasks:**

- [x] Create `agents/specs/fetch/spec.md` (GitHub client, auth, rate limits, queries, the `Fetcher` and its per-resource sync; module location `src/wambatic/fetch/{auth,base,client,errors,queries,ratelimit}.py`) and `agents/specs/cache/spec.md` (the SQLite schema, `Cache`, identity and version checks, `inspect_cache`, `clear_cache`; module location `src/wambatic/fetch/cache.py`), each with every template section, a Prerequisite line and a version history that starts with a paragraph saying it was split from fetch-and-cache 1.x on 2026-10-31 (review-2 Decision 2)
- [x] Move every paragraph of `agents/specs/fetch-and-cache/spec.md` into exactly one of the two, unchanged except for cross-references; turn `fetch-and-cache/spec.md` into a two-line pointer to the new specs, so old links still lead somewhere
- [x] Update `agents/specs/index.md`, `implementation-order.md`, the other specs, README.md and AGENTS.md links; leave reviews and finished task lists as they are (they are records)
- [x] Check that every relative link in `agents/specs/`, README.md and AGENTS.md resolves (a short script; list any that do not)
- [x] `reports/spec.md` and `stats/spec.md` are not split now (Decision 2 A: when they next change)

**Acceptance Criteria:**

- [x] Every paragraph of the old spec appears in one new spec (check with a script that each paragraph of the old file's text, minus link targets, is in one of the new files)
- [x] Each new spec passes the specdev validation criteria; neither is over about 300 lines (the fetch spec is the longer, under twice the specdev guide of about 200 lines; its text is moved unchanged, so it is not cut further)
- [x] Every relative link resolves

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Depends on Task 3 (it edits the same spec first)
- If a paragraph belongs to both halves, put it in the fetch spec and link to it from the cache spec; stop for the user only if a split would change what a paragraph means

---

## Task 5: Fix the specs' version history, prerequisites and the implementation order

**Status:** todo
**Priority:** low
**Complexity:** small
**Source Reference:** G16 (the rest of the spec review)

**Technical Goal:** The spec set is consistent with itself and with the work done since step 10.

**Subtasks:**

- [ ] Put each spec's version paragraphs in order, one paragraph per version (`stats/spec.md` 1.7 before 1.8, `reports/spec.md` 1.10 before 1.11, the fetch 1.12 paragraph of its own in the new fetch spec)
- [ ] `agents/specs/implementation-order.md`: a step (or a closing section) for the audit work after step 10, linking review-1, review-2, tasks-1 and tasks-2; steps 4 and 5 name `compute_all` beside `compute`; bump its version
- [ ] `agents/specs/index.md:10`: true once Task 4's specs carry Prerequisite lines; check it

**Acceptance Criteria:**

- [ ] Every spec's version paragraphs are in ascending order
- [ ] `implementation-order.md` mentions every task list under `agents/tasks/`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)

**Notes:**

- Depends on Task 4

---

## Task 6: One timezone owner, exhaustive splits and honest names

**Status:** todo
**Priority:** low
**Complexity:** medium
**Source Reference:** G4 (A5), G5 (A9, A11, A13)

**Technical Goal:** `StatsRequest` cannot hold two different zones, every split over a `Literal` or enum is checked by mypy, and functions that do I/O are not named as if pure.

**Subtasks:**

- [ ] G4: `StatsRequest.__post_init__` raises the stats `InvalidRequestError` when `str(tz)` differs from `settings.timezone`; test it; fix any caller the check catches
- [ ] G5 A11: end each split review-2 names (`cli.py:271`, `:320`, `fetch/client.py:293`, `stats/buckets.py:70`, `reports/figures.py:318`) with an explicit last branch and `typing.assert_never`
- [ ] G5 A13: pass `full_refresh` and `no_fetch` by keyword at `reports/web.py:345`; in `fetch/base.py:766` `new_state`, name the fallback (`full_synced_at if full_synced_at is not None else now`) with a comment saying a first full read starts the full-read clock
- [ ] G5 A9: rename `fetch/cache.py` `check_identity` to `record_identity` and `fetch/auth.py` `resolve_token` to `fetch_token`, with every caller, test and spec mention; leave the tz lookups (`resolve_tz`, `build_request`, `parse_query`), `compute_all` and `check_host_header` as they are (library reads of package data, or names the spec defines)

**Acceptance Criteria:**

- [ ] `mypy src` passes and would fail if a member were added to any of those `Literal`s or enums (check once by adding one locally)

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `bin/audit-check.sh --path src/wambatic` exits 0
- [ ] `pytest src/tests/stats src/tests/test_cli.py src/tests/fetch src/tests/reports/test_web.py src/tests/reports/test_figures.py src/tests/reports/test_service.py` passes

**Notes:**

- Depends on Task 5 (it renames names the specs mention)

---

## Task 7: Remove the reads and derivations left after read-once

**Status:** todo
**Priority:** low
**Complexity:** medium
**Source Reference:** G6 (A14, P2, P3)

**Technical Goal:** One report reads each cache row once and derives each table and series once.

**Subtasks:**

- [ ] `fetch/base.py` `provenance`: accept the repos and sync states the caller already holds (`read_records` has them), so a report reads the repo list and each `star_events` sync state once; `stars_hidden` uses the same states
- [ ] `reports/html.py` `sections_html`: build each section's table once and use it for both the presence test and the render; derive `popularity_now(total)` and `languages_rows(total)` once per document
- [ ] `reports/terminal.py` `render_terminal`: derive `total_series` and `bucket_list` once and pass them to the table builders
- [ ] `fetch/cache.py`: compute `column_names` once per `Table`, not per row
- [ ] `stats/engine.py:283`: keep each commit's local date from `read_commits` instead of recomputing it in `aggregate` and `activity`
- [ ] `reports/web.py`: read every template once when the app is made, not on the first request
- [ ] A counting test: one HTML report reads each `Fetcher` method once per repository, and `sync_state` once per (repo, resource)

**Acceptance Criteria:**

- [ ] Every HTML, terminal, JSON and web test passes unchanged (output byte for byte)

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `bin/audit-check.sh --path src/wambatic` exits 0
- [ ] `pytest src/tests/stats src/tests/reports src/tests/fetch/test_fetcher.py src/tests/fetch/test_cache.py src/tests/test_cli.py` passes
- [ ] `pytest -m browser src/tests/reports` passes

**Notes:**

- Depends on Task 6

---

## Task 8: Construction helpers, named returns and the terminal shim

**Status:** todo
**Priority:** low
**Complexity:** small
**Source Reference:** G7 (A15, A23; A8 no change), G9 (A17)

**Technical Goal:** Each record type is assembled in one place, no returned value is dropped unnamed, and nothing reads a constant through a compatibility shim.

**Subtasks:**

- [ ] A15: one `series_of(name, unit, buckets, values)` helper used by `stats/flow.py`, `popularity.py`, `delivery.py` and `activity.py`; one helper for `PeriodTable` rows in `reports/rows.py`; build `RestResponse` once in `fetch/client.py` `rest_get`; one `Commit` builder shared by `fetch/base.py:487` and `:861`; one `Bucket` builder in `stats/buckets.py`
- [ ] A23: name the dropped values (`data, _date = await self.graphql_dated(...)` at `fetch/client.py:163`; the same at `bin/record-fixtures.py:135`)
- [ ] G9: remove the module `__getattr__` shim at `reports/terminal.py:14`; point `src/tests/reports/test_terminal.py:322` at `wambatic.reports.rows.TOP_CONTRIBUTORS_SHOWN`
- [ ] A8: no change (`SyncJob`, `SyncProgress` and `Tally` are mutable by design, commented in tasks-1 Task 8)

**Acceptance Criteria:**

- [ ] Every existing test passes unchanged apart from the one shim test

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `bin/audit-check.sh --path src/wambatic --path bin` exits 0
- [ ] `pytest src/tests/stats src/tests/reports/test_rows.py src/tests/reports/test_terminal.py src/tests/fetch/test_client.py src/tests/fetch/test_base.py src/tests/test_record_fixtures.py` passes

**Notes:**

- Depends on Task 7

---

## Task 9: Record the deliberate exceptions and fix the doc details

**Status:** todo
**Priority:** low
**Complexity:** small
**Source Reference:** G8 / Decision 1 (A), G10, G11, G14

**Technical Goal:** Every deliberate departure from a rule is written down where the next audit will read it, and AGENTS.md and README match the repository.

**Subtasks:**

- [ ] Decision 1 A: a comment at `reports/web.py` `Jobs.execute` and at the `convert_errors` middleware saying they are the server's error boundary (a failed job would otherwise hang its progress page; an unexpected error would reach the client unredacted), citing review-2 Decision 1; the same in a line of AGENTS.md
- [ ] G10: lower-case the local variables of `fetch/cache.py` `tables()`; `bin/record-fixtures.py:306` logs its failure with `loguru.logger.error` (and drop the `T20` per-file ignore if nothing else in the file prints); in AGENTS.md's Tests section, list the deliberate test-layout exceptions (property tests, browser tests, live tests, `test_layering.py`, `test_package.py`, the bin-script tests, the fixtures of the fake GitHub) beside the `test_fetcher.py` note
- [ ] G11: a line in AGENTS.md that logins and repository names are logged by design (public identifiers the user typed; the only sink is local stderr)
- [ ] G14: link `.claude/skills/project-setup` to `.agents/claude/skills/project-setup` (and any other shared skill without a link); AGENTS.md says the project's `claude/` directory is created with the first project rule; AGENTS.md's on-commit list names the end-of-file and trailing-whitespace hooks; `README.md:9` says Python 3.14.7 or later 3.14

**Acceptance Criteria:**

- [ ] Every shared skill under `.agents/claude/skills/` has a link in `.claude/skills/`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `bin/audit-check.sh --path src/wambatic --path bin` exits 0
- [ ] `pytest src/tests/fetch/test_cache.py src/tests/test_record_fixtures.py src/tests/reports/test_web.py` passes

**Notes:**

- Depends on Task 8

---

## Task 10: Close the test gaps

**Status:** todo
**Priority:** low
**Complexity:** small
**Source Reference:** G12 (T1, T2, T3)

**Technical Goal:** No unused helper remains, the six small pure functions have property tests, and the audit check script is tested against the real checker.

**Subtasks:**

- [ ] T1: delete `fetch/cache.py` `optional_to_text` (nothing calls it)
- [ ] T2: hypothesis tests for `fetch/cache.py` `to_text`/`from_text` (round-trip, and text order is time order), `identity_differences`, `fetch/client.py` `limit_kind`, `reports/terminal.py` `format_cell`, `stats/buckets.py` `partial_buckets`, and `cli.py` `check_report` over flag and settings combinations; each with `@settings(max_examples=20, deadline=10000)`
- [ ] T3: one test that runs `bin/audit-check.sh` on a tiny fixture project under `tmp_path` (one clean module and one with a known hit), checking exit 0 and exit 1 with the hit printed; mark it `slow` if it takes more than 10 seconds

**Acceptance Criteria:**

- [ ] Each function T2 names appears in a hypothesis test

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/fetch/test_cache.py src/tests/fetch/test_client.py src/tests/reports/test_terminal.py src/tests/stats/test_buckets.py src/tests/test_cli.py src/tests/test_audit_check.py` passes

**Notes:**

- Depends on Task 9

---

## Task 11: Close review-2, tasks-1 and the TODO item

**Status:** todo
**Priority:** medium
**Complexity:** small
**Source Reference:** G13 (no change), tasks-1 Task 15, `TODO.md` item, audit skill step 8b

**Technical Goal:** The audit gates pass on the whole tree, every open record is closed, and the branch is ready to merge.

**Subtasks:**

- [ ] G13: no change (dev tools declared for `uv sync`, as review-1 F18 chose)
- [ ] Run `bin/audit-check.sh`: it must exit 0. Then in `tasks-1.md` Task 15 replace the old note on `bin/audit-check.sh` with a dated line that it exits 0 against agents `108559d`, and set Task 15's `**Status:**` to `done`
- [ ] Move the `TODO.md` item "The auditme checker's 2026-10-31 rules report hits here" to a new `DONE.md`: append its heading and body unchanged, then `Done: 2026-MM-DD - fixed by review-2 G2 (tasks-2 Task 1); the UNITS hit was already fixed by tasks-1 Task 7. Source: agents/audit-reviews/review-2.md; tasks: agents/tasks/audit-reviews/tasks-2.md.` with the real date; `TODO.md` keeps its title and preamble
- [ ] `agents/audit-reviews/summary.md`: move review-2's resolved findings to Recently resolved, and record the checker version the gates now run
- [ ] Set `**Status:**` of every spec this list changed back to `implemented` where it was `proposed`

**Acceptance Criteria:**

- [ ] `bin/audit-check.sh` exits 0
- [ ] `git log --diff-filter=A --format=%H -- agents/tasks/audit-reviews/tasks-2.md` gives the baseline commit, and `git show <that commit>:TODO.md > /tmp/todo-before.md && python3 .agents/claude/skills/todo-review/verify_bodies.py /tmp/todo-before.md TODO.md DONE.md` exits 0

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] `pre-commit run --all-files` passes
- [ ] `pre-commit run --hook-stage pre-push --all-files` passes
- [ ] `pytest -m 'not slow and not live and not browser'` passes: the list changes every source package, so every test module imports a changed module (the importer set, not a routine full run)
- [ ] `pytest -m browser` passes
- [ ] The `verify_bodies.py` check above exits 0

**Notes:**

- Depends on Task 10
- Do not push; the operator merges the branch
