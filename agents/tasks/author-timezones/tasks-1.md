# Tasks: Author timezones

**Spec:** `agents/specs/author-timezones/spec.md`
**Created:** 2026-11-03
**Version:** 1

This list builds author timezones spec 1.0 (step 15 of the implementation order), with the amendments made with it: system spec 1.12, stats spec 1.12, metric groups spec 1.2, cache spec 1.3, fetch spec 1.18, commit sync spec 1.1, CLI spec 1.3, reports spec 1.15, web app spec 1.1, and terminal-report and HTML-report specs 1.3. The choices are in `agents/specs/author-timezones/review-1.md`, every one approved on 2026-11-03. Nothing in it is built yet: no `authored_offset`, `commit_timezone`, `author_timezones` or `commit_zone` is in `src` (checked 2026-11-03).

In the new `author` mode (`stats.commit_timezone = 'author'`, or `--commit-tz author`) each commit's local date is taken in its author's zone: the `stats.author_timezones` entry for its login, else the UTC offset git recorded (clone-read repositories only: GitHub's API returns UTC, measured 2026-11-03), else the report zone, with an `unavailable` row naming the repository. Every other record stays in the report zone. The default `report` mode must leave every result unchanged.

No query text changes, so no fixture is re-recorded. The user guide's drift test (`src/tests/test_docs.py`) compares `docs/reference/settings.md` with the settings and `docs/reference/cli.md` with the flags, so the task that adds a setting or a flag updates that page in the same commit.

The project has no affected-tests tool: each task names its test files. Every `pytest` and `mkdocs` command runs after `source bin/activate.sh`; `mkdocs` needs `uv sync --group docs` first. Never list environment variables or print a token: test one with `[ -n "${GITHUB_TOKEN:-}" ]` and print only yes or no.

---

## Task 1: Add the commit timezone settings

**Status:** done
**Priority:** high
**Complexity:** small
**Spec Reference:** author timezones 1.0, API (`CommitTimezone`, `StatsSettings`, `author_zones`), Error handling, Settings; stats 1.12, Settings

**Technical Goal:** The settings say which zone dates a commit and which zone each named author is in, and refuse a bad value when they load.

**Subtasks:**

- [x] Add `CommitTimezone = typing.Literal['report', 'author']`, `commit_timezone: CommitTimezone = 'report'` and `author_timezones: tuple[tuple[str, str], ...] = ()` to `StatsSettings` in `src/wambatic/settings.py`
- [x] Add a `convert` branch for `tuple[tuple[str, str], ...]`: a JSON object of strings becomes pairs `(login.casefold(), zone)` sorted by login; anything else is `SettingsError('stats.author_timezones has the wrong type')`
- [x] Add `author_zones(settings)`, returning `zoneinfo.ZoneInfo` per casefolded login, and call it when settings load, so an unknown zone is a `SettingsError` naming `stats.author_timezones.<login>` and the value before any sync
- [x] Add both settings to `docs/reference/settings.md`
- [x] Tests in `src/tests/test_settings.py`: the defaults; a JSON object read and sorted, mixed-case logins casefolded; a non-object and a non-string zone refused; an unknown zone refused with the setting name and value; `commit_timezone` outside the two values refused

**Acceptance Criteria:**

- [x] `{"stats": {"author_timezones": {"OctoCat": "Asia/Tokyo"}}}` loads as `(('octocat', 'Asia/Tokyo'),)`
- [x] `{"stats": {"author_timezones": {"octocat": "Mars/Base"}}}` fails at load with `stats.author_timezones.octocat` in the message

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/test_settings.py src/tests/test_docs.py` passes

**Notes:**

- Key files: `src/wambatic/settings.py`, `docs/reference/settings.md`
- `stats.timezone` is resolved with `zoneinfo.ZoneInfo` in `reports/service.py` (`resolve_tz`); follow its message style

---

## Task 2: Keep each commit's recorded offset, cache schema 6

**Status:** done
**Priority:** high
**Complexity:** medium
**Spec Reference:** author timezones 1.0, API (`Commit.authored_offset`, `GitCommit.authored_offset`), Implementation (Keeping the offset, Cache); fetch 1.18; commit sync 1.1; cache 1.3

**Technical Goal:** A commit read from a clone carries the UTC offset git recorded, and the cache stores it, so stats can date the commit on its author's calendar.

**Subtasks:**

- [x] Add `authored_offset: int` to `GitCommit` in `src/wambatic/fetch/git.py`: the parsed `%aI` value's `utcoffset()` in whole minutes, taken before `authored_at` is converted to UTC
- [x] Add `authored_offset: int | None = None` to `Commit` in `src/wambatic/fetch/base.py`; the `clone` method copies it from the `GitCommit`; the `api` and `api-files` methods leave it `None`
- [x] In `src/wambatic/fetch/cache.py`: set `SCHEMA_VERSION` to 6, add the nullable `commits` column `authored_offset INTEGER`, write it with the commit and read it back into `Commit.authored_offset`
- [x] Tests in `src/tests/fetch/test_git.py`: a commit made with `GIT_AUTHOR_DATE='2026-11-02T01:00:00+09:00'` in a `git init` repository has `authored_offset == 540` and a UTC `authored_at`; a negative offset (`-07:00` gives `-420`); in `src/tests/fetch/test_cache.py`: an offset and a `None` written and read back, a cache of schema 5 refused with `CacheVersionError`; in `src/tests/fetch/test_fetcher.py`: a clone sync stores the offset and an `api` sync stores `None`

**Acceptance Criteria:**

- [x] A clone-read commit's offset survives a write and a read of the cache
- [x] Every existing fetch test still passes, and `authored_at` is UTC everywhere

**Definition of Done:**

- [x] `source bin/activate.sh` succeeds
- [x] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [x] `pytest src/tests/fetch/test_git.py src/tests/fetch/test_cache.py src/tests/fetch/test_fetcher.py src/tests/fetch/test_base.py` passes

**Notes:**

- Independent of Task 1
- Key files: `src/wambatic/fetch/git.py` (the `%aI` parse, near the `fromisoformat` call), `base.py`, `cache.py`
- No migration: a cache of 5 is refused, as for every earlier raise (cache spec, Cache)

---

## Task 3: Date commits in their authors' zones in stats

**Status:** todo
**Priority:** high
**Complexity:** medium
**Spec Reference:** author timezones 1.0, API (`commit_zone`), Implementation (Dating a commit, Repositories without offsets, Provenance); stats 1.12, Bucketing and Provenance; metric groups 1.2, `active_days`

**User Story:** As a user whose team spans timezones, I want each commit counted on the day its author made it, so that daily activity and active days match what each author saw.

**Subtasks:**

- [ ] Add `commit_zone(commit, tz, settings, zones)` to `src/wambatic/stats/engine.py`: `tz` in `report` mode; in `author` mode the casefolded login's zone from `zones`, else `datetime.timezone(datetime.timedelta(minutes=commit.authored_offset))`, else `tz`
- [ ] In `read_commits`, build `zones = wambatic.settings.author_zones(request.settings)` once, and compute each commit's day as `commit.authored_at.astimezone(commit_zone(...)).date()`; keep the one-day-widened UTC read window
- [ ] In `author` mode, record which repositories had a commit in the range dated in the report zone for want of an offset and a setting entry, and add one `tables['unavailable']` row per such repository, ordered by name: `{'metric': 'commit dates: <owner/name>', 'reason': 'dated in <report zone>: GitHub gives no author offset for a repository that is not cloned; stats.author_timezones sets an author\'s zone'}`
- [ ] Add the provenance key `commit_timezone` whenever `commits` is read, and `author_timezones` (the JSON object of the map) in `author` mode
- [ ] Tests in `src/tests/stats/test_engine.py`: in `report` mode results are unchanged (an existing fixture's result equal before and after); in `author` mode a commit at `2026-11-02T01:00:00+09:00` (Monday) is in Monday's day bucket of a UTC report, and inside `--since 2026-11-02`; a setting entry overrides the offset; an unattributed commit uses its offset; a commit with no offset is dated in the report zone and its repository gets exactly one `unavailable` row; `active_days` and the `top_contributors` row follow the author's dates; both provenance keys

**Acceptance Criteria:**

- [ ] `report` mode gives the same `StatsResult` as before this task for every existing stats test
- [ ] In `author` mode bucket labels, partial-bucket marks and every non-commit series are unchanged

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/stats/test_engine.py src/tests/stats/test_activity.py src/tests/stats/test_properties.py src/tests/stats/test_fixtures.py` passes

**Notes:**

- Depends on Tasks 1 and 2
- Key files: `src/wambatic/stats/engine.py` (`read_commits`, the provenance and `unavailable` rows), `activity.py` (`DatedCommit`)
- The default `until` stays today in the report zone (author timezones spec, Dating a commit)

---

## Task 4: Add `--commit-tz` and the web app's `commit_tz`

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** author timezones 1.0, Implementation (CLI and web app), Error handling; CLI 1.3; reports 1.15; web app 1.1

**User Story:** As a user, I want to switch commit dating for one run from the command line or the web form, so that I can compare both views without editing my settings.

**Subtasks:**

- [ ] Add `--commit-tz` (`report` or `author`) to `report` in `src/wambatic/cli.py`; it replaces `stats.commit_timezone` in the settings before `make_request`, as `--tz` replaces `stats.timezone`; another value is a `UsageError`
- [ ] Apply the same override for the web app's `commit_tz` query parameter in `src/wambatic/reports/web.py` and `service.py`; another value is a 400 with the CLI's message
- [ ] Add the select (Commit dates: report zone or authors' zones, preset from `stats.commit_timezone`) to `src/wambatic/reports/templates/form.html`, sent as `commit_tz`
- [ ] Add `--commit-tz` to `docs/reference/cli.md`
- [ ] Tests in `src/tests/test_cli.py`: the flag overrides the setting both ways, a bad value is a `UsageError`; in `src/tests/reports/test_service.py` and `src/tests/reports/test_web.py`: the parameter overrides the setting, a bad value is a 400, the form shows the select with the setting's value preset

**Acceptance Criteria:**

- [ ] `wambatic report ... --commit-tz author` gives `provenance['commit_timezone'] == 'author'` with the setting at `report`
- [ ] The form works without script and submits `commit_tz`

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/test_cli.py src/tests/reports/test_service.py src/tests/reports/test_web.py src/tests/test_docs.py` passes

**Notes:**

- Depends on Tasks 1 and 3
- Key files: `src/wambatic/cli.py` (near the `tz` argument and its settings override), `src/wambatic/reports/service.py`, `web.py`, `templates/form.html`

---

## Task 5: Name both zones in the report titles

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** author timezones 1.0, Implementation (Reports); terminal report 1.3, item 1; HTML report 1.3, header

**User Story:** As a reader of a report, I want the title to say when commits are dated in their authors' zones, so that I do not read a daily chart as if it were all in one zone.

**Subtasks:**

- [ ] In `src/wambatic/reports/terminal.py`, when `provenance['commit_timezone']` is `'author'`, show `commits in authors' zones, other events in <timezone>` in place of the timezone in the title line; otherwise unchanged
- [ ] Do the same in the HTML header in `src/wambatic/reports/html.py`
- [ ] Tests in `src/tests/reports/test_terminal.py` and `src/tests/reports/test_html.py`: the two-zone text in `author` mode, the title unchanged in `report` mode and for a result without the key; the `unavailable` row from Task 3 appears in both reports' Unavailable sections

**Acceptance Criteria:**

- [ ] A `report`-mode terminal and HTML report is byte-for-byte what it was before this task for the existing test results

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] The task's commit passes its pre-commit hooks (never `--no-verify`)
- [ ] `pytest src/tests/reports/test_terminal.py src/tests/reports/test_html.py src/tests/reports/test_rows.py` passes

**Notes:**

- Depends on Task 3
- Key files: `src/wambatic/reports/terminal.py`, `html.py`
- The default output does not change, so the screenshots are not re-run

---

## Task 6: Document author timezones and close the list

**Status:** todo
**Priority:** medium
**Complexity:** small
**Spec Reference:** system 1.12 (Limits accepted); implementation order 1.13, step 15; every spec section above (closing)

**User Story:** As a user, I want the guide to say how to date commits in their authors' zones, how to set an author's zone, and why some repositories cannot be, so that I can trust a daily report across zones.

**Subtasks:**

- [ ] Update `docs/guide/periods.md` (the two modes, `--commit-tz`, a worked example of a `+09:00` commit, the default `until`), `docs/guide/config.md` (`stats.commit_timezone`, `stats.author_timezones`), `docs/guide/cache.md` (schema 6 refuses an older cache: clear and refetch), `docs/guide/web.md` (the commit dates select) and `docs/limits.md` (replace "A report uses one time zone" with the limit of system spec 1.12: only cloned repositories carry offsets)
- [ ] Mark step 15 `done` in `agents/specs/implementation-order.md`, linking this list, and set its `**Status:**` to `implemented`
- [ ] Set the spec's `**Status:**` to `implemented` in `agents/specs/author-timezones/spec.md`, and in each amended spec: system, stats, metric groups, cache, fetch, commit sync, CLI, reports, web app, terminal report and HTML report
- [ ] Move the `TODO.md` item "A report has one timezone" to the end of `DONE.md`: append its heading and body unchanged, then `Done: <date> - built by agents/tasks/author-timezones/tasks-1.md against author timezones spec 1.0.`, and remove it from `TODO.md`
- [ ] Add the list to `agents/tasks/index.md` if it is not there

**Acceptance Criteria:**

- [ ] The guide explains both modes, the per-author setting and what the `commit dates` unavailable row means
- [ ] `TODO.md` no longer holds the timezone item, and `DONE.md` ends with it and its `Done:` line

**Definition of Done:**

- [ ] `source bin/activate.sh` succeeds
- [ ] `uv sync --group docs` succeeds
- [ ] `mkdocs build --strict` exits 0
- [ ] `pre-commit run --all-files` exits 0
- [ ] `bin/audit-check.sh` exits 0
- [ ] `python3 ~/.claude/skills/todo-review/verify_bodies.py <before> TODO.md DONE.md` exits 0, where `<before>` is `TODO.md` as of the commit that added this list (`git show "$(git log --diff-filter=A --format=%H -- agents/tasks/author-timezones/tasks-1.md)":TODO.md`)
- [ ] `pytest src/tests/fetch src/tests/reports src/tests/stats src/tests/test_cli.py src/tests/test_settings.py src/tests/test_docs.py src/tests/test_layering.py src/tests/test_package.py src/tests/test_screenshots.py` passes: every test that reaches `settings`, `fetch`, `stats` or `reports`, the modules this list changes

**Notes:**

- Depends on Tasks 1 to 5
- `browser` and `live` tests run in CI's `browser` and `live` jobs; the local run above skips them without Chromium or a token
- The screenshot cache (`~/.cache/wambatic/docs.sqlite3`) is at schema 5 and will be refused by the next `bin/screenshots.sh` run; this list does not re-run it, because the default output is unchanged
