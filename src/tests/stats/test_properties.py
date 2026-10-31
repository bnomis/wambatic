import dataclasses
import datetime

import hypothesis
import hypothesis.strategies

import tests.fixtures.constants
import wambatic.fetch.base
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.buckets
import wambatic.stats.delivery
import wambatic.stats.engine

SINCE = datetime.date(2026, 1, 1)
UNTIL = datetime.date(2026, 12, 31)
START = datetime.datetime(2026, 1, 1, tzinfo=datetime.UTC)
SPAN_HOURS = 365 * 24
REPOS = ('acme/one', 'acme/two')
HOTFIX = tests.fixtures.constants.HOTFIX_LABELS
SETTINGS = wambatic.settings.StatsSettings()
WORKFLOW = dataclasses.replace(SETTINGS, deploy_workflow='deploy.yml')
BUCKETS = wambatic.stats.buckets.bucket_range(SINCE, UNTIL, wambatic.stats.base.Granularity.MONTH)
FAILURE_WINDOW = SETTINGS.failure_window

MOMENTS = hypothesis.strategies.integers(-48, SPAN_HOURS + 48).map(
    lambda hours: START + datetime.timedelta(hours=hours)
)
REPO_NAMES = hypothesis.strategies.sampled_from(REPOS)


@hypothesis.strategies.composite
def run_records(draw: hypothesis.strategies.DrawFn) -> wambatic.fetch.base.WorkflowRun:
    created = draw(MOMENTS)
    return wambatic.fetch.base.WorkflowRun(
        repo=draw(REPO_NAMES),
        id=draw(hypothesis.strategies.integers(1, 10**6)),
        workflow_path=draw(
            hypothesis.strategies.sampled_from(
                ['.github/workflows/deploy.yml', '.github/workflows/ci.yml']
            )
        ),
        name='Deploy',
        event='push',
        head_branch='main',
        status=draw(hypothesis.strategies.sampled_from(['completed', 'in_progress'])),
        conclusion=draw(hypothesis.strategies.sampled_from([None, 'failure', 'success'])),
        created_at=created,
        updated_at=created
        + datetime.timedelta(minutes=draw(hypothesis.strategies.integers(0, 90))),
        run_started_at=created,
        run_attempt=1,
    )


@hypothesis.strategies.composite
def release_records(draw: hypothesis.strategies.DrawFn) -> wambatic.fetch.base.Release:
    published = draw(MOMENTS)
    return wambatic.fetch.base.Release(
        repo=draw(REPO_NAMES),
        tag_name=f'v{draw(hypothesis.strategies.integers(0, 10**6))}',
        created_at=published,
        published_at=published,
        is_prerelease=draw(hypothesis.strategies.booleans()),
    )


def pull_request(
    repo: str, opened: datetime.datetime, labels: tuple[str, ...]
) -> wambatic.fetch.base.PullRequest:
    return wambatic.fetch.base.PullRequest(
        repo=repo,
        number=1,
        author_login=None,
        created_at=opened,
        updated_at=opened,
        merged_at=opened + datetime.timedelta(hours=1),
        closed_at=None,
        first_review_at=None,
        additions=1,
        deletions=1,
        labels=labels,
    )


@hypothesis.strategies.composite
def pull_records(draw: hypothesis.strategies.DrawFn) -> wambatic.fetch.base.PullRequest:
    labels = draw(
        hypothesis.strategies.sampled_from([(), ('bug',), ('Hotfix',), ('hotfix', 'bug')])
    )
    return pull_request(draw(REPO_NAMES), draw(MOMENTS), labels)


def aggregate(
    run_list: list[wambatic.fetch.base.WorkflowRun],
    release_list: list[wambatic.fetch.base.Release],
    pull_list: list[wambatic.fetch.base.PullRequest],
    settings: wambatic.settings.StatsSettings,
) -> tuple[dict[str, wambatic.stats.base.Series], list[dict[str, str]]]:
    series, missing = wambatic.stats.delivery.aggregate(
        run_list, release_list, pull_list, BUCKETS, datetime.UTC, SINCE, UNTIL, settings
    )
    return {s.metric: s for s in series}, missing


def in_range(moment: datetime.datetime) -> bool:
    return SINCE <= moment.date() <= UNTIL


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.lists(run_records(), max_size=12),
    hypothesis.strategies.lists(release_records(), max_size=12),
    hypothesis.strategies.lists(pull_records(), max_size=12),
    hypothesis.strategies.sampled_from([SETTINGS, WORKFLOW]),
)
def test_deployments_and_failures_never_exceed_their_sources(
    run_list: list[wambatic.fetch.base.WorkflowRun],
    release_list: list[wambatic.fetch.base.Release],
    pull_list: list[wambatic.fetch.base.PullRequest],
    settings: wambatic.settings.StatsSettings,
) -> None:
    series, _ = aggregate(run_list, release_list, pull_list, settings)
    if settings.deploy_workflow is None:
        source = [r.published_at for r in release_list if not r.is_prerelease]
    else:
        source = [
            r.updated_at
            for r in run_list
            if r.status == 'completed'
            and r.conclusion == 'success'
            and r.workflow_path.endswith('/deploy.yml')
        ]
    if 'deployments' in series:
        counts = series['deployments'].points
        assert sum(counts.values()) <= sum(1 for moment in source if in_range(moment))
        assert all(value >= 0 for value in counts.values())
    if 'change_failure_rate' in series:
        deployed = series['deployments'].points
        for bucket, rate in series['change_failure_rate'].points.items():
            assert 0 <= rate <= 1
            failures = rate * deployed[bucket]
            assert abs(failures - round(failures)) < 1e-9
    assert sum(series['workflow_runs'].points.values()) <= len(run_list)
    assert sum(series['release_count'].points.values()) <= len(release_list)


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.integers(0, SPAN_HOURS - 1)
    | hypothesis.strategies.integers(SPAN_HOURS - 24 * 10, SPAN_HOURS - 1),
    hypothesis.strategies.integers(1, 24 * 14),
)
def test_the_failure_window_counts_only_when_it_closes_inside_the_range(
    deployed_hours: int, hotfix_hours: int
) -> None:
    deployed = START + datetime.timedelta(hours=deployed_hours)
    release = wambatic.fetch.base.Release('acme/one', 'v1', deployed, deployed, False)
    hotfix = pull_request('acme/one', deployed + datetime.timedelta(hours=hotfix_hours), HOTFIX)
    series, _ = aggregate([], [release], [hotfix], SETTINGS)
    horizon = datetime.datetime.combine(
        UNTIL + datetime.timedelta(days=1), datetime.time(), tzinfo=datetime.UTC
    )
    closed = deployed + FAILURE_WINDOW <= horizon
    within = datetime.timedelta(hours=hotfix_hours) <= FAILURE_WINDOW
    rates = series['change_failure_rate'].points
    assert list(rates.values()) == [1.0 if closed and within else 0.0]


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.booleans(),
    hypothesis.strategies.booleans(),
    hypothesis.strategies.sampled_from([SETTINGS, WORKFLOW]),
)
def test_each_proxy_is_a_series_or_a_missing_row_and_never_both(
    has_deployments: bool, has_hotfix: bool, settings: wambatic.settings.StatsSettings
) -> None:
    missing = wambatic.stats.delivery.missing_inputs(has_deployments, has_hotfix, settings)
    assert set(missing) <= set(wambatic.stats.delivery.DORA_METRICS)
    assert list(missing) == [m for m in wambatic.stats.delivery.DORA_METRICS if m in missing]
    if has_deployments and has_hotfix:
        assert not missing
    if not has_deployments:
        assert wambatic.stats.delivery.DEPLOYMENT_METRICS <= set(missing)
    series, rows = aggregate(
        [], [], [pull_request('acme/one', START, HOTFIX)] if has_hotfix else [], settings
    )
    assert not set(series) & {row['metric'] for row in rows}
    assert set(series) | {row['metric'] for row in rows} == {
        name for name, _ in wambatic.stats.delivery.DELIVERY_METRICS
    }


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.frozensets(
        hypothesis.strategies.sampled_from(sorted(wambatic.stats.base.GROUPS))
    )
)
def test_resources_for_is_the_union_of_the_groups_resources(groups: frozenset[str]) -> None:
    expected: set[str] = set()
    for group in groups:
        expected |= wambatic.stats.engine.RESOURCES_BY_GROUP[group]
    assert wambatic.stats.engine.resources_for(groups) == expected
