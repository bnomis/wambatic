import bisect
import collections.abc
import datetime
import typing

import wambatic.stats.base
import wambatic.stats.errors

ONE_DAY = datetime.timedelta(days=1)


def bucket_start(day: datetime.date, granularity: wambatic.stats.base.Granularity) -> datetime.date:
    """First local date of the bucket holding `day`.

    Raises:
        InvalidRequestError: `granularity` is TOTAL.
    """
    match granularity:
        case wambatic.stats.base.Granularity.YEAR:
            return datetime.date(day.year, 1, 1)
        case wambatic.stats.base.Granularity.MONTH:
            return datetime.date(day.year, day.month, 1)
        case wambatic.stats.base.Granularity.WEEK:
            iso = day.isocalendar()
            return datetime.date.fromisocalendar(iso.year, iso.week, 1)
        case wambatic.stats.base.Granularity.DAY:
            return day
        case wambatic.stats.base.Granularity.TOTAL:
            raise wambatic.stats.errors.InvalidRequestError(
                f'{granularity} has no bucket start; its bucket depends on the range'
            )
        case _:
            typing.assert_never(granularity)


def next_start(start: datetime.date, granularity: wambatic.stats.base.Granularity) -> datetime.date:
    """First local date of the bucket after the one starting at `start`.

    Raises:
        InvalidRequestError: `granularity` is TOTAL.
    """
    match granularity:
        case wambatic.stats.base.Granularity.YEAR:
            return datetime.date(start.year + 1, 1, 1)
        case wambatic.stats.base.Granularity.MONTH:
            if start.month == 12:
                return datetime.date(start.year + 1, 1, 1)
            return datetime.date(start.year, start.month + 1, 1)
        case wambatic.stats.base.Granularity.WEEK:
            return start + datetime.timedelta(days=7)
        case wambatic.stats.base.Granularity.DAY:
            return start + ONE_DAY
        case wambatic.stats.base.Granularity.TOTAL:
            raise wambatic.stats.errors.InvalidRequestError(f'{granularity} has no next bucket')
        case _:
            typing.assert_never(granularity)


def label(start: datetime.date, granularity: wambatic.stats.base.Granularity) -> str:
    match granularity:
        case wambatic.stats.base.Granularity.YEAR:
            return f'{start.year:04d}'
        case wambatic.stats.base.Granularity.MONTH:
            return f'{start.year:04d}-{start.month:02d}'
        case wambatic.stats.base.Granularity.WEEK:
            iso = start.isocalendar()
            return f'{iso.year:04d}-W{iso.week:02d}'
        case wambatic.stats.base.Granularity.DAY:
            return start.isoformat()
        case _:
            return 'total'


def bucket_for(
    when: datetime.datetime, granularity: wambatic.stats.base.Granularity, tz: datetime.tzinfo
) -> wambatic.stats.base.Bucket:
    """Bucket containing `when` (an aware datetime) in `tz`; weeks are ISO 8601 weeks starting
    Monday. Raises InvalidRequestError for Granularity.TOTAL, whose one bucket depends on the range.

    Raises:
        InvalidRequestError: `when` is naive or `granularity` is TOTAL.
    """
    if when.tzinfo is None:
        raise wambatic.stats.errors.InvalidRequestError('when must be timezone-aware')
    start = bucket_start(when.astimezone(tz).date(), granularity)
    return wambatic.stats.base.Bucket(start, label(start, granularity))


def bucket_range(
    since: datetime.date, until: datetime.date, granularity: wambatic.stats.base.Granularity
) -> list[wambatic.stats.base.Bucket]:
    """The buckets covering the local dates `since` to `until`, both inclusive, in order.
    For TOTAL, the single Bucket(since, 'total').

    Raises:
        InvalidRangeError: `since` is after `until`.
    """
    if since > until:
        raise wambatic.stats.errors.InvalidRangeError('since is after until')
    if granularity is wambatic.stats.base.Granularity.TOTAL:
        return [wambatic.stats.base.Bucket(since, 'total')]
    buckets: list[wambatic.stats.base.Bucket] = []
    start = bucket_start(since, granularity)
    while start <= until:
        buckets.append(wambatic.stats.base.Bucket(start, label(start, granularity)))
        start = next_start(start, granularity)
    return buckets


def partial_buckets(
    since: datetime.date, until: datetime.date, buckets: list[wambatic.stats.base.Bucket]
) -> list[wambatic.stats.base.Bucket]:
    """The first and last of `buckets` when the range starts after the first's start or ends
    before the last's end; never a TOTAL bucket."""
    if not buckets or buckets[0].label == 'total':
        return []
    granularity = bucket_granularity(buckets[0])
    partial: list[wambatic.stats.base.Bucket] = []
    if since > buckets[0].start:
        partial.append(buckets[0])
    last = buckets[-1]
    if until < next_start(last.start, granularity) - ONE_DAY and (
        not partial or last is not partial[0]
    ):
        partial.append(last)
    return partial


def bucket_granularity(bucket: wambatic.stats.base.Bucket) -> wambatic.stats.base.Granularity:
    """The granularity a bucket's label belongs to."""
    if 'W' in bucket.label:
        return wambatic.stats.base.Granularity.WEEK
    return {
        4: wambatic.stats.base.Granularity.YEAR,
        7: wambatic.stats.base.Granularity.MONTH,
        10: wambatic.stats.base.Granularity.DAY,
    }[len(bucket.label)]


def bucket_end(buckets: list[wambatic.stats.base.Bucket]) -> datetime.date | None:
    """First local date after the last of `buckets`; None for a TOTAL bucket, which has no end."""
    if not buckets or buckets[0].label == 'total':
        return None
    return next_start(buckets[-1].start, bucket_granularity(buckets[-1]))


def locate(day: datetime.date, starts: list[datetime.date], end: datetime.date | None) -> int:
    """Index of the bucket holding `day`, given the buckets' start dates and the end of the last;
    InvalidRangeError when `day` is before the first or at or after `end`.

    Raises:
        InvalidRangeError: `day` is outside the buckets.
    """
    index = bisect.bisect_right(starts, day) - 1
    if index < 0 or (end is not None and day >= end):
        raise wambatic.stats.errors.InvalidRangeError(f'{day} is outside the buckets')
    return index


def placer(
    buckets: list[wambatic.stats.base.Bucket],
    tz: datetime.tzinfo,
    since: datetime.date,
    until: datetime.date,
) -> collections.abc.Callable[[datetime.datetime | None], int | None]:
    """A function giving the index of the bucket holding a moment's local date in `tz`, or None
    for no moment or a date outside `since` to `until` (the buckets may reach beyond it)."""
    starts = [bucket.start for bucket in buckets]
    end = bucket_end(buckets)

    def place(moment: datetime.datetime | None) -> int | None:
        if moment is None:
            return None
        day = moment.astimezone(tz).date()
        if not since <= day <= until:
            return None
        return locate(day, starts, end)

    return place
