# Audit Summary

**Last updated:** 2026-10-31
**Last review:** review-2
**Total reviews conducted:** 2
**Last script run hit count:** 90 (74 accepted, 16 unaccepted, all `raises-section-drift`)
**Script version:** `4e66ac0cd1e99ce2a8457ebf58915f45c56af2e4191b064a8eb6bc34f85edbc1` (agents `108559d`; from `find -L ~/.claude/skills/auditme/checks -name '*.py' | sort | xargs cat | shasum -a 256`)

## Unresolved findings

### G1: A malformed JSON body on a 200 response escapes as a `ValueError`

- **Rule or category:** A / A1, A2, A3 (review-1 F2 and F5, one path left)
- **Severity:** medium
- **Location:** `src/wambatic/fetch/client.py:254-257`
- **First raised:** review-1 F2/F5 (2026-10-31); narrowed in review-2
- **Description:** `raw.json()` failing on an OK response is re-raised with a bare `raise`; `request` catches only aiohttp errors and `TimeoutError`, so the CLI shows an "Unexpected error" traceback. Every other path review-1 named is translated.
- **Recommendation:** raise `FetchError("GitHub sent a response that is not JSON ...")` from the `ValueError`, with a test using a fake upstream that returns `200` with a non-JSON body.

### G2: `Raises:` sections leave out errors that reach the caller

- **Rule or category:** A / script / A4, and the script's `raises-section-drift` (16 hits)
- **Severity:** low
- **Location:** the 16 script hits and the 14 A4 rows (the two lists overlap: `fetch/client.py:165`, `:190`, `fetch/cache.py:541`, `reports/service.py:238`, `reports/web.py:239`, `stats/engine.py:360`)
- **First raised:** review-2 (2026-10-31)
- **Description:** Task 4 added `Raises:` sections, and later tasks (the `CacheError` envelope, `compute_all`) added errors that now pass through undeclared.
- **Recommendation:** make each section list exactly the domain errors that reach its caller; the script then checks the same-package part on every push.

### G3: Small envelope gaps outside the fetch path

- **Rule or category:** A / A1, A2, A3
- **Severity:** low
- **Location:** `src/wambatic/version.py:10-11`, `bin/audit-check.py:97`, `bin/record-fixtures.py:131`, `:140`, `:150`
- **First raised:** review-2 (2026-10-31)
- **Description:** `version.py` handles only `PackageNotFoundError`; `bin/audit-check.py` runs its checker with no `OSError` envelope; `bin/record-fixtures.py` still raises `RuntimeError` though it now defines `RecordingError`.
- **Recommendation:** catch `OSError`/`UnicodeDecodeError` in `version.py` with the same fallback; translate the checker's `OSError` into the script's exit 2; raise `RecordingError` in the three places.

### G4: Two sources of truth for the timezone, not enforced on the class

- **Rule or category:** A / A5 (review-1 F6, one pair left)
- **Severity:** low
- **Location:** `src/wambatic/stats/base.py:52-53`
- **First raised:** review-1 F6 (2026-10-31); narrowed in review-2
- **Description:** `make_request` now derives `tz` from settings, but `StatsRequest` itself still lets `tz` and `settings.timezone` disagree.
- **Recommendation:** a `__post_init__` check that raises the stats `InvalidRequestError` when `str(tz)` differs from `settings.timezone`, or drop `timezone` from `StatsSettings` for the request.

### G5: Remaining naming, exhaustiveness and slot findings

- **Rule or category:** A / A9, A11, A13
- **Severity:** low
- **Location:** A9: `fetch/auth.py:7`, `fetch/cache.py:443`, `stats/engine.py:360`, `reports/service.py:87`, `cli.py:204`, `reports/web.py:239`, `:424`; A11: `cli.py:271`, `:320`, `fetch/client.py:293`, `stats/buckets.py:70`, `reports/figures.py:318`; A13: `fetch/base.py:766`, `reports/web.py:345`, `:358`, `:372`
- **First raised:** review-2 (2026-10-31)
- **Description:** Functions with pure-sounding prefixes that do I/O; two-way and `else` splits over a `Literal` or enum with no `assert_never`; the same `False` passed by position to `full_refresh` and `no_fetch`.
- **Recommendation:** A11: end each with `typing.assert_never`. A13: pass the two flags by keyword in `needs_sync`, and name the `now` fallback in `new_state`. A9: rename where the I/O is the point (`check_identity` to `record_identity`, `resolve_token` to `fetch_token`), and leave the tz lookups, which are library reads of package data.

### G6: Repeated reads and derivations left after the read-once change

- **Rule or category:** A / P / A14, P2, P3 (review-1 F8 leftovers)
- **Severity:** low
- **Location:** `fetch/base.py:742` (repos read 3 times), `:1272` (star sync state read 3 times), `reports/html.py:559-603`, `:500`/`:303`, `:505`/`:326`, `reports/terminal.py:346`, `fetch/cache.py:211`, `stats/engine.py:283`, `reports/web.py:325`
- **First raised:** review-1 F8 (2026-10-31); leftovers in review-2
- **Description:** The cache is read once per report, but `provenance` and `stars_hidden` re-read the repo list and sync state, the HTML sections still build tables only to test for `None`, and a few derivations repeat per row or per period.
- **Recommendation:** pass the repos and states `read_records` already has into `provenance`; reuse the built tables; compute `column_names` once per `Table`; read templates once at app start-up.

### G7: Construction and return-value leftovers

- **Rule or category:** A / A8, A15, A23
- **Severity:** low
- **Location:** A8: `reports/web.py:89`, `:122`, `stats/activity.py:89` (deliberate, commented in Task 8); A15: `fetch/base.py:487`/`:861`, `fetch/client.py:214`/`:221`, `stats/buckets.py:86`/`:105`, `reports/rows.py:244-339`, the `Series` sites; A23: `fetch/client.py:163`, `bin/record-fixtures.py:135`
- **First raised:** review-2 (2026-10-31)
- **Description:** A few record types are still assembled at two or more sites, and two calls drop the second element of a returned tuple without naming it.
- **Recommendation:** a `make_series` helper and a `period_table` helper; name the dropped values (`data, _date = ...`). A8 needs no change.

### G8: Broad handlers that degrade gracefully

- **Rule or category:** A / A19
- **Severity:** low
- **Location:** `fetch/cache.py:423`, `reports/html.py:684`, `reports/web.py:150`, `:420`
- **First raised:** review-2 (2026-10-31)
- **Description:** The two `except BaseException` handlers clean up and re-raise, which is the right shape. The two in `web.py` are the server's error boundary: they turn any error into a reply and log with `logger.exception` only for a 500. See Decision 1.
- **Recommendation:** see Decision 1.

### G9: Public surface and a compatibility shim

- **Rule or category:** A / A17
- **Severity:** low
- **Location:** `src/wambatic/__init__.py:7-13`, `src/wambatic/reports/terminal.py:14`, `src/tests/reports/test_terminal.py:322`
- **First raised:** review-2 (2026-10-31)
- **Description:** The top-level re-exports, kept as review-1 Decision 4 chose, are used only by `test_package.py`. `terminal.py` has a module `__getattr__` shim that serves `TOP_CONTRIBUTORS_SHOWN` from `rows.py`.
- **Recommendation:** no change to the re-exports (the system spec promises them). Remove the shim and point the one test at `wambatic.reports.rows`.

### G10: Naming and layout standards

- **Rule or category:** S / S2, S4
- **Severity:** low
- **Location:** `fetch/cache.py:303-351`; the S4 rows above; `bin/record-fixtures.py:306`
- **First raised:** review-2 (2026-10-31)
- **Description:** UPPER_SNAKE local variables in `tables()`; test modules and fixture files that mirror no source module, and fixtures defined in test modules; `record-fixtures.py` prints its failure to stderr where the standard asks for loguru.
- **Recommendation:** lower-case the locals; log the failure with `loguru.logger.error`; list the deliberate test-layout exceptions (property, browser, live and layering tests, fixtures of the fake GitHub) in AGENTS.md beside the `test_fetcher.py` note, so the rule and the layout agree.

### G11: GitHub logins in INFO logs

- **Rule or category:** Sec / Sec5
- **Severity:** low
- **Location:** `reports/web.py:594`, `cli.py:387`, `fetch/base.py:806`, `:906`, `:1016`, `:1117`
- **First raised:** review-2 (2026-10-31)
- **Description:** Log lines name the login or repository being fetched. They are public GitHub identifiers and the only sink is local stderr.
- **Recommendation:** no change; record in AGENTS.md that logins and repository names are logged by design, as public identifiers the user typed.

### G12: Test gaps

- **Rule or category:** T / T1, T2, T3
- **Severity:** low
- **Location:** `fetch/cache.py:175` (`optional_to_text`, unused), the six T2 functions, `bin/audit-check.py:105`
- **First raised:** review-2 (2026-10-31)
- **Description:** One helper nothing calls; six small pure functions without property tests; no test runs `bin/audit-check.py` against the real checker.
- **Recommendation:** delete `optional_to_text`; add the six hypothesis tests; add one test that runs `bin/audit-check.sh` on a tiny fixture project.

### G13: Dev tools declared but never imported

- **Rule or category:** D / D2
- **Severity:** low
- **Location:** `pyproject.toml:24`, `:26`, `:28`
- **First raised:** review-1 F18 (2026-10-31)
- **Description:** As review-1 F18: `mypy`, `pre-commit`, `ruff` are command-line tools in the dev group.
- **Recommendation:** no change (chosen in review-1).

### G14: AGENTS.md and README details

- **Rule or category:** Doc / Doc1, Doc2, Doc5
- **Severity:** low
- **Location:** `AGENTS.md:28`, `:35`, `:44`, `README.md:9`
- **First raised:** review-2 (2026-10-31)
- **Description:** `.claude/skills/project-setup` has no link though AGENTS.md says every shared skill is linked; AGENTS.md names a `claude/` directory that does not exist; its on-commit list leaves out the whitespace and end-of-file hooks; README says Python 3.14 where `pyproject.toml` needs 3.14.7.
- **Recommendation:** add the link (or make the links a glob the session-start hook refreshes); say `claude/` is created when the first project rule is written; list every hook; say 3.14.7.

### G15: Spec text that no longer matches the code

- **Rule or category:** Doc / Doc4
- **Severity:** medium
- **Location:** the 12 Doc4 rows above; mainly `fetch-and-cache/spec.md:409-410`, `system/spec.md:48`, `:88`, `stats/spec.md:19-28`, `:215`, `reports/spec.md:200-201`, `:221`, `:234`, `:315`, `:27`
- **First raised:** review-2 (2026-10-31)
- **Description:** The fetch spec still says exhausted retries re-raise the aiohttp error unchanged, the behaviour review-1 F2 removed; the reports spec still names `OSError` for `--out` and port failures and omits the 2008 / tomorrow date bounds; `percentile.py` is missing from the stats module table.
- **Recommendation:** amend each row; the `FetchError` wording in the fetch spec first, since a reader of that spec would expect the old behaviour.

### G16: Spec structure and the implementation order

- **Rule or category:** Doc / spec review (review-1 F19, in part)
- **Severity:** low
- **Location:** `fetch-and-cache/spec.md` (475 lines), `reports/spec.md` (343), `stats/spec.md` (269); version paragraphs out of order (`fetch-and-cache/spec.md:41-43`, `stats/spec.md:13`, `reports/spec.md:13`); no Prerequisite line in the fetch spec (`index.md:10` says each has one); `implementation-order.md` stops at step 10 and still names `compute`
- **First raised:** review-1 F19 (2026-10-31)
- **Description:** The size gap review-1 raised is still open: the fetch spec changed twice in tasks-1 without the split review-1 recommended at its next change.
- **Recommendation:** see Decision 2 for the split; fix the paragraph order, the Prerequisite line and the implementation order now.

## Recently resolved

| Finding | Severity | Raised in | Resolved in |
|---------|----------|-----------|-------------|
| Mechanical hits of the review-1 rules | low to medium | review-1 | tasks-1, confirmed in review-2 |
| F1: Web server logs unexpected errors without redacting the token | high | review-1 | tasks-1, confirmed in review-2 |
| F3: Settings validation lets an `OverflowError` through | medium | review-1 | tasks-1, confirmed in review-2 |
| F4: The web report accepts an unbounded date range | medium | review-1 | tasks-1, confirmed in review-2 |
| F7: `match`/`if` chains end in `raise`, not `assert_never` | medium | review-1 | tasks-1, confirmed in review-2 |
| F9: Spec and code disagree | medium | review-1 | tasks-1, confirmed in review-2 |
| F10: README drift | medium | review-1 | tasks-1, confirmed in review-2 |
| F11: AGENTS.md has no structure or tools section | medium | review-1 | tasks-1, confirmed in review-2 |
| F12: Blocking calls on the event loop | medium | review-1 | tasks-1, confirmed in review-2 |
| F13: Mutable module-level containers read from other modules | low | review-1 | tasks-1, confirmed in review-2 |
| F14: Duplicated record construction between the parsers and the cache | low | review-1 | tasks-1, confirmed in review-2 |
| F15: Smaller architecture findings | low | review-1 | tasks-1, confirmed in review-2 |
| F16: Standards findings | low | review-1 | tasks-1, confirmed in review-2 |
| F17: Test coverage gaps | low | review-1 | tasks-1, confirmed in review-2 |

F2 and F5 were recorded here as resolved after tasks-1; review-2 found one path left (G1). F6 and F8 are resolved apart from the leftovers in G4 and G6, and F18 stays open by choice (G13).

## Recurring patterns

- Docstring `Raises:` sections drift from what reaches the caller as error envelopes are added (review-1 A4 by hand, review-2 G2 by script).
- Spec text lags behind behaviour changes made in task lists (review-1 F9, review-2 G15).

## Checker changes since the last review

- `raises-section-drift` added and `mutable-module-level-exported` refined for builtin constructor calls (agents `c437b07`, digest `4d7de71f...` to `4e66ac0c...`): 16 new hits in this project, all `raises-section-drift`.
