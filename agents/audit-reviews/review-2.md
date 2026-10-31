# Audit Review 2

**Date:** 2026-10-31
**Scope:** full (`agents/specs/`, `src/wambatic/`, `src/tests/`, `bin/`, `AGENTS.md`, `README.md`; there is no `docs/`), on branch `worktree-audit-reviews-tasks-1` at `381366e` (PR #39)
**Script output:** `/tmp/audit-wambatic.jsonl` (90 hits, 74 accepted, 16 unaccepted)
**Script version:** `4e66ac0cd1e99ce2a8457ebf58915f45c56af2e4191b064a8eb6bc34f85edbc1` (agents `108559d`)
**Convergence note:** script extended since review-1 (digest `4d7de71f...` then): the two requests shipped in agents `c437b07` add `raises-section-drift` and refine `mutable-module-level-exported` for builtin constructor calls. The 16 unaccepted hits are all `raises-section-drift`, the expected catch-up of the new check. Phase B also reports some hits in code unchanged since review-1 (the two-way `Literal` splits of A11, more log lines under Sec5, the A9 names); those are a different reading of the same predicates by a different reviewer, not new defects.
**Review page:** https://claude.ai/artifact/BHMfRN44sus5PpLUYVqXVa

## What is being reviewed and how

This is the second `/auditme` audit of wambatic, run on 2026-10-31 against the branch that ran review-1's task list ([tasks-1.md](../tasks/audit-reviews/tasks-1.md), Tasks 1-14 done, Task 15 open for this review), before it merges. As in review-1, a script swept every Python file under `src/` and `bin/`, ten reviewers applied every Phase B question (A1-A25, S1-S4, P1-P3, Sec1-Sec5, T1-T3, D1-D3, Doc1-Doc5) and the spec review, and one re-checked each review-1 finding against the code. For each **item** below, approve it for the fix list or flag it with a comment; for each **decision**, pick an option.

## Summary

Review-1's findings are resolved except one path left over from F2 and F5 (a malformed JSON body on a 200 response still escapes as a `ValueError`), two small leftovers of F8, and F19's spec sizes. The script reports 16 unaccepted hits, all `raises-section-drift` from the newly shipped check, and Phase B found hits on 27 of the 48 questions, nearly all low severity. The two medium findings are the JSON leftover (G1) and the fetch spec still describing the errors review-1 removed (G20).

## Automatic checks

| Check | Result |
|---|---|
| `requests.md` `## Open` empty at audit start | pass (both review-14 requests shipped in agents `c437b07`, checked 17:07 UTC) |
| `checks/audit.py` run, JSONL saved | pass: 90 hits, 74 accepted |
| Every unaccepted hit listed below | pass: 16 of 16 (generated from the JSONL) |
| Every Phase B question run with per-question fan-out | pass: 48 questions, ten reviewers, no `--category` |
| Every reviewer returned a hit list or "no hits" | pass |
| Earlier `summary.md` findings re-verified | pass: F1-F19 and M1, see below |
| Incomplete audit task files re-verified | pass: tasks-1 Task 15 is the only one open (this review is one of its subtasks) |
| No check added to the checker during the audit | pass (the checker changed before the audit started) |
| No Phase B predicate widened during the audit | pass |
| `uv lock --check` | pass |
| PR #39 CI (`check`, `browser`, `live`, `audit`, CodeQL) | pass, 2026-10-31 |
| `pytest -m browser` | pass: 8 passed, 2026-10-31 |

Accepted hits, by rule (each carries a scoped `accept[...]` marker with its reason): `non-alphabetical-literal` 47, `except-interpolation` 17, `non-alphabetical-dict-keys` 2, `silent-broad-except` 2, `passthrough-shim` 4, `filesystem-op-without-envelope` 1, `subprocess-without-memoisation` 1.

## Mechanical findings (from checks/audit.py)

### Rule: raises-section-drift

- **Severity:** low
- **Instance count:** 16
- **Locations:**
  - `src/wambatic/fetch/cache.py:541` - write_rows: Raises: omits CacheError, declared by wambatic.fetch.cache.Cache.locked: `def write_rows[T: Record](`
  - `src/wambatic/fetch/client.py:165` - graphql_dated: Raises: omits AuthError, declared by wambatic.fetch.client.GitHubClient.request: `async def graphql_dated(`
  - `src/wambatic/fetch/client.py:165` - graphql_dated: Raises: omits FetchError, declared by wambatic.fetch.client.GitHubClient.request: `async def graphql_dated(`
  - `src/wambatic/fetch/client.py:165` - graphql_dated: Raises: omits RateLimitError, declared by wambatic.fetch.client.GitHubClient.request: `async def graphql_dated(`
  - `src/wambatic/fetch/client.py:190` - rest_get: Raises: omits AuthError, declared by wambatic.fetch.client.GitHubClient.request: `async def rest_get(`
  - `src/wambatic/fetch/client.py:190` - rest_get: Raises: omits FetchError, declared by wambatic.fetch.client.GitHubClient.request: `async def rest_get(`
  - `src/wambatic/fetch/client.py:190` - rest_get: Raises: omits NotFoundError, declared by wambatic.fetch.client.GitHubClient.request: `async def rest_get(`
  - `src/wambatic/fetch/client.py:190` - rest_get: Raises: omits RateLimitError, declared by wambatic.fetch.client.GitHubClient.request: `async def rest_get(`
  - `src/wambatic/reports/service.py:238` - sync_and_compute: Raises: omits InvalidRequestError, declared by wambatic.stats.engine.compute_all: `async def sync_and_compute(`
  - `src/wambatic/reports/web.py:239` - parse_query: Raises: omits SettingsError, declared by wambatic.reports.service.make_request: `def parse_query(`
  - `src/wambatic/reports/web.py:239` - parse_query: Raises: omits UnknownGroupError, declared by wambatic.stats.engine.resources_for: `def parse_query(`
  - `src/wambatic/stats/buckets.py:89` - bucket_range: Raises: omits InvalidRequestError, declared by wambatic.stats.buckets.bucket_start: `def bucket_range(`
  - `src/wambatic/stats/engine.py:235` - aggregate: Raises: omits InvalidRequestError, declared by wambatic.stats.buckets.bucket_start: `def aggregate(`
  - `src/wambatic/stats/engine.py:360` - compute_all: Raises: omits EmptySubjectError, declared by wambatic.stats.engine.aggregate: `async def compute_all(`
  - `src/wambatic/stats/engine.py:360` - compute_all: Raises: omits InvalidRangeError, declared by wambatic.stats.engine.aggregate: `async def compute_all(`
  - `src/wambatic/stats/engine.py:360` - compute_all: Raises: omits UnknownGroupError, declared by wambatic.stats.engine.read_records: `async def compute_all(`
- **Recommendation:** make each `Raises:` section list exactly the domain errors that reach the caller: add the ones a same-package callee raises and this function does not catch, and drop the ones its own `except` always catches.

## Phase B per-question results

### A1: External call envelope
- Hits:
  - `src/wambatic/fetch/client.py:254` - a `ValueError` from `raw.json()` on an OK response is re-raised at 257; the only caller, `request` (line 333), catches only aiohttp errors and `TimeoutError`, so the `ValueError` escapes untranslated
  - `src/wambatic/version.py:10` - `importlib.metadata.version` reads package metadata from disk; only `PackageNotFoundError` is handled (to a fallback value), so `OSError`/`UnicodeDecodeError` escape at import
  - `bin/audit-check.py:97` - `subprocess.run` is in no `try`, so an `OSError` (for example `python3` missing) escapes `main`
- Files inspected: 35; 24 had no external-IO call

### A2: Except tuple coverage
- Hits:
  - `src/wambatic/version.py:11` - `except importlib.metadata.PackageNotFoundError` around a body that reads and decodes metadata from disk; `OSError` and `UnicodeDecodeError` missing
  - `src/wambatic/fetch/client.py:255` - `except ValueError` around a JSON parse (`raw.json`); the locked set's `OSError` is missing, though the body does no disk I/O
- Files inspected: 35; 28 had no `try`/`except` or envelope over disk or JSON parsing

### A3: Domain-error layering
- Hits:
  - `src/wambatic/fetch/client.py:257` - a bare `raise` re-raises the stdlib `ValueError` from `raw.json`, in a package that defines `FetchError`
  - `bin/record-fixtures.py:131` - `raise RuntimeError` (GraphQL error), though the script defines `RecordingError`
  - `bin/record-fixtures.py:140` - `raise RuntimeError` (not an object), though the script defines `RecordingError`
  - `bin/record-fixtures.py:150` - `raise RuntimeError` (unexpected compare commit), though the script defines `RecordingError`
- Files inspected: 35; 20 had no `raise`

### A4: Docstring `Raises` accuracy
- Hits:
  - `src/wambatic/fetch/client.py:165` - `graphql_dated` declares `GraphQLError`, `NotFoundError`; `self.request` also lets `AuthError`, `RateLimitError`, `FetchError` reach the caller undeclared
  - `src/wambatic/fetch/client.py:190` - `rest_get` declares only `StatsPendingError`; `self.request` adds `AuthError`, `NotFoundError`, `RateLimitError`, `FetchError`
  - `src/wambatic/fetch/cache.py:541` - `write_rows` declares only `InvalidRequestError`; `self.locked()` raises `CacheError`
  - `src/wambatic/fetch/base.py:595` - `owner_kind` declares only `NotFoundError`; `self.client.rest_get` adds `StatsPendingError`, `AuthError`, `RateLimitError`, `FetchError`
  - `src/wambatic/fetch/base.py:633` - `list_repos` declares only `NotFoundError`; `client.graphql` and `parse_repo` add `GraphQLError`, `AuthError`, `RateLimitError`, `FetchError`
  - `src/wambatic/fetch/base.py:725` - `provenance` declares only `InvalidRequestError`; `self.db(self.cache.identity / sync_state / ...)` raises `CacheError`
  - `src/wambatic/fetch/base.py:822` - `line_counts` declares only `GraphQLError`; `client.graphql` adds `NotFoundError`, `AuthError`, `RateLimitError`, `FetchError`
  - `src/wambatic/reports/service.py:238` - `sync_and_compute` declares only `EmptySubjectError`; from `sync_target`, `AuthError`, `NotFoundError`, `UsageError`, `UnknownGroupError`, `CacheError` and other `FetchError`s reach the caller, and from `compute_all`, `InvalidRequestError` and `InvalidRangeError`
  - `src/wambatic/stats/engine.py:171` - `read_records`: `CacheError` reaches the caller through `fetcher.repos` and `fetcher.provenance`, undeclared
  - `src/wambatic/stats/engine.py:338` - `compute`: `CacheError` reaches the caller through `read_records`, undeclared
  - `src/wambatic/stats/engine.py:360` - `compute_all` declares only `InvalidRequestError`; `read_records` and `aggregate` raise `UnknownGroupError`, `InvalidRangeError`, `EmptySubjectError`, and `CacheError` comes through the fetcher
  - `src/wambatic/reports/web.py:239` - `parse_query` declares only `UsageError`; `make_request` raises `SettingsError` and `resources_for` raises `UnknownGroupError`
  - `src/wambatic/reports/web.py:381` - `results_or_job` declares only `JobError`; the `compute` closure (through `sync_and_compute`) raises `EmptySubjectError` and others, and the `stale` closure (through `provenance`) raises `CacheError`
  - `src/wambatic/reports/web.py:566` - `serve` declares `UsageError`, `ServeError`; `Cache.open` raises `CacheError`, `CacheVersionError`, and `cache.close` raises `CacheError`
- Files inspected: 35; 23 had no function with a `Raises:` section

### A16: CLI entry envelope
- Hits: no hits. Entry points: `run_report` (takes the cappa `Report`) and `run_cache` (takes the cappa `CacheCommand`); neither contains a `raise`, and `run_report` has `try`/`finally` only.
- Files inspected: 1 (`src/wambatic/cli.py`)

### A19: Wrong logger level for broad-except
- Hits:
  - `src/wambatic/fetch/cache.py:423` - `except BaseException` closes the connection and re-raises, with no `logger.exception`
  - `src/wambatic/reports/html.py:684` - `except BaseException` unlinks the temporary file and re-raises, with no `logger.exception`
  - `src/wambatic/reports/web.py:150` - `except Exception` in `Jobs.execute` degrades gracefully (job marked failed); `logger.exception` runs only for status 500 (through `error_response`)
  - `src/wambatic/reports/web.py:420` - `except Exception` in the `convert_errors` middleware degrades gracefully into an HTTP error reply; `logger.exception` only for status 500
- Files inspected: 35; 31 had no `except Exception`/`except BaseException` (`cli.py:397` has one and passes)

### A22: Fall-through after partial handling
- Hits: no hits
- Files inspected: 35; 23 had no `if`/`else` chain mixing `raise` and `return`

### A5: Two sources of truth
- Hits:
  - `src/wambatic/stats/base.py:52` - `StatsRequest.tz` and `StatsRequest.settings.timezone` (line 53) should always agree, but nothing enforces it (no `__post_init__` check); `tz` wins silently, because `stats/engine.py:266` reads only `request.tz` and `reports/base.py:61` drops `timezone` from the JSON. The rule is stated only at construction (`reports/service.py:103-104`), not on the class.
- Files inspected: 34; 27 had no matching construct

### A6: Stage method dual-path
- Hits: no hits
- Files inspected: 34; 29 had no matching construct (methods of `Recorder`, `Fetcher`, `GitHubClient`, `Cache`, `Jobs` and `SyncJob` checked)

### A7: Constructor purity
- Hits: no hits
- Files inspected: 34; 28 had no `__init__`

### A8: Late dataclass mutation
- Hits:
  - `src/wambatic/reports/web.py:122` - `SyncJob` built in `Jobs.start` and changed afterwards at `web.py:146`, `:148` (`phase`), `:151` (`status`, `error`), `:152` (`phase`), `:367` (`subject`)
  - `src/wambatic/reports/web.py:89` - `SyncProgress`, built by `default_factory` inside each `SyncJob`, changed afterwards at `src/wambatic/fetch/base.py:1349`, `:1350`, `:1374`, `:1378` (`repos_listed`, `repos_pending`, `rows_written`, `repos_done`)
  - `src/wambatic/stats/activity.py:89` - the `Tally` instances built at `:89`, `:103`, `:105`, `:107` are changed afterwards through `Tally.add` and directly at `:102` (`totals[index].logins.add(key)`)
- Files inspected: 34; 18 had no dataclass built inside a function

### A13: Same value to multiple structural slots
- Hits:
  - `src/wambatic/fetch/base.py:766` - in `new_state`, `now` goes to both `synced_at` and `full_synced_at` (`:767`, `full_synced_at or now`) whenever `full_synced_at` is None
  - `src/wambatic/reports/web.py:345` - `needs_sync(provenance, resources, settings.fetch, False, False, clock())` passes `False` by position to both `full_refresh` and `no_fetch`
  - `src/wambatic/reports/web.py:358` - `sync_and_compute(..., full_refresh=False, no_fetch=False, ...)` (`:358-359`)
  - `src/wambatic/reports/web.py:372` - `sync_target(..., full_refresh=False, no_fetch=False, ...)` (`:372-373`)
- Files inspected: 34; 10 had no call with several distinguishable slots

### A15: Duplicate constructor / serialisation logic
- Hits:
  - `src/wambatic/fetch/base.py:487` - `Commit` built with all its fields at `:487` (`parse_history_node`) and again at `:861` (`line_counts`), with no shared helper
  - `src/wambatic/fetch/client.py:214` - `RestResponse` built twice in `rest_get` (`:214`, `:221`) with the same field set and `date=header_date(response)`
  - `src/wambatic/stats/buckets.py:86` - `Bucket(start, label(start, granularity))` written out in full at `:86` and `:105`
  - `src/wambatic/reports/rows.py:244` - `PeriodTable(title, HEADERS, METRICS, rows, total)` built at `:244`, `:260`, `:277`, `:301`, `:339`, with the `period_row` row-building repeated at each
  - `src/wambatic/stats/flow.py:94` - `Series(name, unit, dict(zip(buckets, counts[name], strict=True)))` assembled the same way at `flow.py:94`, `src/wambatic/stats/popularity.py:123`, `src/wambatic/stats/delivery.py:213`/`:228`; `Series(name, unit, points)` also at `flow.py:104` and `src/wambatic/stats/activity.py:72`
- Files inspected: 34; 23 had no class built from 2 or more sites

### A23: Discarded multi-return
- Hits:
  - `src/wambatic/fetch/client.py:163` - `graphql` returns `(await self.graphql_dated(...))[0]`, dropping the response `Date` (GitHub's clock, used for watermarks) without naming it
  - `bin/record-fixtures.py:135` - `rest` returns `self.send(...)[0]`, dropping the response headers (ETag, rate limit) without naming them
- Files inspected: 34; 18 had no call to a function returning a tuple or dataclass

### A9: Pure-named function side effects
- Hits:
  - `src/wambatic/fetch/auth.py:7` - `resolve_token` reads `os.environ` and runs the `gh auth token` subprocess (line 18)
  - `src/wambatic/fetch/cache.py:443` - `check_identity` writes rows to `meta` (lines 448, 457) and calls `datetime.datetime.now` (line 459)
  - `src/wambatic/stats/engine.py:360` - `compute_all` reads the cache through `read_records` (line 384), and its default clock calls `datetime.datetime.now` (line 385)
  - `src/wambatic/reports/service.py:87` - `resolve_tz` calls `zoneinfo.ZoneInfo`, which reads the tzdata file from disk (it catches `OSError`, lines 89-90)
  - `src/wambatic/cli.py:204` - `build_request` reaches the tzdata read through `make_request` -> `resolve_tz` (`service.py:111`)
  - `src/wambatic/reports/web.py:239` - `parse_query` reaches the same tzdata read through `make_request` (line 273)
  - `src/wambatic/reports/web.py:424` - `check_host_header` awaits `call_next(request)` (line 436), which runs the downstream handler with its cache and network I/O
- Files inspected: 35; 20 had no function with a pure-name prefix

### A10: Predicate semantics
- Hits: no hits
- Files inspected: 35; 31 had no `is_`/`has_`/`should_` predicate (checked: `flow.has_event_in_range`, `delivery.has_event_in_range`, `web.is_loopback`, `rows.PeriodTable.has_partial`, `rows.has_activity`/`has_flow`/`has_delivery`/`has_popularity`/`has_dora`)

### A11: Exhaustion via assert_never
- Hits:
  - `src/wambatic/cli.py:271` - an `if as_html` / `elif == 'json'` / `else` chain over `report.format` (the `Format` Literal); the bare `else` stands for `'terminal'`, with no `assert_never`
  - `src/wambatic/cli.py:320` - a two-way split on `command.action == 'info'` over `Literal['clear', 'info']`; the fall-through stands for `'clear'`
  - `src/wambatic/fetch/client.py:293` - a two-way split on `on_rate_limit == 'fail'` over `Literal['wait', 'fail']`; the fall-through stands for `'wait'` (the `raise` is the real `'fail'` behaviour, not an unreachable branch)
  - `src/wambatic/stats/buckets.py:70` - in `label()`, `match granularity` ends in `case _: return 'total'`, standing for `Granularity.TOTAL`
  - `src/wambatic/reports/figures.py:318` - in `trace_json`, the split on `trace.kind == 'bar'` over `Literal['bar', 'line']`; the fall-through stands for `'line'`
- No chain in scope ends in `raise <SomeError>(...)` in place of `assert_never`. Already exhaustive with `assert_never` (not hits): `fetch/base.py:1371`, `stats/buckets.py:33`, `:56`. Two-way splits whose `else` covers the remaining members generically, not counted: `cli.py:258`, `cache.py:497`, `base.py:639`, `:715`, `engine.py:278`, `rows.py:219`, `terminal.py:78`, `html.py:196`, `web.py:99`.
- Files inspected: 35; 23 had no chain over a Literal or enum

### A12: assert misuse
- Hits: no hits
- Files inspected: 35; none has an `assert`

### A17: Public-surface drift
- Hits:
  - `src/wambatic/__init__.py:8` - `Settings` has no named consumer outside the package; `src/tests/test_package.py:35-37` reaches it only through `getattr` over `__all__`
  - `src/wambatic/__init__.py:13` - `load_settings`, the same
  - `src/wambatic/__init__.py:7,9,10,11,12` - `Fetcher`, `StatsRequest`, `StatsResult`, `Subject`, `compute`: the only consumers outside the package are the identity asserts in `src/tests/test_package.py:46-50`; every working consumer imports them from their owning modules (`wambatic.fetch.base`, `wambatic.stats.base`, `wambatic.stats.engine`)
  - `src/tests/reports/test_terminal.py:322` - reads `wambatic.reports.terminal.TOP_CONTRIBUTORS_SHOWN` through the module `__getattr__` shim at `src/wambatic/reports/terminal.py:14`, bypassing its owning module `wambatic.reports.rows`
- Files inspected: 4 `__init__.py`; `src/wambatic/__init__.py` has `__all__`, the `fetch`, `stats` and `reports` ones are empty (trimmed under review-1 Decision 4). Consumers searched across `src/wambatic`, `src/tests`, `bin` by `wambatic.<name>`, `from wambatic ... import`, `importlib.import_module` and `sys.modules`

### A14: Repeated computation per request
- Hits:
  - `src/wambatic/fetch/base.py:742` - `Fetcher.repos(subject)` (the subject's cached repo list) runs 3 times in one report flow with nothing changed in between: `reports/service.py:220`, `stats/engine.py:197`, `stats/engine.py:219` (two of them through `provenance()`); web `/report` and `/api/stats` follow the same path (`reports/web.py:343`, `engine.py:197`, `engine.py:219`)
  - `src/wambatic/fetch/base.py:1272` - for a popularity request with no sync, each repo's `sync_state(repo, 'star_events')` is read 3 times: `provenance` at `base.py:746` (from `service.py:220` or `web.py:343`), `stars_hidden` (from `engine.py:145`), `provenance` again (from `engine.py:219`)
- Files inspected: 35; 30 had no matching construct

### A18: Hot-path setup
- Hits: no hits
- Files inspected: 35; 35 had no matching construct (no `on_*` callback methods)

### A20: Mutable module-level singleton
- Hits: no hits
- Files inspected: 35; 29 had no matching construct. The mutable containers (`settings.py:62 DURATION_UNITS`, `fetch/base.py:280 PROBES`, `reports/html.py:38 JSON_ESCAPES`, `reports/figures.py:21 PERCENT_RANGE`, `reports/service.py:26 PREFIXES`, `reports/rows.py:51 DELIVERY_HEADERS`) are read by none of the three forms outside their own module, in `src/wambatic`, `src/tests` or `bin`

### A21: Lazy init race
- Hits: no hits
- Files inspected: 35; 35 had no matching construct (the lazy inits at `fetch/cache.py:300` and `reports/html.py:140` use `functools.cache`, which is not this pattern)

### A24: Identity of subprocess / shell-out calls
- Hits: no hits
- Files inspected: 35; 32 had no matching construct (`fetch/auth.py:18` runs at most once per request: `service.py:208` and `:226` exclude each other through `online is None`; `bin/audit-check.py:97` and `bin/record-fixtures.py:279` each run once)

### A25: Shallow immutable wrapper
- Hits: no hits
- Files inspected: 35; 23 had no matching construct (every wrapped member is a str, int, type, function, `frozenset` or frozen dataclass; `PALETTE` holds `Theme`, which is `frozen=True`)

### P1: O(n^2) on real-size inputs
- Hits: no hits
- Files inspected: 35; 30 had no matching construct (the nested loops in `stats/activity.py`, `stats/delivery.py`, `fetch/base.py`, `reports/figures.py` and `reports/terminal.py` multiply two different collections, use bisect, or run a constant-size outer loop)

### P2: Blocking I/O in hot paths
- Hits:
  - `src/wambatic/reports/web.py:325` - `page()` calls `reports.html.read_template` (a `functools.cache`d package-file read) on the event loop inside async handlers `form` (464), `error_reply` (333) and `report` (479, 484); the first request for each template does a synchronous disk read in the handler
- Files inspected: 35; 34 had no matching construct

### P3: Repeated expensive computation per request
- Hits:
  - `src/wambatic/reports/html.py:559` - `sections_html` builds `activity_table(total)` (559), `flow_table(total)` (575), `delivery_table(total)` (590), `dora_table(total)` (591) and `popularity_table(total)` (603) only to test for None, each re-deriving `rows.total_series(total)`, which `tiles_html` (449) already derived
  - `src/wambatic/reports/html.py:500` - `popularity_now(total)` is derived twice (500, 303), and `languages_rows(total)` twice (505, 326), in one `html_document`
  - `src/wambatic/reports/terminal.py:346` - `render_terminal` derives `total_series(result)` here, then again through `activity_table` (347), `trend_lines` (138), `flow_table`/`flow_times_table` (253-254), `delivery_table`/`dora_table` (266-267) and `popularity_table` (288)
  - `src/wambatic/fetch/cache.py:211` - `record_values` re-derives `column_names(type(record))` (`dataclasses.fields`) for every record, called per row from `Table.values` (254) in `write_rows` (574), though `Table.columns` already holds the names
  - `src/wambatic/stats/engine.py:283` - each commit's local date is derived 3 times: `read_commits` (65), the range filter in `aggregate` (283), and `stats/activity.py:95`; the filter at 283 runs again for each of the five HTML periods
  - `src/wambatic/fetch/base.py:742` - the repeated `Fetcher.repos` read, as in A14
- Files inspected: 35; 30 had no matching construct

### S1: Type annotations on every signature
- Hits: no hits
- src/tests count: 0 missing parameter annotations, 0 missing return annotations, 0 modules affected, 60 modules fully annotated (AGENTS.md records no test-annotation exemption)
- Files inspected: 35

### S2: PascalCase / UPPER_SNAKE / lower_snake
- Hits:
  - `src/wambatic/fetch/cache.py:303` - the local variables in `tables()` (`COMMITS`, `PULL_REQUESTS`, `ISSUES`, `RELEASES`, `WORKFLOW_RUNS`, `STAR_EVENTS`, `FORKS`, lines 303-351) are UPPER_SNAKE; the convention for function-local variables is snake_case
- Files inspected: 95

### S3: TYPE_CHECKING block placement
- Hits: no hits
- Files inspected: 95

### S4: Project-specific rule files
- Hits:
  - testing.md layout, test file mirrors no source module: `src/tests/fetch/test_live.py:1`, `src/tests/fetch/test_parse_properties.py:1`, `src/tests/fetch/test_server.py:1` (tests the fixture `fixtures/fetch/server.py`), `src/tests/reports/test_properties.py:1`, `src/tests/reports/test_html_browser.py:1`, `src/tests/reports/test_web_browser.py:1`, `src/tests/stats/test_fixtures.py:1`, `src/tests/stats/test_properties.py:1`, `src/tests/test_layering.py:1`, `src/tests/test_package.py:1`, `src/tests/test_audit_check.py:1` (tests `bin/audit-check.py`), `src/tests/test_record_fixtures.py:1` (tests `bin/record-fixtures.py`)
  - `src/wambatic/__main__.py:1` - testing.md layout: no mirrored test file
  - testing.md, fixture file name mirrors no source module: `src/tests/fixtures/constants.py:1`, `src/tests/fixtures/thaw.py:1`, `src/tests/fixtures/audit_check.py:1`, `src/tests/fixtures/fetch/constants.py:1`, `src/tests/fixtures/fetch/recorded.py:1`, `src/tests/fixtures/fetch/responses.py:1`, `src/tests/fixtures/fetch/server.py:1`, `src/tests/fixtures/fetch/upstream.py:1`
  - testing.md "load fixtures in src/tests/conftest.py", fixture defined in a test module: `src/tests/test_audit_check.py:112` (`errors`), `src/tests/test_record_fixtures.py:92` (`upstream`), `src/tests/test_record_fixtures.py:99` (`formatted`), `src/tests/test_cli.py:890` (`clock_after_fixtures`), `src/tests/reports/test_web_browser.py:41` (`running_server`), `src/tests/reports/test_html_browser.py:31` (`open_report`)
  - testing.md, fixture in a second, package-level conftest: `src/tests/reports/conftest.py:14` (`fresh_templates`), `src/tests/reports/conftest.py:47` (`chromium`)
  - `bin/record-fixtures.py:306` - coding-standards.md Logging: the failure message is written with `print(..., file=sys.stderr)`, not `loguru.logger.error`; `pyproject.toml` silences ruff's T20 for this file, but AGENTS.md records no reason, and only machine-readable stdout may use `print`
- Files inspected: 95

### Sec1: Secrets in source
- Hits: no hits. Every token-shaped literal in `src/tests` is a made-up placeholder, checked without printing: they are lower-case dictionary words or contain words such as "fake" or "test" (`src/tests/test_cli.py:1123`, `src/tests/test_logs.py:65`, `src/tests/test_record_fixtures.py:20`, `src/tests/test_settings.py:234`, `src/tests/reports/test_web.py:417`). The recorded fixtures (`src/tests/fixtures/fetch/*`) hold no Authorization or bearer values. `.github/workflows/ci.yml` uses `secrets.AGENTS_DEPLOY_KEY` and `github.token` only through `env`. No key or env files are committed.
- Files inspected: 159

### Sec2: Input validation at system boundaries
- Hits: no hits
- Files inspected: 39

### Sec3: Command injection
- Hits: no hits. Every `subprocess.run` call takes an argument list without `shell=True` (`src/wambatic/fetch/auth.py:18`, `bin/audit-check.py:97`, `bin/record-fixtures.py:279`). No `${{ github.event.* }}` is interpolated into a `run:` step of `ci.yml`.
- Files inspected: 39

### Sec4: Path traversal
- Hits: no hits. Web template names are constants; `report_filename` cleans subject names (`src/wambatic/reports/html.py:33,92`); `--out` paths are the local user's own choice and are not joined to project paths.
- Files inspected: 39

### Sec5: PII in logs
- Hits:
  - `src/wambatic/reports/web.py:594` - the raw `serve` target (a GitHub login, traceable to a person) is logged at INFO
  - `src/wambatic/cli.py:387` - logs at ERROR the `NotFoundError` text that embeds the user-supplied login or repo (built at `src/wambatic/fetch/base.py:609`, `:644`, `:650`)
  - `src/wambatic/fetch/base.py:806` - INFO line includes `repo.name_with_owner` (owner login)
  - `src/wambatic/fetch/base.py:906` - INFO line includes `repo.name_with_owner`
  - `src/wambatic/fetch/base.py:1016` - INFO line includes `repo.name_with_owner`
  - `src/wambatic/fetch/base.py:1117` - WARNING line includes `repo.name_with_owner`
  - Common to all of them: the only log sink is local stderr (`src/wambatic/logs.py:17-19`), and the values are public GitHub identifiers, not free-form text.
- Files inspected: 39

### T1: Test coverage of branchy logic
- Hits:
  - `src/wambatic/fetch/cache.py:175` - `optional_to_text` (None-or-`to_text` branch): no test calls it, and nothing in `src/` or `bin/` calls it either; its definition is the only reference
- Files inspected: 95

### T2: Property-based tests
- Hits:
  - `src/wambatic/fetch/cache.py:164` - `to_text`/`from_text`: the docstring promises "one fixed width, so text order is time order", a pure datetime-to-text mapping; example tests only (naive refusal), no hypothesis test of round-trip or order
  - `src/wambatic/fetch/cache.py:153` - `identity_differences`: pure function over two str-to-str mappings; no hypothesis test (reached only through `check_identity` example tests)
  - `src/wambatic/fetch/client.py:270` - `limit_kind`: maps endpoint, status, headers and body to one of retry-after/primary/secondary/None; parametrised examples only
  - `src/wambatic/reports/terminal.py:47` - `format_cell`: maps metric (FLOW_TIMES / DELIVERY_UNITS / SIGNED_METRICS) and value to a cell; no hypothesis test (`format_number` and `sparkline` have one)
  - `src/wambatic/stats/buckets.py:110` - `partial_buckets`: pure function over date range, buckets and granularity; example tests only (`bucket_range` has a partition property test)
  - `src/wambatic/cli.py:180` - `check_report`: a domain of Report flag and settings combinations; a fixed parametrised list, no hypothesis test
- Files inspected: 30

### T3: Integration vs unit balance
- Hits:
  - `bin/audit-check.py:105` - `main`: every test replaces `run_checker` (`test_audit_check.py:103`, `:144`) with a canned `CompletedProcess`, so no test runs `main` against the real checker subprocess
- Orchestrators with end-to-end tests (not hits): `cli.main` through report, cache and serve (`test_cli.py:1077`, `:1112`, `:1623`, uvicorn stubbed); `reports/service.sync_and_compute` through a replay server (`test_cli.py:437`, `test_service.py:338`); `reports/web.make_app` through the app client and middleware (`test_web.py:395`, `:466`, `:605`); `Fetcher.sync` through ReplayServer (`test_fetcher.py`); `stats/engine.compute_all` (`test_engine.py`); `reports/html` (`test_html.py`, `test_html_browser.py`); `bin/record-fixtures.py` `main` against a fake urlopen upstream (`test_record_fixtures.py:255`)
- Files inspected: 18

### D1: Declared in pyproject
- Hits: no hits
- Items checked: 11 (third-party top-level modules imported across src/wambatic/, bin/ and src/tests/: aiohttp, cappa, fastapi, httpx, hypothesis, loguru, playwright, plotly, pytest, rich, uvicorn)

### D2: Unused declarations
- Hits:
  - `pyproject.toml:24` - `mypy` (dev) is imported by no file; run only as a command (pre-commit, CI)
  - `pyproject.toml:26` - `pre-commit` (dev) is imported by no file; run only as a command
  - `pyproject.toml:28` - `ruff` (dev) is imported by no file; run only as a command (pre-commit, CI, and `subprocess.run(['ruff', ...])` at `bin/record-fixtures.py:279`)
- Items checked: 14 (7 runtime, 7 dev)

### D3: Lockfile coherence
- Hits: no hits (`uv lock --check` exited 0, "Resolved 60 packages"; uv.lock unchanged)
- Items checked: 1

### Doc1: AGENTS.md project structure
- Hits:
  - `AGENTS.md:28` - says `.claude/skills/*` link to `.agents/claude/skills/*`, but `.agents/claude/skills/project-setup` has no link in `.claude/skills/`
  - `AGENTS.md:35` - names "this repository's own `claude/` directory" for project rules and skills, but there is no `claude/` directory at the repo root
- Items checked: 13

### Doc2: AGENTS.md tools and libraries list
- Hits:
  - `AGENTS.md:44` - lists the on-commit checks as "ruff ..., ruff format, mypy", but `.pre-commit-config.yaml` also runs `end-of-file-fixer` and `trailing-whitespace` (pre-commit-hooks v6.0.0)
- Items checked: 16

### Doc3: README.md and AGENTS.md consistent
- Hits: no hits
- Items checked: 4

### Doc5: User docs match implementation
- Hits:
  - `README.md:9` - says "You need Python 3.14", but `pyproject.toml:6` requires `>=3.14.7,<3.15`, so Python 3.14.0 to 3.14.6 cannot install it
- Items checked: 80 (every `report` and `serve` option row, every config setting and default, the exit statuses, target forms, the `--since` 2008 floor and `--until` tomorrow limit, token fallback and redaction, `WAMBATIC_CONFIG`, durations, HTML naming and atomic write, the web app's statuses and checks, `cache clear`/`cache info`, the language limits, the spec links)

### Doc4: Specs match implementation
- Hits:
  - `agents/specs/fetch-and-cache/spec.md:409` - says exhausted retries re-raise "the last exception ... unchanged" / `src/wambatic/fetch/client.py:334-339`, `:379-381` wraps `aiohttp.ClientConnectionError`/`TimeoutError` in `FetchError`, and `status_error` raises `FetchError` for 500/502/503/504
  - `agents/specs/fetch-and-cache/spec.md:410` - says any other non-2xx status "propagates as `aiohttp.ClientResponseError`" / `src/wambatic/fetch/client.py:343-347`, `:387-393` raises `FetchError("GitHub answered HTTP <status> to ...")`, and other `aiohttp.ClientError`s become `FetchError` too
  - `agents/specs/system/spec.md:48` - says `wambatic.cli` "builds the `Cache` and `Fetcher`, syncs, calls `compute`" / `src/wambatic/cli.py:254-268` only opens the `Cache`; `src/wambatic/reports/service.py:204-235`, `:267-271` builds the `Fetcher`, syncs and calls `compute_all`
  - `agents/specs/system/spec.md:88` - says the runtime libraries "are proposals pending a maintenance check before each `uv add`" / `pyproject.toml` declares every one already (the spec is `implemented`)
  - `agents/specs/stats/spec.md:19-28` - the module table omits `src/wambatic/stats/percentile.py` (`p90`, `summary`, `hours`, `minutes`, used by flow and delivery)
  - `agents/specs/stats/spec.md:215` - says the workflow file name is "`workflow_path` after its last `/`" / `src/wambatic/stats/delivery.py:58-60` first strips a trailing `@ref` (`path.partition('@')[0]`)
  - `agents/specs/stats/spec.md:257`, `:261` - type `tuple[str, ...]` with defaults written as lists / `src/wambatic/settings.py:27`, `:31` defaults are tuples
  - `agents/specs/reports/spec.md:221` - says `cache info` prints what "`Cache.inspect` (fetch spec) returns" / `src/wambatic/fetch/cache.py:785` the function is `inspect_cache`; `Cache` has no `inspect`
  - `agents/specs/reports/spec.md:234` - the error table maps "`OSError` writing `--out`, or binding `serve`'s port" to exit 1 / `src/wambatic/reports/html.py:158-160` raises `OutputError` and `src/wambatic/reports/web.py:308-311`, `:603-607` raises `ServeError` (exit 1 through `ReportsError`, not `OSError`)
  - `agents/specs/reports/spec.md:315` - says binding first "makes a busy port an ordinary `OSError` (exit 1, with the reason)" / `src/wambatic/reports/web.py` `listen` raises `ServeError("cannot listen on HOST:PORT: ...")`
  - `agents/specs/reports/spec.md:200-201` - `--since`/`--until` specified only as "exactly `YYYY-MM-DD`", `--groups` only as a list / `src/wambatic/reports/service.py:113-116`, `:125-133` also refuses `--since` before 2008-01-01, `--until` after tomorrow in the zone, and an empty `--groups`
  - `agents/specs/reports/spec.md:27` - the `service.py` row of the module table omits `redact_error` / `src/wambatic/reports/service.py:285` defines it, and the spec's own API block (line 124) lists it
- Claims checked per spec (approximate): system ~30, fetch-and-cache ~90, stats ~60, reports ~65

### Spec review (against specdev SKILL.md)
- Hits:
  - `agents/specs/system/spec.md` - no hits
  - `agents/specs/fetch-and-cache/spec.md` (475 lines) - Spec size (about 200 at most); it reads as several specs (transport and rate limits, cache schema, per-resource sync, testing)
  - `agents/specs/fetch-and-cache/spec.md:41-43` - version history: no 1.12 paragraph of its own; 1.12 is folded into the 1.13 paragraph
  - `agents/specs/fetch-and-cache/spec.md` - cross-referencing: no "Prerequisite" line, though `agents/specs/index.md:10` says each component spec lists its prerequisites
  - `agents/specs/stats/spec.md` (269 lines) - Spec size
  - `agents/specs/stats/spec.md:13` - version history: the 1.8 paragraph precedes 1.7 and carries 1.7 inside it
  - `agents/specs/stats/spec.md:19-28` - module paths: `percentile.py` missing
  - `agents/specs/stats/spec.md:257`, `:261` - Settings: default notation (list) does not match the declared type (tuple)
  - `agents/specs/reports/spec.md` (343 lines) - Spec size; the CLI, terminal, HTML and web app could each be split out
  - `agents/specs/reports/spec.md:221` - names: `Cache.inspect` does not exist
  - `agents/specs/reports/spec.md:13` - version history: the 1.11 paragraph precedes 1.10
  - `agents/specs/index.md:10` - cross-referencing: says each component spec lists prerequisites; fetch-and-cache does not
  - `agents/specs/implementation-order.md:3-5`, `:19-30` - consistency: dated 2026-10-30 at version 1.9, with no step covering the amendments after step 10 (fetch 1.9-1.13, stats 1.5-1.8, reports 1.8-1.11); steps 4 and 5 still name only `compute` (`:54`, `:59`)
  - Every relative link in the four specs, `index.md` and `implementation-order.md` resolves (checked with a script)

## Phase B findings (consolidated)

Each finding groups the hits of one question, or of one cause seen by several; the per-hit locations are in the per-question results above. G-numbers are this review's own.

### G1: A malformed JSON body on a 200 response escapes as a `ValueError`

- **Category:** A
- **Question:** A1, A2, A3 (review-1 F2 and F5, one path left)
- **Severity:** medium
- **Location:** `src/wambatic/fetch/client.py:254-257`
- **Description:** `raw.json()` failing on an OK response is re-raised with a bare `raise`; `request` catches only aiohttp errors and `TimeoutError`, so the CLI shows an "Unexpected error" traceback. Every other path review-1 named is translated.
- **Recommendation:** raise `FetchError("GitHub sent a response that is not JSON ...")` from the `ValueError`, with a test using a fake upstream that returns `200` with a non-JSON body.

### G2: `Raises:` sections leave out errors that reach the caller

- **Category:** A / script
- **Question:** A4, and the script's `raises-section-drift` (16 hits)
- **Severity:** low
- **Location:** the 16 script hits and the 14 A4 rows (the two lists overlap: `fetch/client.py:165`, `:190`, `fetch/cache.py:541`, `reports/service.py:238`, `reports/web.py:239`, `stats/engine.py:360`)
- **Description:** Task 4 added `Raises:` sections, and later tasks (the `CacheError` envelope, `compute_all`) added errors that now pass through undeclared.
- **Recommendation:** make each section list exactly the domain errors that reach its caller; the script then checks the same-package part on every push.

### G3: Small envelope gaps outside the fetch path

- **Category:** A
- **Question:** A1, A2, A3
- **Severity:** low
- **Location:** `src/wambatic/version.py:10-11`, `bin/audit-check.py:97`, `bin/record-fixtures.py:131`, `:140`, `:150`
- **Description:** `version.py` handles only `PackageNotFoundError`; `bin/audit-check.py` runs its checker with no `OSError` envelope; `bin/record-fixtures.py` still raises `RuntimeError` though it now defines `RecordingError`.
- **Recommendation:** catch `OSError`/`UnicodeDecodeError` in `version.py` with the same fallback; translate the checker's `OSError` into the script's exit 2; raise `RecordingError` in the three places.

### G4: Two sources of truth for the timezone, not enforced on the class

- **Category:** A
- **Question:** A5 (review-1 F6, one pair left)
- **Severity:** low
- **Location:** `src/wambatic/stats/base.py:52-53`
- **Description:** `make_request` now derives `tz` from settings, but `StatsRequest` itself still lets `tz` and `settings.timezone` disagree.
- **Recommendation:** a `__post_init__` check that raises the stats `InvalidRequestError` when `str(tz)` differs from `settings.timezone`, or drop `timezone` from `StatsSettings` for the request.

### G5: Remaining naming, exhaustiveness and slot findings

- **Category:** A
- **Question:** A9, A11, A13
- **Severity:** low
- **Location:** A9: `fetch/auth.py:7`, `fetch/cache.py:443`, `stats/engine.py:360`, `reports/service.py:87`, `cli.py:204`, `reports/web.py:239`, `:424`; A11: `cli.py:271`, `:320`, `fetch/client.py:293`, `stats/buckets.py:70`, `reports/figures.py:318`; A13: `fetch/base.py:766`, `reports/web.py:345`, `:358`, `:372`
- **Description:** Functions with pure-sounding prefixes that do I/O; two-way and `else` splits over a `Literal` or enum with no `assert_never`; the same `False` passed by position to `full_refresh` and `no_fetch`.
- **Recommendation:** A11: end each with `typing.assert_never`. A13: pass the two flags by keyword in `needs_sync`, and name the `now` fallback in `new_state`. A9: rename where the I/O is the point (`check_identity` to `record_identity`, `resolve_token` to `fetch_token`), and leave the tz lookups, which are library reads of package data.

### G6: Repeated reads and derivations left after the read-once change

- **Category:** A / P
- **Question:** A14, P2, P3 (review-1 F8 leftovers)
- **Severity:** low
- **Location:** `fetch/base.py:742` (repos read 3 times), `:1272` (star sync state read 3 times), `reports/html.py:559-603`, `:500`/`:303`, `:505`/`:326`, `reports/terminal.py:346`, `fetch/cache.py:211`, `stats/engine.py:283`, `reports/web.py:325`
- **Description:** The cache is read once per report, but `provenance` and `stars_hidden` re-read the repo list and sync state, the HTML sections still build tables only to test for `None`, and a few derivations repeat per row or per period.
- **Recommendation:** pass the repos and states `read_records` already has into `provenance`; reuse the built tables; compute `column_names` once per `Table`; read templates once at app start-up.

### G7: Construction and return-value leftovers

- **Category:** A
- **Question:** A8, A15, A23
- **Severity:** low
- **Location:** A8: `reports/web.py:89`, `:122`, `stats/activity.py:89` (deliberate, commented in Task 8); A15: `fetch/base.py:487`/`:861`, `fetch/client.py:214`/`:221`, `stats/buckets.py:86`/`:105`, `reports/rows.py:244-339`, the `Series` sites; A23: `fetch/client.py:163`, `bin/record-fixtures.py:135`
- **Description:** A few record types are still assembled at two or more sites, and two calls drop the second element of a returned tuple without naming it.
- **Recommendation:** a `make_series` helper and a `period_table` helper; name the dropped values (`data, _date = ...`). A8 needs no change.

### G8: Broad handlers that degrade gracefully

- **Category:** A
- **Question:** A19
- **Severity:** low
- **Location:** `fetch/cache.py:423`, `reports/html.py:684`, `reports/web.py:150`, `:420`
- **Description:** The two `except BaseException` handlers clean up and re-raise, which is the right shape. The two in `web.py` are the server's error boundary: they turn any error into a reply and log with `logger.exception` only for a 500. See Decision 1.
- **Recommendation:** see Decision 1.

### G9: Public surface and a compatibility shim

- **Category:** A
- **Question:** A17
- **Severity:** low
- **Location:** `src/wambatic/__init__.py:7-13`, `src/wambatic/reports/terminal.py:14`, `src/tests/reports/test_terminal.py:322`
- **Description:** The top-level re-exports, kept as review-1 Decision 4 chose, are used only by `test_package.py`. `terminal.py` has a module `__getattr__` shim that serves `TOP_CONTRIBUTORS_SHOWN` from `rows.py`.
- **Recommendation:** no change to the re-exports (the system spec promises them). Remove the shim and point the one test at `wambatic.reports.rows`.

### G10: Naming and layout standards

- **Category:** S
- **Question:** S2, S4
- **Severity:** low
- **Location:** `fetch/cache.py:303-351`; the S4 rows above; `bin/record-fixtures.py:306`
- **Description:** UPPER_SNAKE local variables in `tables()`; test modules and fixture files that mirror no source module, and fixtures defined in test modules; `record-fixtures.py` prints its failure to stderr where the standard asks for loguru.
- **Recommendation:** lower-case the locals; log the failure with `loguru.logger.error`; list the deliberate test-layout exceptions (property, browser, live and layering tests, fixtures of the fake GitHub) in AGENTS.md beside the `test_fetcher.py` note, so the rule and the layout agree.

### G11: GitHub logins in INFO logs

- **Category:** Sec
- **Question:** Sec5
- **Severity:** low
- **Location:** `reports/web.py:594`, `cli.py:387`, `fetch/base.py:806`, `:906`, `:1016`, `:1117`
- **Description:** Log lines name the login or repository being fetched. They are public GitHub identifiers and the only sink is local stderr.
- **Recommendation:** no change; record in AGENTS.md that logins and repository names are logged by design, as public identifiers the user typed.

### G12: Test gaps

- **Category:** T
- **Question:** T1, T2, T3
- **Severity:** low
- **Location:** `fetch/cache.py:175` (`optional_to_text`, unused), the six T2 functions, `bin/audit-check.py:105`
- **Description:** One helper nothing calls; six small pure functions without property tests; no test runs `bin/audit-check.py` against the real checker.
- **Recommendation:** delete `optional_to_text`; add the six hypothesis tests; add one test that runs `bin/audit-check.sh` on a tiny fixture project.

### G13: Dev tools declared but never imported

- **Category:** D
- **Question:** D2
- **Severity:** low
- **Location:** `pyproject.toml:24`, `:26`, `:28`
- **Description:** As review-1 F18: `mypy`, `pre-commit`, `ruff` are command-line tools in the dev group.
- **Recommendation:** no change (chosen in review-1).

### G14: AGENTS.md and README details

- **Category:** Doc
- **Question:** Doc1, Doc2, Doc5
- **Severity:** low
- **Location:** `AGENTS.md:28`, `:35`, `:44`, `README.md:9`
- **Description:** `.claude/skills/project-setup` has no link though AGENTS.md says every shared skill is linked; AGENTS.md names a `claude/` directory that does not exist; its on-commit list leaves out the whitespace and end-of-file hooks; README says Python 3.14 where `pyproject.toml` needs 3.14.7.
- **Recommendation:** add the link (or make the links a glob the session-start hook refreshes); say `claude/` is created when the first project rule is written; list every hook; say 3.14.7.

### G15: Spec text that no longer matches the code

- **Category:** Doc
- **Question:** Doc4
- **Severity:** medium
- **Location:** the 12 Doc4 rows above; mainly `fetch-and-cache/spec.md:409-410`, `system/spec.md:48`, `:88`, `stats/spec.md:19-28`, `:215`, `reports/spec.md:200-201`, `:221`, `:234`, `:315`, `:27`
- **Description:** The fetch spec still says exhausted retries re-raise the aiohttp error unchanged, the behaviour review-1 F2 removed; the reports spec still names `OSError` for `--out` and port failures and omits the 2008 / tomorrow date bounds; `percentile.py` is missing from the stats module table.
- **Recommendation:** amend each row; the `FetchError` wording in the fetch spec first, since a reader of that spec would expect the old behaviour.

### G16: Spec structure and the implementation order

- **Category:** Doc
- **Question:** spec review (review-1 F19, in part)
- **Severity:** low
- **Location:** `fetch-and-cache/spec.md` (475 lines), `reports/spec.md` (343), `stats/spec.md` (269); version paragraphs out of order (`fetch-and-cache/spec.md:41-43`, `stats/spec.md:13`, `reports/spec.md:13`); no Prerequisite line in the fetch spec (`index.md:10` says each has one); `implementation-order.md` stops at step 10 and still names `compute`
- **Description:** The size gap review-1 raised is still open: the fetch spec changed twice in tasks-1 without the split review-1 recommended at its next change.
- **Recommendation:** see Decision 2 for the split; fix the paragraph order, the Prerequisite line and the implementation order now.

## Files reviewed (Phase B)

Questions A1-A25, S1-S4, P1-P3, Sec1-Sec5, T1-T3 and D1 were applied to every file below; S1 (as a count), S2, S3, S4, Sec1, T1-T3 and D1 also covered every file under `src/tests/`; D2-D3 covered `pyproject.toml` and `uv.lock`; Doc1-Doc5 covered `AGENTS.md`, `README.md` and the four specs.

- `bin/audit-check.py`, `bin/audit-check.sh`, `bin/record-fixtures.py`, `bin/record-fixtures.sh`, `bin/activate.sh`
- `src/wambatic/__init__.py`, `__main__.py`, `cli.py`, `logs.py`, `settings.py`, `version.py`
- `src/wambatic/fetch/`: `__init__.py`, `auth.py`, `base.py`, `cache.py`, `client.py`, `errors.py`, `queries.py`, `ratelimit.py`
- `src/wambatic/stats/`: `__init__.py`, `activity.py`, `base.py`, `buckets.py`, `delivery.py`, `engine.py`, `errors.py`, `flow.py`, `percentile.py`, `popularity.py`
- `src/wambatic/reports/`: `__init__.py`, `base.py`, `errors.py`, `figures.py`, `html.py`, `rows.py`, `service.py`, `terminal.py`, `web.py`
- `src/tests/**/*.py` (for the questions named above)
- `agents/specs/system/spec.md`, `fetch-and-cache/spec.md`, `stats/spec.md`, `reports/spec.md`, `index.md`, `implementation-order.md`

## Prior findings re-verified

| Review-1 finding | Now |
|---|---|
| F1 web log redaction | resolved: `reports/web.py:78`, `:80` |
| F2 boundary errors | one path still present: `fetch/client.py:254-257` (G1); every other path fixed |
| F3 duration overflow | resolved: `settings.py:88-89` |
| F4 date range | resolved: `reports/service.py:125-132` |
| F5 stdlib raises | one site still present: `fetch/client.py:257` (G1); no other `raise ValueError/TypeError/RuntimeError` in `src/wambatic` |
| F6 one owner per setting | resolved, apart from the class-level check (G4) |
| F7 `assert_never` | resolved: `stats/buckets.py:33`, `:56`, `fetch/base.py:1371` |
| F8 read once, build once | resolved: `stats/engine.py:360-386`, `reports/html.py:419-430`; leftovers in G6 |
| F9 spec drift | resolved (rows amended, `cache info` read-only at `fetch/cache.py:796`) |
| F10 README | resolved: `README.md:41`, `:172`, `:228-229` |
| F11 AGENTS.md | resolved; `claude/` still missing (G14) |
| F12 blocking calls | resolved: `reports/service.py:208`, `:226`, `reports/html.py:140` |
| F13 frozen constants | resolved: `stats/delivery.py:39`, `reports/figures.py:42` |
| F14 one field list | resolved: `fetch/cache.py:196-258` |
| F15 smaller architecture | resolved |
| F16 standards | resolved; the proposed change to the shared coding standard was not made (it belongs to the agents repository) |
| F17 tests | resolved |
| F18 dev tools | resolved as chosen (no change) |
| F19 spec structure | partly: the sizes remain (G16) |
| M1 script hits | the review-1 rules have no unaccepted hit; the 16 `raises-section-drift` hits are new (G2) |

`summary.md` recorded F2 and F5 as resolved; that is corrected in this review's summary.

## Recommendations

1. **Medium:** G1 (the JSON path) and G15 (the fetch spec's error wording first).
2. **Low, before the merge:** G2, because the pre-push hook now refuses the branch until the 16 `raises-section-drift` hits are fixed.
3. **Low:** G3-G7, G9, G10, G12, G14, G16.
4. **No change:** G11, G13, and G8 as Decision 1 settles.

## Decisions

### Decision 1: The two broad error handlers in the web server

- **What is being decided:** whether `Jobs.execute` (`reports/web.py:150`) and the `convert_errors` middleware (`:420`) keep catching `Exception`.
- **Background:** the audit skill's rule for a broad handler that degrades gracefully (its "conflicts with no winner" ruling, 2026-10-14) is to remove or narrow it, unless the user decides it has to stay; then it keeps `logger.exception` and is accepted with a scoped marker. These two are the web app's error boundary: a sync job runs in a background task, where an uncaught error would vanish and leave the job shown as running forever, and the middleware is what turns an error into the documented JSON or HTML reply. Both log the traceback with `logger.exception` for an unexpected error (a 500), through `error_response`, and log nothing for an expected domain error (a 4xx or 502).
- **What it affects:** `reports/web.py`, `src/tests/reports/test_web.py`, the next audit's A19 answer.
- **Options:**
  - **A (recommended): keep both, and record why.** A comment at each handler and a line in AGENTS.md that these are the server's error boundary, so the next audit reads the decision. Recommended because without them a failed job would hang its progress page and an unexpected error would reach the client as FastAPI's own 500 page, unredacted.
  - **B: narrow them to the domain errors.** Catch `FetchError`, `StatsError`, `ReportsError` and `SettingsError` only, and let anything else reach FastAPI's default handler. That gives up the redacted 500 page, and a job that fails unexpectedly needs its own clean-up path.

### Decision 2: Split the three oversized specs

- **What is being decided:** whether to split `fetch-and-cache/spec.md` (475 lines), `reports/spec.md` (343) and `stats/spec.md` (269), which are over the specdev guide of about 200 lines.
- **Background:** review-1 (F19, 2026-10-31) recommended splitting the fetch spec when it next changed; tasks-1 changed it twice (1.12, 1.13) and did not split it. Each spec is read whole by every planning step that touches its component.
- **What it affects:** the four specs, `agents/specs/index.md`, every link into them (task lists, reviews, README), and future planning steps.
- **Options:**
  - **A (recommended): split the fetch spec now, the others when they next change.** Fetch and cache become two specs (`fetch` for the client, rate limits and sync; `cache` for the schema and identity), with links updated. Recommended because the fetch spec is more than twice the guide and is the one planning steps load most.
  - **B: split all three now.** Reports into CLI, terminal, HTML and web; stats into its API and its metric groups. The most link churn now.
  - **C: no split.** Record the sizes as accepted, so later audits stop raising them.

## Answers

Answered on the review page (https://claude.ai/artifact/BHMfRN44sus5PpLUYVqXVa) on 2026-10-31 at 17:19 UTC, with the accept-all button; no comments were left.

**Findings:** G1-G16 all approved for the fix list.

**Decisions:**

- Decision 1 (the web server's broad handlers): **A**, keep both and record why, with a comment at each handler and a line in AGENTS.md.
- Decision 2 (oversized specs): **A**, split `fetch-and-cache/spec.md` into a fetch spec and a cache spec now; split `reports` and `stats` when they next change.
