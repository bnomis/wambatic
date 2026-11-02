import datetime
import pathlib
import types

NO_TOKEN_MESSAGE = 'No GitHub token found: set GITHUB_TOKEN or run `gh auth login`'


class FetchError(Exception):
    """Base class of every error the fetch layer raises."""


class InvalidRequestError(FetchError):
    """A caller mistake: an unknown resource, a malformed subject, records of another repo."""


class AuthError(FetchError):
    pass


class GraphQLError(FetchError):
    def __init__(self, errors: list[tuple[str, str]], context: str | None = None) -> None:
        self.errors = tuple(errors)
        message = '; '.join(f'{kind}: {message}' for kind, message in errors)
        super().__init__(f'{message} ({context})' if context else message)


class NotFoundError(FetchError):
    pass


class RateLimitError(FetchError):
    def __init__(self, reset_at: datetime.datetime) -> None:
        self.reset_at = reset_at
        stamp = reset_at.astimezone(datetime.UTC).isoformat()
        super().__init__(f'GitHub rate limit exhausted; resets at {stamp}')


class StatsPendingError(FetchError):
    pass


class ServerVersionError(FetchError):
    """An Enterprise Server host reports no usable version, or one older than `minimum`.

    `host` is None where the version text is parsed without a host to hand.
    """

    def __init__(
        self,
        host: str | None,
        found: str | None,
        minimum: tuple[int, int],
    ) -> None:
        self.host = host
        self.found = found
        self.minimum = minimum
        where = host or 'the GitHub host'
        seen = f'version {found!r}' if found else 'no version'
        super().__init__(
            f'{where} reports {seen}; wambatic needs GitHub Enterprise Server '
            f'{minimum[0]}.{minimum[1]} or newer'
        )


class CacheError(FetchError):
    """The cache file cannot be opened, read or written (a locked or corrupt file, a full
    disc, a directory that cannot be created)."""


class CacheHostError(CacheError):
    """The cache was made for another GitHub host; `--ignore-cache-version` does not override it."""

    def __init__(self, path: pathlib.Path, recorded: str, requested: str) -> None:
        self.path = path
        self.recorded = recorded
        self.requested = requested
        super().__init__(
            f'The cache {path} was made for {recorded}, not {requested}. Set `fetch.cache_path` '
            f'to another file, or run `wambatic cache clear` with the host {recorded}'
        )


class CacheVersionError(FetchError):
    """The cache was written under a different schema, wambatic or query version.

    `differences` maps each differing key to its (recorded, running) values; None means the key
    is absent on that side.
    """

    def __init__(self, differences: dict[str, tuple[str | None, str | None]]) -> None:
        self.differences = types.MappingProxyType(dict(differences))
        lines = '; '.join(
            f'{key}: cache has {recorded or "nothing"}, this wambatic has {running or "nothing"}'
            for key, (recorded, running) in sorted(differences.items())
        )
        super().__init__(
            f'The cache was written by a different version ({lines}). Run `wambatic cache clear` '
            'to start again, or pass `--ignore-cache-version` for this run'
        )
