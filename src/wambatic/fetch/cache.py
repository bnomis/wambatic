import collections.abc
import contextlib
import dataclasses
import datetime
import functools
import hashlib
import json
import pathlib
import sqlite3
import threading
import types
import typing

import wambatic.fetch.base
import wambatic.fetch.errors
import wambatic.fetch.queries
import wambatic.version

SCHEMA_VERSION = 4

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE IF NOT EXISTS repos (
    name_with_owner TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    default_branch TEXT,
    head_oid TEXT,
    is_archived INTEGER NOT NULL,
    is_fork INTEGER NOT NULL,
    pushed_at TEXT,
    updated_at TEXT NOT NULL,
    pull_requests_updated_at TEXT,
    issues_updated_at TEXT,
    releases_count INTEGER NOT NULL DEFAULT 0,
    releases_updated_at TEXT,
    stargazer_count INTEGER NOT NULL DEFAULT 0,
    fork_count INTEGER NOT NULL DEFAULT 0,
    watcher_count INTEGER NOT NULL DEFAULT 0,
    languages TEXT NOT NULL DEFAULT '[]',
    languages_size INTEGER NOT NULL DEFAULT 0,
    missing INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS repos_owner ON repos (owner);
CREATE TABLE IF NOT EXISTS commits (
    repo TEXT NOT NULL,
    oid TEXT NOT NULL,
    authored_at TEXT NOT NULL,
    author_login TEXT,
    additions INTEGER NOT NULL,
    deletions INTEGER NOT NULL,
    is_merge INTEGER NOT NULL,
    PRIMARY KEY (repo, oid)
);
CREATE INDEX IF NOT EXISTS commits_repo_authored_at ON commits (repo, authored_at);
CREATE TABLE IF NOT EXISTS pull_requests (
    repo TEXT NOT NULL,
    number INTEGER NOT NULL,
    author_login TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    merged_at TEXT,
    closed_at TEXT,
    first_review_at TEXT,
    additions INTEGER NOT NULL,
    deletions INTEGER NOT NULL,
    labels TEXT NOT NULL DEFAULT '[]',
    first_commit_at TEXT,
    PRIMARY KEY (repo, number)
);
CREATE INDEX IF NOT EXISTS pull_requests_repo_updated_at ON pull_requests (repo, updated_at);
CREATE TABLE IF NOT EXISTS issues (
    repo TEXT NOT NULL,
    number INTEGER NOT NULL,
    author_login TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    closed_at TEXT,
    PRIMARY KEY (repo, number)
);
CREATE INDEX IF NOT EXISTS issues_repo_updated_at ON issues (repo, updated_at);
CREATE TABLE IF NOT EXISTS releases (
    repo TEXT NOT NULL,
    tag_name TEXT NOT NULL,
    created_at TEXT NOT NULL,
    published_at TEXT NOT NULL,
    is_prerelease INTEGER NOT NULL,
    PRIMARY KEY (repo, tag_name)
);
CREATE TABLE IF NOT EXISTS workflow_runs (
    repo TEXT NOT NULL,
    id INTEGER NOT NULL,
    workflow_path TEXT NOT NULL,
    name TEXT NOT NULL,
    event TEXT NOT NULL,
    head_branch TEXT,
    status TEXT NOT NULL,
    conclusion TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    run_started_at TEXT,
    run_attempt INTEGER NOT NULL,
    PRIMARY KEY (repo, id)
);
CREATE INDEX IF NOT EXISTS workflow_runs_repo_created_at ON workflow_runs (repo, created_at);
CREATE INDEX IF NOT EXISTS workflow_runs_repo_status ON workflow_runs (repo, status);
CREATE TABLE IF NOT EXISTS star_events (
    repo TEXT NOT NULL,
    user_id TEXT NOT NULL,
    starred_at TEXT NOT NULL,
    PRIMARY KEY (repo, user_id)
);
CREATE INDEX IF NOT EXISTS star_events_repo_starred_at ON star_events (repo, starred_at);
CREATE TABLE IF NOT EXISTS forks (
    repo TEXT NOT NULL,
    id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    PRIMARY KEY (repo, id)
);
CREATE INDEX IF NOT EXISTS forks_repo_created_at ON forks (repo, created_at);
CREATE TABLE IF NOT EXISTS etags (url TEXT PRIMARY KEY, etag TEXT NOT NULL, body TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS sync_state (
    repo TEXT NOT NULL,
    resource TEXT NOT NULL,
    watermark TEXT,
    head_oid TEXT,
    pushed_at TEXT,
    updated_at TEXT NOT NULL,
    synced_at TEXT NOT NULL,
    full_synced_at TEXT NOT NULL,
    probe TEXT,
    PRIMARY KEY (repo, resource)
);
"""
OVERRIDE_KEY = 'version_override_at'


def expected_identity() -> dict[str, str]:
    """What a cache written by the running code records in `meta`."""
    identity = {
        'schema_version': str(SCHEMA_VERSION),
        'wambatic_version': wambatic.version.VERSION,
    }
    for name, value in vars(wambatic.fetch.queries).items():
        if name.isupper() and isinstance(value, str):
            identity[f'query:{name}'] = hashlib.sha256(value.encode()).hexdigest()
    return identity


def identity_differences(
    recorded: dict[str, str], expected: dict[str, str]
) -> dict[str, tuple[str | None, str | None]]:
    """Each key whose recorded and expected values differ, as (recorded, expected)."""
    return {
        key: (recorded.get(key), expected.get(key))
        for key in sorted(recorded.keys() | expected.keys())
        if recorded.get(key) != expected.get(key)
    }


def to_text(value: datetime.datetime) -> str:
    """ISO 8601 UTC at one fixed width, so text order is time order.

    Raises:
        InvalidRequestError: `value` is naive.
    """
    if value.tzinfo is None:
        raise wambatic.fetch.errors.InvalidRequestError('cache times must be timezone-aware')
    return value.astimezone(datetime.UTC).isoformat(timespec='microseconds')


def optional_to_text(value: datetime.datetime | None) -> str | None:
    return None if value is None else to_text(value)


def from_text(value: str) -> datetime.datetime:
    return datetime.datetime.fromisoformat(value)


def optional_from_text(value: str | None) -> datetime.datetime | None:
    return None if value is None else from_text(value)


class Record(typing.Protocol):
    @property
    def repo(self) -> str: ...


type Converters = collections.abc.Mapping[str, collections.abc.Callable[[typing.Any], object]]


def column_names(record_type: type) -> tuple[str, ...]:
    """The record's field names, in order: its table's columns."""
    return tuple(field.name for field in dataclasses.fields(record_type))


def to_column(value: object) -> object:
    if isinstance(value, datetime.datetime):
        return to_text(value)
    if isinstance(value, tuple):
        return json.dumps(value)
    return value


def record_values(record: object) -> tuple[object, ...]:
    """The record's fields as column values, in `column_names` order."""
    return tuple(to_column(getattr(record, name)) for name in column_names(type(record)))


def as_labels(value: str) -> tuple[str, ...]:
    return tuple(str(label) for label in json.loads(value))


def as_languages(value: str) -> tuple[tuple[str, int], ...]:
    return tuple((str(name), int(size)) for name, size in json.loads(value))


def record_from_row[T](
    build: collections.abc.Callable[..., T],
    converters: Converters,
    columns: tuple[str, ...],
    row: tuple[typing.Any, ...],
    **fixed: object,
) -> T:
    """Build a record from a row of `columns`: each column named in `converters` is converted,
    the rest are used as read; `fixed` supplies the fields the row does not hold."""
    values = dict(zip(columns, row, strict=True))
    for name, convert in converters.items():
        values[name] = convert(values[name])
    return build(**fixed, **values)


@dataclasses.dataclass(frozen=True, slots=True)
class Table[T: Record]:
    """A per-repo table whose columns are the fields of its record type."""

    name: str
    record_type: collections.abc.Callable[..., T]
    columns: tuple[str, ...]
    converters: Converters
    key: tuple[str, ...]

    @classmethod
    def of(
        cls, name: str, record_type: type[T], converters: Converters, key: tuple[str, ...]
    ) -> Table[T]:
        return cls(name, record_type, column_names(record_type), converters, key)

    def values(self, record: T) -> tuple[object, ...]:
        return record_values(record)

    def record(self, repo: str, row: tuple[typing.Any, ...]) -> T:
        """Build a record from a row of the columns after `repo`."""
        return record_from_row(self.record_type, self.converters, self.columns[1:], row, repo=repo)


REPO_CONVERTERS: Converters = types.MappingProxyType(
    {
        'is_archived': bool,
        'is_fork': bool,
        'issues_updated_at': optional_from_text,
        'languages': as_languages,
        'missing': bool,
        'pull_requests_updated_at': optional_from_text,
        'pushed_at': optional_from_text,
        'releases_updated_at': optional_from_text,
        'updated_at': from_text,
    }
)
SYNC_STATE_CONVERTERS: Converters = types.MappingProxyType(
    {
        'full_synced_at': from_text,
        'pushed_at': optional_from_text,
        'synced_at': from_text,
        'updated_at': from_text,
        'watermark': optional_from_text,
    }
)


@dataclasses.dataclass(frozen=True, slots=True)
class Tables:
    """The cache's tables and column lists, each derived once from its record's fields."""

    commits: Table[wambatic.fetch.base.Commit]
    forks: Table[wambatic.fetch.base.Fork]
    issues: Table[wambatic.fetch.base.Issue]
    pull_requests: Table[wambatic.fetch.base.PullRequest]
    releases: Table[wambatic.fetch.base.Release]
    star_events: Table[wambatic.fetch.base.StarEvent]
    workflow_runs: Table[wambatic.fetch.base.WorkflowRun]
    repo_columns: tuple[str, ...]
    sync_state_columns: tuple[str, ...]


@functools.cache
def tables() -> Tables:
    """Built on first use: `wambatic.fetch.base` is not yet reachable while this module loads."""
    COMMITS = Table.of(
        'commits',
        wambatic.fetch.base.Commit,
        {'authored_at': from_text, 'is_merge': bool},
        ('repo', 'oid'),
    )
    PULL_REQUESTS = Table.of(
        'pull_requests',
        wambatic.fetch.base.PullRequest,
        {
            'closed_at': optional_from_text,
            'created_at': from_text,
            'first_commit_at': optional_from_text,
            'first_review_at': optional_from_text,
            'labels': as_labels,
            'merged_at': optional_from_text,
            'updated_at': from_text,
        },
        ('repo', 'number'),
    )
    ISSUES = Table.of(
        'issues',
        wambatic.fetch.base.Issue,
        {'closed_at': optional_from_text, 'created_at': from_text, 'updated_at': from_text},
        ('repo', 'number'),
    )
    RELEASES = Table.of(
        'releases',
        wambatic.fetch.base.Release,
        {'created_at': from_text, 'is_prerelease': bool, 'published_at': from_text},
        ('repo', 'tag_name'),
    )
    WORKFLOW_RUNS = Table.of(
        'workflow_runs',
        wambatic.fetch.base.WorkflowRun,
        {
            'created_at': from_text,
            'run_started_at': optional_from_text,
            'updated_at': from_text,
        },
        ('repo', 'id'),
    )
    STAR_EVENTS = Table.of(
        'star_events',
        wambatic.fetch.base.StarEvent,
        {'starred_at': from_text},
        ('repo', 'user_id'),
    )
    FORKS = Table.of(
        'forks',
        wambatic.fetch.base.Fork,
        {'created_at': from_text},
        ('repo', 'id'),
    )
    return Tables(
        commits=COMMITS,
        forks=FORKS,
        issues=ISSUES,
        pull_requests=PULL_REQUESTS,
        releases=RELEASES,
        star_events=STAR_EVENTS,
        workflow_runs=WORKFLOW_RUNS,
        repo_columns=column_names(wambatic.fetch.base.Repo),
        sync_state_columns=column_names(wambatic.fetch.base.SyncState),
    )


def repo_from_row(row: tuple[typing.Any, ...]) -> wambatic.fetch.base.Repo:
    return record_from_row(wambatic.fetch.base.Repo, REPO_CONVERTERS, tables().repo_columns, row)


def repo_row(repo: wambatic.fetch.base.Repo) -> tuple[object, ...]:
    """The `repos` row for `repo`: the owner after the name, and never marked missing."""
    values = record_values(dataclasses.replace(repo, missing=False))
    return (repo.name_with_owner, repo.name_with_owner.partition('/')[0], *values[1:])


@contextlib.contextmanager
def translate_errors(path: pathlib.Path) -> collections.abc.Iterator[None]:
    """Turn an `sqlite3.Error` or `OSError` raised inside the block into a `CacheError` naming
    `path`, with the original chained.

    Raises:
        CacheError: for an `sqlite3.Error` or `OSError` raised inside the block.
    """
    try:
        yield
    except (sqlite3.Error, OSError) as error:
        # auditme: accept[except-interpolation] the SQLite or OS reason is the payload
        raise wambatic.fetch.errors.CacheError(f'cache {path}: {error}') from error


class Cache:
    """The SQLite cache. One connection, serialised by one lock taken by every public method.

    Each write method is one transaction. Helpers that run inside a method's transaction do not
    take the lock again.
    """

    def __init__(self, connection: sqlite3.Connection, path: pathlib.Path) -> None:
        self.connection = connection
        self.path = path
        self.lock = threading.Lock()

    @classmethod
    def open(cls, path: pathlib.Path, *, ignore_version: bool = False) -> Cache:
        """Create the parent directory and file if absent, set WAL mode, create the schema,
        then check or write the identity; raises CacheVersionError on a mismatch unless
        `ignore_version`, which is recorded in `meta` as `version_override_at`. Raises
        CacheError when the file cannot be created, opened or written."""
        with translate_errors(path):
            # auditme: accept[filesystem-op-without-envelope] translate_errors is its envelope
            path.parent.mkdir(parents=True, exist_ok=True)
            connection = sqlite3.connect(path, check_same_thread=False)
            try:
                connection.execute('PRAGMA journal_mode=WAL')
                connection.execute('PRAGMA foreign_keys=ON')
                connection.executescript(SCHEMA)
                cache = cls(connection, path)
                cache.check_identity(ignore_version)
            except BaseException:
                # Cleans up the half-opened connection, then re-raises the original error.
                connection.close()
                raise
        return cache

    @contextlib.contextmanager
    def locked(self) -> collections.abc.Iterator[None]:
        """Hold the lock, with `translate_errors` around the block.

        Raises:
            CacheError: when the file cannot be read or written.
        """
        with self.lock, translate_errors(self.path):
            yield

    def close(self) -> None:
        with self.locked():
            self.connection.close()

    def check_identity(self, ignore_version: bool) -> None:
        expected = expected_identity()
        with self.locked(), self.connection:
            recorded = self.recorded_identity()
            if not recorded:
                self.connection.executemany(
                    'INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)', expected.items()
                )
                return
            differences = identity_differences(recorded, expected)
            if not differences:
                return
            if not ignore_version:
                raise wambatic.fetch.errors.CacheVersionError(differences)
            self.connection.execute(
                'INSERT OR REPLACE INTO meta (key, value) VALUES (?, ?)',
                (OVERRIDE_KEY, to_text(datetime.datetime.now(datetime.UTC))),
            )

    def recorded_identity(self) -> dict[str, str]:
        rows = self.connection.execute('SELECT key, value FROM meta').fetchall()
        return {key: value for key, value in rows if key != OVERRIDE_KEY}

    def identity(self) -> dict[str, str]:
        with self.locked():
            return self.recorded_identity()

    def version_override_at(self) -> str | None:
        """When the cache was opened with `ignore_version` over a difference, if it was."""
        with self.locked():
            row = self.connection.execute(
                'SELECT value FROM meta WHERE key = ?', (OVERRIDE_KEY,)
            ).fetchone()
        return None if row is None else str(row[0])

    def upsert_repos(
        self, owner: str, repos: list[wambatic.fetch.base.Repo], *, complete: bool
    ) -> None:
        """Insert or replace each repo; with `complete`, mark the owner's other repos missing."""
        with self.locked(), self.connection:
            if complete:
                self.connection.execute(
                    'UPDATE repos SET missing = 1 WHERE owner = ? COLLATE NOCASE', (owner,)
                )
            names = (tables().repo_columns[0], 'owner', *tables().repo_columns[1:])
            self.connection.executemany(
                f'INSERT OR REPLACE INTO repos ({", ".join(names)}) '
                f'VALUES ({", ".join("?" * len(names))})',
                [repo_row(repo) for repo in repos],
            )

    def read_repos(self, subject: wambatic.fetch.base.Subject) -> list[wambatic.fetch.base.Repo]:
        columns = ', '.join(tables().repo_columns)
        with self.locked():
            if subject.kind == 'repo':
                rows = self.connection.execute(
                    f'SELECT {columns} FROM repos WHERE name_with_owner = ? COLLATE NOCASE',
                    (subject.full_name,),
                ).fetchall()
            else:
                rows = self.connection.execute(
                    f'SELECT {columns} FROM repos WHERE owner = ? COLLATE NOCASE '
                    'ORDER BY name_with_owner',
                    (subject.login,),
                ).fetchall()
        return [repo_from_row(row) for row in rows]

    def sync_state(self, repo: str, resource: str) -> wambatic.fetch.base.SyncState | None:
        with self.locked():
            row = self.connection.execute(
                f'SELECT {", ".join(tables().sync_state_columns[2:])} FROM sync_state '
                'WHERE repo = ? AND resource = ?',
                (repo, resource),
            ).fetchone()
        if row is None:
            return None
        return record_from_row(
            wambatic.fetch.base.SyncState,
            SYNC_STATE_CONVERTERS,
            tables().sync_state_columns[2:],
            row,
            repo=repo,
            resource=resource,
        )

    def put_state(self, state: wambatic.fetch.base.SyncState) -> None:
        """Write a `sync_state` row inside the caller's transaction."""
        self.connection.execute(
            f'INSERT OR REPLACE INTO sync_state ({", ".join(tables().sync_state_columns)}) '
            f'VALUES ({", ".join("?" * len(tables().sync_state_columns))})',
            record_values(state),
        )

    def write_state(self, state: wambatic.fetch.base.SyncState) -> None:
        """Write a `sync_state` row alone, in its own transaction."""
        with self.locked(), self.connection:
            self.put_state(state)

    def write_rows[T: Record](
        self,
        table: Table[T],
        repo: str,
        records: list[T],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
        gone: collections.abc.Collection[int] = (),
    ) -> int:
        """In one transaction: with `replace`, delete the repo's rows from `table` first; upsert
        each record by its key; delete the rows whose second key column is in `gone`; write
        `state`. Returns the number of rows written.

        Raises:
            InvalidRequestError: a record or the state belongs to another repo.
        """
        if any(record.repo != repo for record in records) or state.repo != repo:
            raise wambatic.fetch.errors.InvalidRequestError(
                f'every record and the state must belong to {repo}'
            )
        columns = table.columns
        updates = ', '.join(
            f'{name} = excluded.{name}' for name in columns if name not in table.key
        )
        sql = (
            f'INSERT INTO {table.name} ({", ".join(columns)}) '
            f'VALUES ({", ".join("?" * len(columns))}) '
            f'ON CONFLICT ({", ".join(table.key)}) DO UPDATE SET {updates}'
        )
        with self.locked(), self.connection:
            if replace:
                self.connection.execute(f'DELETE FROM {table.name} WHERE repo = ?', (repo,))
            self.connection.executemany(sql, [table.values(record) for record in records])
            self.connection.executemany(
                f'DELETE FROM {table.name} WHERE repo = ? AND {table.key[1]} = ?',
                [(repo, identifier) for identifier in sorted(gone)],
            )
            self.put_state(state)
        return len(records)

    def read_table[T: Record](
        self,
        table: Table[T],
        repo: str,
        since: datetime.datetime | None,
        until: datetime.datetime | None = None,
        *,
        time_column: str,
        order: str,
    ) -> list[T]:
        """The repo's records with `since <= time_column < until`, each bound optional."""
        query = f'SELECT {", ".join(table.columns[1:])} FROM {table.name} WHERE repo = ?'
        params: list[str] = [repo]
        if since is not None:
            query += f' AND {time_column} >= ?'
            params.append(to_text(since))
        if until is not None:
            query += f' AND {time_column} < ?'
            params.append(to_text(until))
        with self.locked():
            rows = self.connection.execute(f'{query} ORDER BY {order}', params).fetchall()
        return [table.record(repo, row) for row in rows]

    def write_commits(
        self,
        repo: str,
        commits: list[wambatic.fetch.base.Commit],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
    ) -> int:
        """In one transaction: with `replace`, delete the repo's commits first; upsert by oid;
        write `state`. Returns the number of rows written."""
        return self.write_rows(tables().commits, repo, commits, state, replace=replace)

    def write_pull_requests(
        self,
        repo: str,
        pulls: list[wambatic.fetch.base.PullRequest],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
    ) -> int:
        """As `write_commits`, upserting by number."""
        return self.write_rows(tables().pull_requests, repo, pulls, state, replace=replace)

    def write_issues(
        self,
        repo: str,
        issues: list[wambatic.fetch.base.Issue],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
    ) -> int:
        """As `write_commits`, upserting by number."""
        return self.write_rows(tables().issues, repo, issues, state, replace=replace)

    def write_releases(
        self,
        repo: str,
        releases: list[wambatic.fetch.base.Release],
        state: wambatic.fetch.base.SyncState,
    ) -> int:
        """As `write_commits` with `replace`: every read of releases is a full read."""
        return self.write_rows(tables().releases, repo, releases, state, replace=True)

    def write_workflow_runs(
        self,
        repo: str,
        runs: list[wambatic.fetch.base.WorkflowRun],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
        gone: collections.abc.Collection[int] = (),
    ) -> int:
        """As `write_commits`, upserting by id; the runs whose ids are in `gone` are deleted."""
        return self.write_rows(
            tables().workflow_runs, repo, runs, state, replace=replace, gone=gone
        )

    def write_star_events(
        self,
        repo: str,
        stars: list[wambatic.fetch.base.StarEvent],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
    ) -> int:
        """As `write_commits`, upserting by `user_id`."""
        return self.write_rows(tables().star_events, repo, stars, state, replace=replace)

    def write_forks(
        self,
        repo: str,
        forks: list[wambatic.fetch.base.Fork],
        state: wambatic.fetch.base.SyncState,
        *,
        replace: bool,
    ) -> int:
        """As `write_commits`, upserting by id."""
        return self.write_rows(tables().forks, repo, forks, state, replace=replace)

    def read_commits(
        self, repo: str, since: datetime.datetime | None, until: datetime.datetime | None
    ) -> list[wambatic.fetch.base.Commit]:
        return self.read_table(
            tables().commits,
            repo,
            since,
            until,
            time_column='authored_at',
            order='authored_at, oid',
        )

    def read_pull_requests(
        self, repo: str, since: datetime.datetime | None
    ) -> list[wambatic.fetch.base.PullRequest]:
        """Rows with `updated_at >= since` (all when None), by number."""
        return self.read_table(
            tables().pull_requests, repo, since, time_column='updated_at', order='number'
        )

    def read_issues(
        self, repo: str, since: datetime.datetime | None
    ) -> list[wambatic.fetch.base.Issue]:
        """Rows with `updated_at >= since` (all when None), by number."""
        return self.read_table(
            tables().issues, repo, since, time_column='updated_at', order='number'
        )

    def read_releases(self, repo: str) -> list[wambatic.fetch.base.Release]:
        """All the repo's rows, oldest `published_at` first."""
        return self.read_table(
            tables().releases,
            repo,
            None,
            time_column='published_at',
            order='published_at, tag_name',
        )

    def read_workflow_runs(
        self, repo: str, since: datetime.datetime | None
    ) -> list[wambatic.fetch.base.WorkflowRun]:
        """Rows with `created_at >= since` (all when None), oldest first."""
        return self.read_table(
            tables().workflow_runs, repo, since, time_column='created_at', order='created_at, id'
        )

    def read_star_events(self, repo: str) -> list[wambatic.fetch.base.StarEvent]:
        """All the repo's rows, oldest `starred_at` first."""
        return self.read_table(
            tables().star_events, repo, None, time_column='starred_at', order='starred_at, user_id'
        )

    def read_forks(self, repo: str) -> list[wambatic.fetch.base.Fork]:
        """All the repo's rows, oldest `created_at` first."""
        return self.read_table(
            tables().forks, repo, None, time_column='created_at', order='created_at, id'
        )

    def unfinished_runs(self, repo: str) -> list[int]:
        """Ids of the repo's runs whose status is not `completed`, ascending."""
        with self.locked():
            rows = self.connection.execute(
                "SELECT id FROM workflow_runs WHERE repo = ? AND status != 'completed' ORDER BY id",
                (repo,),
            ).fetchall()
        return [int(row[0]) for row in rows]

    def etag(self, url: str) -> tuple[str, object] | None:
        """The stored ETag and parsed body for a REST URL."""
        with self.locked():
            row = self.connection.execute(
                'SELECT etag, body FROM etags WHERE url = ?', (url,)
            ).fetchone()
        return None if row is None else (row[0], json.loads(row[1]))

    def store_etag(self, url: str, etag: str, body: object) -> None:
        with self.locked(), self.connection:
            self.connection.execute(
                'INSERT OR REPLACE INTO etags (url, etag, body) VALUES (?, ?, ?)',
                (url, etag, json.dumps(body)),
            )


@dataclasses.dataclass(frozen=True, slots=True)
class CacheInfo:
    path: pathlib.Path
    size_bytes: int
    identity: dict[str, str]
    differences: dict[str, tuple[str | None, str | None]]
    version_override_at: str | None
    repos: int
    commits: int
    pull_requests: int
    issues: int
    releases: int
    workflow_runs: int
    star_events: int
    forks: int
    last_synced_at: datetime.datetime | None


def inspect_cache(path: pathlib.Path) -> CacheInfo | None:
    """What `path` holds, read with plain SELECTs on its own connection, or None when it does
    not exist. It creates, migrates and stamps nothing, so a cache `Cache.open` refuses can still
    be inspected; a table absent from the file counts as 0 rows."""
    with translate_errors(path):
        return read_cache_info(path)


def read_cache_info(path: pathlib.Path) -> CacheInfo | None:
    if not path.exists():
        return None
    connection = sqlite3.connect(path)
    try:
        tables = {
            name
            for (name,) in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }

        def scalar(table: str, query: str) -> object:
            return connection.execute(query).fetchone()[0] if table in tables else None

        meta: dict[str, str] = (
            dict(connection.execute('SELECT key, value FROM meta').fetchall())
            if 'meta' in tables
            else {}
        )
        last_synced = scalar('sync_state', 'SELECT MAX(synced_at) FROM sync_state')
        repos = scalar('repos', 'SELECT COUNT(*) FROM repos WHERE missing = 0')
        commits = scalar('commits', 'SELECT COUNT(*) FROM commits')
        pull_requests = scalar('pull_requests', 'SELECT COUNT(*) FROM pull_requests')
        issues = scalar('issues', 'SELECT COUNT(*) FROM issues')
        releases = scalar('releases', 'SELECT COUNT(*) FROM releases')
        workflow_runs = scalar('workflow_runs', 'SELECT COUNT(*) FROM workflow_runs')
        star_events = scalar('star_events', 'SELECT COUNT(*) FROM star_events')
        forks = scalar('forks', 'SELECT COUNT(*) FROM forks')
    finally:
        connection.close()
    identity = {key: value for key, value in meta.items() if key != OVERRIDE_KEY}
    wal = path.with_name(path.name + '-wal')
    return CacheInfo(
        path=path,
        size_bytes=path.stat().st_size + (wal.stat().st_size if wal.exists() else 0),
        identity=identity,
        differences=identity_differences(identity, expected_identity()),
        version_override_at=meta.get(OVERRIDE_KEY),
        repos=int(str(repos or 0)),
        commits=int(str(commits or 0)),
        pull_requests=int(str(pull_requests or 0)),
        issues=int(str(issues or 0)),
        releases=int(str(releases or 0)),
        workflow_runs=int(str(workflow_runs or 0)),
        star_events=int(str(star_events or 0)),
        forks=int(str(forks or 0)),
        last_synced_at=None if last_synced is None else from_text(str(last_synced)),
    )


def clear_cache(path: pathlib.Path) -> list[pathlib.Path]:
    """Delete `path` and its `-wal` and `-shm` files where present; return those deleted.

    Raises:
        CacheError: when a file that exists cannot be deleted.
    """
    deleted: list[pathlib.Path] = []
    for candidate in (path, path.with_name(path.name + '-wal'), path.with_name(path.name + '-shm')):
        try:
            candidate.unlink()
        except FileNotFoundError:
            continue
        except OSError as error:
            # auditme: accept[except-interpolation] the SQLite or OS reason is the payload
            raise wambatic.fetch.errors.CacheError(f'cannot delete {candidate}: {error}') from error
        deleted.append(candidate)
    return deleted
