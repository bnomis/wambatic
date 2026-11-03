# Cache

**Version:** 1.3
**Status:** proposed
**Date:** 2026-11-03

The local SQLite store behind [Fetch](../fetch/spec.md): repositories, commits, pull requests, issues, releases, workflow runs, stars and forks, the per-repository sync state that makes a later sync incremental, REST ETags, and the identity (schema, wambatic and query versions) that refuses a cache written by different code. It knows nothing about GitHub requests or metrics; `Fetcher` writes it and reads it back for [Stats](../stats/spec.md).

**Prerequisite:** the record dataclasses of the [Fetch spec](../fetch/spec.md) exist in `src/wambatic/fetch/base.py` (check: `python -c 'import wambatic.fetch.base'`). Terms such as "step 5" and "Incremental sync" below refer to the [implementation order](../implementation-order.md) and to the Implementation section of the Fetch spec.

Version 1.1 records the GitHub host in the identity, refuses a cache made for another host with `CacheHostError`, records the Enterprise server's version, and gives each host its own default file, for GitHub Enterprise Server ([Fetch](../fetch/spec.md) 1.16); the choices are in the [fetch review 1](../fetch/review-1.md), decided 2026-11-02.

Version 1.2 stores each commit's per-file line counts (`commit_files`) and each repository's followed branch heads (`branch_heads`), deletes the commits a sync finds gone, and clears the bare clones with the file, for the clone-based commit sync ([Commit sync](../commit-sync/spec.md), [Fetch](../fetch/spec.md) 1.17); `SCHEMA_VERSION` becomes 5. The choices are in the [commit sync review 1](../commit-sync/review-1.md), decided 2026-11-02.

Version 1.3 stores each commit's recorded UTC offset (`commits.authored_offset`) for dating commits in their authors' zones ([Author timezones](../author-timezones/spec.md)); `SCHEMA_VERSION` becomes 6. The choices are in the [author timezones review 1](../author-timezones/review-1.md), decided 2026-11-03.

## Module location

`src/wambatic/fetch/cache.py`, with tests in `src/tests/fetch/test_cache.py`:

| Module | Holds | Built in implementation step |
|--------|-------|------------------------------|
| `cache.py` | `Cache`, `SCHEMA_VERSION`: SQLite schema, identity, watermarks, ETags; `CacheInfo`, `inspect_cache`, `clear_cache` | 3 (`CacheInfo`, `inspect_cache`, `clear_cache` in 5; the `pull_requests` and `issues` tables in 6; the `releases` and `workflow_runs` tables in 8; the `star_events` and `forks` tables and the `repos` popularity columns in 10; the `commit_files` and `branch_heads` tables in 14) |

Version history. This spec was split from the fetch-and-cache spec (1.x) on 2026-10-31 (audit review 2, Decision 2, option A). The history of the cache before the split is in the version paragraphs of the [Fetch spec](../fetch/spec.md) (1.4 to 1.14), whose text describes the cache and the fetcher together.

## API

The cache, used only inside `wambatic.fetch` and by the CLI's `cache` command. Its methods are synchronous; `Fetcher` calls them through `asyncio.to_thread`, and one `threading.Lock` serialises them on the cache's single connection (opened with `check_same_thread=False`):

```python
import pathlib

SCHEMA_VERSION: int = 6   # 2 from step 6: the pull_requests and issues tables; 3 from step 8, 4 from step 10, 5 from step 14, 6 from step 15: see Cache

# Repo, Commit, PullRequest, Issue, Release, WorkflowRun, StarEvent, Fork and SyncState
# are the records of the Fetch spec (base.py); cache.py imports them

class Cache:
    @classmethod
    def open(cls, path: pathlib.Path, *, host: str = 'github.com', ignore_version: bool = False) -> Cache:
        """Create the parent directory and file if absent, set WAL mode, create the schema,
        then check or write the identity; raises CacheVersionError on a mismatch unless
        `ignore_version`, which is recorded in `meta` as `version_override_at`. Raises
        CacheHostError when the recorded `github_host` is not `host`, whatever
        `ignore_version` says (1.1)."""
    def close(self) -> None: ...

    def identity(self) -> dict[str, str]:
        """The recorded `meta` rows except `version_override_at`."""
    def version_override_at(self) -> str | None:
        """The recorded `version_override_at`, or None when the identity matched."""
    def server_version(self) -> str | None:
        """The recorded `server_version` row, or None (1.1)."""
    def write_server_version(self, version: str) -> None:
        """Insert or replace the `server_version` row (1.1)."""
    def upsert_repos(self, owner: str, repos: list[Repo], *, complete: bool) -> None:
        """Insert or replace each repo; with `complete`, mark the owner's other repos missing."""
    def read_repos(self, subject: Subject) -> list[Repo]: ...
    def sync_state(self, repo: str, resource: str) -> SyncState | None: ...
    def write_commits(self, repo: str, commits: list[Commit], state: SyncState, *, replace: bool,
                      gone: collections.abc.Collection[str] = (),
                      branch_heads: collections.abc.Mapping[str, str] | None = None,
                      generated: collections.abc.Collection[str] | None = None) -> int:
        """In one transaction: with `replace`, delete the repo's commits first; delete the commits
        whose oids are in `gone`, with their files; upsert by oid, each commit's `files` replacing
        its file rows; when `generated` is given, set every file row of the repo whose path is in
        it to generated and every other to not (1.2); when `branch_heads` is given, replace the
        repo's branch heads with it (1.2); write `state`. Returns the number of commits written."""
    # auditme: accept[spec-api-signature-drift] Cache.read_commits; the checker matches stats.read_commits by name
    def read_commits(self, repo: str, since: datetime.datetime | None, until: datetime.datetime | None) -> list[Commit]:
        """With each commit's `files`, by path (1.2)."""
    def commit_oids(self, repo: str) -> frozenset[str]:
        """Every cached commit oid of the repo (1.2)."""
    def commit_paths(self, repo: str) -> frozenset[str]:
        """Every path in the repo's file rows (1.2)."""
    def branch_heads(self, repo: str) -> dict[str, str]:
        """The followed branch heads written by the last commit sync (1.2)."""
    def write_pull_requests(self, repo: str, pulls: list[PullRequest], state: SyncState, *, replace: bool) -> int:
        """As `write_commits`, upserting by number."""
    def read_pull_requests(self, repo: str, since: datetime.datetime | None) -> list[PullRequest]:
        """Rows with `updated_at >= since` (all when None), by number."""
    def write_issues(self, repo: str, issues: list[Issue], state: SyncState, *, replace: bool) -> int: ...
    def read_issues(self, repo: str, since: datetime.datetime | None) -> list[Issue]: ...
    def write_releases(self, repo: str, releases: list[Release], state: SyncState) -> int:
        """In one transaction: delete the repo's releases, insert these, write `state`. Every
        read of releases is a full read, so there is no `replace` flag."""
    def read_releases(self, repo: str) -> list[Release]: ...
    def write_workflow_runs(self, repo: str, runs: list[WorkflowRun], state: SyncState, *, replace: bool, gone: collections.abc.Collection[int] = ()) -> int:
        """As `write_commits`, upserting by `id`; also deletes the runs whose ids are in `gone`."""
    def read_workflow_runs(self, repo: str, since: datetime.datetime | None) -> list[WorkflowRun]:
        """Rows with `created_at >= since` (all when None), oldest first."""
    def unfinished_runs(self, repo: str) -> list[int]:
        """Ids of the repo's cached runs whose `status` is not `completed`, ascending."""
    def write_state(self, state: SyncState) -> None:
        """Write a `sync_state` row alone, in its own transaction (1.9)."""
    def write_star_events(self, repo: str, stars: list[StarEvent], state: SyncState, *, replace: bool) -> int:
        """As `write_commits`, upserting by `user_id` (step 10)."""
    def read_star_events(self, repo: str) -> list[StarEvent]:
        """Every row, oldest `starred_at` first, then `user_id`."""
    def write_forks(self, repo: str, forks: list[Fork], state: SyncState, *, replace: bool) -> int:
        """As `write_commits`, upserting by `id` (step 10)."""
    def read_forks(self, repo: str) -> list[Fork]:
        """Every row, oldest `created_at` first, then `id`."""
    def etag(self, url: str) -> tuple[str, object] | None:
        """The stored ETag and parsed body for a REST URL."""
    def store_etag(self, url: str, etag: str, body: object) -> None: ...

@dataclasses.dataclass(frozen=True, slots=True)
class CacheInfo:
    path: pathlib.Path
    size_bytes: int                                        # the file plus its -wal file
    identity: dict[str, str]                               # recorded `meta` rows, as Cache.identity()
    differences: dict[str, tuple[str | None, str | None]]  # key -> (recorded, running), as CacheVersionError
    version_override_at: str | None
    repos: int                                             # rows not marked missing
    commits: int
    commit_files: int                                      # from step 14
    clones_bytes: int                                      # the clones directory, from step 14
    pull_requests: int                                     # from step 6
    issues: int                                            # from step 6
    releases: int                                          # from step 8
    workflow_runs: int                                     # from step 8
    star_events: int                                       # from step 10
    forks: int                                             # from step 10
    last_synced_at: datetime.datetime | None               # latest `sync_state.synced_at`

def inspect_cache(path: pathlib.Path, clones_dir: pathlib.Path) -> CacheInfo | None:
    """None when `path` does not exist. Otherwise reads the file with plain SELECTs on its own
    connection: no schema creation, no identity check or write, no WAL pragma, so a cache that
    `Cache.open` refuses can still be inspected. A table absent from the file counts as 0 rows."""

def clear_cache(path: pathlib.Path, clones_dir: pathlib.Path) -> list[pathlib.Path]:
    """Delete `path` and its `-wal` and `-shm` files where present, and the `clones_dir`
    tree (1.2); return those deleted. Callers pass `clones_dir_for(settings)`."""
```

## Error handling

- `FetchError` and its other subclasses are in the [Fetch spec](../fetch/spec.md); the errors below are `FetchError`s too.
- `CacheError`: the cache file cannot be opened, read or written (a locked or corrupt file, a full disc, a directory that cannot be created); `sqlite3` and `OSError` failures are translated to it at the `Cache` boundary and by `inspect_cache`.
- `CacheHostError` (1.1), a `CacheError`: the cache was made for another GitHub host. It names the cache path and both hosts, and says to set `fetch.cache_path` to another file or run `wambatic cache clear` with that host. `--ignore-cache-version` does not override it: records from two hosts must never share a cache.
- `CacheVersionError`: the cache was written under a different schema or query version (see Cache). It names both versions and tells the user to run `wambatic cache clear` or pass `--ignore-cache-version`. It never warns and carries on, per the shared versions rule.

## Implementation

**Cache.** One SQLite file (`fetch.cache_path`, default `~/.cache/wambatic/cache.sqlite3`) in WAL mode. Tables: `meta(key, value)`, `repos`, `commits`, `pull_requests`, `issues`, `releases`, `workflow_runs`, `star_events`, `forks`, `etags(url, etag, body)`, and `sync_state(repo, resource, watermark, head_oid, pushed_at, updated_at, synced_at, full_synced_at, probe)`. Each step creates only the tables its resources use; step 3 creates `meta`, `repos`, `commits`, `etags` and `sync_state`, and a later table is a `SCHEMA_VERSION` increase. Step 6 adds `pull_requests` and `issues` (primary key `(repo, number)`, indexed on `(repo, updated_at)`) and the `repos` columns `pull_requests_updated_at` and `issues_updated_at`, and sets `SCHEMA_VERSION` to 2, so a cache written before step 6 is refused once with the `CacheVersionError` message and is cleared and refetched; there is no migration. Step 8 adds `releases` (primary key `(repo, tag_name)`) and `workflow_runs` (primary key `(repo, id)`, indexed on `(repo, created_at)` and `(repo, status)`), the `pull_requests` columns `labels` (a JSON array of names) and `first_commit_at`, the `repos` columns `releases_count` and `releases_updated_at`, and the `sync_state` column `probe`, and sets `SCHEMA_VERSION` to 3, with the same refusal. Step 10 adds `star_events` (primary key `(repo, user_id)`, indexed on `(repo, starred_at)`) and `forks` (primary key `(repo, id)`, indexed on `(repo, created_at)`), the `repos` columns `stargazer_count`, `fork_count`, `watcher_count`, `languages` (a JSON array of `[name, bytes]` pairs, largest first) and `languages_size`, and sets `SCHEMA_VERSION` to 4, with the same refusal. Step 14 adds `commit_files(repo, oid, path, additions, deletions, binary, generated)` (primary key `(repo, oid, path)`, rows deleted with their commit) `branch_heads(repo, branch, head_oid)` (primary key `(repo, branch)`) and the `repos` column `visibility`, and sets `SCHEMA_VERSION` to 5, with the same refusal: a cache of 4 holds totals only, and its commits are refetched through a clone. Step 15 adds the `commits` column `authored_offset` (minutes east of UTC, null when unknown) and sets `SCHEMA_VERSION` to 6, with the same refusal. Timestamps are stored as ISO 8601 UTC text. REST responses also store their `ETag` and are revalidated with `If-None-Match`, which does not count against the limit when answered 304; a 304 returns the stored body.

**Cache identity.** `meta` records `schema_version` (`SCHEMA_VERSION` in `cache.py`), the wambatic version (`wambatic.version.VERSION`), and `query:<NAME>` = the SHA-256 hex digest of each query text constant in `queries.py`. A new file has its identity written; opening a file whose recorded identity differs in any key from the running code raises `CacheVersionError` naming each differing key with both values, unless `ignore_version` is passed. Provenance reads the same values from `Cache.identity()`.

**The host (1.1).** `meta` also records `github_host`, the `fetch.github_host` the cache was made for. A file without that row was made before 1.1, when only github.com could be read, so `open` reads it as `github.com` and writes the row; nothing else changes, so a github.com cache made before 1.1 keeps working. `github_host` is checked before the other keys and apart from them (`CacheHostError` above), and is part of `Cache.identity()`, so provenance names it. `server_version`, the Enterprise server's `installed_version` at the last sync, is a `meta` row outside the identity, like `version_override_at`: a server upgrade changes it without refusing the cache. `inspect_cache` reports both rows.

**One file per host (1.1).** `wambatic.settings.cache_path_for(settings: FetchSettings) -> pathlib.Path` gives the file: `fetch.cache_path` when set; otherwise `~/.cache/wambatic/cache.sqlite3` for github.com, as before, and `~/.cache/wambatic/cache-<host>.sqlite3` for another host, with `:` in the host replaced by `-`. Every caller that opened `settings.fetch.cache_path` (the `report`, `serve` and `cache` commands) uses `cache_path_for`.

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `fetch.cache_path` | `Path \| None` | `None` | SQLite cache file; `None` gives the host's default file (see One file per host) |

## External dependencies

- Stdlib `sqlite3`.
