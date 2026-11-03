import collections.abc
import dataclasses
import datetime
import json
import types
import typing
import zoneinfo

import wambatic.fetch.base
import wambatic.settings
import wambatic.stats.activity
import wambatic.stats.base
import wambatic.stats.buckets
import wambatic.stats.delivery
import wambatic.stats.errors
import wambatic.stats.flow
import wambatic.stats.popularity

RESOURCES_BY_GROUP = types.MappingProxyType(
    {
        'activity': frozenset({'commits'}),
        'delivery': frozenset({'pull_requests', 'releases', 'workflow_runs'}),
        'flow': frozenset({'issues', 'pull_requests'}),
        'popularity': frozenset({'forks', 'star_events'}),
    }
)


def resources_for(groups: frozenset[str]) -> frozenset[str]:
    """The fetch resources the groups read, for the caller's Fetcher.sync before compute.

    Raises:
        UnknownGroupError: a group is outside `GROUPS`.
    """
    unknown = sorted(groups - wambatic.stats.base.GROUPS)
    if unknown:
        raise wambatic.stats.errors.UnknownGroupError(f'unknown groups: {", ".join(unknown)}')
    return frozenset().union(*(RESOURCES_BY_GROUP[group] for group in groups))


def utc_midnight(day: datetime.date) -> datetime.datetime:
    return datetime.datetime.combine(day, datetime.time(), tzinfo=datetime.UTC)


def commit_zone(
    commit: wambatic.fetch.base.Commit,
    tz: datetime.tzinfo,
    settings: wambatic.settings.StatsSettings,
    zones: collections.abc.Mapping[str, zoneinfo.ZoneInfo],
) -> datetime.tzinfo:
    """The zone that dates `commit`: `tz` in `report` mode; in `author` mode the zone set for its
    author, else the offset recorded with the commit, else `tz`."""
    if settings.commit_timezone == 'report':
        return tz
    zone = zones.get((commit.author_login or '').casefold())
    if zone is not None:
        return zone
    if commit.authored_offset is not None:
        return datetime.timezone(datetime.timedelta(minutes=commit.authored_offset))
    return tz


def commit_date_gaps(
    commits: collections.abc.Iterable[wambatic.stats.activity.DatedCommit],
    tz: datetime.tzinfo,
    settings: wambatic.settings.StatsSettings,
) -> list[dict[str, typing.Any]]:
    """One `unavailable` row per repository with a commit dated in the report zone in `author`
    mode for want of an offset and a setting entry, ordered by name."""
    if settings.commit_timezone != 'author':
        return []
    zones = wambatic.settings.author_zones(settings)
    names = sorted(
        {
            dated.commit.repo
            for dated in commits
            if dated.commit.authored_offset is None
            and (dated.commit.author_login or '').casefold() not in zones
        }
    )
    return [
        {
            'metric': f'commit dates: {name}',
            'reason': f'dated in {tz}: GitHub gives no author offset for a repository that is '
            "not cloned; stats.author_timezones sets an author's zone",
        }
        for name in names
    ]


async def read_commits(
    subject: wambatic.fetch.base.Subject,
    fetcher: wambatic.fetch.base.Fetcher,
    repos: list[wambatic.fetch.base.Repo],
    request: wambatic.stats.base.StatsRequest,
) -> list[wambatic.stats.activity.DatedCommit]:
    """The cached commits whose local date is inside the requested bounds, each with that date,
    from the subject's own authors only for a user subject."""
    lo = (
        None
        if request.since is None
        else utc_midnight(request.since) - wambatic.stats.buckets.ONE_DAY
    )
    hi = (
        None
        if request.until is None
        else utc_midnight(request.until + wambatic.stats.buckets.ONE_DAY)
        + wambatic.stats.buckets.ONE_DAY
    )
    login = subject.login.casefold()
    zones = wambatic.settings.author_zones(request.settings)
    kept: list[wambatic.stats.activity.DatedCommit] = []
    for repo in repos:
        async for commit in fetcher.commits(repo, lo, hi):
            zone = commit_zone(commit, request.tz, request.settings, zones)
            day = commit.authored_at.astimezone(zone).date()
            if request.since is not None and day < request.since:
                continue
            if request.until is not None and day > request.until:
                continue
            if subject.kind == 'user' and (commit.author_login or '').casefold() != login:
                continue
            kept.append(wambatic.stats.activity.DatedCommit(commit, day))
    return kept


async def read_flow(
    subject: wambatic.fetch.base.Subject,
    fetcher: wambatic.fetch.base.Fetcher,
    repos: list[wambatic.fetch.base.Repo],
    request: wambatic.stats.base.StatsRequest,
) -> tuple[list[wambatic.fetch.base.PullRequest], list[wambatic.fetch.base.Issue]]:
    """The cached pull requests and issues updated since a day before the requested start (every
    event of an item is at or before its `updated_at`), from the subject's own items only for a
    user subject. The flow aggregation keeps the events whose local date is in the range."""
    lo = (
        None
        if request.since is None
        else utc_midnight(request.since) - wambatic.stats.buckets.ONE_DAY
    )
    login = subject.login.casefold()

    def wanted(author: str | None) -> bool:
        return subject.kind != 'user' or (author or '').casefold() == login

    pulls: list[wambatic.fetch.base.PullRequest] = []
    issues: list[wambatic.fetch.base.Issue] = []
    for repo in repos:
        pulls.extend([p async for p in fetcher.pull_requests(repo, lo) if wanted(p.author_login)])
        issues.extend([i async for i in fetcher.issues(repo, lo) if wanted(i.author_login)])
    return pulls, issues


async def read_delivery(
    fetcher: wambatic.fetch.base.Fetcher,
    repos: list[wambatic.fetch.base.Repo],
    request: wambatic.stats.base.StatsRequest,
) -> tuple[
    list[wambatic.fetch.base.WorkflowRun],
    list[wambatic.fetch.base.Release],
    list[wambatic.fetch.base.PullRequest],
]:
    """Every cached release and pull request of the subject's repositories, and the runs created
    since a day before the requested start (all of them when `since` is None or a deploy workflow
    is set, since deployments are then runs and a lead time reaches back). No author filter: a
    release ships the repository's work, not one author's."""
    lo = (
        None
        if request.since is None or request.settings.deploy_workflow is not None
        else utc_midnight(request.since) - wambatic.stats.buckets.ONE_DAY
    )
    runs: list[wambatic.fetch.base.WorkflowRun] = []
    releases: list[wambatic.fetch.base.Release] = []
    pulls: list[wambatic.fetch.base.PullRequest] = []
    for repo in repos:
        runs.extend([run async for run in fetcher.workflow_runs(repo, lo)])
        releases.extend([release async for release in fetcher.releases(repo)])
        pulls.extend([pull async for pull in fetcher.pull_requests(repo, None)])
    return runs, releases, pulls


async def read_popularity(
    fetcher: wambatic.fetch.base.Fetcher,
    repos: list[wambatic.fetch.base.Repo],
    states: collections.abc.Mapping[tuple[str, str], wambatic.fetch.base.SyncState | None],
) -> tuple[
    list[wambatic.fetch.base.StarEvent],
    list[wambatic.fetch.base.Fork],
    list[wambatic.fetch.base.Repo],
]:
    """Every cached star and fork of the subject's repositories, since a cumulative count reaches
    back before any range, and the repositories whose stargazers the token could not see (their
    stars are left out), read from the `star_events` sync `states` the caller holds. No author
    filter: a star is given to a repository, not to an author."""
    stars: list[wambatic.fetch.base.StarEvent] = []
    forks: list[wambatic.fetch.base.Fork] = []
    hidden: list[wambatic.fetch.base.Repo] = []
    for repo in repos:
        if wambatic.fetch.base.hides_stars(states[repo.name_with_owner, 'star_events']):
            hidden.append(repo)
        else:
            stars.extend([star async for star in fetcher.star_events(repo)])
        forks.extend([fork async for fork in fetcher.forks(repo)])
    return stars, forks, hidden


@dataclasses.dataclass(frozen=True, slots=True)
class CachedRecords:
    """What `read_records` reads from the cache for one subject and one request, before the range
    is resolved. Nothing in it depends on the request's granularity."""

    repos: tuple[wambatic.fetch.base.Repo, ...]
    commits: tuple[wambatic.stats.activity.DatedCommit, ...]
    pulls: tuple[wambatic.fetch.base.PullRequest, ...]
    issues: tuple[wambatic.fetch.base.Issue, ...]
    runs: tuple[wambatic.fetch.base.WorkflowRun, ...]
    releases: tuple[wambatic.fetch.base.Release, ...]
    delivery_pulls: tuple[wambatic.fetch.base.PullRequest, ...]
    stars: tuple[wambatic.fetch.base.StarEvent, ...]
    forks: tuple[wambatic.fetch.base.Fork, ...]
    hidden: tuple[wambatic.fetch.base.Repo, ...]
    provenance: types.MappingProxyType[str, str]
    commit_methods: types.MappingProxyType[str, str] = types.MappingProxyType({})


async def read_records(
    subject: wambatic.fetch.base.Subject,
    fetcher: wambatic.fetch.base.Fetcher,
    request: wambatic.stats.base.StatsRequest,
) -> CachedRecords:
    """Validate the request and read what its groups need from the cache, with the fetch
    provenance. The only part of `compute` that touches the cache.

    Raises:
        UnknownGroupError: a group is outside `GROUPS`.
        InvalidRequestError: `by_author` is set for a user.
        InvalidRangeError: `since` is after `until`.
        EmptySubjectError: no group is requested, or the cache holds no repositories.
        CacheError: the cache cannot be read.
    """
    resources = resources_for(request.groups)
    if request.by_author and subject.kind == 'user':
        raise wambatic.stats.errors.InvalidRequestError('by_author is not meaningful for a user')
    if request.since is not None and request.until is not None and request.since > request.until:
        raise wambatic.stats.errors.InvalidRangeError(
            f'since {request.since} is after until {request.until}'
        )
    built = request.groups
    if not built:
        raise wambatic.stats.errors.EmptySubjectError(
            'no requested group: name at least one metric group'
        )
    repos = await fetcher.repos(subject)
    if not repos:
        raise wambatic.stats.errors.EmptySubjectError(
            f'the cache holds no repositories for {subject.login}'
        )
    states = await fetcher.sync_states(repos, resources)
    commits: list[wambatic.stats.activity.DatedCommit] = []
    pulls: list[wambatic.fetch.base.PullRequest] = []
    issues: list[wambatic.fetch.base.Issue] = []
    runs: list[wambatic.fetch.base.WorkflowRun] = []
    releases: list[wambatic.fetch.base.Release] = []
    delivery_pulls: list[wambatic.fetch.base.PullRequest] = []
    stars: list[wambatic.fetch.base.StarEvent] = []
    forks: list[wambatic.fetch.base.Fork] = []
    hidden: list[wambatic.fetch.base.Repo] = []
    if 'activity' in built:
        commits = await read_commits(subject, fetcher, repos, request)
    if 'flow' in built:
        pulls, issues = await read_flow(subject, fetcher, repos, request)
    if 'delivery' in built:
        runs, releases, delivery_pulls = await read_delivery(fetcher, repos, request)
    if 'popularity' in built:
        stars, forks, hidden = await read_popularity(fetcher, repos, states)
    provenance = await fetcher.provenance(subject, resources, repos, states)
    commit_methods: dict[str, str] = {}
    if 'activity' in built:
        for repo in repos:
            state = states[repo.name_with_owner, 'commits']
            if state is not None:
                commit_methods[repo.name_with_owner] = wambatic.fetch.base.parse_commit_probe(
                    state.probe
                ).method
    return CachedRecords(
        repos=tuple(repos),
        commits=tuple(commits),
        pulls=tuple(pulls),
        issues=tuple(issues),
        runs=tuple(runs),
        releases=tuple(releases),
        delivery_pulls=tuple(delivery_pulls),
        stars=tuple(stars),
        forks=tuple(forks),
        hidden=tuple(hidden),
        provenance=types.MappingProxyType(dict(provenance)),
        commit_methods=types.MappingProxyType(commit_methods),
    )


# auditme: accept[raises-section-drift] bucket_start is only called for non-TOTAL
def aggregate(
    subject: wambatic.fetch.base.Subject,
    records: CachedRecords,
    request: wambatic.stats.base.StatsRequest,
    now: datetime.datetime,
) -> wambatic.stats.base.StatsResult:
    """Resolve the range against `now` and build every series, table and the stats provenance.
    Pure: `records` must come from `read_records` of a request that differs from this one in
    granularity at most.

    Raises:
        InvalidRangeError: the range resolves backwards.
        EmptySubjectError: there are no records of any requested group in the range.
    """
    built = request.groups
    commits = list(records.commits)
    pulls = list(records.pulls)
    issues = list(records.issues)
    runs = list(records.runs)
    releases = list(records.releases)
    delivery_pulls = list(records.delivery_pulls)
    stars = list(records.stars)
    forks = list(records.forks)
    hidden = list(records.hidden)
    repos = list(records.repos)
    empty = wambatic.stats.errors.EmptySubjectError(
        f'no {" or ".join(sorted(built))} records in the cache for this range'
    )
    popularity = 'popularity' in built
    if not (commits or pulls or issues or runs or releases or popularity):
        raise empty
    tz = request.tz
    granularity = request.granularity
    until = request.until if request.until is not None else now.astimezone(tz).date()
    since = request.since
    if since is None:
        moments = [pull.created_at for pull in pulls] + [issue.created_at for issue in issues]
        moments += [run.created_at for run in runs]
        moments += [release.published_at for release in releases]
        moments += [star.starred_at for star in stars] + [fork.created_at for fork in forks]
        firsts = [day for _, day in commits]
        firsts += [moment.astimezone(tz).date() for moment in moments]
        earliest = min(firsts) if firsts else until
        since = (
            earliest
            if granularity is wambatic.stats.base.Granularity.TOTAL
            else wambatic.stats.buckets.bucket_start(earliest, granularity)
        )
    if since > until:
        raise wambatic.stats.errors.InvalidRangeError(f'since {since} is after until {until}')
    commits = [dated for dated in commits if since <= dated.day <= until]
    flow_found = wambatic.stats.flow.has_event_in_range(pulls, issues, tz, since, until)
    delivery_found = wambatic.stats.delivery.has_event_in_range(runs, releases, tz, since, until)
    if not (commits or flow_found or delivery_found or popularity):
        raise empty
    buckets = wambatic.stats.buckets.bucket_range(since, until, granularity)
    series: list[wambatic.stats.base.Series] = []
    tables: dict[str, list[dict[str, typing.Any]]] = {}
    if 'activity' in built:
        series, tables = wambatic.stats.activity.aggregate(
            commits,
            buckets,
            request.settings,
            by_author=request.by_author,
            by_repo=subject.kind != 'repo',
            methods=records.commit_methods,
        )
    totals = len(wambatic.stats.activity.TOTAL_METRICS) if 'activity' in built else 0
    gaps: list[dict[str, typing.Any]] = []
    if 'activity' in built:
        gaps = wambatic.stats.activity.unfiltered_gaps(
            repos,
            records.commit_methods,
            request.settings,
            branches=json.loads(records.provenance.get('branches', '[]')) != [],
        )
        gaps.extend(commit_date_gaps(commits, tz, request.settings))
    if 'flow' in built:
        flow = wambatic.stats.flow.aggregate(pulls, issues, buckets, tz, since, until)
        series = [*series[:totals], *flow, *series[totals:]]
        totals += len(flow)
    if 'delivery' in built:
        delivery, missing = wambatic.stats.delivery.aggregate(
            runs, releases, delivery_pulls, buckets, tz, since, until, request.settings
        )
        series = [*series[:totals], *delivery, *series[totals:]]
        totals += len(delivery)
        gaps.extend(missing)
    if popularity:
        liked, popular_tables = wambatic.stats.popularity.aggregate(
            stars, forks, repos, buckets, tz, since, until
        )
        series = [*series[:totals], *liked, *series[totals:]]
        tables.update(popular_tables)
        gaps.extend(wambatic.stats.popularity.hidden_star_gaps(hidden))
    tables['unavailable'] = gaps
    provenance = dict(records.provenance)
    provenance['computed_at'] = now.astimezone(datetime.UTC).isoformat()
    provenance['timezone'] = str(tz)
    if 'commit_methods' in provenance:
        provenance['exclude_paths'] = json.dumps(list(request.settings.exclude_paths))
        provenance['linguist'] = 'true' if request.settings.linguist else 'false'
        provenance['commit_timezone'] = request.settings.commit_timezone
        if request.settings.commit_timezone == 'author':
            provenance['author_timezones'] = json.dumps(dict(request.settings.author_timezones))
    provenance['partial_buckets'] = ','.join(
        bucket.label for bucket in wambatic.stats.buckets.partial_buckets(since, until, buckets)
    )
    return wambatic.stats.base.StatsResult(
        subject=subject,
        request=request,
        since=since,
        until=until,
        series=series,
        tables=tables,
        provenance=provenance,
    )


async def compute(
    subject: wambatic.fetch.base.Subject,
    fetcher: wambatic.fetch.base.Fetcher,
    request: wambatic.stats.base.StatsRequest,
    *,
    clock: collections.abc.Callable[[], datetime.datetime] | None = None,
) -> wambatic.stats.base.StatsResult:
    """All requested metric groups for the subject, from the cache, bucketed by
    request.granularity. Never syncs: the caller runs Fetcher.sync first, or not at all for
    --no-fetch. `clock` (default: now in UTC) gives today's date when `until` is None.

    Raises:
        UnknownGroupError: a group is outside `GROUPS`.
        InvalidRequestError: `by_author` is set for a user.
        InvalidRangeError: `since` is after `until`.
        EmptySubjectError: there is nothing to report.
        CacheError: the cache cannot be read.
    """
    records = await read_records(subject, fetcher, request)
    now = (clock or (lambda: datetime.datetime.now(datetime.UTC)))()
    return aggregate(subject, records, request, now)


async def compute_all(
    subject: wambatic.fetch.base.Subject,
    fetcher: wambatic.fetch.base.Fetcher,
    requests: list[wambatic.stats.base.StatsRequest],
    *,
    clock: collections.abc.Callable[[], datetime.datetime] | None = None,
) -> list[wambatic.stats.base.StatsResult]:
    """One result per request, in order, from one `read_records` of the first request and one
    `now` from `clock`: the cache is read once however many requests there are.

    Raises:
        InvalidRequestError: `requests` is empty, or two requests differ in more than granularity.
        UnknownGroupError: a group is outside `GROUPS`.
        InvalidRangeError: `since` is after `until`, or the range resolves backwards.
        EmptySubjectError: no group is requested, the cache holds no repositories, or no
            records of any requested group are in the range.
        CacheError: the cache cannot be read.
    """
    if not requests:
        raise wambatic.stats.errors.InvalidRequestError('compute_all needs at least one request')
    first = requests[0]
    for request in requests[1:]:
        for field in dataclasses.fields(first):
            if field.name != 'granularity' and getattr(request, field.name) != getattr(
                first, field.name
            ):
                raise wambatic.stats.errors.InvalidRequestError(
                    f'requests differ in {field.name}: only granularity may differ'
                )
    records = await read_records(subject, fetcher, first)
    now = (clock or (lambda: datetime.datetime.now(datetime.UTC)))()
    return [aggregate(subject, records, request, now) for request in requests]
