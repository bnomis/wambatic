# Reports

**Version:** 1.15
**Status:** implemented
**Date:** 2026-11-03

The three ways a user sees a `StatsResult`: a terminal report, a self-contained static HTML report, and a local web app. All three render the same result object, so they never disagree. It also defines the `wambatic` command line.

**Prerequisites:** [Fetch](../fetch/spec.md), [Cache](../cache/spec.md) and [Stats](../stats/spec.md) are implemented (check: `python -c 'import wambatic.stats'`).

Version 1.2 settles what step 5 of the [implementation order](../implementation-order.md) (terminal report and CLI) needed; the gaps and the choices made are in [review-1.md](review-1.md). Version 1.3 adds the terminal's flow sections for step 6 (flow data and stats); the choices are in the [stats review 2](../stats/review-2.md). Version 1.4 settles what step 7 (static HTML report) needed: the figure type, the results the page is built from, the page layout, themes and palette, the output path and the browser test; the choices are in [review-2.md](review-2.md). Version 1.5 adds the delivery sections of the terminal and the HTML page, and the release and workflow-run counts of `cache info`, for step 8 (delivery data and stats); the choices are in the [stats review 3](../stats/review-3.md). Version 1.6 settles what step 9 (local web app) needed: the server library (FastAPI with uvicorn, chosen 2026-10-30), the sync jobs and progress page that keep a large org from blocking the page, the query parameters and statuses, `serve`'s flags, the loopback and `Host` checks, and the move of the CLI's sync-then-compute code to `service.py` so the web app can share it; the choices are in [review-3.md](review-3.md). Version 1.7 adds the popularity sections of the terminal and the HTML page (the languages chart among them), the star and fork counts of `cache info`, and `popularity` in the `--groups` help, for step 10 (popularity data and stats); the choices are in the [stats review 4](../stats/review-4.md). Version 1.8 states that a repository whose star history is not visible to the token appears in Unavailable in every front end. Version 1.9 builds an HTML report from one read of the cache (`sync_and_compute` calls the stats `compute_all`) and builds each figure, table and series list of the page once; the choice is Decision 3 (option B) of the [audit review 1](../../audit-reviews/review-1.md), answered 2026-10-31.

Version 1.10 makes every error `wambatic.reports` raises itself a `ReportsError` (`UsageError`, `OutputError` and `ServeError`): `build_range_figures`, `build_calendar` and `html_document` raise `UsageError` where they raised `ValueError`; the choice is [audit review 1](../../audit-reviews/review-1.md), Decision 2 (option B), answered 2026-10-31.

Version 1.11 brings the spec in line with the code after [audit review 1](../../audit-reviews/review-1.md) (F9, F10): the Languages table and chart end in one `Other` row, `SyncJob` stores `phase`, and `redact_error` is listed.

Version 1.12 corrects the text to the code after [audit review 2](../../audit-reviews/review-2.md) (G15): `inspect_cache`, `OutputError` and `ServeError` in the error table and the binding paragraph, the `--since`, `--until` and `--groups` refusals, and `redact_error` in the module table.

Version 1.13 splits this spec, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked, on 2026-11-02. Each front end has its own spec, with its text moved there and only its cross-references updated: the [CLI](../cli/spec.md) (the command line, its flags and exit statuses), the [Terminal report](../terminal-report/spec.md), the [HTML report](../html-report/spec.md) (figures, the page, palette and browser test) and the [Web app](../web-app/spec.md). This spec keeps what they share: the module layout and its import rules, the errors, the JSON output, `service.py`, the settings and the dependencies.

Version 1.14 adds the Enterprise host to the `AuthError` message rule, for GitHub Enterprise Server ([Fetch](../fetch/spec.md) 1.16, [fetch review 1](../fetch/review-1.md)).

Version 1.15 applies the `--commit-tz` and `commit_tz` override to the settings before `make_request` ([Author timezones](../author-timezones/spec.md)); the choices are in the [author timezones review 1](../author-timezones/review-1.md), decided 2026-11-03.

## Module location

`src/wambatic/cli.py` (command line), `src/wambatic/__main__.py` (`python -m wambatic`), `src/wambatic/reports/`, with tests in `src/tests/reports/` (the headless-browser test in `src/tests/reports/test_html_browser.py`), `src/tests/test_cli.py` and fixtures in `src/tests/fixtures/reports.py`:

| Module | Holds | Built in implementation step |
|--------|-------|------------------------------|
| `errors.py` | `ReportsError`, `UsageError`, `OutputError`, `ServeError` | 5 |
| `base.py` | `result_to_dict`, `render_json` | 5 |
| `terminal.py` | `render_terminal`, `sparkline` | 5 |
| `rows.py` | the table rows both the terminal and the HTML page show (moved out of `terminal.py`) | 7 |
| `figures.py` | `Figure`, `build_figures`, `build_range_figures`, `build_calendar`, `PALETTE` | 7 |
| `html.py`, `templates/` (`report.html`, `report.css`, `report.js`) | `HtmlReport`, `html_document`, `render_html`, `report_filename` | 7 |
| `service.py` | `parse_target`, `parse_date`, `make_request`, `resolve_tz`, `check_by_author`, `make_fetcher`, `needs_sync`, `log_sync`, `sync_and_compute`, `redact_environment_token` (moved out of `cli.py`), `redact_error` | 9 |
| `web.py`, `templates/` (`form.html`, `progress.html`, `progress.js`, `message.html`) | `SyncJob`, `Jobs`, `make_app`, `is_loopback`, `warn_on_bind`, `serve` | 9 |

`wambatic.cli` is the composition root: it is the one module that imports every layer (settings, logs, fetch, stats, reports). `wambatic.reports` imports `wambatic.stats`, `wambatic.settings` and `wambatic.version`; only `wambatic.reports.service` and `wambatic.reports.web`, which sync on the CLI's and the web app's behalf, also import `wambatic.fetch` (review-3.md choice 2), and no reports module imports `wambatic.cli`; renderers read `result.subject` through `StatsResult` without importing it. Of the third-party libraries, only `html.py` imports `plotly`, and only for the plotly.js it bundles (`plotly.offline.get_plotlyjs()`); figures are plain Plotly JSON built by wambatic's own typed code (review-2.md decision 1).

## API

The parts every front end uses; each front end's own API is in its spec.

```python
import typing

def result_to_dict(result: StatsResult) -> dict[str, object]:
    """The result as JSON-ready data (see JSON output); shared by --format json and /api/stats."""
def render_json(result: StatsResult, stream: typing.TextIO) -> None:
    """`json.dumps(result_to_dict(result), indent=2, ensure_ascii=False)` and a newline."""

# service.py: the sync-then-compute pipeline the CLI and the web app share
def parse_target(text: str) -> Subject | str:
    """A `Subject`, or a bare NAME's login for `sync_and_compute` to resolve; UsageError otherwise."""
def parse_date(text: str, flag: str = 'a date') -> datetime.date: ...
def make_request(
    by: str, since: str | None, until: str | None, groups: str | None, by_author: bool,
    settings: Settings, today: datetime.datetime,
) -> StatsRequest:
    """The `StatsRequest` of the computing flags or query parameters; the zone is
    `settings.stats.timezone` (a `--tz` or `tz` override, and since 1.15 a `--commit-tz` or `commit_tz` override of `stats.commit_timezone`, is applied to `settings` first);
    UsageError on a bad value."""
def resolve_tz(settings: Settings) -> zoneinfo.ZoneInfo: ...
def check_by_author(subject: Subject) -> None: ...
def make_fetcher(token: str, cache: Cache, settings: FetchSettings) -> Fetcher: ...
def needs_sync(provenance: dict[str, str], resources: frozenset[str], settings: FetchSettings,
               full_refresh: bool, no_fetch: bool, now: datetime.datetime) -> bool: ...
def log_sync(report: SyncReport) -> None: ...
async def sync_and_compute(
    settings: Settings, cache: Cache, target: Subject | str, requests: list[StatsRequest], *,
    full_refresh: bool, no_fetch: bool, sync: bool | None = None,
    progress: SyncProgress | None = None,
    clock: Callable[[], datetime.datetime] = utc_now,
) -> tuple[Subject, list[StatsResult]]:
    """Resolve a bare NAME, sync when `sync` is True (or, when None, when `needs_sync` says so),
    then compute every request (`by_author` is read from `requests[0]`) with one `stats.compute_all`, so the cache is read once however
    many requests there are; the network is used only to resolve or sync."""
def redact_environment_token(text: str) -> str: ...
def redact_error(error: BaseException) -> str:
    """The message of `error` without the environment's token, which is also removed from the
    args of `error` and of what it was raised from, so a logged traceback cannot carry it."""

class ReportsError(Exception):
    """Base class of every error `wambatic.reports` raises itself."""

class UsageError(ReportsError):
    """A command line that parses but cannot be run; exit status 2."""

class OutputError(ReportsError):
    """A report that was built but could not be written; exit status 1."""

class ServeError(ReportsError):
    """A web app that cannot listen on its address; exit status 1."""
```

## Error handling

Each front end converts errors once: the exit statuses are in the [CLI](../cli/spec.md) spec and the HTTP statuses in the [Web app](../web-app/spec.md) spec. In both:

- Messages state the fix: `AuthError` says to set `GITHUB_TOKEN` or run `gh auth login` when there is no token (for an Enterprise host, `GH_ENTERPRISE_TOKEN` or `gh auth login --hostname HOST`), `GitHub rejected the token (401)` for a 401 and `GitHub denied access (403)` with the reason for a 403; `RateLimitError` gives the reset time, `CacheVersionError` names `wambatic cache clear` and `--ignore-cache-version`, and `EmptySubjectError` with `--no-fetch` adds that the cache may only need a sync. These texts come from the errors themselves where they already carry them.
- No message repeats a token or a config value (system spec, Settings).

## Implementation

**One result, three renderers.** Rendering is a pure function of `StatsResult` (for HTML, of the five results of one request that differ only in granularity). Only `--format` and the command select a renderer; there is no per-renderer metric logic, and the table rows the terminal and HTML share are built once in `rows.py`. There is no `Renderer` protocol: the CLI dispatches on the format, and the HTML renderer takes several results, so a one-result protocol would have no caller (review-2.md).

**JSON output.** `--format json` writes `render_json(result, sys.stdout)` (the one place output bypasses loguru). `result_to_dict` returns, in this key order:

- `format_version`: `1`, raised whenever a key below changes meaning, per the shared versions rule;
- `subject`: `{"kind", "login", "name"}`;
- `request`: `{"granularity", "groups" (sorted list), "since", "until" (ISO date or null, as requested), "by_author", "tz" (`str(tz)`), "settings"}`, where `settings` is every `StatsSettings` field except `timezone` (`tz` is the one zone) with tuples as lists and durations as `"<total seconds>s"`, which the settings parser reads back;
- `since`, `until`: the resolved range as ISO dates;
- `series`: one object per series in result order, `{"metric", "unit", "by", "by_kind", "points"}`, with `points` a list of `{"label", "start", "value"}` in bucket order; a value whose unit is `count`, `days` or `lines` is an integer, any other a float;
- `tables` and `provenance`: as in the result.

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `report.allow_remote` | `bool` | `False` | Permit the web app on non-loopback hosts |
| `report.format` | `Literal['html', 'json', 'terminal']` | `'terminal'` | Default report format |
| `report.html_theme` | `Literal['auto', 'dark', 'light']` | `'auto'` | HTML theme; `auto` follows the viewer's system setting |
| `report.out_dir` | `Path` | `./wambatic-reports` | Default HTML output directory, used when `--out` is absent |
| `report.web_host` | `str` | `'127.0.0.1'` | Web app bind address |
| `report.web_port` | `int` | `8000` | Web app port |

Settings load from a JSON file (`~/.config/wambatic/config.json`) and are overridden by flags. The token is deliberately not a setting.

## External dependencies

- [Plotly](https://plotly.com/python/), [Rich](https://rich.readthedocs.io/), [cappa](https://cappa.readthedocs.io/) (the shared Python rules name cappa for CLI definitions), `loguru`, and [FastAPI](https://fastapi.tiangolo.com/) with [uvicorn](https://www.uvicorn.org/) for the web app (review-3.md decision 1), without their `standard` extras. FastAPI, Starlette and uvicorn ship `py.typed` (checked on 2026-10-30), so no mypy override is added.
- Plotly ships no type information (no `py.typed`, checked on 7.1.0 on 2026-10-30), so `pyproject.toml` gains a mypy override with `ignore_missing_imports` for `plotly` and `plotly.*` only, and the one call `html.py` makes is wrapped in `str(...)` (review-2.md decision 1).
- Development only: [Playwright for Python](https://playwright.dev/python/) for the headless-browser test (step 7), and [HTTPX](https://www.python-httpx.org/) for the web tests' ASGI client (step 9).
- Maintenance status of each is to be checked before `uv add`, per the shared tools-and-libraries rule; alternatives noted if a check fails: Altair for Plotly, Typer for cappa.
