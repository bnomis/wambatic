# Commit sync

**Version:** 1.1
**Status:** implemented
**Date:** 2026-11-03

How the `commits` resource is synced from 1.0 of this spec ([Fetch](../fetch/spec.md) 1.17). Each repository's commits are read by one of three methods, chosen per repository at each sync:

- `clone`, for a public repository and for one the user has allowed in `fetch.clone_repos`: a local bare clone, read with `git`, gives every commit's per-file line counts, every followed branch and every history rewrite at no API cost; GraphQL only maps each new commit to its author's GitHub login.
- `api`, the default for every other repository: the sync of Fetch 1.16, unchanged: the default branch only, from the GraphQL history and the REST compare, with per-commit totals and no files.
- `api-files`, when the user sets `fetch.api_history` to `'files'`: the followed branches' GraphQL histories, and each new commit's files from REST, one request per commit; slow, and without linguist attributes.

It lifts two limits the [system spec](../system/spec.md) accepted for the first release, "line counts are not filtered for generated files" and "Default-branch history only", for the repositories read by `clone` or `api-files`; a report names the repositories it could not filter.

**Prerequisite:** the [Fetch](../fetch/spec.md) 1.16 and [Cache](../cache/spec.md) 1.1 code is in place (check: `python -c 'from wambatic.fetch.hosts import GitHubHost'`), and `git` 2.40 or later is on `PATH` (check: `git --version`).

**Motivation.** From `TODO.md`, "The commit sync reads only default-branch totals", consolidated on 2026-11-02 from two findings of that date: each commit's additions and deletions are stored as totals, so a lock file, vendored code or build output cannot be told apart from written code; and incremental sync follows one head per repository, from the stored head of its default branch. Measured on 2026-11-02, on the pallets cache used for the user guide's screenshots (11 repositories, 21,193 default-branch commits):

- GitHub's GraphQL `Commit` has no per-file counts; REST `GET /repos/{owner}/{name}/commits/{sha}` has them, at one request per commit (more for a commit touching over 300 files): 21,193 requests, about 4 hours 15 minutes of the 5,000-per-hour REST budget for a first sync.
- A bare clone of `pallets/flask` took 3 s and 13 MB, and `git log --numstat` over all its branches 1 s; `pallets/werkzeug` took 4 s, 19 MB and 2 s. Their per-file rows over all branches number 9,500 and 13,223.
- Lock files, `requirements*.txt`, `vendor/` and minified files were 6.7% of flask's and 3.5% of werkzeug's non-merge default-branch lines.
- flask had 4 branches and 2 commits not on its default branch; werkzeug 2 branches and none.

**Decisions**, answered by the user on 2026-11-02 through the question tool: per-file counts come from a local bare clone; the default branch alone is followed unless `fetch.branches` names more; generated files are those matching `stats.exclude_paths` and those a repository marks `linguist-generated` or `linguist-vendored`; and the cache keeps every file, so the filter is applied when stats are computed, not when commits are synced. The review of the choices made while writing this spec ([review-1.md](review-1.md)) approved every choice but the first, which the user flagged on 2026-11-02: a repository is cloned only when it is open source or the user has allowed it, otherwise it falls back to the default branch, with a slow GraphQL and REST history as an explicit option. The four follow-up decisions, answered the same day: permission is a pattern list, `fetch.clone_repos`; the slow option reads per-file counts and follows `fetch.branches`; a report counts both kinds of repository and names those whose lines could not be filtered; and a repository whose method changes is read again in the new method.

## Module location

| Module | Holds |
|--------|-------|
| `src/wambatic/fetch/git.py` (new) | `Git`, `GitCommit`, `MIN_GIT_VERSION`, `GIT_TIMEOUT`, `clone_url` |
| `src/wambatic/fetch/errors.py` | `GitError`, `BranchesMismatchError` |
| `src/wambatic/fetch/base.py` | `CommitFile`, `Commit.files`, `Repo.visibility`, `CommitMethod`, `commit_method`, `Fetcher.commit_method`, the three methods in `Fetcher` (the `api` method's history read, `compare` and line-count lookup kept) |
| `src/wambatic/fetch/queries.py` | `COMMIT_AUTHORS`, `BRANCHES` and `BRANCH_HISTORY` (new); `COMMIT_HISTORY` and `COMMIT_COUNTS` kept for `api`; `visibility` added to the listing queries |
| `src/wambatic/settings.py` | `fetch.branches`, `fetch.clone_repos`, `fetch.api_history`, `fetch.clone_dir`, `clones_dir_for` |

Tests are in `src/tests/fetch/test_git.py` and the existing `test_fetcher.py`; their repositories are made at test time with `git init` in a temporary directory, so no clone reaches the network.

## API

```python
# base.py
@dataclasses.dataclass(frozen=True, slots=True)
class CommitFile:
    path: str            # the path after the commit; a rename is stored under its new path
    additions: int       # 0 for a binary file
    deletions: int
    binary: bool         # git printed '-' for its counts
    generated: bool      # linguist-generated or linguist-vendored at the default branch's head

@dataclasses.dataclass(frozen=True, slots=True)
class Commit:            # fields as in Fetch 1.16, plus:
    ...
    files: tuple[CommitFile, ...] = ()   # by path; empty for the `api` method, whose totals stand alone

@dataclasses.dataclass(frozen=True, slots=True)
class Repo:              # fields as in Fetch 1.16, plus:
    ...
    visibility: typing.Literal['PUBLIC', 'PRIVATE', 'INTERNAL'] = 'PRIVATE'   # the listing's `visibility`

CommitMethod = typing.Literal['clone', 'api', 'api-files']

def commit_method(repo: Repo, settings: FetchSettings) -> CommitMethod:
    """'clone' when `repo.visibility == 'PUBLIC'` or `repo.name_with_owner` matches a
    `fetch.clone_repos` pattern; else 'api-files' when `fetch.api_history == 'files'`; else 'api'."""

# Fetcher, from the cache:
    # auditme: accept[spec-api-signature-drift] Fetcher.commit_method; the checker matches the module function by name
    async def commit_method(self, repo: Repo) -> CommitMethod | None:
        """The method of the repo's last commit sync, from its state's probe; None when never synced."""

# git.py
MIN_GIT_VERSION: tuple[int, int] = (2, 40)   # `git check-attr --source` arrived in 2.40
GIT_TIMEOUT: float = 600.0                   # seconds for one git command

def clone_url(host: GitHubHost, repo: str) -> str:
    """'https://github.com/<owner>/<name>.git', or 'https://<host.name>/<owner>/<name>.git'."""

@dataclasses.dataclass(frozen=True, slots=True)
class GitCommit:
    oid: str
    parents: tuple[str, ...]
    authored_at: datetime.datetime        # UTC
    authored_offset: int                  # minutes east of UTC, from %aI (1.1)
    files: tuple[CommitFile, ...]         # `generated` is False here; the fetcher sets it

class Git:
    def __init__(self, token: str, host: GitHubHost, clones_dir: pathlib.Path, *,
                 url_for: collections.abc.Callable[[str], str] | None = None,
                 timeout: float = GIT_TIMEOUT) -> None:
        """`url_for(repo)` defaults to `clone_url(host, repo)`; tests pass local paths."""
    async def check_version(self) -> None:
        """GitError when `git` is not on PATH or older than MIN_GIT_VERSION. Once per Git."""
    def path(self, repo: str) -> pathlib.Path:
        """`clones_dir / '<owner>' / '<name>.git'`."""
    async def update(self, repo: str) -> None:
        """Bare-clone the repository when absent, else fetch every branch, pruning deleted ones."""
    async def branches(self, repo: str) -> dict[str, str]:
        """Branch name -> head oid, from the clone's refs/heads."""
    async def reachable(self, repo: str, heads: collections.abc.Collection[str]) -> frozenset[str]:
        """Every commit reachable from `heads` (`git rev-list`)."""
    async def commits(self, repo: str, oids: collections.abc.Collection[str]) -> list[GitCommit]:
        """These commits with their per-file counts, in no set order."""
    async def attributes_probe(self, repo: str, head: str) -> str:
        """The sha256 hex of the path and blob oid of every `.gitattributes` in `head`'s tree."""
    async def generated_paths(self, repo: str, head: str, paths: collections.abc.Collection[str]) -> frozenset[str]:
        """Those of `paths` that `head`'s attributes mark linguist-generated or linguist-vendored."""
    def remove(self, repo: str) -> None:
        """Delete the repository's clone, if any."""
```

`Fetcher.__init__` gains `git: Git | None = None`, built by default from the token, `parse_host(settings.github_host)` and `clones_dir_for(settings)`; tests pass one. `Fetcher.commits` returns each commit with its `files`.

## Error handling

- `GitError(FetchError)`, in `errors.py`: `git` missing or older than 2.40 (the message names the version found and says to install git 2.40 or later); a git command that exits non-zero (the message names the repository, the command's verb and the last lines of its standard error, passed through `redact`); a command that runs longer than `GIT_TIMEOUT` (killed, then raised); output that does not parse. Never retried: git retries its own transfers, and a repeat of a failed clone would fail the same way.
- `BranchesMismatchError(FetchError)`: `Fetcher.provenance` finds a repository read by `clone` or `api-files` whose last commit sync followed other branch patterns than `fetch.branches` now names (a `--no-fetch` or `--max-age` run after the setting changed). It names the repositories and both pattern lists and says to run without `--no-fetch` or `--max-age`. A report never mixes counts made under two branch settings.
- A new commit with no GitHub object, or no author field in the `COMMIT_AUTHORS` response, raises `GraphQLError` naming its oid, as the line-count lookup did.
- The `api-files` method's REST and GraphQL requests fail with the errors of the [Fetch spec](../fetch/spec.md); a REST 404 for a commit that the branch history has just listed is a `FetchError` naming the oid, not a `NotFoundError` of the repository.

## Implementation

**Choosing the method.** Every sync computes `commit_method(repo, settings)` from the listing, which since 1.0 selects each repository's `visibility` (`PUBLIC`, `PRIVATE` or `INTERNAL`, the last an Enterprise visibility). Only a positive answer clones: a repository whose visibility is not `PUBLIC` is cloned only when its `owner/name` matches a `fetch.clone_repos` pattern (`fnmatch.fnmatchcase`, compared lower-cased), so private code reaches the disk only with the user's permission, and a `Repo` built without the field defaults to `PRIVATE`. The method is recorded in the commit state's `probe` as `method=<method>`. When it differs from the method recorded at the last sync (the repository was made public or private, a pattern was added or removed, `fetch.api_history` changed), the repository is not skipped, and its commits are read again in full in the new method, replacing its rows (`replace=True`); a repository that leaves `clone` has its clone removed. A repository's rows therefore always come from one method.

**Where clones live.** `clones_dir_for(settings)` is `fetch.clone_dir` when set; otherwise a `clones` directory beside the host's cache file (`cache_path_for`, [Cache](../cache/spec.md)) named after the cache file's stem, so `~/.cache/wambatic/clones/cache/` for github.com and `~/.cache/wambatic/clones/cache-<host>/` for another host. A clone is bare, holds `refs/heads/*` only (no tags, no pull request refs) and is kept between runs, so a later sync fetches only what is new. `clear_cache` removes the clones directory with the file.

**Running git.** Every command runs through `asyncio.create_subprocess_exec`, never a shell, inside the fetcher's `fetch.workers` semaphore, with `GIT_TERMINAL_PROMPT=0`, `-c credential.helper=` and `-c core.quotePath=false`. The token never appears in an argument, a URL or the clone's config: it reaches git through the environment as `GIT_CONFIG_COUNT=1`, `GIT_CONFIG_KEY_0=http.extraHeader` and `GIT_CONFIG_VALUE_0=Authorization: Basic <base64 of x-access-token:TOKEN>`, the basic scheme GitHub accepts for a token over HTTPS. Standard error is read in full and passed through `redact` for both the token and its base64 form before it is logged or raised. The commands are:

- clone: `git clone --bare --no-tags --quiet <url> <path>`; update: `git -C <path> fetch --prune --no-tags --quiet origin '+refs/heads/*:refs/heads/*'`;
- branches: `git for-each-ref --format='%(refname:strip=2) %(objectname)' refs/heads`;
- reachable: `git rev-list --stdin` with the heads on standard input;
- commits: `git log --no-walk=unsorted --stdin -z -M --diff-merges=first-parent --numstat --format=%x01%H%x02%P%x02%aI`, the oids on standard input. `-M` gives a renamed file's counts against its old path, and `--diff-merges=first-parent` gives a merge commit's counts against its first parent, both as GitHub's own commit totals do; with `-z` a rename is printed as its counts, then the old and new paths, and the new path is stored;
- attributes: `git ls-tree -r -z --full-tree <head>`, keeping the entries whose name is `.gitattributes`, for the probe; `git check-attr -z --stdin --source <head> linguist-generated linguist-vendored` for the paths, where `set` or `true` marks a path generated.

**The skip rule.** The listing's rule of the fetch spec is kept: `commits` is unchanged when the listed `pushedAt` and `updatedAt` equal the recorded ones, the method recorded in the state's `probe` equals `commit_method`, and, for `clone` and `api-files`, the branch patterns recorded there equal `fetch.branches`.

**The `clone` method**, for one repository that is not skipped:

1. `Git.update`; an empty repository (no default branch) has no clone, no commits and no `head_oid`, as before.
2. The followed branches are the default branch and every branch whose name matches a `fetch.branches` pattern (`fnmatch.fnmatchcase`). Their heads are the repository's branch heads (`Cache.write_commits`, below); `SyncState.head_oid` stays the default branch's head.
3. `reachable` from the followed heads is the set of commits the repository should hold. New commits are those reachable and not cached; gone commits are those cached and not reachable, which a force-push, a rewritten history, a deleted branch or a pattern removed from `fetch.branches` leaves. This set difference is the whole of the rewrite detection, per branch and for the repository at once: no compare is made, and nothing is re-read that has not changed.
4. The new commits are read with `Git.commits`, and their authors with `COMMIT_AUTHORS`: up to 100 aliased `object(oid: $oN) { ... on Commit { author { user { login } } } }` fields per query, variables `$o0` to `$o99` of type `GitObjectID!`, as `commit_counts` reads line counts. That is one GraphQL point per 100 new commits, the same as the `api` method's history paging; the commit's author email is never stored. `authored_at` is the `%aI` author date in UTC, `authored_offset` its offset in minutes (1.1, [Author timezones](../author-timezones/spec.md)), and `is_merge` is more than one parent.
5. Generated paths: when the `attributes_probe` of the default branch's head differs from the one recorded in the state's `probe`, `generated_paths` is asked for every path of the repository's cached and new files, and every file row's `generated` flag is rewritten; otherwise only the new files' paths are asked. A repository's attributes are therefore read at its default branch's current head and applied to every commit, an accepted limit, as GitHub's own language bar does.
6. One `Cache.write_commits` transaction inserts the new commits and their files, deletes the gone ones, writes the generated flags and branch heads, and writes the state, whose `probe` is `method=clone attrs=<probe> branches=<JSON list of fetch.branches>`. A repository with gone commits is named in `SyncReport.full_refetches`.

**The `api` method** is the commit sync of Fetch 1.16, unchanged (the fetch spec's Incremental sync step 2, `commits`): the default branch's `COMMIT_HISTORY` on a first or full read, and REST `compare` with the `COMMIT_COUNTS` line-count lookup when the head moved. Its commits have no `files`, its state's `probe` is `method=api`, and `fetch.branches` does not apply to it.

**The `api-files` method**, for one repository that is not skipped:

1. `BRANCHES` lists the repository's branches with their heads (`refs(refPrefix: "refs/heads/", first: 100)`, paged); the followed branches are chosen as for `clone` (step 2 above) and written as its branch heads.
2. For each followed branch whose head differs from its stored head, REST `compare` from the stored head, as the `api` method does; a newly followed branch is read in full with `BRANCH_HISTORY` (`repository { ref(qualifiedName:) { target { ... on Commit { history(first: 100, after:) { ... } } } } }`, the fields of `COMMIT_HISTORY`), its commits not yet cached being new. A `diverged` or `behind` compare, a 404, or a branch no longer followed or deleted can leave commits that no branch reaches, which the API cannot list, so every followed branch is then read in full and the cached commits listed by none of them are gone, as in step 3 of `clone`.
3. Each new commit, by oid, is read with REST `GET /repos/{owner}/{name}/commits/{sha}` (paged with `page` when it lists more than 300 files): each entry of `files` gives `filename` (the path after the commit), `additions` and `deletions`. The commit's `additions` and `deletions` stay GitHub's totals from the history or the `COMMIT_COUNTS` lookup. A cached commit is never read again: a commit's files do not change.
4. `generated` is False on every file: without a clone the attributes are not read. `stats.exclude_paths` still applies.
5. One `Cache.write_commits` transaction, as in step 6 of `clone`, with the `probe` `method=api-files branches=<JSON list of fetch.branches>`.

`--full-refresh` (`sync(..., full_refresh=True)`) reads every repository in full in its method, replacing its rows (`replace=True`), and for `clone` removes the clone and clones again first; the `fetch.full_refresh_after` interval does not apply to commits, as before. `Fetcher.provenance` adds `branches`, the JSON list of `fetch.branches` (`[]` for the default branch only), after checking every repository's recorded patterns against it (`BranchesMismatchError` above).

**Cost.** `clone`: a first sync costs one clone per repository and one GraphQL point per 100 commits; a later sync one `git fetch` per changed repository and one point per 100 new commits; no REST request; disk use about the size of each repository's history (13 MB for flask, 2026-11-02). `api`: as in Fetch 1.16. `api-files`: one GraphQL point per 100 commits of each branch read, and one REST request per new commit, which for the pallets cache's 21,193 commits would be about 4 hours 15 minutes of the 5,000-per-hour REST budget on a first sync (measured 2026-11-02); the rate-limit rules of the fetch spec wait or fail as `fetch.on_rate_limit` says, and the `ETA:` line reports the wait.

**What a report is told.** For each repository of the subject whose method is not `clone`, `Fetcher.commit_method` lets stats name it ([Metric groups](../metric-groups/spec.md) 1.1): an `api` repository's lines include generated files and only its default branch is counted when `fetch.branches` names more; an `api-files` repository's lines leave out `stats.exclude_paths` but not linguist attributes.

**Accepted limits.** Attributes are read at the default branch's current head (step 5 of `clone`), and not at all for `api-files`. REST lists at most 3,000 files of one commit (GitHub's REST reference, checked 2026-11-02), so an `api-files` commit touching more counts only the files listed. `pr_size_p50` in the [metric groups](../metric-groups/spec.md) still uses GitHub's pull request totals, which include generated files. Only branches are followed: a commit reachable only from a tag or a pull request ref is not counted. A commit on an unfollowed branch leaves the cache when its branch stops being followed.

**Testing.** `test_git.py` builds repositories with `git init`, `git commit` and `git push` into a local bare remote that `url_for` names, and covers: a first clone and an incremental fetch; a rename, a binary file and a merge commit's first-parent counts; a force-pushed branch and a deleted branch (their commits leave); a `.gitattributes` added, then changed (every flag rewritten); a pattern added to `fetch.branches` (the repo is not skipped, its commits arrive); git missing or too old; a failing command whose standard error holds the token (redacted). A test runs the commands through a recording runner and checks that no argument holds the token. The replay server serves `COMMIT_AUTHORS`, `BRANCHES`, `BRANCH_HISTORY` and REST commits with files. `commit_method` is tested on a public, a private and an internal repository, with and without a matching `fetch.clone_repos` pattern and with each `fetch.api_history`; a repository made private, or removed from the patterns, is read again by the API method and its clone removed; an `api-files` sync covers a new branch, a moved head, a force-push and a commit with more than 300 files (two pages). The opt-in live test syncs `octocat/Hello-World` through a real clone and checks, as before, that its summed non-merge additions and deletions equal REST `stats/code_frequency`.

## Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `fetch.branches` | `tuple[str, ...]` | `()` | Branch name patterns (`fnmatch`) followed beside the default branch by `clone` and `api-files`; `()` follows the default branch only, `('*',)` every branch |
| `fetch.clone_repos` | `tuple[str, ...]` | `()` | `owner/name` patterns (`fnmatch`) of private or internal repositories the user allows to be cloned; public repositories are cloned without it |
| `fetch.api_history` | `Literal['totals', 'files']` | `'totals'` | How a repository that is not cloned is read: `'totals'` is the default branch with per-commit totals (Fetch 1.16); `'files'` also reads each commit's files by REST, one request per commit, and follows `fetch.branches` |
| `fetch.clone_dir` | `Path \| None` | `None` | Where bare clones are kept; `None` puts them beside the cache file (see Where clones live) |

The patterns that leave files out of line counts are stats settings, `stats.exclude_paths` and `stats.linguist` ([Stats](../stats/spec.md)).

## External dependencies

- `git` 2.40 or later on `PATH` ([`git check-attr --source`](https://git-scm.com/docs/git-check-attr) is in the 2.40 release notes, checked 2026-11-02); no Python git library.
- GitHub's Git HTTPS endpoint, with the token the API uses; a token that reads a repository's contents can clone it.
