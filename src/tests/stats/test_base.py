import dataclasses
import datetime

import pytest

import tests.fixtures.stats
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.errors


def test_groups_are_the_four_metric_groups() -> None:
    assert wambatic.stats.base.GROUPS == tests.fixtures.stats.GROUPS_ALL


def test_granularity_has_the_five_values() -> None:
    assert {g.value for g in wambatic.stats.base.Granularity} == {
        'day',
        'month',
        'total',
        'week',
        'year',
    }


def test_a_default_request_is_monthly_activity_and_flow_in_utc() -> None:
    request = wambatic.stats.base.StatsRequest()
    assert request.granularity is wambatic.stats.base.Granularity.MONTH
    assert request.groups == tests.fixtures.stats.GROUPS_ACTIVITY_FLOW
    assert request.since is None
    assert request.until is None
    assert request.by_author is False
    assert request.tz is datetime.UTC
    assert request.settings == wambatic.settings.StatsSettings()


def test_a_request_is_hashable() -> None:
    assert hash(wambatic.stats.base.StatsRequest()) == hash(wambatic.stats.base.StatsRequest())


def test_buckets_sort_by_start() -> None:
    later = wambatic.stats.base.Bucket(datetime.date(2026, 11, 1), '2026-11')
    earlier = wambatic.stats.base.Bucket(datetime.date(2026, 10, 1), '2026-10')
    assert sorted([later, earlier]) == [earlier, later]


def test_records_are_immutable() -> None:
    bucket = wambatic.stats.base.Bucket(datetime.date(2026, 10, 1), '2026-10')
    with pytest.raises(dataclasses.FrozenInstanceError):
        bucket.label = 'x'  # type: ignore[misc]
    series = wambatic.stats.base.Series('commits', 'count', {bucket: 1})
    with pytest.raises(dataclasses.FrozenInstanceError):
        series.metric = 'x'  # type: ignore[misc]
    request = wambatic.stats.base.StatsRequest()
    with pytest.raises(dataclasses.FrozenInstanceError):
        request.by_author = True  # type: ignore[misc]


def test_a_series_with_both_or_neither_key_is_valid() -> None:
    assert wambatic.stats.base.Series('commits', 'count', {}).by is None
    assert (
        wambatic.stats.base.Series('commits', 'count', {}, by='octocat', by_kind='author').by
        == 'octocat'
    )


@pytest.mark.parametrize('by, by_kind', [('octocat', None), (None, 'author')])
def test_a_series_with_only_one_key_is_rejected(by: str | None, by_kind: str | None) -> None:
    with pytest.raises(wambatic.stats.errors.InvalidRequestError, match='by_kind'):
        wambatic.stats.base.Series('commits', 'count', {}, by=by, by_kind=by_kind)  # type: ignore[arg-type]
