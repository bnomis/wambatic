# Implementation order

**Version:** 1.14
**Status:** proposed
**Date:** 2026-11-11

The order in which wambatic is built, with what each step delivers, what it depends on and how to tell it is done. It sequences the components in the [system spec](system/spec.md) into steps that [taskdev](../../.agents/claude/skills/taskdev/SKILL.md) can break into tasks. Component detail stays in the component specs; this document only sequences them.

## Principles

- **Vertical slices.** From step 4 on, every step ends with something runnable end to end, not a layer with nothing using it.
- **Cheapest risk first.** The riskiest unknowns are GitHub's rate limits, per-commit line counts and incremental sync correctness. They are tackled in steps 2 to 4, before any rendering work.
- **Tests first on fixtures.** Each step records small real API responses as fixtures once, then every later test replays them offline.
- **One step, one PR.** Each step is a branch and a PR that passes `ruff check`, `ruff format --check`, `pre-commit run --all-files` and the tests for the changed modules.
- **Dependencies are checked, not assumed.** Before a step adds a library, it checks maintenance status as the shared tools-and-libraries rule requires.

## Steps

| # | Step | Specs | Depends on | Status |
|---|------|-------|------------|--------|
| 1 | Skeleton and settings | [system](system/spec.md) | none | done: [tasks-1](../tasks/system/tasks-1.md) |
| 2 | Fetch core: auth, aiohttp client, rate limits | [fetch](fetch/spec.md), [cache](cache/spec.md) | 1 | done: [tasks-1](../tasks/fetch-and-cache/tasks-1.md) |
| 3 | Cache and incremental sync for repos and commits | [fetch](fetch/spec.md), [cache](cache/spec.md) | 2 | done: [tasks-2](../tasks/fetch-and-cache/tasks-2.md) |
| 4 | Activity stats with bucketing | [stats](stats/spec.md) | 3 | done: [tasks-1](../tasks/stats/tasks-1.md) |
| 5 | Terminal report and CLI | [reports](reports/spec.md) | 4 | done: [tasks-1](../tasks/reports/tasks-1.md) |
| 6 | Flow data and stats (PRs, issues) | [fetch](fetch/spec.md), [cache](cache/spec.md), [stats](stats/spec.md) | 3, 4 | done: [tasks-2](../tasks/stats/tasks-2.md) |
| 7 | Static HTML report | [reports](reports/spec.md) | 5 | done: [tasks-2](../tasks/reports/tasks-2.md) |
| 8 | Delivery data and stats (releases, Actions, DORA proxies) | [fetch](fetch/spec.md), [cache](cache/spec.md), [stats](stats/spec.md), [reports](reports/spec.md) | 6, 7 | done: [tasks-3](../tasks/stats/tasks-3.md) |
| 9 | Local web app | [reports](reports/spec.md), [fetch](fetch/spec.md), [cache](cache/spec.md) | 7 | done: [tasks-3](../tasks/reports/tasks-3.md) |
| 10 | Popularity data and stats (stars, forks, watchers, languages) | [fetch](fetch/spec.md), [cache](cache/spec.md), [stats](stats/spec.md), [reports](reports/spec.md) | 7 | done: [tasks-4](../tasks/stats/tasks-4.md) |
| 11 | Audit work: errors, specs and code fixes from the two audit reviews | every spec | 10 | done: [tasks-1](../tasks/audit-reviews/tasks-1.md), [tasks-2](../tasks/audit-reviews/tasks-2.md) |
| 12 | User guide: MkDocs site, reference pages, screenshots, drift test | [user guide](user-guide/spec.md) | 11 | done: [tasks-1](../tasks/user-guide/tasks-1.md) |
| 13 | GitHub Enterprise Server: host setting, addresses, token, rate limits off, version check, cache per host | [fetch](fetch/spec.md), [cache](cache/spec.md), [system](system/spec.md), [CLI](cli/spec.md), [reports](reports/spec.md), [terminal report](terminal-report/spec.md), [HTML report](html-report/spec.md) | 12 | done: [tasks-1](../tasks/fetch/tasks-1.md) |
| 14 | Commit sync: bare clones for public and allowed repositories, an opt-in per-file API read for the rest, generated files left out, followed branches | [commit sync](commit-sync/spec.md), [fetch](fetch/spec.md), [cache](cache/spec.md), [stats](stats/spec.md), [metric groups](metric-groups/spec.md), [system](system/spec.md), [CLI](cli/spec.md), [terminal report](terminal-report/spec.md), [HTML report](html-report/spec.md) | 13 | done: [tasks-1](../tasks/commit-sync/tasks-1.md) |
| 15 | Author timezones: commits dated in their authors' zones, from settings or the offset git recorded | [author timezones](author-timezones/spec.md), [system](system/spec.md), [stats](stats/spec.md), [metric groups](metric-groups/spec.md), [cache](cache/spec.md), [fetch](fetch/spec.md), [commit sync](commit-sync/spec.md), [CLI](cli/spec.md), [reports](reports/spec.md), [web app](web-app/spec.md), [terminal report](terminal-report/spec.md), [HTML report](html-report/spec.md) | 14 | done: [tasks-1](../tasks/author-timezones/tasks-1.md) |
| 16 | Tabbed HTML report with collapsible, sortable, filterable and exportable tables, an assets folder beside the page, and a GraphQL API replacing the REST routes | [HTML report](html-report/spec.md), [GraphQL API](graphql-api/spec.md), [web app](web-app/spec.md), [reports](reports/spec.md) | 15 | proposed |

Steps 6 and 7 are independent and may be built in either order or in parallel once 5 is done. Step 10 was split from step 8 on 2026-10-30 (stats review 3), because its fetch resources were not specified and the two together were more than one task list; it was specified on 2026-10-30 (stats review 4). Steps 9 and 10 are independent of each other. Step 11 is the audit work after step 10; it changes no feature. Step 12 is the user guide; it changes no source module.

## Step detail

### 1. Skeleton and settings

Deliver: `pyproject.toml` (Python 3.14, ruff, mypy, pytest, hypothesis, pre-commit config, `uv.lock`), `src/wambatic/` with `settings.py` (`load_settings` layering defaults, JSON file, flag overrides), loguru setup, `src/tests/` layout, and a CI workflow running ruff, mypy and pytest.
Done when: `pytest` passes with settings-layering tests, CI is green on an empty-feature PR, and the token is shown to be read only from the environment.

### 2. Fetch core

Deliver: `fetch_token`, the aiohttp transport `GitHubClient` (`__aenter__`/`__aexit__`) that `Fetcher` wraps in step 3, the GraphQL and REST request paths with ETag revalidation, `rateLimit` accounting, transient and secondary-limit backoff, the typed error classes except `CacheVersionError`, and token redaction in logs.
Done when: replayed fixtures cover 401, 404, primary and secondary rate limits and REST 202; an opt-in live test lists the repos of a small public account.

### 3. Cache and incremental sync (repos and commits)

Deliver: `Subject`, `Fetcher` wrapping the step 2 `GitHubClient`, the `fetch.workers` semaphore, the SQLite schema, `meta` identity and `CacheVersionError`, ETag storage, `sync_state` rows, `sync()` with `repos()` and `commits()` reading the cache, per-commit additions and deletions and merge flags, compare-based increments from the stored head, de-duplication, rewritten-history detection and atomic state advance, and `full_refresh` (the `--full-refresh` flag itself is step 5's CLI).
This is the highest-risk step; it proves the incremental design before anything depends on it.
Done when: a second run of the same fixture fetches nothing; an interrupted run resumes; a simulated force-push triggers a full refetch of that repo; and an opt-in live test's line totals match `stats/code_frequency` for a small repo.

### 4. Activity stats

Deliver: `Granularity`, `bucket_for` and `bucket_range` (ISO weeks, timezones, partial buckets), the stats errors, `Fetcher.provenance`, and `compute` (with `compute_all` from stats spec 1.6) for the `activity` group's commit metrics: commits, contributors, active days, lines added, deleted and net, per-repo and `by_author` breakdowns, and the top-contributors table. Groups and metrics not built yet are listed as `unavailable`; stars, forks, watchers and languages wait for step 10.
Done when: hypothesis tests show buckets partition any date range with no gaps or overlaps, and known-good fixture totals match by hand.

### 5. Terminal report and CLI

Deliver: the `rich` and `cappa` dependencies, `cli.main` with `report` and `cache` commands, `<target>` parsing (bare `NAME` through `Fetcher.owner_kind`), `--by`, `--since`, `--until`, `--groups`, `--by-author`, `--tz`, `--format terminal|json`, `--full-refresh`, `--no-fetch`, `--max-age`, `--ignore-cache-version`, `-v`/`-q`, the terminal renderer and JSON output, `BUILT_RESOURCES`, `inspect_cache` and `clear_cache`, the `wambatic` console script, a README user guide, the single error-to-exit-status conversion, and the sync-then-compute call (`compute`, or `compute_all` from stats spec 1.6 when several granularities share one read). `--format html` and `--out` wait for step 7 and `serve` for step 9.
Done when: `wambatic report repo:OWNER/NAME --by month --no-fetch` (or with a `--max-age` the cache is younger than) prints a correct report from a warm cache with no network and no `GITHUB_TOKEN`, and every typed error maps to its documented exit status. Without either flag the report syncs first, since `fetch.max_age` defaults to zero.

### 6. Flow data and stats

Deliver: the `PullRequest` and `Issue` records and tables (cache schema 2), `pull_requests()` and `issues()` with updated-at paging from a `Date`-header watermark, the repo listing's newest pull request and issue update times so unchanged repos are skipped, `issues` and `pull_requests` in `BUILT_RESOURCES`, the `flow` group (throughput, time to first review, merge and close, PR size) in `compute`, the terminal's Flow by period and Flow times tables, and the README's flow section. Fetch spec 1.5, stats spec 1.2 and reports spec 1.3; the choices are in the [stats review 2](stats/review-2.md).
Done when: incremental refresh updates a PR that changed and leaves unchanged ones untouched, the full-refresh interval removes a deleted issue, a repo whose newest PR and issue are older than the watermark costs no per-repo request, and the default report (`activity,flow`) lists nothing as unavailable for `flow`.

### 7. Static HTML report

Deliver: the `plotly` dependency (used only for its bundled plotly.js) and Playwright for Python as a development dependency, the table rows moved from `terminal.py` to `rows.py`, `figures.py` (`Figure`, `build_figures`, `build_range_figures`, `build_calendar`, the palette), `html.py` and its templates (`HtmlReport`, `html_document`, `render_html`, `report_filename`) with the summary tiles, granularity switch, data tables, themes and provenance footer, `--format html` and `--out` with an atomic write, a `browser` CI job, and the README's HTML section. Reports spec 1.4; the choices are in the [reports review 2](reports/review-2.md).
Done when: the file opens offline with no network request, shows all four granularities, and passes a headless-browser smoke test (Playwright for Python with the preinstalled Chromium here, and Playwright's own Chromium in CI).

### 8. Delivery data and stats

Deliver: the `Release` and `WorkflowRun` records and tables, the `PullRequest` fields `labels` and `first_commit_at`, the listing's release probe and `sync_state.probe` (cache schema 3), `releases()` (full read when the probe changes) and `workflow_runs()` (REST, a free 304 when unchanged, in-progress runs re-read), `releases` and `workflow_runs` in `BUILT_RESOURCES`, the `delivery` group (Actions and release metrics, and the DORA proxies emitted only when their inputs exist), the terminal's Delivery by period and DORA proxies by period tables, the HTML page's delivery tiles, charts and tables, the release and run counts in `cache info`, and the README's delivery section. Fetch spec 1.6, stats spec 1.3 and reports spec 1.5; the choices are in the [stats review 3](stats/review-3.md).
Done when: unconfigured proxies are listed as `unavailable` with a reason, in-progress runs are refreshed on the next sync, an unchanged repo's workflow runs cost one 304 and its releases no request, and `--groups delivery` renders in the terminal, JSON and HTML formats.

### 9. Local web app

Deliver: the CLI's sync-then-compute code moved to `reports/service.py` and the five-result HTML build to `html.py`, `SyncProgress` and `Fetcher.sync`'s `progress` argument, the `fastapi` and `uvicorn` dependencies (and `httpx` for tests), the sync jobs, a FastAPI app with `/`, `/report`, `/api/stats` and `/api/progress`, the form, progress and message pages, the `Host` check, loopback-only binding and `--allow-remote`, the `serve` command, and the README's web app section. Reports spec 1.6 and fetch spec 1.7; the choices are in the [reports review 3](reports/review-3.md).
Done when: a large-org fixture does not block the page, invalid parameters return 400, and a non-loopback bind without the flag refuses to start.

### 10. Popularity data and stats

Deliver: the `StarEvent` and `Fork` records and tables, the listing's star, fork and watcher counts and language sizes, the star and fork probes (cache schema 4), `star_events()` (GraphQL stargazers, newest first, stopping at the watermark) and `forks()` (the REST fork list), both read in full when their count falls, `star_events` and `forks` in `BUILT_RESOURCES`, the `popularity` group (stars and forks added and cumulative per period, the `popularity` and `languages` tables) in `compute`, with the four metrics leaving `activity`'s unavailable list, the terminal's Popularity by period, Popularity now and Languages tables, the HTML page's popularity tiles, charts, languages chart and tables, the star and fork counts in `cache info`, and the README's popularity section. Fetch spec 1.8, stats spec 1.4 and reports spec 1.7; the choices are in the [stats review 4](stats/review-4.md).
Done when: an unchanged repo's stars and forks cost no request, a removed star leaves the cache on the next sync, the default report lists nothing as unavailable, and `--groups popularity` renders in the terminal, JSON and HTML formats.

### 11. Audit work

Deliver: the fixes for [review-1](../audit-reviews/review-1.md) ([tasks-1](../tasks/audit-reviews/tasks-1.md)) and [review-2](../audit-reviews/review-2.md) ([tasks-2](../tasks/audit-reviews/tasks-2.md)): every error that reaches a caller is typed and listed in its `Raises` section, the specs match the code, the fetch-and-cache spec is split into the fetch and cache specs, and the whole-tree audit check passes.
Done when: `bin/audit-check.sh` reports no unaccepted hit and every task in both lists is done.
### 12. User guide

Deliver: the MkDocs site in `docs/` and `mkdocs.yml`, the reference pages and the drift test that checks them against the code, the screenshot script, the guide pages, the slimmed README and the `docs` workflow that deploys the site.
Done when: `mkdocs build --strict` exits 0, `pytest src/tests/test_docs.py` passes and the README points at the guide.

### 13. GitHub Enterprise Server

Deliver: `fetch.github_host` and its checks in `wambatic.settings`, `cache_path_for`, `hosts.py` (`GitHubHost`, `parse_host`, `MIN_SERVER_VERSION`, `parse_server_version`), `GitHubClient` taking a `GitHubHost` in place of `api_url`, `fetch_token(host)`, `GitHubClient.server_version` and `ServerVersionError`, rate limits that may be switched off on an Enterprise host, the `github_host` identity row, `CacheHostError` and the `server_version` row, `--github-host` on `report`, `serve` and `cache`, the host line in the terminal and HTML provenance footers, and the user guide's Enterprise page and setting. Fetch spec 1.16, cache spec 1.1, system spec 1.10, CLI spec 1.1, reports spec 1.14, terminal report and HTML report specs 1.1; the choices are in the [fetch review 1](fetch/review-1.md).
Done when: replayed Enterprise fixtures show every request going to `/api/v3` or `/api/graphql` on the host with the Enterprise token and never `GITHUB_TOKEN`; a server below `MIN_SERVER_VERSION` is refused before any other request; a response without rate-limit headers or `rateLimit` syncs on an Enterprise host and still fails on github.com; a cache made for one host is refused for another even with `--ignore-cache-version`; a github.com cache made before this step opens unchanged; and `mkdocs build --strict` and `pytest src/tests/test_docs.py` pass.

### 14. Commit sync from bare clones

Deliver: `git.py` (`Git`, `GitCommit`, `clone_url`), `GitError` and `BranchesMismatchError`, `CommitFile`, `Commit.files` and `Repo.visibility`, `commit_method` and the `clone`, `api` (the 1.16 sync, kept) and `api-files` methods in `Fetcher`, with `COMMIT_AUTHORS`, `BRANCHES` and `BRANCH_HISTORY`, `fetch.branches`, `fetch.clone_repos`, `fetch.api_history`, `fetch.clone_dir` and `clones_dir_for`, the `commit_files` and `branch_heads` tables and `SCHEMA_VERSION` 5, `clear_cache` and `inspect_cache` with the clones, `stats.exclude_paths` and `stats.linguist` applied to the `activity` line counts, the `unavailable` rows for repositories that could not be filtered, the `commit_methods`, `branches`, `exclude_paths` and `linguist` provenance keys and their footer lines, and the user guide's pages and settings. Commit sync spec 1.0, fetch spec 1.17, cache spec 1.2, stats spec 1.11, metric groups spec 1.1, system spec 1.11, CLI spec 1.2, terminal report and HTML report specs 1.2; the choices are in the [commit sync review 1](commit-sync/review-1.md).
Done when: a private repository is cloned only when `fetch.clone_repos` matches it, and otherwise is read by the 1.16 sync or, with `fetch.api_history = 'files'`, by per-commit REST reads; a change of method re-reads the repository and removes a clone it no longer may keep; a sync of local test repositories stores every followed branch's commits once with their per-file counts, and a force-push or a deleted branch removes the commits no longer reachable; no git argument holds the token; a lock file and a `linguist-generated` path are left out of `lines_added` and counted in `commits`; a `--no-fetch` report after `fetch.branches` changed raises `BranchesMismatchError`; the live sync of `octocat/Hello-World` matches `stats/code_frequency`; and `mkdocs build --strict` and `pytest src/tests/test_docs.py` pass.

### 15. Author timezones

Deliver: `GitCommit.authored_offset` and `Commit.authored_offset` from a clone's `%aI`, the `commits` column `authored_offset` and `SCHEMA_VERSION` 6, `stats.commit_timezone` and `stats.author_timezones` with `author_zones` and the new `convert` branch, `commit_zone` and the author-local day in `read_commits`, the `unavailable` rows for repositories whose commits have no offset, the `commit_timezone` and `author_timezones` provenance keys, `--commit-tz`, the web app's `commit_tz` field and parameter, the two-zone title in the terminal and HTML reports, and the user guide's settings and report pages. Author timezones spec 1.0, system spec 1.12, stats spec 1.12, metric groups spec 1.2, cache spec 1.3, fetch spec 1.18, commit sync spec 1.1, CLI spec 1.3, reports spec 1.15, web app spec 1.1, terminal report and HTML report specs 1.3; the choices are in the [author timezones review 1](author-timezones/review-1.md).
Done when: in `report` mode every result is unchanged; in `author` mode a clone-read commit made at 01:00 +09:00 on a Monday is counted on that Monday in a UTC report, `stats.author_timezones` overrides its offset, an API-read repository's commits are dated in the report zone with a row in `tables['unavailable']`, `--commit-tz author` overrides the setting, the title names both zones, a cache of schema 5 is refused, and `mkdocs build --strict` and `pytest src/tests/test_docs.py` pass.

### 16. Tabbed report and GraphQL API

Deliver: `assets.py` and the assets folder written beside the page, the vendored `write-excel-file` 4.1.1, the tab bar and panels, `tables.js` (collapsible blocks, sorting, filtering, CSV and Excel export), `jobs.py` moved out of `web.py`, `api.py` with the Strawberry schema at `/graphql`, `/assets/HASH/` in the web app, the progress page polling GraphQL, the removal of `/api/stats`, `/api/progress`, `/openapi.json` and `/docs`, and the user guide's HTML report and web app pages with new screenshots. Build the GraphQL half after checking that strawberry-graphql 0.341.2 installs and runs under Python 3.14.
Done when: `report --format html` writes a page and its `wambatic-assets-HASH` folder that open offline, the browser test passes for tabs, sorting, filtering and both exports, the exported schema equals the GraphQL API spec's SDL, the API tests pass, and the four removed routes answer 404.
