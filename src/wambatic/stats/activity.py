import collections.abc
import dataclasses
import datetime
import pathlib
import typing

import wambatic.fetch.base
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.buckets

UNATTRIBUTED = 'unattributed'
TOTAL_METRICS = (
    ('commits', 'count'),
    ('contributors', 'count'),
    ('active_days', 'days'),
    ('lines_added', 'lines'),
    ('lines_deleted', 'lines'),
    ('lines_net', 'lines'),
)
BREAKDOWN_METRICS = ('commits', 'lines_added', 'lines_deleted', 'lines_net')
Tables = dict[str, list[dict[str, typing.Any]]]


class DatedCommit(typing.NamedTuple):
    """A commit with its local date in the request's timezone, derived once where it is read."""

    commit: wambatic.fetch.base.Commit
    day: datetime.date


@dataclasses.dataclass(slots=True)
class Tally:
    """What the commits of one group add up to, in one bucket or over the whole range.

    A mutable accumulator by design: the stats code adds each commit to it while it reads them.
    """

    commits: int = 0
    lines_added: int = 0
    lines_deleted: int = 0
    logins: set[str] = dataclasses.field(default_factory=set)
    days: set[datetime.date] = dataclasses.field(default_factory=set)

    def add(self, day: datetime.date, lines: tuple[int, int] | None) -> None:
        self.commits += 1
        self.days.add(day)
        if lines is not None:
            self.lines_added += lines[0]
            self.lines_deleted += lines[1]

    def value(self, metric: str) -> float:
        match metric:
            case 'commits':
                return self.commits
            case 'contributors':
                return len(self.logins)
            case 'active_days':
                return len(self.days)
            case 'lines_added':
                return self.lines_added
            case 'lines_deleted':
                return self.lines_deleted
            case _:
                return self.lines_added - self.lines_deleted


def kept_lines(
    commit: wambatic.fetch.base.Commit,
    method: str | None,
    settings: wambatic.settings.StatsSettings,
) -> tuple[int, int]:
    """The lines a commit adds and deletes. A `clone` or `api-files` commit counts the files left
    after `stats.exclude_paths` and, with `stats.linguist`, generated files; any other commit
    counts its own totals. The recorded method decides, never whether the commit has files."""
    if method not in ('clone', 'api-files'):
        return commit.additions, commit.deletions
    added = deleted = 0
    for file in commit.files:
        if settings.linguist and file.generated:
            continue
        path = pathlib.PurePosixPath(file.path)
        if any(path.full_match(pattern) for pattern in settings.exclude_paths):
            continue
        added += file.additions
        deleted += file.deletions
    return added, deleted


def series_of(
    metric: str,
    unit: str,
    buckets: list[wambatic.stats.base.Bucket],
    tallies: collections.abc.Mapping[int, Tally],
    by: str | None = None,
    by_kind: wambatic.stats.base.ByKind | None = None,
) -> wambatic.stats.base.Series:
    empty = Tally()
    values = [tallies.get(index, empty).value(metric) for index in range(len(buckets))]
    return wambatic.stats.base.series_of(metric, unit, buckets, values, by, by_kind)


def aggregate(
    commits: collections.abc.Iterable[DatedCommit],
    buckets: list[wambatic.stats.base.Bucket],
    settings: wambatic.settings.StatsSettings,
    *,
    by_author: bool,
    by_repo: bool,
    methods: collections.abc.Mapping[str, str] | None = None,
) -> tuple[list[wambatic.stats.base.Series], Tables]:
    """The activity series and tables for `commits`, which the caller has already restricted to
    the range `buckets` covers; a commit outside it raises InvalidRangeError. `methods` maps a
    repository to the method that read its commits (`api` when absent)."""
    methods = methods or {}
    bots = {login.casefold() for login in settings.bot_logins}
    starts = [bucket.start for bucket in buckets]
    end = wambatic.stats.buckets.bucket_end(buckets)
    totals = [Tally() for _ in buckets]
    authors: dict[str | None, dict[int, Tally]] = {}
    spellings: dict[str | None, str] = {}
    repos: dict[str, dict[int, Tally]] = {}
    overall: dict[str | None, Tally] = {}
    for commit, day in commits:
        index = wambatic.stats.buckets.locate(day, starts, end)
        lines = (
            None
            if settings.exclude_merge_commits and commit.is_merge
            else kept_lines(commit, methods.get(commit.repo), settings)
        )
        key = None if commit.author_login is None else commit.author_login.casefold()
        spellings.setdefault(key, UNATTRIBUTED if key is None else str(commit.author_login))
        totals[index].add(day, lines)
        if key is not None and key not in bots:
            totals[index].logins.add(key)
        overall.setdefault(key, Tally()).add(day, lines)
        if by_author:
            authors.setdefault(key, {}).setdefault(index, Tally()).add(day, lines)
        if by_repo:
            repos.setdefault(commit.repo, {}).setdefault(index, Tally()).add(day, lines)
    series = [
        series_of(metric, unit, buckets, dict(enumerate(totals))) for metric, unit in TOTAL_METRICS
    ]
    breakdowns: list[tuple[str, str, dict[int, Tally]]] = [
        ('author', spellings[key], tallies) for key, tallies in authors.items()
    ] + [('repo', name, tallies) for name, tallies in repos.items()]
    for kind, by, tallies in sorted(breakdowns, key=lambda item: (item[0], item[1])):
        for metric in BREAKDOWN_METRICS:
            unit = 'count' if metric == 'commits' else 'lines'
            series.append(series_of(metric, unit, buckets, tallies, by, kind))  # type: ignore[arg-type]
    rows: list[dict[str, typing.Any]] = [
        {
            'login': spellings[key],
            'commits': tally.commits,
            'lines_added': tally.lines_added,
            'lines_deleted': tally.lines_deleted,
            'lines_net': tally.lines_added - tally.lines_deleted,
            'active_days': len(tally.days),
        }
        for key, tally in overall.items()
        if key is None or key not in bots
    ]
    rows.sort(key=lambda row: (-row['commits'], row['login']))
    return series, {'top_contributors': rows}


def unfiltered_gaps(
    repos: collections.abc.Iterable[wambatic.fetch.base.Repo],
    methods: collections.abc.Mapping[str, str],
    settings: wambatic.settings.StatsSettings,
    *,
    branches: bool,
) -> list[dict[str, typing.Any]]:
    """The `unavailable` rows for repositories whose line counts or branches could not be
    filtered, ordered by name."""
    lines = 'lines_added, lines_deleted, lines_net'
    rows: list[dict[str, typing.Any]] = []
    for name in sorted(repo.name_with_owner for repo in repos):
        method = methods.get(name)
        if method == 'api':
            rows.append(
                {
                    'metric': f'{lines}: {name}',
                    'reason': 'generated files are counted: the repository is not cloned '
                    '(public repositories, and those fetch.clone_repos allows, are cloned; '
                    'fetch.api_history files reads per-file counts by API)',
                }
            )
            if branches:
                rows.append(
                    {
                        'metric': f'commits: {name}',
                        'reason': 'default branch only: the repository is not cloned and '
                        'fetch.api_history is totals',
                    }
                )
        elif method == 'api-files' and settings.linguist:
            rows.append(
                {
                    'metric': f'{lines}: {name}',
                    'reason': 'linguist attributes not read: the repository is not cloned; '
                    'stats.exclude_paths applies',
                }
            )
    return rows
