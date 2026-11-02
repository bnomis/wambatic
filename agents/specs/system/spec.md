# System

**Version:** 1.11
**Status:** implemented
**Date:** 2026-11-02

wambatic reports statistics from github.com, or from a GitHub Enterprise Server, for a user, a repository or an organisation, as a terminal report, a static HTML report or a local web app, with the numbers bucketed by year, month, week or day. This spec is the top of the set: it fixes the architecture, the boundaries between components, the data flow, the stack and the build order. The detail of each component is in its own spec; where this spec and a component spec differ, the component spec wins and this one is amended.

Version 1.10 lifts the first release's GitHub Enterprise Server limit ([Fetch](../fetch/spec.md) 1.16): the token variables of an Enterprise host, and the limits that remain; the choices are in the [fetch review 1](../fetch/review-1.md), decided 2026-11-02.

Version 1.11 lifts two more of the first release's limits, default-branch history only and line counts that include generated files, for public repositories and those the user allows to be cloned, and by an explicit slow API option for the others: a clone needs `git` ([Commit sync](../commit-sync/spec.md), [Fetch](../fetch/spec.md) 1.17); the choices are in the [commit sync review 1](../commit-sync/review-1.md), decided 2026-11-02.

## Module location

`src/wambatic/` is the package. `src/wambatic/__init__.py` re-exports the public API listed below; `src/tests/` mirrors the source layout; `bin/` holds entry-point scripts.

| Component | Package | Spec |
|-----------|---------|------|
| Fetch | `src/wambatic/fetch/` | [fetch](../fetch/spec.md) |
| Cache | `src/wambatic/fetch/cache.py` | [cache](../cache/spec.md) |
| Stats | `src/wambatic/stats/` | [stats](../stats/spec.md) |
| Reports and CLI | `src/wambatic/reports/`, `src/wambatic/cli.py` | [reports](../reports/spec.md) |
| Settings | `src/wambatic/settings.py` | this spec |
| Version identity | `src/wambatic/version.py` | this spec |

## API

The public surface other code and the three front ends may rely on, re-exported from `wambatic`:

- `Subject`: a user, repo or org target
- `Fetcher`: GitHub access plus cache
- `StatsRequest`: granularity, groups, range, timezone
- `StatsResult`: series, tables, provenance
- `compute`: `async (Subject, Fetcher, StatsRequest) -> StatsResult`
- `Settings`: layered configuration

```python
import dataclasses
import pathlib

@dataclasses.dataclass(frozen=True, slots=True)
class Settings:
    fetch: FetchSettings
    report: ReportSettings
    stats: StatsSettings

def load_settings(config_path: pathlib.Path | None, overrides: dict[str, object]) -> Settings:
    """Defaults, then the JSON file, then command-line overrides; later wins."""
```

## Architecture

Three layers with one-way dependencies: `reports` imports `stats`, `stats` imports `fetch`, and `fetch` imports nothing from wambatic except `settings` and `version`. `settings` and `version` are leaves: they import nothing from wambatic, and any layer may import them. `reports` may also import `fetch` directly, for the `Fetcher`, the cache and the fetch errors it presents (reports spec, review 3 choice 2); `stats` never imports `reports`, and `fetch` never imports `stats` or `reports`. `wambatic.cli` sits above the three as the composition root: it opens the `Cache` and hands it to `wambatic.reports.service`, which builds the `Fetcher`, syncs and calls `compute_all`, and then calls a renderer (and uses `wambatic.logs`).

```text
GitHub GraphQL / REST
        |  aiohttp
   [ fetch ]  -- reads/writes -->  SQLite cache (local file)
        |  typed records (Commit, PullRequest, Issue, Release, WorkflowRun, StarEvent, Fork)
   [ stats ]  -- pure computation, no I/O
        |  StatsResult (series, tables, provenance)
   [ reports ]  -->  terminal | static HTML file | local web app | JSON
```

Rules that hold across the system:

- **One result, many views.** All renderers take a `StatsResult`; no metric logic lives in a renderer.
- **Pure core.** The aggregation functions in `stats` perform no I/O, so every metric is testable from fixture records; only `compute` awaits the fetcher, then hands the records to them.
- **Cache is the only state.** Everything else is derived and reproducible from the cache plus the request.
- **Provenance travels with the data.** Every `StatsResult` carries wambatic version, cache schema version, query hashes and fetch times. The cache refuses a mismatch rather than mixing versions, per the shared versions rule.
- **Secrets stay in the environment.** The token is read from `GITHUB_TOKEN` (or `gh auth token`), or for an Enterprise host from `GH_ENTERPRISE_TOKEN` or `GITHUB_ENTERPRISE_TOKEN` (or `gh auth token --hostname HOST`), and never reaches the cache, logs, reports or the browser.

## Data flow

1. The CLI or web handler parses `<target>` into a `Subject` and the flags into a `StatsRequest`.
2. Unless `--no-fetch` applies, the front end calls `Fetcher.sync` for the resources the requested groups need (`stats.resources_for`: commits for activity, pull requests and issues for flow, releases, workflow runs and pull requests for delivery, star events and forks for popularity; the popularity group's counts and languages come with the repository listing every sync reads).
3. `Fetcher` backfills everything on a subject's first sync and afterwards fetches only the delta since each per-repo, per-resource watermark, and writes it back atomically. `compute` then asks `Fetcher` for the subject's repositories and their typed records, which come from the cache alone; `compute` never syncs.
4. `compute` normalises timestamps to the request timezone, assigns each record to a bucket, aggregates per group, and returns the `StatsResult`.
5. A renderer presents the result. The web app repeats steps 1 to 5 per request; the cache makes repeats cheap.

## Error handling

Errors are typed in the layer that detects them and presented only at the edge:

- `settings` raises `SettingsError`.
- `fetch` raises `AuthError`, `NotFoundError`, `RateLimitError`, `StatsPendingError`, `GraphQLError`, `CacheVersionError`, `CacheError`, `InvalidRequestError`, all subclasses of `FetchError`.
- `stats` raises `InvalidRangeError`, `InvalidRequestError`, `UnknownGroupError`, `EmptySubjectError`, all subclasses of `StatsError`.
- `reports` raises `UsageError`, `OutputError` and `ServeError`, all `ReportsError`s, and converts all of the above once, in `cli.main` (exit status 1, or 2 for `UsageError` and `SettingsError`) and in the web app's error middleware (HTTP 400, 404, 502 or 500, as the [Web app](../web-app/spec.md) spec lists).
- Unexpected exceptions propagate and are logged with `loguru.logger.exception`.

## Implementation

**Stack.** Python 3.14 (as in the shared Python rules), managed with [uv](https://docs.astral.sh/uv/) and a committed `uv.lock`; ruff and pre-commit as in the shared rules; pytest and hypothesis for tests; mypy for type checking. Runtime libraries, declared in `pyproject.toml`: [aiohttp](https://docs.aiohttp.org/en/stable/), [loguru](https://loguru.readthedocs.io/), [Rich](https://rich.readthedocs.io/), [Plotly](https://plotly.com/python/), [FastAPI](https://fastapi.tiangolo.com/) with [uvicorn](https://www.uvicorn.org/), [cappa](https://cappa.readthedocs.io/). The local web app is FastAPI on uvicorn, chosen over aiohttp's own server (reports review 3, decision 1, answered 2026-10-30). The stdlib covers `sqlite3`, `datetime`, `zoneinfo`, `statistics` and `json`.

**Build order.** The sequence of steps, with deliverables, dependencies and done criteria, is in [Implementation order](../implementation-order.md).

**Testing.** Unit tests run on recorded fixture responses and never touch the network. The opt-in live tests, skipped without `GITHUB_TOKEN`, fetch a small public repository and check line totals against the REST `stats/code_frequency` endpoint, and read its star events and forks. Tests are scoped to changed modules, as the shared rules require.

**Limits accepted for the first release.** One timezone per report. Since 1.11 a public repository, or one the user allows in `fetch.clone_repos`, is read from a local clone, which follows the branches `fetch.branches` names and leaves generated files out of line counts (`stats.exclude_paths`, `stats.linguist`); any other repository keeps the default branch and unfiltered totals unless `fetch.api_history` is `'files'`, a slow per-commit REST read that follows the branches and applies `stats.exclude_paths`. A report names the repositories it could not filter. A repository's attributes are read at its default branch's head, and pull request sizes still include generated files. Since 1.10 GitHub Enterprise Server is supported from the oldest release GitHub supported when the wambatic release was made (3.19 on 2026-11-02); GitHub Enterprise Cloud with data residency (`*.ghe.com`) is out of scope.

## Settings

Layered, later wins: built-in defaults, `~/.config/wambatic/config.json`, command-line flags. Component settings are defined in the component specs under the `fetch.`, `stats.` and `report.` prefixes. The token is never a setting: it is read from the environment only. The two environment variables the system reads are:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GITHUB_TOKEN` | string | none | API token for github.com |
| `GH_ENTERPRISE_TOKEN`, then `GITHUB_ENTERPRISE_TOKEN` | string | none | API token for a GitHub Enterprise Server host (1.10) |
| `WAMBATIC_CONFIG` | path | `~/.config/wambatic/config.json` | Config file path |

**Config file.** A JSON object with optional `fetch`, `stats` and `report` objects whose keys are the setting names without their prefix, for example `{"fetch": {"workers": 8}}`. The file is chosen as `config_path`, else `WAMBATIC_CONFIG`, else the default path. A missing default file means built-in defaults; a missing file named by `config_path` or `WAMBATIC_CONFIG` raises `SettingsError`.

**Overrides.** `overrides` has the same nested shape as the file, for example `{"fetch": {"workers": 8}}`, and is merged section by section over it.

**Values.** A `timedelta` setting is written as a string of a non-negative integer and one unit, `s`, `m`, `h`, `d` or `w` (`"30d"`, `"1h"`, `"0s"`); command-line flags take the same syntax. A list setting is a JSON array of strings. A `Path` setting has a leading `~` expanded with `Path.expanduser()`; environment variables are not expanded, and relative paths stay relative to the working directory.

**Errors.** An unknown section or key, a token-like key among them, a value of the wrong type, a malformed duration or a value outside a `Literal` set raises `SettingsError`. The message names the key and, for a `Literal`, the allowed values; it never echoes the value, so a token put in the wrong place is not repeated in logs.

**Version identity.** `src/wambatic/version.py` defines `VERSION`, read once by `package_version()` from the installed package metadata (`UNKNOWN_VERSION` when the source tree was never installed). The cache identity and `StatsResult.provenance` both take the version from it.

## External dependencies

- The GitHub [GraphQL](https://docs.github.com/en/graphql) and [REST](https://docs.github.com/en/rest) APIs, and since 1.11 its Git HTTPS endpoint.
- `git` 2.40 or later on `PATH`, for the bare clones (1.11, [Commit sync](../commit-sync/spec.md)).
- The libraries named under Implementation, each declared in `pyproject.toml`.
- The shared rules and skills from the agents repository, linked as the `.agents/` submodule.
