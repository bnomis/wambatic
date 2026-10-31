import datetime
import json
import re
import urllib.parse

import hypothesis
import hypothesis.strategies
import plotly.graph_objects
import pytest

import tests.reports.test_figures
import wambatic.fetch.base
import wambatic.reports.errors
import wambatic.reports.figures
import wambatic.reports.html
import wambatic.reports.rows
import wambatic.reports.terminal
import wambatic.reports.web
import wambatic.settings
import wambatic.stats.activity
import wambatic.stats.base
import wambatic.stats.buckets
import wambatic.stats.delivery
import wambatic.stats.flow
import wambatic.stats.popularity

SUBJECT = wambatic.fetch.base.Subject('org', 'octo-org')
PERIODS = (
    wambatic.stats.base.Granularity.DAY,
    wambatic.stats.base.Granularity.MONTH,
    wambatic.stats.base.Granularity.WEEK,
    wambatic.stats.base.Granularity.YEAR,
)
GROUP_METRICS = {
    'activity': wambatic.stats.activity.TOTAL_METRICS,
    'delivery': wambatic.stats.delivery.DELIVERY_METRICS,
    'flow': wambatic.stats.flow.FLOW_METRICS,
    'popularity': wambatic.stats.popularity.POPULARITY_METRICS,
}
FILLED_UNITS = frozenset({'count', 'days', 'lines'})
DATES = hypothesis.strategies.dates(
    min_value=datetime.date(2000, 1, 1), max_value=datetime.date(2100, 12, 31)
)
NUMBERS = hypothesis.strategies.integers(0, 10000)
SHORT_TEXT = hypothesis.strategies.text(max_size=12)


@hypothesis.strategies.composite
def results(
    draw: hypothesis.strategies.DrawFn, granularities: tuple[wambatic.stats.base.Granularity, ...]
) -> wambatic.stats.base.StatsResult:
    """A result with random whole-number points for the groups it holds. Counts, days and lines
    have a point in every bucket; the other units miss some buckets."""
    granularity = draw(hypothesis.strategies.sampled_from(granularities))
    first = draw(DATES)
    since = first
    until = first + datetime.timedelta(days=draw(hypothesis.strategies.integers(0, 400)))
    if granularity is wambatic.stats.base.Granularity.DAY:
        until = since + datetime.timedelta(days=draw(hypothesis.strategies.integers(0, 40)))
    buckets = wambatic.stats.buckets.bucket_range(since, until, granularity)
    groups = draw(
        hypothesis.strategies.frozensets(
            hypothesis.strategies.sampled_from(sorted(GROUP_METRICS)), min_size=1
        )
    )
    series: list[wambatic.stats.base.Series] = []
    for group in sorted(groups):
        for metric, unit in GROUP_METRICS[group]:
            points = {}
            for bucket in buckets:
                if unit in FILLED_UNITS or draw(hypothesis.strategies.booleans()):
                    points[bucket] = float(draw(NUMBERS))
            series.append(wambatic.stats.base.Series(metric, unit, points))
    request = wambatic.stats.base.StatsRequest(granularity=granularity, groups=groups)
    return wambatic.stats.base.StatsResult(SUBJECT, request, since, until, series, {}, {})


def labels_of(result: wambatic.stats.base.StatsResult) -> list[str]:
    return [bucket.label for bucket in wambatic.reports.rows.bucket_list(result)]


def column(table: wambatic.reports.rows.PeriodTable, metric: str) -> list[float | None]:
    index = table.metrics.index(metric)
    return [row.values[index] for row in table.rows]


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(results(PERIODS))
def test_every_table_has_one_row_per_bucket_in_bucket_order(
    result: wambatic.stats.base.StatsResult,
) -> None:
    labels = labels_of(result)
    starts = [bucket.start for bucket in wambatic.reports.rows.bucket_list(result)]
    assert starts == sorted(starts)
    builders = (
        wambatic.reports.rows.activity_table,
        wambatic.reports.rows.flow_table,
        wambatic.reports.rows.flow_times_table,
        wambatic.reports.rows.delivery_table,
        wambatic.reports.rows.dora_table,
        wambatic.reports.rows.popularity_table,
    )
    for build in builders:
        table = build(result)
        if table is not None:
            assert [row.label for row in table.rows] == labels
            assert all(len(row.values) == len(table.metrics) for row in table.rows)


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(results(PERIODS))
def test_a_total_row_adds_up_the_columns_the_spec_says_add_up(
    result: wambatic.stats.base.StatsResult,
) -> None:
    activity = wambatic.reports.rows.activity_table(result)
    if activity is not None:
        assert (activity.total is None) == (len(activity.rows) < 2)
        if activity.total is not None:
            for metric, total in zip(activity.metrics, activity.total, strict=True):
                if metric != 'contributors':
                    assert total == sum(v for v in column(activity, metric) if v is not None)
    flow = wambatic.reports.rows.flow_table(result)
    if flow is not None and flow.total is not None:
        for metric, total in zip(flow.metrics, flow.total, strict=True):
            assert total == sum(v for v in column(flow, metric) if v is not None)
    popularity = wambatic.reports.rows.popularity_table(result)
    if popularity is not None and popularity.total is not None:
        for metric, total in zip(popularity.metrics, popularity.total, strict=True):
            values = [v for v in column(popularity, metric) if v is not None]
            if metric in wambatic.reports.rows.POPULARITY_ADDED:
                assert total == sum(values)
            else:
                assert total == values[-1]
    for build in (wambatic.reports.rows.delivery_table, wambatic.reports.rows.dora_table):
        table = build(result)
        if table is not None and table.total is not None:
            for metric, total in zip(table.metrics, table.total, strict=True):
                if metric in wambatic.reports.rows.DELIVERY_TOTALS:
                    assert total == sum(v for v in column(table, metric) if v is not None)
                else:
                    assert total is None


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(results(PERIODS))
def test_every_figure_validates_has_at_most_three_series_and_no_colour(
    result: wambatic.stats.base.StatsResult,
) -> None:
    figures = wambatic.reports.figures.build_figures(result)
    keys = [figure.key for figure in figures]
    assert len(keys) == len(set(keys))
    for figure in figures:
        plotly.graph_objects.Figure(data=figure.data, layout=figure.layout)
        assert 1 <= len(figure.data) <= wambatic.reports.figures.CATEGORICAL_SLOTS
        text = json.dumps([figure.data, figure.layout])
        assert not tests.reports.test_figures.HEX.search(text)
        assert 'color' not in text.replace('"colorway"', '')


@hypothesis.strategies.composite
def total_results(draw: hypothesis.strategies.DrawFn) -> wambatic.stats.base.StatsResult:
    result = draw(results((wambatic.stats.base.Granularity.TOTAL,)))
    names = hypothesis.strategies.text(
        alphabet=hypothesis.strategies.characters(categories=['L', 'N']), min_size=1, max_size=8
    )
    contributors = draw(
        hypothesis.strategies.lists(
            hypothesis.strategies.tuples(names, NUMBERS),
            unique_by=lambda item: item[0],
            max_size=25,
        )
    )
    languages = draw(
        hypothesis.strategies.lists(
            hypothesis.strategies.tuples(names, NUMBERS),
            unique_by=lambda item: item[0],
            max_size=25,
        )
    )
    tables = {
        'languages': [
            {'language': name, 'bytes': size, 'share': size / (1 + sum(s for _, s in languages))}
            for name, size in languages
        ],
        'top_contributors': [
            {
                'login': name,
                'commits': commits,
                'lines_added': 0,
                'lines_deleted': 0,
                'lines_net': 0,
                'active_days': 1,
            }
            for name, commits in contributors
        ],
    }
    series = [
        wambatic.stats.base.Series(metric, 'count', points, by, 'repo')
        for by in ('alpha', 'beta')
        for metric in wambatic.stats.activity.BREAKDOWN_METRICS
        for points in [{bucket: 1.0 for bucket in wambatic.reports.rows.bucket_list(result)}]
    ]
    return wambatic.stats.base.StatsResult(
        result.subject,
        result.request,
        result.since,
        result.until,
        [*result.series, *series],
        tables,
        {},
    )


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(total_results())
def test_every_range_figure_validates_has_at_most_three_series_and_no_colour(
    result: wambatic.stats.base.StatsResult,
) -> None:
    assert wambatic.reports.figures.build_figures(result) == []
    for figure in wambatic.reports.figures.build_range_figures(result):
        plotly.graph_objects.Figure(data=figure.data, layout=figure.layout)
        assert 1 <= len(figure.data) <= wambatic.reports.figures.CATEGORICAL_SLOTS
        assert not tests.reports.test_figures.HEX.search(json.dumps([figure.data, figure.layout]))


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(results(PERIODS))
def test_range_figures_refuse_a_result_that_is_not_a_total(
    result: wambatic.stats.base.StatsResult,
) -> None:
    with pytest.raises(wambatic.reports.errors.UsageError):
        wambatic.reports.figures.build_range_figures(result)


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.sampled_from(['org', 'repo', 'user']), SHORT_TEXT, SHORT_TEXT
)
def test_report_filename_is_safe_for_any_login(kind: str, login: str, name: str) -> None:
    class Named:
        def __init__(self) -> None:
            self.kind = kind
            self.login = login
            self.full_name = f'{login}/{name}'

    filename = wambatic.reports.html.report_filename(Named())
    assert re.fullmatch(r'(org|repo|user)-[A-Za-z0-9._-]*\.html', filename)
    assert filename.startswith(f'{kind}-')


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(results(PERIODS), results(PERIODS))
def test_first_difference_is_none_for_a_result_and_itself_and_ignores_granularity(
    first: wambatic.stats.base.StatsResult, second: wambatic.stats.base.StatsResult
) -> None:
    assert wambatic.reports.html.first_difference(first, first) is None
    other = wambatic.stats.base.StatsResult(
        first.subject,
        wambatic.stats.base.StatsRequest(
            granularity=second.request.granularity, groups=first.request.groups
        ),
        first.since,
        first.until,
        second.series,
        second.tables,
        second.provenance,
    )
    assert wambatic.reports.html.first_difference(first, other) is None
    changed = wambatic.stats.base.StatsResult(
        wambatic.fetch.base.Subject('user', 'someone'),
        first.request,
        first.since,
        first.until,
        first.series,
        first.tables,
        first.provenance,
    )
    assert wambatic.reports.html.first_difference(first, changed) == 'subject'


QUERY_TEXT = hypothesis.strategies.none() | hypothesis.strategies.text(max_size=20)


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    *[QUERY_TEXT] * 8,
    hypothesis.strategies.booleans(),
)
def test_parse_query_returns_a_query_or_raises_a_usage_error(
    target: str | None,
    by: str | None,
    since: str | None,
    until: str | None,
    groups: str | None,
    by_author: str | None,
    tz: str | None,
    job: str | None,
    page: bool,
) -> None:
    raw = wambatic.reports.web.RawQuery(target, by, since, until, groups, by_author, tz, job)
    today = datetime.datetime(2027, 1, 20, 12, 0, tzinfo=datetime.UTC)
    try:
        query = wambatic.reports.web.parse_query(
            wambatic.settings.Settings(), raw, today, page=page
        )
    except wambatic.reports.errors.UsageError, wambatic.settings.SettingsError:
        return
    assert query.request.groups <= wambatic.stats.base.GROUPS
    assert query.key[0] == (target or '').strip()
    assert query.job == (job.strip() or None if job is not None else None)
    assert not (page and query.request.granularity is wambatic.stats.base.Granularity.TOTAL)


PARAMETERS = hypothesis.strategies.lists(
    hypothesis.strategies.tuples(SHORT_TEXT, SHORT_TEXT), max_size=6
)


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    PARAMETERS,
    hypothesis.strategies.none() | hypothesis.strategies.text(alphabet='abc-123', min_size=1),
)
def test_reload_path_sets_or_removes_only_the_job_parameter(
    parameters: list[tuple[str, str]], job_id: str | None
) -> None:
    url = urllib.parse.SplitResult('', '', '/report', urllib.parse.urlencode(parameters), '')
    path = wambatic.reports.web.reload_path(url, job_id)
    parsed = urllib.parse.urlsplit(path)
    assert parsed.path == '/report'
    found = urllib.parse.parse_qsl(parsed.query)
    kept = [(k, v) for k, v in urllib.parse.parse_qsl(url.query) if k != 'job']
    assert [(k, v) for k, v in found if k != 'job'] == kept
    jobs = [v for k, v in found if k == 'job']
    assert jobs == ([] if job_id is None else [job_id])


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.floats(-1e12, 1e12, allow_nan=False),
    hypothesis.strategies.booleans(),
    hypothesis.strategies.none() | hypothesis.strategies.integers(0, 4),
)
def test_format_number_round_trips_and_signs_only_positive_values(
    value: float, signed: bool, decimals: int | None
) -> None:
    text = wambatic.reports.terminal.format_number(value, signed=signed, decimals=decimals)
    parsed = float(text.replace(',', '').removeprefix('+'))
    places = 2 if decimals is None else decimals
    assert abs(parsed - value) <= 0.5 * 10**-places + 1e-6 * abs(value)
    assert text.startswith('+') == (signed and value > 0)
    if decimals is None and float(value).is_integer():
        assert '.' not in text
