# Tasks: Commit sync

**Spec:** `agents/specs/commit-sync/spec.md`
**Created:** 2026-11-02
**Version:** 1

This list builds commit sync spec 1.0 (step 14 of the implementation order), with the amendments made with it: fetch spec 1.17, cache spec 1.2, stats spec 1.11, metric groups spec 1.1, system spec 1.11, CLI spec 1.2, and terminal-report and HTML-report specs 1.2. The choices are in `agents/specs/commit-sync/review-1.md`, every one answered on 2026-11-02 (item 1 flagged, and settled by the approved items 15 to 20). Nothing in it is built yet: `src/wambatic/fetch/git.py` does not exist, and no `CommitFile`, `fetch.clone_repos` or `fetch.api_history` is in `src` (checked 2026-11-02).

Each repository's commits are read by one of three methods: `clone` (a bare clone, for a public repository or one `fetch.clone_repos` allows), `api` (the fetch 1.16 sync, kept unchanged) and `api-files` (per-branch GraphQL histories and per-commit REST file lists, when `fetch.api_history` is `'files'`). The `api-files` method is modelled on the `api` method's history and compare reads, so its last task has a deduplication subtask.

The user guide's drift test (`src/tests/test_docs.py`) compares `docs/reference/settings.md` with the settings, so the task that adds a setting updates that page in the same commit.

A task that changes a query text in `src/wambatic/fetch/queries.py` re-runs `bin/record-fixtures.sh`, because a test in `src/tests/fetch/test_queries.py` fails while a query's recorded sha256 is stale. The recorder needs a GitHub token (`GITHUB_TOKEN` or `gh auth token`); a task that cannot get one stops as `blocked`, naming the recording it needs, and never edits `recorded.py` by hand. Never list environment variables or print a token: test one with `[ -n "${GITHUB_TOKEN:-}" ]` and print only yes or no.

The project has no affected-tests tool: each task names its test files. Every `pytest` and `mkdocs` command runs after `source bin/activate.sh`; `mkdocs` needs `uv sync --group docs` first. Tests make their git repositories with `git init` in a temporary directory; no test but the opt-in live test clones from the network.

---

## Task 1: Add the commit sync and line-filter settings

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** commit sync 1.0, Settings and Where clones live; fetch 1.17, Settings; stats 1.11, Settings

**Technical Goal:** The settings every later task reads exist, with their defaults and checks, before any code uses them.

**Subtasks:**

- [x] Add to `FetchSettings` in `src/wambatic/settings.py`: `branches: tuple[str, ...] = ()`, `clone_repos: tuple[str, ...] = ()`, `api_history: Literal['totals', 'files'] = 'totals'` and `clone_dir: pathlib.Path | None = None`
- [x] Add to `StatsSettings`: `exclude_paths: tuple[str, ...]` with the default of stats spec 1.11 (`'**/*.lock'`, `'**/package-lock.json'`, `'**/pnpm-lock.yaml'`, `'**/go.sum'`, `'**/vendor/**'`, `'**/node_modules/**'`, `'**/dist/**'`, `'**/*.min.js'`, `'**/*.min.css'`, `'**/*.map'`) and `linguist: bool = True`
- [x] Add `clones_dir_for(settings: FetchSettings) -> pathlib.Path` beside `cache_path_for`: `fetch.clone_dir` when set, else `<cache file parent>/clones/<cache file stem>`
- [x] Add the six settings to `docs/reference/settings.md`, with their defaults and one line each
- [x] Tests in `src/tests/test_settings.py`: each default, a config file and a flag override of each, an `api_history` other than `totals` or `files` raising `SettingsError`, and `clones_dir_for` for github.com, an Enterprise host and a set `clone_dir`

**Acceptance Criteria:**

- [x] `load_settings(None, {})` gives the defaults of the spec tables
- [x] `clones_dir_for` gives `~/.cache/wambatic/clones/cache` for github.com and `~/.cache/wambatic/clones/cache-ghe.example.com` for `ghe.example.com`

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_settings.py src/tests/test_docs.py` passes

**Notes:**

- Key files: `src/wambatic/settings.py`, `docs/reference/settings.md`
- Nothing reads the settings yet; later tasks do

---

## Task 2: Add per-file commit records, visibility and cache schema 5

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** commit sync 1.0, API (`CommitFile`, `Commit.files`, `Repo.visibility`); fetch 1.17, API and Incremental sync step 1; cache 1.2, API and Implementation

**Technical Goal:** The records and the cache hold per-file counts, branch heads and visibility, so the sync methods have somewhere to write them.

**Subtasks:**

- [x] Add `CommitFile` (`path`, `additions`, `deletions`, `binary`, `generated`) to `src/wambatic/fetch/base.py`, `files: tuple[CommitFile, ...] = ()` to `Commit`, and `visibility: Literal['PUBLIC', 'PRIVATE', 'INTERNAL'] = 'PRIVATE'` to `Repo`
- [x] Select `visibility` in `OWNER_REPOSITORIES` and `REPOSITORY` in `src/wambatic/fetch/queries.py`, and parse it in the listing parser; a value outside the three is a `GraphQLError` (`MALFORMED`)
- [x] In `src/wambatic/fetch/cache.py`: set `SCHEMA_VERSION` to 5; add the `commit_files` table (primary key `(repo, oid, path)`) and the `branch_heads` table (primary key `(repo, branch)`), and the `repos` column `visibility`
- [x] Extend `Cache.write_commits` with `gone`, `branch_heads` and `generated` as cache spec 1.2 says, in its one transaction; make `read_commits` return each commit's `files` by path; add `commit_oids`, `commit_paths` and `branch_heads`
- [x] Add `commit_files` to `CacheInfo` and count it in `inspect_cache` (a table absent from the file counts 0)
- [x] Re-run `bin/record-fixtures.sh` for the changed listing queries, and add `visibility` to the listing fixtures in `src/tests/fixtures/fetch/responses.py`
- [x] Tests in `src/tests/fetch/test_cache.py`: files written and read back by path, `gone` deleting commits with their files, `generated` rewriting every flag, `branch_heads` replaced, a cache of schema 4 refused with `CacheVersionError`; in `src/tests/fetch/test_base.py`: visibility parsed, and a `Repo` built without it is `PRIVATE`

**Acceptance Criteria:**

- [x] A commit written with files reads back with the same files, and `gone` leaves no file rows behind
- [x] Every existing fetch test still passes with `Commit.files` empty

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_cache.py src/tests/fetch/test_base.py src/tests/fetch/test_fetcher.py src/tests/fetch/test_queries.py src/tests/fetch/test_parse_properties.py` passes

**Notes:**

- Depends on Task 1
- The `inspect_cache` and `clear_cache` `clones_dir` argument is Task 8, not this task
- Key files: `src/wambatic/fetch/base.py`, `cache.py`, `queries.py`, `src/tests/fixtures/fetch/`

---

## Task 3: Add the git runner and bare clones

**Status:** done
**Priority:** high
**Complexity:** large
**Spec Reference:** commit sync 1.0, API (`git.py`), Error handling (`GitError`), Running git, Testing; External dependencies

**Technical Goal:** A `Git` object clones, fetches and reads a repository with `git`, without the token ever reaching an argument, a URL or the clone's config.

**Subtasks:**

- [x] Add `GitError(FetchError)` to `src/wambatic/fetch/errors.py`
- [x] Create `src/wambatic/fetch/git.py` with `MIN_GIT_VERSION`, `GIT_TIMEOUT`, `clone_url`, `GitCommit` and `Git` as commit sync 1.0 API says
- [x] Run every command with `asyncio.create_subprocess_exec` (never a shell), `GIT_TERMINAL_PROMPT=0`, `-c credential.helper=` and `-c core.quotePath=false`, and the token only in `GIT_CONFIG_COUNT`, `GIT_CONFIG_KEY_0=http.extraHeader` and `GIT_CONFIG_VALUE_0=Authorization: Basic <base64 of x-access-token:TOKEN>`; give the runner a seam tests can record through
- [x] Implement `check_version`, `path`, `update` (clone `--bare --no-tags`, else `fetch --prune --no-tags origin '+refs/heads/*:refs/heads/*'`), `branches`, `reachable`, `commits` (`git log --no-walk=unsorted --stdin -z -M --diff-merges=first-parent --numstat` with the spec's format, renames stored under the new path, `-` counts as 0 and `binary`), `attributes_probe`, `generated_paths` (`check-attr -z --stdin --source`) and `remove`
- [x] Kill a command past `GIT_TIMEOUT` and raise `GitError`; pass standard error through `redact` for the token and its base64 form before raising or logging it
- [x] Tests in a new `src/tests/fetch/test_git.py`, with repositories made by `git init` and pushed to a local bare remote named by `url_for`: first clone and incremental fetch; a rename, a binary file and a merge's first-parent counts; a force-pushed and a deleted branch; `.gitattributes` added and changed (probe changes, generated paths); git missing (an empty `PATH`) and too old (a fake `git` script printing `git version 2.39.0`); a failing command whose standard error holds the token (redacted); and, through the recording runner, that no argument holds the token

**Acceptance Criteria:**

- [x] `Git.commits` on the test repositories gives the counts `git log --numstat` prints, with renames under their new paths
- [x] No recorded argument, and no file in a clone's `config`, contains the token

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_git.py src/tests/fetch/test_errors.py` passes

**Notes:**

- Depends on Task 2 (`CommitFile`)
- `git check-attr --source` needs git 2.40 (its release notes, checked 2026-11-02); the local git is 2.56.0
- Key files: `src/wambatic/fetch/git.py`, `src/wambatic/fetch/errors.py`

---

## Task 4: Look up commit authors by oid

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** commit sync 1.0, The `clone` method step 4, Error handling; fetch 1.17, GraphQL cost control

**Technical Goal:** Commits read from git get their GitHub logins at one GraphQL point per 100 commits.

**Subtasks:**

- [x] Add `commit_authors(n)` and `COMMIT_AUTHORS = commit_authors(100)` to `src/wambatic/fetch/queries.py`: aliased `object(oid: $oN) { ... on Commit { author { user { login } } } }` fields, variables `$o0` to `$o99` of type `GitObjectID!`, with `rateLimit`, modelled on `commit_counts`
- [x] Add a `Fetcher` helper that maps oids to logins (`None` for a commit with no user), 100 per query, raising `GraphQLError` naming the oid when an object or its author field is missing
- [x] Re-run `bin/record-fixtures.sh` so `recorded.py` holds a `COMMIT_AUTHORS` response for `octocat/Hello-World` commits, and serve it from the replay server
- [x] Tests in `src/tests/fetch/test_queries.py` (variables typed by oid, no node id) and `src/tests/fetch/test_fetcher.py` (logins mapped, a missing object raising, 101 oids making two queries)

**Acceptance Criteria:**

- [x] 250 oids cost three queries and give a login or `None` for each

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_queries.py src/tests/fetch/test_fetcher.py src/tests/test_record_fixtures.py` passes

**Notes:**

- Depends on Task 2
- Key files: `src/wambatic/fetch/queries.py`, `src/wambatic/fetch/base.py`, `bin/record-fixtures.py`, `src/tests/fixtures/fetch/`

---

## Task 5: Choose the method and sync cloned repositories

**Status:** done
**Priority:** high
**Complexity:** large
**Spec Reference:** commit sync 1.0, Choosing the method, Where clones live, The skip rule, The `clone` method, The `api` method, `--full-refresh`, Cost; fetch 1.17, Fetcher

**User Story:** As a user reporting on public repositories, I want their commits read from a local clone, so that line counts can leave out generated files and other branches can be counted without spending the API budget.

**Subtasks:**

- [x] Add `CommitMethod` and `commit_method(repo, settings)` to `src/wambatic/fetch/base.py`: `clone` for `PUBLIC` or a lower-cased `owner/name` matching a `fetch.clone_repos` pattern (`fnmatch.fnmatchcase`), else `api-files` when `fetch.api_history == 'files'`, else `api`
- [x] Write and parse the commit state's `probe` (`method=<method>`, then `attrs=<probe>` and `branches=<JSON list>` where the method has them), and add `Fetcher.commit_method(repo)` reading it from the cache
- [x] Extend the commit skip rule: unchanged only when `pushedAt` and `updatedAt` match, the recorded method equals `commit_method`, and for `clone` and `api-files` the recorded branches equal `fetch.branches`
- [x] A method different from the recorded one reads the repository in full in the new method, replacing its rows; a repository leaving `clone` has its clone removed (`Git.remove`)
- [x] Give `Fetcher.__init__` its `git: Git | None = None`, built by default from the token, the host and `clones_dir_for(settings)`; check the git version once, before the first clone of a sync
- [x] Implement the `clone` method's steps 1 to 6: update, followed branches, the reachable set difference (new and gone), `Git.commits` with the Task 4 logins, generated paths (all paths when the attributes probe changed, else the new files'), and one `Cache.write_commits` with `gone`, `branch_heads` and `generated`; name a repository with gone commits in `SyncReport.full_refetches`
- [x] Leave the `api` method as the fetch 1.16 sync, with `probe` `method=api`; `--full-refresh` re-clones a `clone` repository and replaces its rows
- [x] Tests in `src/tests/fetch/test_fetcher.py`, with local repositories through `url_for` and the replay server for the listing and authors: `commit_method` for a public, a private and an internal repository, with and without a matching pattern, and for each `fetch.api_history`; a first clone sync, an incremental one, a force-push, a deleted branch, a pattern added to `fetch.branches` (not skipped), a `.gitattributes` change (every flag rewritten); a repository made private and not allowed (read by `api`, clone removed); `--full-refresh`

**Acceptance Criteria:**

- [x] A private repository is cloned only when `fetch.clone_repos` matches it
- [x] After a force-push, the cache holds exactly the commits reachable from the followed heads
- [x] A repository's rows never come from two methods

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_fetcher.py src/tests/fetch/test_git.py src/tests/fetch/test_cache.py src/tests/fetch/test_base.py` passes

**Notes:**

- Depends on Tasks 1 to 4
- `api-files` is Task 6; until then `commit_method` may return it but the sync raises `InvalidRequestError` for it, which Task 6 removes
- Key files: `src/wambatic/fetch/base.py`

---

## Task 6: Sync uncloned repositories with per-file counts by API

**Status:** done
**Priority:** medium
**Complexity:** large
**Spec Reference:** commit sync 1.0, The `api-files` method, Error handling, Cost, Accepted limits, Testing

**User Story:** As a user reporting on private repositories I do not allow to be cloned, I want an explicit option to read their per-file counts and other branches through the API, so that their line counts can be filtered too, at the cost of time.

**Subtasks:**

- [x] Add `BRANCHES` (`refs(refPrefix: "refs/heads/", first: 100, after:)` with each target oid) and `BRANCH_HISTORY` (`ref(qualifiedName:)` history with the fields of `COMMIT_HISTORY`) to `src/wambatic/fetch/queries.py`, each with `rateLimit`
- [x] Implement the `api-files` method's steps 1 to 5: branches and followed heads; per branch, `compare` from a stored head, `BRANCH_HISTORY` for a new branch, and every followed branch in full after a `diverged` or `behind` compare, a 404 or a branch dropped, with gone commits those no branch listed
- [x] Read each new commit's files with REST `GET /repos/{owner}/{name}/commits/{sha}`, paged with `page` past 300 files; `generated` and `binary` False; the commit's totals from the history or `COMMIT_COUNTS`; a 404 for a listed commit is a `FetchError` naming the oid; remove Task 5's `InvalidRequestError` for this method
- [x] Write with `probe` `method=api-files branches=<JSON list>`
- [x] Re-run `bin/record-fixtures.sh` for `BRANCHES`, `BRANCH_HISTORY` and one REST commit with its files (`octocat/Hello-World`); build a two-page file list in `responses.py` from GitHub's documented shape
- [x] Tests in `src/tests/fetch/test_fetcher.py`: a first sync, a moved head, a new branch, a force-push (every branch re-read, gone commits deleted), a commit with more than 300 files (two pages), and a cached commit never read again
- [x] Hoist anything this method duplicates from the `api` method to a single owner: grep the tree for each literal collection, constant and one-line helper the new code defines (history parsing, compare paging, the 100-per-query constants), and import rather than copy. Choose the owner from the existing import graph; prefer a module the consumer already imports over adding a new edge

**Acceptance Criteria:**

- [x] With `fetch.api_history = 'files'`, a private repository's commits on every followed branch are stored once, each with its files
- [x] No REST request is made for a commit already cached

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_fetcher.py src/tests/fetch/test_queries.py src/tests/fetch/test_client.py src/tests/test_record_fixtures.py` passes

**Notes:**

- Depends on Task 5
- REST lists at most 3,000 files of a commit (GitHub's REST reference, checked 2026-11-02): an accepted limit, not an error
- Key files: `src/wambatic/fetch/base.py`, `queries.py`, `src/tests/fixtures/fetch/`

---

## Task 7: Leave generated files out of line counts and name unfiltered repositories

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** metric groups 1.1, activity (Code contributions, Repositories that could not be filtered, top contributors); stats 1.11, Provenance; fetch 1.17, `provenance`; commit sync 1.0, Error handling (`BranchesMismatchError`), What a report is told

**User Story:** As a user, I want lines added and deleted to leave out lock files, vendored and generated code, and the report to say which repositories it could not filter, so that the numbers measure written code and I know where they do not.

**Subtasks:**

- [x] Add `BranchesMismatchError(FetchError)` to `src/wambatic/fetch/errors.py`; make `Fetcher.provenance` add `commit_methods` (comma-separated, in the order `clone`, `api-files`, `api`) and `branches` when `commits` is read, raising `BranchesMismatchError` for a `clone` or `api-files` repository whose recorded branches differ from `fetch.branches`
- [x] In `src/wambatic/stats/engine.py`, keep each repository's `Fetcher.commit_method` in what `read_records` returns, and add `exclude_paths` (JSON list) and `linguist` (`'true'` or `'false'`) to the provenance when `commits` is read
- [x] In `src/wambatic/stats/activity.py`, take a commit's lines from its kept files for `clone` and `api-files` (a file left out when `PurePosixPath(path).full_match(pattern)` for a `stats.exclude_paths` pattern, or when `generated` with `stats.linguist`) and from its totals for `api`, chosen by the recorded method; apply the same rule in `tables['top_contributors']`; a commit whose every file is left out still counts in `commits`, `contributors` and `active_days`
- [x] Add the `tables['unavailable']` rows of metric groups 1.1 for `api` and `api-files` repositories, ordered by name, beside any rows other groups add
- [x] Tests in `src/tests/stats/test_activity.py` and `src/tests/stats/test_engine.py`: a lock file and a `generated` file left out of lines and kept in `commits`; an `api` repository's totals used whatever its files; `stats.linguist` off; the unavailable rows for each method and with `fetch.branches` set; the provenance keys; in `src/tests/fetch/test_fetcher.py`, `BranchesMismatchError` after `fetch.branches` changed without a sync

**Acceptance Criteria:**

- [x] A report over a cloned and an `api` repository counts both, and names the `api` one in `tables['unavailable']`
- [x] Two results computed with different `stats.exclude_paths` differ in their `exclude_paths` provenance

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/stats/test_activity.py src/tests/stats/test_engine.py src/tests/stats/test_properties.py src/tests/fetch/test_fetcher.py` passes

**Notes:**

- Depends on Tasks 5 and 6
- `pr_size_p50` keeps GitHub's pull request totals (metric groups 1.1); do not change `flow.py`
- Key files: `src/wambatic/stats/activity.py`, `engine.py`, `src/wambatic/fetch/base.py`, `errors.py`

---

## Task 8: Clear and inspect the clones with the cache

**Status:** done
**Priority:** medium
**Complexity:** small
**Spec Reference:** cache 1.2, API (`inspect_cache`, `clear_cache`, `CacheInfo`); CLI 1.2, `cache clear` and `cache info`; commit sync 1.0, Where clones live

**User Story:** As a user, I want `wambatic cache clear` to remove the clones too and `cache info` to say how much room they take, so that clearing the cache really frees the disk.

**Subtasks:**

- [x] Give `inspect_cache` and `clear_cache` in `src/wambatic/fetch/cache.py` their `clones_dir` argument; `clear_cache` deletes the tree and returns it among the paths removed; `inspect_cache` fills `CacheInfo.clones_bytes` (0 when absent)
- [x] Pass `clones_dir_for(settings)` from the `cache` command in `src/wambatic/cli.py`, and show the clones' size and the commit file rows in `cache info`
- [x] Remove the two `auditme: accept[spec-api-signature-drift]` lines above `inspect_cache` and `clear_cache` in `agents/specs/cache/spec.md`; keep the one above `Cache.read_commits`
- [x] Tests in `src/tests/fetch/test_cache.py` and `src/tests/test_cli.py`: clear removes the file and the clones, info reports their size, a missing clones directory is fine

**Acceptance Criteria:**

- [x] After `wambatic cache clear`, neither the cache file nor its clones directory exists
- [x] `bin/audit-check.sh` passes without the two removed markers

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_cache.py src/tests/test_cli.py src/tests/test_docs.py` passes
- [x] `bin/audit-check.sh` exits 0

**Notes:**

- Depends on Tasks 1 and 2
- Key files: `src/wambatic/fetch/cache.py`, `src/wambatic/cli.py`, `agents/specs/cache/spec.md`

---

## Task 9: Say in the report footers how commits were read

**Status:** done
**Priority:** medium
**Complexity:** small
**Spec Reference:** terminal report 1.2, item 14; HTML report 1.2, provenance footer

**User Story:** As a reader of a report, I want its footer to say how commits were read, which branches were counted and which files were left out, so that I can tell what the line counts measure.

**Subtasks:**

- [x] In the terminal provenance footer (`src/wambatic/reports/terminal.py`), when `branches` is present, add `Commits read by: ...` (`local clone`, `API with files`, `API totals`), `Branches: ...` and `Line counts leave out: ...` as terminal report 1.2 says
- [x] Add the same lines to the HTML footer (`src/wambatic/reports/html.py`)
- [x] Tests in `src/tests/reports/test_terminal.py` and `src/tests/reports/test_html.py`: each line for default and set `fetch.branches`, with `stats.linguist` on and off, and no lines when `commits` was not read

**Acceptance Criteria:**

- [x] A report with default settings over a cloned repository ends with `Branches: default branch` and the default patterns with linguist files

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/reports/test_terminal.py src/tests/reports/test_html.py src/tests/reports/test_rows.py` passes

**Notes:**

- Depends on Task 7 (the provenance keys)
- Key files: `src/wambatic/reports/terminal.py`, `src/wambatic/reports/html.py`

---

## Task 10: Check a real clone sync against GitHub's totals

**Status:** done
**Priority:** medium
**Complexity:** small
**Spec Reference:** commit sync 1.0, Testing (the opt-in live test); review-1.md item 14

**Technical Goal:** The first sync through a real clone is checked against GitHub's own line totals before the list closes.

**Subtasks:**

- [x] In `src/tests/fetch/test_live.py`, make the existing `octocat/Hello-World` live sync go through a real clone (a public repository) in a temporary clones directory, and keep its check that summed non-merge additions and deletions equal REST `stats/code_frequency`
- [x] Add a live check of the `api-files` method: sync the same repository with `fetch.api_history = 'files'` and its `Repo` built with `visibility='PRIVATE'`, so it is not cloned, and check that each commit's per-file sums equal its totals
- [x] Run the live tests once with a token; if no token is set (`[ -n "${GITHUB_TOKEN:-}" ]` prints no and `gh auth token` fails), stop as `blocked`, naming this task's live run

**Acceptance Criteria:**

- [x] `pytest -m live src/tests/fetch/test_live.py` passes with a token

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest -m live src/tests/fetch/test_live.py` passes

**Notes:**

- Depends on Tasks 5 and 6
- The CI `live` job runs the same tests with its token
- Key files: `src/tests/fetch/test_live.py`

---

## Task 11: Document the commit sync and close the list

**Status:** done
**Priority:** medium
**Complexity:** medium
**Spec Reference:** system 1.11 (Limits accepted, External dependencies); implementation order 1.12, step 14; every spec section above (closing)

**User Story:** As a user, I want the guide to say how commits are read, how to allow a private repository to be cloned, how to switch on the slow API read, and which files are left out, so that I can choose what my reports count.

**Subtasks:**

- [x] Update `docs/guide/activity.md` (line counts leave out generated files; the patterns and linguist attributes; what an unavailable row means), `docs/guide/cache.md` (the clones, their size, `cache clear`), `docs/guide/config.md` (`fetch.branches`, `fetch.clone_repos`, `fetch.api_history`, `fetch.clone_dir`, `stats.exclude_paths`, `stats.linguist`), `docs/limits.md` (the limits of system spec 1.11), `docs/install.md` (`git` 2.40 or later) and `docs/reference/exit-statuses.md` (`GitError` and `BranchesMismatchError`)
- [x] Re-run `bin/screenshots.sh` for the new footer lines and commit the new images; it rebuilds its cache through clones, so it needs a token and the network; if either is missing, stop as `blocked`, naming the screenshots
- [x] Mark step 14 `done` in `agents/specs/implementation-order.md`, linking this list, and set its `**Status:**` to `implemented`
- [x] Set the spec's `**Status:**` to `implemented` in `agents/specs/commit-sync/spec.md`, and in each amended spec: fetch, cache, stats, metric groups, system, CLI, terminal report and HTML report
- [x] Move the `TODO.md` item "The commit sync reads only default-branch totals" to the end of `DONE.md`: append its heading and body unchanged, then `Done: <date> - built by agents/tasks/commit-sync/tasks-1.md against commit sync spec 1.0.`, and remove it from `TODO.md`
- [x] Add the list to `agents/tasks/index.md` if it is not there

**Acceptance Criteria:**

- [x] The guide explains the three methods, how to allow a clone and what the footer lines mean
- [x] `TODO.md` no longer holds the commit sync item, and `DONE.md` ends with it and its `Done:` line

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] `uv sync --group docs` succeeds
- [x] `mkdocs build --strict` exits 0
- [x] `pre-commit run --all-files` exits 0
- [x] `bin/audit-check.sh` exits 0
- [x] `python3 ~/.claude/skills/todo-review/verify_bodies.py <before> TODO.md DONE.md` exits 0, where `<before>` is `TODO.md` as of the commit that added this list (`git show "$(git log --diff-filter=A --format=%H -- agents/tasks/commit-sync/tasks-1.md)":TODO.md`)
- [x] `pytest src/tests/fetch src/tests/reports src/tests/stats src/tests/test_cli.py src/tests/test_settings.py src/tests/test_docs.py src/tests/test_layering.py src/tests/test_package.py src/tests/test_screenshots.py src/tests/test_record_fixtures.py` passes: every test that reaches `settings`, `fetch`, `stats` or `reports`, the modules this list changes

**Notes:**

- Depends on Tasks 1 to 10
- `browser` and `live` tests run in CI's `browser` and `live` jobs; the local run above skips them without Chromium or a token
