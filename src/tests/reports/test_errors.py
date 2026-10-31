import pytest

import wambatic.fetch.errors
import wambatic.reports.errors
import wambatic.stats.errors


@pytest.mark.parametrize(
    'error',
    [
        wambatic.reports.errors.OutputError,
        wambatic.reports.errors.ServeError,
        wambatic.reports.errors.UsageError,
    ],
)
def test_every_error_is_a_reports_error_and_not_a_fetch_or_stats_error(
    error: type[Exception],
) -> None:
    assert issubclass(error, wambatic.reports.errors.ReportsError)
    assert not issubclass(error, wambatic.fetch.errors.FetchError)
    assert not issubclass(error, wambatic.stats.errors.StatsError)
    assert str(error('why')) == 'why'
