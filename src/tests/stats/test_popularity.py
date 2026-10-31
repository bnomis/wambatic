import datetime
import zoneinfo

import hypothesis
import hypothesis.strategies
import pytest

import tests.fixtures.stats
import wambatic.fetch.base
import wambatic.stats.base
import wambatic.stats.buckets
import wambatic.stats.popularity

BERLIN = zoneinfo.ZoneInfo('Europe/Berlin')
ORG = {tests.fixtures.stats.ALPHA, tests.fixtures.stats.BETA}
ORG_STARS = [s for s in tests.fixtures.stats.STAR_EVENTS if s.repo in ORG]
ORG_FORKS = [f for f in tests.fixtures.stats.FORKS if f.repo in ORG]
ORG_REPOS = [r for r in tests.fixtures.stats.REPOS if r.name_with_owner in ORG]
METRICS = list(tests.fixtures.stats.POPULARITY_METRICS)


def run(
    stars: list[wambatic.fetch.base.StarEvent] | None = None,
    forks: list[wambatic.fetch.base.Fork] | None = None,
    repos: list[wambatic.fetch.base.Repo] | None = None,
    granularity: wambatic.stats.base.Granularity = wambatic.stats.base.Granularity.MONTH,
    tz: datetime.tzinfo = datetime.UTC,
    since: datetime.date = tests.fixtures.stats.SINCE,
    until: datetime.date = tests.fixtures.stats.UNTIL,
) -> tuple[list[wambatic.stats.base.Series], dict[str, list[dict[str, object]]]]:
    buckets = wambatic.stats.buckets.bucket_range(since, until, granularity)
    return wambatic.stats.popularity.aggregate(
        ORG_STARS if stars is None else stars,
        ORG_FORKS if forks is None else forks,
        ORG_REPOS if repos is None else repos,
        buckets,
        tz,
        since,
        until,
    )


def check(
    series: list[wambatic.stats.base.Series], expected: tests.fixtures.stats.MonthFigures
) -> None:
    for metric in METRICS:
        assert tests.fixtures.stats.pick(series, metric) == {
            label: values[metric] for label, values in expected.items()
        }, metric


def test_the_fixture_by_month_in_utc_matches_the_hand_written_values() -> None:
    series, _ = run()
    check(series, tests.fixtures.stats.ORG_POPULARITY_BY_MONTH_UTC)


def test_the_fixture_by_month_in_berlin_moves_the_star_at_midnight_into_january() -> None:
    series, _ = run(tz=BERLIN)
    check(series, tests.fixtures.stats.ORG_POPULARITY_BY_MONTH_BERLIN)


def test_the_user_fixture_counts_every_star_and_fork_of_its_repo() -> None:
    gamma = [
        r for r in tests.fixtures.stats.REPOS if r.name_with_owner == tests.fixtures.stats.GAMMA
    ]
    stars = [s for s in tests.fixtures.stats.STAR_EVENTS if s.repo == tests.fixtures.stats.GAMMA]
    forks = [f for f in tests.fixtures.stats.FORKS if f.repo == tests.fixtures.stats.GAMMA]
    series, _ = run(stars, forks, gamma)
    check(series, tests.fixtures.stats.USER_POPULARITY_BY_MONTH_UTC)


def test_series_come_in_the_listed_order_with_unit_count_and_whole_numbers() -> None:
    series, _ = run()
    assert [(s.metric, s.unit) for s in series] == [(name, 'count') for name in METRICS]
    assert all(s.by is None and s.by_kind is None for s in series)
    assert all(isinstance(value, int) for s in series for value in s.points.values())


def test_the_total_bucket_gives_the_counts_over_the_range_and_the_totals_at_until() -> None:
    for (tz,) in ((datetime.UTC,), (BERLIN,)):
        series, _ = run(granularity=wambatic.stats.base.Granularity.TOTAL, tz=tz)
        for metric in METRICS:
            assert list(tests.fixtures.stats.pick(series, metric)) == list(
                tests.fixtures.stats.TOTAL_LABELS
            )
            assert (
                tests.fixtures.stats.pick(series, metric)['total']
                == tests.fixtures.stats.ORG_POPULARITY_TOTAL[metric]
            )


def test_events_after_until_count_in_nothing_and_events_before_since_only_in_the_totals() -> None:
    series, _ = run(since=datetime.date(2026, 11, 1), until=datetime.date(2026, 11, 30))
    assert tests.fixtures.stats.pick(series, 'stars_added') == {'2026-11': 0}
    assert tests.fixtures.stats.pick(series, 'stars_total') == {'2026-11': 5}  # a1 b1 a2 a3 b2
    assert tests.fixtures.stats.pick(series, 'forks_added') == {'2026-11': 1}
    assert tests.fixtures.stats.pick(series, 'forks_total') == {'2026-11': 3}  # 1001 1002 1003


def test_the_tables_match_the_hand_written_values() -> None:
    _, tables = run()
    assert tables['popularity'] == list(tests.fixtures.stats.ORG_POPULARITY_TABLE)
    languages = tables['languages']
    assert [(row['language'], row['bytes']) for row in languages] == [
        (row['language'], row['bytes']) for row in tests.fixtures.stats.ORG_LANGUAGES_TABLE
    ]
    assert [row['share'] for row in languages] == pytest.approx(
        [row['share'] for row in tests.fixtures.stats.ORG_LANGUAGES_TABLE]
    )


def test_a_user_with_no_language_has_an_empty_languages_table() -> None:
    gamma = [
        r for r in tests.fixtures.stats.REPOS if r.name_with_owner == tests.fixtures.stats.GAMMA
    ]
    _, tables = run([], [], gamma)
    assert tables['languages'] == []
    assert tables['popularity'] == list(tests.fixtures.stats.USER_POPULARITY_TABLE)


def test_other_is_left_out_when_the_listed_languages_cover_the_size_and_is_last_when_biggest() -> (
    None
):
    covered = wambatic.fetch.base.Repo(
        'o/a',
        None,
        None,
        False,
        False,
        None,
        tests.fixtures.stats.NOW,
        languages=(('C', 5),),
        languages_size=5,
    )
    _, tables = run([], [], [covered])
    assert [row['language'] for row in tables['languages']] == ['C']
    huge = wambatic.fetch.base.Repo(
        'o/b',
        None,
        None,
        False,
        False,
        None,
        tests.fixtures.stats.NOW,
        languages=(('C', 5),),
        languages_size=500,
    )
    _, tables = run([], [], [huge])
    assert [row['language'] for row in tables['languages']] == ['C', 'Other']
    assert tables['languages'][1]['share'] == pytest.approx(495 / 500)


def test_the_popularity_table_is_ordered_by_stars_then_name() -> None:
    def repo(name: str, stars: int) -> wambatic.fetch.base.Repo:
        return wambatic.fetch.base.Repo(
            name, None, None, False, False, None, tests.fixtures.stats.NOW, stargazer_count=stars
        )

    _, tables = run([], [], [repo('o/b', 2), repo('o/a', 2), repo('o/c', 9)])
    assert [row['repo'] for row in tables['popularity']] == ['o/c', 'o/a', 'o/b']


TIMES = hypothesis.strategies.datetimes(
    min_value=datetime.datetime(2025, 6, 1), max_value=datetime.datetime(2027, 6, 1)
).map(lambda t: t.replace(tzinfo=datetime.UTC))
YEAR = (datetime.date(2026, 1, 1), datetime.date(2026, 12, 31))


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(
    hypothesis.strategies.lists(TIMES, max_size=40),
    hypothesis.strategies.sampled_from(list(wambatic.stats.base.Granularity)),
    hypothesis.strategies.sampled_from([datetime.UTC, BERLIN]),
)
def test_added_sums_to_the_stars_in_range_and_the_total_never_falls_to_the_stars_until(
    moments: list[datetime.datetime],
    granularity: wambatic.stats.base.Granularity,
    tz: datetime.tzinfo,
) -> None:
    stars = [
        wambatic.fetch.base.StarEvent('o/a', f'U_{n}', moment) for n, moment in enumerate(moments)
    ]
    series, _ = run(stars, [], [], granularity, tz, *YEAR)
    local = [moment.astimezone(tz).date() for moment in moments]
    added = tests.fixtures.stats.pick(series, 'stars_added')
    totals = list(tests.fixtures.stats.pick(series, 'stars_total').values())
    assert sum(added.values()) == sum(1 for day in local if YEAR[0] <= day <= YEAR[1])
    assert totals == sorted(totals)
    assert totals[-1] == sum(1 for day in local if day <= YEAR[1])
