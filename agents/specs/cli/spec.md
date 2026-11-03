# CLI

**Version:** 1.3
**Status:** proposed
**Date:** 2026-11-03

The `wambatic` command line: its commands and flags, the order `report` runs in, the `cache` commands, and the one place every error becomes an exit status. Part of [Reports](../reports/spec.md), which holds what the front ends share.

Version 1.0 is the reports spec 1.12 text moved here, with only its cross-references updated, when that spec was split on 2026-11-02, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked. `review-N.md` in the text below means the [reports reviews](../reports/review-1.md) in `agents/specs/reports/`.

Version 1.1 adds `--github-host` to `report`, `serve` and `cache`, for GitHub Enterprise Server ([Fetch](../fetch/spec.md) 1.16); the choices are in the [fetch review 1](../fetch/review-1.md), decided 2026-11-02.

Version 1.2 has `cache clear` remove the bare clones with the file, and `cache info` report the commit file rows and the clones' size, for the clone-based commit sync ([Commit sync](../commit-sync/spec.md)); the choices are in the [commit sync review 1](../commit-sync/review-1.md), decided 2026-11-02.

Version 1.3 adds `--commit-tz` to `report` ([Author timezones](../author-timezones/spec.md)); the choices are in the [author timezones review 1](../author-timezones/review-1.md), decided 2026-11-03.

**Prerequisites:** [Reports](../reports/spec.md), [Terminal report](../terminal-report/spec.md), [HTML report](../html-report/spec.md) and [Web app](../web-app/spec.md), whose renderers it dispatches to.

## Module location

`src/wambatic/cli.py` (command line) and `src/wambatic/__main__.py` (`python -m wambatic`), with tests in `src/tests/test_cli.py`. `wambatic.cli` is the composition root (see the [Reports](../reports/spec.md) module location).

## API

```python
def main(argv: list[str] | None = None) -> int:
    """Parse `argv` (default `sys.argv[1:]`), run the command, convert errors once (see Error
    handling) and return the exit status. Never calls `sys.exit`."""

def run() -> None:
    """The `wambatic` console script and `python -m wambatic`: `sys.exit(main())`."""
```

Command line (`wambatic <command> <target>`):

```text
wambatic [-v | -q] report <target> [--format terminal|html|json] [--out PATH]
                         [--by year|month|week|day|total] [--since DATE] [--until DATE]
                         [--groups activity,flow,delivery,popularity] [--by-author] [--tz ZONE]
                         [--full-refresh | --no-fetch] [--max-age DURATION]
                         [--ignore-cache-version] [--github-host HOST]
wambatic [-v | -q] serve  [<target>] [--host 127.0.0.1] [--port 8000] [--allow-remote]
                         [--max-age DURATION] [--ignore-cache-version]
wambatic [-v | -q] cache  clear|info [--github-host HOST]
```

The CLI is defined with [cappa](https://cappa.readthedocs.io/) dataclasses, as the shared Python rules require: a root command holding `-v`/`--verbose` and `-q`/`--quiet` and a `cappa.Subcommands` field of the `report`, `serve` and `cache` command classes. Step 5 built `report` (without `--format html` and `--out`) and `cache`; step 7 added `--format html` and `--out`, and step 9 adds `serve`.

**Flags.**

- `<target>` is `user:NAME`, `org:NAME` or `repo:OWNER/NAME`. Bare `OWNER/NAME` means a repo, and bare `NAME` is resolved with `Fetcher.owner_kind`, which asks GitHub whether the login is a user or an organisation (user and organisation logins share one namespace on GitHub, so a name is never both). A `NAME` or `OWNER` is 1 to 39 characters of ASCII letters, digits and `-`; a repo `NAME` is 1 to 100 characters of ASCII letters, digits, `.`, `_` and `-`. Anything else, including an empty part, an unknown prefix or more than one `/`, is a `UsageError`. Bare `NAME` with `--no-fetch` is a `UsageError` asking for `user:NAME` or `org:NAME`, since resolving it needs the network.
- `--by` maps to `StatsRequest.granularity` (`total` is `Granularity.TOTAL`); default `month`. With `--format html` it picks the granularity the page shows on load, and `total` is a `UsageError` (the page's summary tiles are the totals; its switch offers year, month, week and day).
- `--since` and `--until` are local dates `YYYY-MM-DD` exactly (no other ISO forms), both inclusive, in the report timezone; anything else is a `UsageError`. `--since` before 2008-01-01 and `--until` after tomorrow in the report timezone are also a `UsageError`.
- `--groups` is a comma-separated list of `activity`, `flow`, `delivery` and `popularity`; default `activity,flow`, as `StatsRequest`. An empty list is a `UsageError`. Its help text, the web app's `groups` parameter description and the form's hint name every group. An unknown name is passed through to `compute`, which raises `UnknownGroupError`.
- `--by-author` sets `StatsRequest.by_author`; with a user target, after any bare-`NAME` resolution, it is a `UsageError`.
- `--tz` overrides `stats.timezone`; the zone is resolved with `zoneinfo.ZoneInfo`, and an unknown zone from either source is a `SettingsError` naming `stats.timezone`.
- `--commit-tz report|author` (1.3) overrides `stats.commit_timezone` for one run, as `--tz` overrides `stats.timezone`: `author` dates each commit in its author's zone ([Author timezones](../author-timezones/spec.md)); another value is a `UsageError`.
- `--out PATH` is where `--format html` writes: a file path, or an existing directory to write `report_filename(subject)` into. Without it the file is `report.out_dir / report_filename(subject)`. Missing parent directories are created and an existing file is replaced. `--out` with a format other than `html` (after the config file) is a `UsageError`.
- `--format` overrides `report.format`; `--max-age` overrides `fetch.max_age` in the settings duration syntax (`30m`, `1d`), so a malformed value is a `SettingsError`. Flags reach `Settings` only through `load_settings(None, overrides)`.
- `--full-refresh` passes `full_refresh=True` to `Fetcher.sync` and ignores `--max-age`. `--no-fetch` skips the network entirely. The two together are a `UsageError`.
- `--ignore-cache-version` opens the cache with `Cache.open(..., ignore_version=True)`, as `CacheVersionError`'s message tells the user to; provenance then records it.
- `-v` sets the log level to `DEBUG`, `-q` to `WARNING`; the default is `INFO`. Both together are a `UsageError`. Logs go to stderr, as `{level}: {message}` at `INFO` and `WARNING` and in loguru's default format (time and source location) at `DEBUG`, through `wambatic.logs.configure_logging`; reports go to stdout.
- `serve`'s `<target>` is optional and parsed as `report`'s, at start-up (a bad one is a `UsageError`); it fills the form's default and the start-up line names its report URL. `--host`, `--port` and `--allow-remote` override `report.web_host`, `report.web_port` and `report.allow_remote`; a port outside 1 to 65535 is a `UsageError`. `--max-age` and `--ignore-cache-version` are as for `report` (review-3.md choice 9).
- `--github-host HOST` (1.1) overrides `fetch.github_host` for `report`, `serve` and `cache`; the setting's checks apply, so a bad host is a `SettingsError`. It is not `--host`, which `serve` already uses for its bind address. `cache clear` and `cache info` act on that host's cache file (`cache_path_for`, [Cache](../cache/spec.md)).
- The config file is chosen as the system spec says (`WAMBATIC_CONFIG`, else the default path); there is no `--config` flag.

**Running `report`.** In this order:

1. Configure logging, load settings with the flag overrides, parse the target, and check the flag combinations above; nothing touches the cache or the network before these pass.
2. Open the cache at `fetch.cache_path`.
3. Decide whether to sync. The resources are `resources_for(groups) & BUILT_RESOURCES` (fetch spec): resources whose step is not built are never synced, so the default groups run before step 6. There is no sync when `--no-fetch` is given, when the resources are empty, or when `fetch.max_age` is above zero, `--full-refresh` is absent and every `fetched_at:<resource>` in `Fetcher.provenance(subject, resources)` is a time less than `max_age` before now. Otherwise sync.
4. Only when a sync or a bare-`NAME` resolution is needed, resolve the token with `fetch_token()` and enter the `Fetcher` (which opens the aiohttp session). Otherwise the `Fetcher` is built with an empty token and never entered, so no session is opened and no request can be made; a warm cache with `--no-fetch` or a fresh `--max-age` needs no `GITHUB_TOKEN`.
5. Sync, logging one `info` line from the `SyncReport`: repositories listed, unchanged, the rows written for each resource synced (`commits 12, issues 3, pull_requests 5`) and any full refetches.
6. `compute`, then render to stdout with the selected format. For `html`, `compute_all` computes five requests from one read of the synced cache, with the request's granularity set to `TOTAL`, `YEAR`, `MONTH`, `WEEK` and `DAY` and everything else unchanged, giving the `HtmlReport`; `render_html` writes the file with `report.html_theme`, and the path written is printed to stdout as one line (the report itself is the file).

**`cache info`** prints, for `fetch.cache_path`, what `inspect_cache` (fetch spec) returns: the path and size, the recorded identity and every key that differs from the running code (with both values), `version_override_at` when set, the number of repositories, commits, pull requests, issues, releases, workflow runs, star events and forks, and the latest sync time. It opens the file read-only and never creates, migrates or stamps it, so it works on a cache that `report` refuses. A missing file prints that there is no cache at the path and exits 0.

**`cache clear`** deletes the cache file and its `-wal` and `-shm` files, and since 1.2 the host's clones directory (`clones_dir_for`), with `clear_cache` ([Cache](../cache/spec.md)), logs each path removed at `info`, and exits 0 when there was nothing to remove. It does not prompt: the cache is derived data that the next `report` refetches.

## Error handling

`main` converts every error once, logging a one-line message with `loguru.logger.error` and no traceback unless stated:

| Raised | Exit status |
|--------|-------------|
| success, and `--help` | 0 |
| any `FetchError` (`AuthError`, `CacheVersionError`, `GraphQLError`, `NotFoundError`, `RateLimitError`, `StatsPendingError`) | 1 |
| any `StatsError` (`EmptySubjectError`, `InvalidRangeError`, `InvalidRequestError`, `UnknownGroupError`) | 1 |
| `OutputError` writing `--out` (step 7), or `ServeError` binding `serve`'s port (step 9); both are `ReportsError`s | 1 |
| `BrokenPipeError` (the reader of stdout went away): no message | 1 |
| any other exception: logged with `loguru.logger.exception` (traceback included) | 1 |
| `UsageError`, `SettingsError`, and a command line cappa cannot parse (cappa prints its own message) | 2 |
| `KeyboardInterrupt`: no message | 130 |

The rules every front end follows for messages are in [Reports](../reports/spec.md), Error handling.
