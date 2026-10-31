import datetime

import pytest

import wambatic.fetch.errors

FORBIDDEN_NO = ('FORBIDDEN', 'no')
INTERNAL_BOOM = ('INTERNAL', 'boom')
LETTERS = ('a', 'b')
SCHEMA_DIFFERENCE = ('1', '2')


@pytest.mark.parametrize(
    'cls',
    [
        wambatic.fetch.errors.AuthError,
        wambatic.fetch.errors.CacheVersionError,
        wambatic.fetch.errors.GraphQLError,
        wambatic.fetch.errors.NotFoundError,
        wambatic.fetch.errors.RateLimitError,
        wambatic.fetch.errors.StatsPendingError,
    ],
)
def test_every_class_is_a_fetch_error(cls: type[Exception]) -> None:
    assert issubclass(cls, wambatic.fetch.errors.FetchError)


def test_rate_limit_error_names_reset() -> None:
    reset = datetime.datetime(2026, 10, 29, 17, 0, tzinfo=datetime.UTC)
    error = wambatic.fetch.errors.RateLimitError(reset)
    assert error.reset_at == reset
    assert '2026-10-29T17:00:00+00:00' in str(error)


def test_graphql_error_exposes_pairs() -> None:
    pairs = [INTERNAL_BOOM, FORBIDDEN_NO]
    error = wambatic.fetch.errors.GraphQLError(pairs)
    assert error.errors == tuple(pairs)
    assert 'INTERNAL' in str(error)
    assert 'FORBIDDEN' in str(error)


def test_cache_version_error_names_each_key_with_both_values_and_the_remedies() -> None:
    error = wambatic.fetch.errors.CacheVersionError(
        {
            'schema_version': SCHEMA_DIFFERENCE,
            'query:NEW': (None, 'abc'),
            'query:OLD': ('def', None),
        }
    )
    message = str(error)
    assert 'schema_version: cache has 1, this wambatic has 2' in message
    assert 'query:NEW: cache has nothing, this wambatic has abc' in message
    assert 'query:OLD: cache has def, this wambatic has nothing' in message
    assert 'wambatic cache clear' in message
    assert '--ignore-cache-version' in message
    assert error.differences['schema_version'] == SCHEMA_DIFFERENCE


def test_graphql_error_keeps_its_own_copy_of_the_pairs() -> None:
    pairs = [INTERNAL_BOOM]
    error = wambatic.fetch.errors.GraphQLError(pairs)
    pairs.append(FORBIDDEN_NO)
    assert error.errors == (INTERNAL_BOOM,)


def test_cache_version_error_differences_cannot_be_changed() -> None:
    source: dict[str, tuple[str | None, str | None]] = {'schema_version': SCHEMA_DIFFERENCE}
    error = wambatic.fetch.errors.CacheVersionError(source)
    source['other'] = LETTERS
    assert 'other' not in error.differences
    with pytest.raises(TypeError):
        error.differences['other'] = LETTERS  # type: ignore[index]
