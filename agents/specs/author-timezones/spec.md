# Author timezones

**Version:** 1.0
**Status:** proposed
**Date:** 2026-11-03

Dates each commit on its author's own calendar, when the user asks for it, instead of the one report timezone. Today every record is dated by its local date in `StatsRequest.tz` (`--tz`, or `stats.timezone`), so a commit made at 09:00 on a Monday in Tokyo is a Sunday commit in a UTC report, and its author's `active_days` and the daily buckets say so. In the new `author` mode a commit's local date is taken in its author's zone: from the per-author setting `stats.author_timezones` when it names the author, else from the UTC offset git recorded on the commit, else, when the commit has no recorded offset, in the report zone, and the report names the repositories whose commits that was. Every other record (pull requests, issues, workflow runs, releases, stars, forks) stays in the report zone. The default mode, `report`, is today's behaviour, so no existing report changes until the user switches.

It lifts the limit "one timezone per report" that the [system spec](../system/spec.md) accepted for the first release, for commits.

**Prerequisite:** the [Commit sync](../commit-sync/spec.md) 1.0 code is in place (check: `python -c 'from wambatic.fetch.git import Git'`).

**Motivation.** From `TODO.md`, "A report has one timezone", found on 2026-11-02 by `/todo-review` from the system spec's accepted limits; the user chose on 2026-11-02 to lift it. Its cause: bucketing takes a single `--tz` for every author and repository. Found on 2026-11-03 while writing this spec:

- The report zone decides only each record's local date: its bucket, `active_days`, and whether it is inside `--since` and `--until`. No metric reads the hour of day or the weekday.
- Each commit's offset is discarded when it is read: `fetch/git.py` converts git's `%aI` to UTC, and `fetch/base.py`'s `timestamp()` does the same for GitHub's dates.
- Measured on 2026-11-03 on `pallets/flask`'s latest default-branch commits: GitHub returns every commit date in UTC, in GraphQL `authoredDate`, GraphQL `author { date }` (a `GitTimestamp`) and REST `commit.author.date` alike (`2026-10-30T15:05:20Z`); the bare clone gives the same commit as `2026-10-30T08:05:20-07:00`. A commit's own offset is therefore known only for repositories read by the `clone` method.

**Decisions**, answered by the user on 2026-11-03 through the question tool: an author's zone comes from the commit's own offset, with a per-author setting that overrides it; the mode is opt in, by a setting; non-commit records keep the report zone; a commit's author-local date decides both its bucket and whether it is inside `--since` and `--until`; the report title names both zones; a CLI flag overrides the mode for one run; and, once the measurement above showed that only clones keep the offset, a commit with no offset and no setting entry is dated in the report zone, and the report names its repository.

## Module location

| Module | Holds |
|--------|-------|
| `src/wambatic/fetch/base.py` | `Commit.authored_offset` |
| `src/wambatic/fetch/git.py` | `GitCommit.authored_offset`, read from `%aI` |
| `src/wambatic/fetch/cache.py` | the `commits` column `authored_offset`, `SCHEMA_VERSION` 6 |
| `src/wambatic/settings.py` | `stats.commit_timezone`, `stats.author_timezones`, `author_zones` |
| `src/wambatic/stats/engine.py` | `commit_zone`, the author-local date in `read_commits`, the `unavailable` rows and provenance keys |
| `src/wambatic/cli.py`, `src/wambatic/reports/service.py`, `src/wambatic/reports/web.py` | `--commit-tz` and the web app's `commit_tz` parameter |
| `src/wambatic/reports/terminal.py`, `src/wambatic/reports/html.py` | the title's zone text |

Tests are in the existing `src/tests/stats/test_engine.py`, `src/tests/fetch/test_git.py`, `src/tests/fetch/test_cache.py`, `src/tests/test_settings.py`, `src/tests/test_cli.py` and the report tests.

## API

```python
# fetch/base.py
@dataclasses.dataclass(frozen=True, slots=True)
class Commit:
    ...                                  # fields unchanged
    authored_offset: int | None = None   # minutes east of UTC that git recorded, None when unknown

# fetch/git.py
@dataclasses.dataclass(frozen=True, slots=True)
class GitCommit:
    oid: str
    parents: tuple[str, ...]
    authored_at: datetime.datetime       # UTC, as before
    authored_offset: int                 # from %aI's offset
    files: tuple[wambatic.fetch.base.CommitFile, ...]

# settings.py
CommitTimezone = typing.Literal['report', 'author']

class StatsSettings:
    ...
    commit_timezone: CommitTimezone = 'report'
    author_timezones: tuple[tuple[str, str], ...] = ()   # (login casefolded, IANA zone), sorted

def author_zones(settings: StatsSettings) -> dict[str, zoneinfo.ZoneInfo]:
    """`stats.author_timezones` as zones keyed by casefolded login.

    Raises:
        SettingsError: a zone is not a known IANA zone; the message names
            `stats.author_timezones.<login>` and the value.
    """

# stats/engine.py
def commit_zone(
    commit: wambatic.fetch.base.Commit,
    tz: datetime.tzinfo,
    settings: wambatic.settings.StatsSettings,
    zones: dict[str, zoneinfo.ZoneInfo],
) -> datetime.tzinfo:
    """The zone whose calendar dates `commit`: `tz` in `report` mode; in `author` mode the
    author's `stats.author_timezones` zone, else `datetime.timezone(timedelta(minutes=
    commit.authored_offset))`, else `tz` when the offset is None."""
```

`StatsRequest` is unchanged: the mode and the map are read from `request.settings`, and `--commit-tz` replaces `stats.commit_timezone` in the settings before the request is made, as `--tz` replaces `stats.timezone`.

## Error handling

- `SettingsError`: `stats.commit_timezone` is not `report` or `author` (the existing `Literal` check); `stats.author_timezones` is not a JSON object of strings (`stats.author_timezones has the wrong type`); a zone in it is unknown to `zoneinfo`, naming `stats.author_timezones.<login>` and the value. Each is raised when settings are loaded, before any sync.
- `UsageError`: `--commit-tz` is not `report` or `author`; for the web app, a 400 with the same message.
- `CacheVersionError`: a cache of schema 5 is refused, as for every earlier raise (see Implementation).
- `GitError`: a `git log` date without an offset is a date that does not parse, as today.
- No new error otherwise: a commit with no offset is not an error; it is dated in the report zone and its repository is named in `tables['unavailable']`.

## Implementation

**Keeping the offset.** `fetch/git.py` parses `%aI` with `datetime.datetime.fromisoformat` as now, and keeps `utcoffset()` in whole minutes as `GitCommit.authored_offset` before converting `authored_at` to UTC. The `clone` method copies it to `Commit.authored_offset`. The `api` and `api-files` methods leave it `None`: GitHub's dates carry no offset (measured 2026-11-03, above). `authored_at` stays UTC everywhere, so nothing that compares or orders commits changes.

**Cache.** The `commits` table gains `authored_offset INTEGER` (nullable), written and read with the commit. `SCHEMA_VERSION` becomes 6, with the same refusal as every earlier raise and no migration: a cache of 5 is refused once with the `CacheVersionError` message, and the user clears and refetches it. A clone-read repository is re-read cheaply from its clone; only the `COMMIT_AUTHORS` login lookups cost requests.

**Dating a commit.** `read_commits` computes each commit's day as `commit.authored_at.astimezone(commit_zone(commit, request.tz, settings, zones)).date()`, where `zones = author_zones(settings)` is built once per call. That day is the commit's `DatedCommit.day`, so it decides the bucket, `active_days`, the `top_contributors` row's `active_days`, and the `--since`/`--until` check, all on the author's calendar. A commit with no login (`unattributed`) uses its offset, else the report zone. The read window stays the UTC range of the requested dates widened by one day each side, which covers every real offset (UTC-12 to UTC+14). The default `until` stays today in the report zone, so in `author` mode a commit already dated tomorrow by an author east of the report zone is outside a range that ends today, until tomorrow. Bucket labels, bucket boundaries, partial buckets and every non-commit record are unchanged: they stay in the report zone.

**Repositories without offsets.** In `author` mode, `compute` adds one row to `tables['unavailable']` per repository of the subject whose commits in the range include one dated in the report zone because it had no offset and its author had no `stats.author_timezones` entry, ordered by name: `{'metric': 'commit dates: <owner/name>', 'reason': 'dated in <report zone>: GitHub gives no author offset for a repository that is not cloned; stats.author_timezones sets an author's zone'}`. The series still count those commits. In `report` mode no row is added.

**Provenance.** Stats adds `commit_timezone` (`'report'` or `'author'`) whenever `commits` is read, and in `author` mode `author_timezones`, the JSON object of the map, so two results computed with different zones say so. `timezone` keeps the report zone.

**Reports.** The terminal title's zone (today `str(tz)`) and the HTML header's become, in `author` mode, `commits in authors' zones, other events in <tz>`; in `report` mode they are unchanged. The `unavailable` rows appear in the terminal's and the HTML page's existing unavailable tables. The JSON output needs no change: `request.settings` already lists every `StatsSettings` field but `timezone`.

**CLI and web app.** `report` takes `--commit-tz report|author`, overriding `stats.commit_timezone` as `--tz` overrides `stats.timezone`. The web app's form gains a select, Commit dates: report zone (checked by default from the setting) or authors' zones, submitted as `commit_tz`, parsed by `service.make_request` as the CLI parses the flag. `serve` itself takes no new flag.

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `stats.commit_timezone` | `'report' \| 'author'` | `'report'` | `report`: every commit is dated in the report zone (`--tz`, `stats.timezone`); `author`: each commit in its author's zone. `--commit-tz` overrides it for one run |
| `stats.author_timezones` | `tuple[tuple[str, str], ...]`, a JSON object in the config file | `{}` | Login to IANA zone (`{"octocat": "Europe/London"}`), compared case-insensitively; in `author` mode it overrides a commit's recorded offset, and dates the commits of a repository with no offsets |

The config file's object is converted to pairs sorted by casefolded login, by a new `convert` branch for `tuple[tuple[str, str], ...]`, so the settings stay hashable and their JSON output is stable.

## External dependencies

None new: `zoneinfo` (standard library) resolves the zones, as it does for `stats.timezone`; git's `%aI` already gives the offset.
