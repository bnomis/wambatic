# Tasks: Fetch

**Spec:** `agents/specs/fetch/spec.md`
**Created:** 2026-11-02
**Version:** 1

This list builds fetch spec 1.16, GitHub Enterprise Server (step 13 of the implementation order), with the amendments made with it: cache spec 1.1, system spec 1.10, CLI spec 1.1, reports spec 1.14, and terminal-report and HTML-report specs 1.1. The choices are in `agents/specs/fetch/review-1.md`, every one approved on 2026-11-02. Nothing in it is built yet: `src/wambatic/fetch/hosts.py` does not exist, `GitHubClient` takes `api_url`, and no setting or flag names a host (checked 2026-11-02).

The user guide's drift test (`src/tests/test_docs.py`) compares `docs/reference/settings.md` with the settings and `docs/reference/cli.md` with the CLI's options, so the task that adds a setting or a flag updates that page in the same commit.

The project has no affected-tests tool: each task names its test files. Every `pytest` and `mkdocs` command runs after `source bin/activate.sh`; `mkdocs` needs `uv sync --group docs` first.

No GitHub Enterprise server is available, so no task makes a live request to one; the Enterprise fixtures are written from GitHub's Enterprise Server documentation (fetch spec, GitHub hosts, Testing).

---

## Task 1: Add the `fetch.github_host` setting and a cache file per host

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** fetch spec 1.16, GitHub hosts (Host names) and Settings; cache spec 1.1, One file per host and Settings

**Technical Goal:** Settings name the host and give each host its own default cache file, before any code reads them.

**Subtasks:**

- [x] Add `github_host: str = 'github.com'` to `FetchSettings` in `src/wambatic/settings.py`, checked when settings load: lower-cased; `github.com`, or a name of letters, digits, `-` and `.` with at least one `.`, optionally `:` and a port from 1 to 65535; no scheme, path, user or query. `api.github.com` raises `SettingsError` saying to use `github.com`; a name ending in `.ghe.com` raises `SettingsError` saying GitHub Enterprise Cloud with data residency is not supported. Every message names `fetch.github_host` and never echoes the value, as the other settings errors do
- [x] Make `fetch.cache_path` `pathlib.Path | None`, default `None`, and add `cache_path_for(settings: FetchSettings) -> pathlib.Path`: the setting when set, else `~/.cache/wambatic/cache.sqlite3` for `github.com` and `~/.cache/wambatic/cache-<host>.sqlite3` for another host, `:` replaced by `-`
- [x] Replace every read of `settings.fetch.cache_path` with `cache_path_for(settings.fetch)`: `src/wambatic/cli.py` (the `report` and `cache` commands) and `src/wambatic/reports/web.py` (`serve`)
- [x] Update the fixture settings in `src/tests/fixtures/settings.py` and the tests that set `cache_path`, keeping their temporary paths
- [x] Tests in `src/tests/test_settings.py`: accepted names (with and without a port, upper case lower-cased), each refusal (`api.github.com`, `*.ghe.com`, a scheme, a path, a port of 0 and of 65536, no dot), and `cache_path_for` for an unset path on both kinds of host and for a set path
- [x] Add `fetch.github_host` to `docs/reference/settings.md`, and the new `fetch.cache_path` type and default

**Acceptance Criteria:**

- [x] `load_settings` with `{"fetch": {"github_host": "GHE.Example.com:8443"}}` gives `ghe.example.com:8443`, and `cache_path_for` gives `~/.cache/wambatic/cache-ghe.example.com-8443.sqlite3`
- [x] A default github.com run opens `~/.cache/wambatic/cache.sqlite3`, as before
- [x] `pytest src/tests/test_docs.py` passes with the new setting

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_settings.py src/tests/test_cli.py src/tests/reports/test_web.py src/tests/test_docs.py` passes

**Notes:**

- Key files: `src/wambatic/settings.py`, `src/wambatic/cli.py`, `src/wambatic/reports/web.py`, `docs/reference/settings.md`
- `wambatic.settings` imports nothing from wambatic (system spec, layering), so the host checks live there and `hosts.py` (Task 2) assumes a checked name

---

## Task 2: Add `hosts.py` and `ServerVersionError`

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** fetch spec 1.16, Module location (`hosts.py`), API (hosts.py), Error handling (`ServerVersionError`), GitHub hosts (Addresses, Server version)

**Technical Goal:** One place turns a host name into its REST and GraphQL addresses and parses a server version.

**Subtasks:**

- [x] Create `src/wambatic/fetch/hosts.py` with `GitHubHost` (frozen, slots: `name`, `rest_url`, `graphql_url`, and the `is_dotcom` property), `GITHUB_COM`, `MIN_SERVER_VERSION = (3, 19)` with a comment naming 2026-11-02 and the oldest supported release, `parse_host` and `parse_server_version`, as the spec's API gives them
- [x] `parse_host('github.com')` gives `https://api.github.com` and `https://api.github.com/graphql`; any other checked name gives `https://<name>/api/v3` and `https://<name>/api/graphql`; text that fails the settings' rules raises `InvalidRequestError`
- [x] Add `ServerVersionError(FetchError)` to `src/wambatic/fetch/errors.py`, carrying the host, the version found (or none) and `MIN_SERVER_VERSION`, with a message naming all three
- [x] Tests in a new `src/tests/fetch/test_hosts.py` (both kinds of host, a port, a refused name, `'3.19.2'`, `'3.19'`, `'3'`, `'x.y'`, `''`), and the new error in `src/tests/fetch/test_errors.py`

**Acceptance Criteria:**

- [x] `parse_host('ghe.example.com').graphql_url == 'https://ghe.example.com/api/graphql'`
- [x] `parse_server_version('3.19.2') == (3, 19)`; `parse_server_version('3')` raises `ServerVersionError`

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_hosts.py src/tests/fetch/test_errors.py src/tests/test_package.py src/tests/test_layering.py` passes

**Notes:**

- Depends on Task 1 (the host rules `parse_host` relies on)
- `src/tests/test_layering.py` checks the package's import rules; `hosts.py` imports only `wambatic.fetch.errors`

---

## Task 3: Point `GitHubClient` at a `GitHubHost`

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** fetch spec 1.16, API (`GitHubClient`), GitHub hosts (Addresses)

**Technical Goal:** The client takes its REST and GraphQL addresses from a `GitHubHost`, so an Enterprise host's GraphQL goes to `/api/graphql`, outside `/api/v3`.

**Subtasks:**

- [x] Replace `GitHubClient`'s `api_url` with `host: GitHubHost = GITHUB_COM`; `graphql` posts to `host.graphql_url` and `rest_get` gets `{host.rest_url}{path}`
- [x] `Fetcher` builds its client with `parse_host(settings.github_host)` when it is given none
- [x] Change every test and fixture that passed `api_url` (`src/tests/conftest.py`, `src/tests/test_cli.py`, the fetch tests) to build a `GitHubHost` directly with the replay server's URLs
- [x] Teach the replay server (`src/tests/fixtures/fetch/server.py`) an Enterprise layout that serves REST under `/api/v3` and GraphQL at `/api/graphql`, and records each request's path
- [x] Tests in `src/tests/fetch/test_client.py`: a github.com host and an Enterprise host each send GraphQL and REST to their own paths

**Acceptance Criteria:**

- [x] Against the Enterprise layout, a GraphQL query reaches `/api/graphql` and a REST request `/api/v3/...`; no request reaches `/api/v3/graphql`
- [x] No source or test file mentions `api_url` (`grep -rn api_url src` prints nothing)

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_client.py src/tests/fetch/test_server.py src/tests/fetch/test_base.py src/tests/fetch/test_fetcher.py src/tests/test_cli.py` passes

**Notes:**

- Depends on Task 2
- Key files: `src/wambatic/fetch/client.py`, `src/wambatic/fetch/base.py`, `src/tests/fixtures/fetch/server.py`, `src/tests/conftest.py`

---

## Task 4: Accept rate limits that are switched off

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** fetch spec 1.16, Implementation (Requests, retries and rate limits, step 6, and the `rateLimit` paragraph), GitHub hosts (Rate limits)

**Technical Goal:** An Enterprise server with rate limits switched off, the default, syncs; github.com keeps its check that every query selects `rateLimit`.

**Subtasks:**

- [x] A response with no `x-ratelimit-*` headers leaves its `RateLimitState` unchanged, on any host (check the current behaviour first and change it only if it does not)
- [x] In `graphql_dated`, a `rateLimit` that is absent or `null` is accepted when `host.is_dotcom` is false and leaves the GraphQL state unchanged; on github.com it still raises `GraphQLError` (`MALFORMED`)
- [x] Add Enterprise fixtures to `src/tests/fixtures/fetch/responses.py`, written from GitHub's Enterprise Server documentation and naming the page each comes from: a GraphQL response with `rateLimit: null`, one without `rateLimit`, and REST responses without `x-ratelimit-*` headers
- [x] Tests in `src/tests/fetch/test_client.py` and `src/tests/fetch/test_ratelimit.py`: both Enterprise shapes are accepted and never wait; the same responses from a github.com host raise; a header-less run of many requests never becomes exhausted

**Acceptance Criteria:**

- [x] A sync of a fixture repository against the Enterprise layout with no rate-limit data completes and never sleeps
- [x] The github.com test that a query lacking `rateLimit` fails still passes

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_client.py src/tests/fetch/test_ratelimit.py src/tests/fetch/test_fetcher.py` passes

**Notes:**

- Depends on Task 3
- GitHub documents that rate limits are disabled by default on Enterprise Server, but not what `rateLimit` returns then (checked 2026-11-02); both shapes are therefore accepted (fetch review 1, item 2)

---

## Task 5: Read an Enterprise host's token as `gh` does

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** fetch spec 1.16, API (`fetch_token`), Error handling (`AuthError`), GitHub hosts (Token); system spec 1.10, Settings (variables); reports spec 1.14, Error handling

**User Story:** As a user of a GitHub Enterprise server, I want wambatic to find my Enterprise token the way `gh` does, so that my github.com token is never sent to that server.

**Subtasks:**

- [x] `fetch_token(host: GitHubHost = GITHUB_COM)` in `src/wambatic/fetch/auth.py`: github.com unchanged; an Enterprise host reads `GH_ENTERPRISE_TOKEN`, else `GITHUB_ENTERPRISE_TOKEN`, else `gh auth token --hostname <host.name>`, and never `GITHUB_TOKEN`
- [x] The no-token `AuthError` message for an Enterprise host says to set `GH_ENTERPRISE_TOKEN` or run `gh auth login --hostname <host>`; the github.com message is unchanged
- [x] `src/wambatic/reports/service.py` and `src/wambatic/reports/web.py` pass `parse_host(settings.fetch.github_host)` to `fetch_token`
- [x] Remove the `# auditme: accept[spec-api-signature-drift]` line above `fetch_token` in the fetch spec's API block: with the host argument built, spec and code agree and `bin/audit-check.sh` must pass without it
- [x] Tests in `src/tests/fetch/test_auth.py` (the order of the variables, `gh` called with `--hostname`, `GITHUB_TOKEN` ignored for an Enterprise host, both messages) and `src/tests/reports/test_service.py`; the tests set variables with `monkeypatch` and never print a token

**Acceptance Criteria:**

- [x] With `GITHUB_TOKEN` set and no Enterprise variable, an Enterprise host's `fetch_token` runs `gh auth token --hostname <host>` and, when that fails, raises `AuthError`
- [x] A replayed Enterprise sync sends the Enterprise token in `Authorization`

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_auth.py src/tests/reports/test_service.py src/tests/reports/test_web.py src/tests/test_cli.py` passes
- [x] `bin/audit-check.sh` exits 0 (the spec's accept line is gone)

**Notes:**

- Depends on Task 3
- Never list or print environment variables in a test or a log; test for a variable with `monkeypatch.setenv` and `monkeypatch.delenv` only (shared security rule)

---

## Task 6: Record the host and the server version in the cache

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** cache spec 1.1, API (`Cache.open`, `server_version`, `write_server_version`), Error handling (`CacheHostError`), Implementation (The host); fetch spec 1.16, GitHub hosts (Provenance)

**Technical Goal:** A cache knows which host it holds and refuses another, and keeps the Enterprise server's last version outside its identity.

**Subtasks:**

- [x] `Cache.open(path, *, host='github.com', ignore_version=False)`: a file without a `github_host` row gets `github.com` written; a recorded host other than `host` raises `CacheHostError` before the other identity keys are compared, whatever `ignore_version` says; a new file records `host`
- [x] Add `CacheHostError(CacheError)` naming the cache path and both hosts and saying to set `fetch.cache_path` or run `wambatic cache clear` with that host
- [x] `github_host` is part of `Cache.identity()`; `server_version` is a `meta` row outside it, with `Cache.server_version()` and `Cache.write_server_version(version)`
- [x] `inspect_cache` and `CacheInfo` report both rows
- [x] Every `Cache.open` caller passes `settings.fetch.github_host` (`src/wambatic/cli.py`, `src/wambatic/reports/web.py`)
- [x] Tests in `src/tests/fetch/test_cache.py`: a cache without the row (made by the current code before the change, built in the test) opens as github.com and gains the row; a github.com cache opened for an Enterprise host raises `CacheHostError` with and without `ignore_version`; `server_version` survives a reopen and does not change the identity

**Acceptance Criteria:**

- [x] A github.com cache written before this task opens unchanged, with no `CacheVersionError`
- [x] `--ignore-cache-version` never lets a cache made for one host be read for another

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_cache.py src/tests/fetch/test_errors.py src/tests/test_cli.py src/tests/reports/test_web.py` passes

**Notes:**

- Depends on Task 1
- No `SCHEMA_VERSION` increase: the missing row is read as github.com, the only host the code could reach before (fetch review 1, item 4)

---

## Task 7: Check the Enterprise server's version before syncing

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** fetch spec 1.16, API (`GitHubClient.server_version`), Error handling (`ServerVersionError`, `GraphQLError`), GitHub hosts (Server version, Provenance, Testing)

**User Story:** As a user of a GitHub Enterprise server, I want an unsupported server refused up front with its version named, so that I do not get a half-finished sync or a puzzling schema error.

**Subtasks:**

- [x] `GitHubClient.server_version()`: `None` on github.com with no request; on an Enterprise host one REST `GET /meta`, its `installed_version` parsed with `parse_server_version` and refused below `MIN_SERVER_VERSION`, missing or unparseable with `ServerVersionError`; the result is kept for the client's life and the error is never retried
- [x] `Fetcher.sync` and `Fetcher.owner_kind` call it before any other request; `sync` writes the version with `Cache.write_server_version`
- [x] `Fetcher.provenance` adds `server_version` when the cache records one (`github_host` already comes with the identity from Task 6)
- [x] On an Enterprise host, `GraphQLError`'s message also names the host and the server version
- [x] Add `GET /meta` fixtures written from GitHub's Enterprise Server documentation (3.19.0 accepted, 3.18.4 refused, and none) and serve them in the replay server's Enterprise layout
- [x] Tests in `src/tests/fetch/test_client.py`, `src/tests/fetch/test_fetcher.py` and `src/tests/fetch/test_base.py`: `GET /meta` is requested once per client and never on github.com; a refused server makes no other request; provenance carries both keys

**Acceptance Criteria:**

- [x] Syncing against a server reporting 3.18.4 raises `ServerVersionError` naming 3.18.4 and 3.19, and the replay server saw only `GET /api/v3/meta`
- [x] A github.com sync makes exactly the requests it made before this task

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_client.py src/tests/fetch/test_fetcher.py src/tests/fetch/test_base.py src/tests/fetch/test_server.py` passes

**Notes:**

- Depends on Tasks 4, 5 and 6
- Whether `GET /meta` needs authentication is not documented; the request carries the token like every other

---

## Task 8: Add `--github-host` to `report`, `serve` and `cache`

**Status:** done
**Priority:** medium
**Complexity:** small
**Spec Reference:** CLI spec 1.1, Command line and Flags

**User Story:** As a user with both github.com and an Enterprise server, I want a `--github-host` flag, so that I can switch hosts without editing the config file.

**Subtasks:**

- [x] Add `--github-host HOST` to the `report`, `serve` and `cache` commands in `src/wambatic/cli.py`, passed to settings as an override of `fetch.github_host`, so the settings' checks apply and a bad host exits 2 with `SettingsError`
- [x] `cache clear` and `cache info` act on that host's file (`cache_path_for`), and `cache info` shows `github_host` and `server_version`
- [x] Add the flag to `docs/reference/cli.md` for each command
- [x] Tests in `src/tests/test_cli.py`: each command with the flag reaches the right cache file and host; a bad host exits 2; `serve --host` still means the bind address

**Acceptance Criteria:**

- [x] `wambatic cache info --github-host ghe.example.com` reports `~/.cache/wambatic/cache-ghe.example.com.sqlite3` (or that there is no cache there)
- [x] `pytest src/tests/test_docs.py` passes with the new flag

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_cli.py src/tests/test_docs.py` passes

**Notes:**

- Depends on Tasks 1 and 6

---

## Task 9: Name an Enterprise host in the reports

**Status:** done
**Priority:** medium
**Complexity:** small
**Spec Reference:** terminal-report spec 1.1, Implementation (item 14); HTML-report spec 1.1, Implementation (Layout, item 8)

**User Story:** As a reader of a report from an Enterprise server, I want the footer to say which host and server version the numbers came from, so that a saved report is not mistaken for github.com data.

**Subtasks:**

- [x] The terminal provenance footer starts with `GitHub host: <host> (Enterprise Server <server_version>)` when `provenance['github_host']` is not `github.com`, in `src/wambatic/reports/terminal.py`
- [x] The HTML footer shows the same line, in `src/wambatic/reports/html.py` and its template
- [x] Tests in `src/tests/reports/test_terminal.py` and `src/tests/reports/test_html.py`: the line appears for an Enterprise host and is absent for github.com, whose output is unchanged byte for byte

**Acceptance Criteria:**

- [x] The existing terminal, HTML and JSON tests pass unchanged for github.com results

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/reports/test_terminal.py src/tests/reports/test_html.py src/tests/reports/test_base.py` passes

**Notes:**

- Depends on Task 7 (the provenance keys)
- The JSON output already carries every provenance key, so `base.py` does not change

---

## Task 10: Document Enterprise Server and close the list

**Status:** todo
**Priority:** medium
**Complexity:** medium
**Spec Reference:** system spec 1.10 (Limits accepted, Settings); implementation order 1.11, step 13; every spec section above (closing)

**User Story:** As a user of a GitHub Enterprise server, I want the guide to say how to point wambatic at my server and what it needs, so that I can set it up without reading the specs.

**Subtasks:**

- [ ] Add a guide page on GitHub Enterprise Server under `docs/guide/` (the host setting and flag, the token variables, the minimum server version, the cache file per host, rate limits switched off, what is not supported: `*.ghe.com`), and add it to the `nav` in `mkdocs.yml`
- [ ] Update `docs/token.md` with the Enterprise variables and `gh auth login --hostname`, `docs/limits.md` (Enterprise Server is supported from 3.19; Enterprise Cloud with data residency is not), `docs/guide/cache.md` (one file per host, `CacheHostError`) and `docs/reference/exit-statuses.md` (`ServerVersionError` and `CacheHostError`, both exit 1)
- [ ] Mark step 13 `done` in `agents/specs/implementation-order.md`, linking this list, and set its `**Status:**` to `implemented`
- [ ] Set the `**Status:**` of each amended spec to `implemented`: fetch, cache, system, CLI, reports, terminal report and HTML report
- [ ] Move the `TODO.md` item "GitHub Enterprise Server is not supported" to the end of `DONE.md`: append its heading and body unchanged, then `Done: <date> - built by agents/tasks/fetch/tasks-1.md against fetch spec 1.16.`, and remove it from `TODO.md`
- [ ] Add the list to `agents/tasks/index.md` if it is not there

**Acceptance Criteria:**

- [ ] The guide explains how to use an Enterprise server, from setting the host to the first report
- [ ] `TODO.md` no longer holds the Enterprise item, and `DONE.md` ends with it and its `Done:` line

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] `uv sync --group docs` succeeds
- [ ] `mkdocs build --strict` exits 0
- [ ] `pre-commit run --all-files` exits 0
- [ ] `bin/audit-check.sh` exits 0
- [ ] `python3 ~/.claude/skills/todo-review/verify_bodies.py <before> TODO.md DONE.md` exits 0, where `<before>` is `TODO.md` as of the commit that added this list (`git show "$(git log --diff-filter=A --format=%H -- agents/tasks/fetch/tasks-1.md)":TODO.md`)
- [ ] `pytest src/tests/fetch src/tests/reports src/tests/stats src/tests/test_cli.py src/tests/test_settings.py src/tests/test_docs.py src/tests/test_layering.py src/tests/test_package.py src/tests/test_screenshots.py` passes: every test that reaches `settings`, `fetch` or `reports`, the modules this list changes

**Notes:**

- Depends on Tasks 1 to 9
- When the output changes, the user-guide rule in `AGENTS.md` asks for `bin/screenshots.sh`; the github.com output does not change, so no screenshot is retaken
- `browser` and `live` tests run in CI's `browser` and `live` jobs; the local run above skips them without Chromium or a token
