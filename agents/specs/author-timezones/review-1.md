# Review: author timezones 1.0, commits dated in their authors' zones

**Date:** 2026-11-03
**Spec:** `agents/specs/author-timezones/spec.md` (new, 1.0), with amendments to `agents/specs/system/spec.md` (1.11 to 1.12), `agents/specs/stats/spec.md` (1.11 to 1.12), `agents/specs/metric-groups/spec.md` (1.1 to 1.2), `agents/specs/cache/spec.md` (1.2 to 1.3), `agents/specs/fetch/spec.md` (1.17 to 1.18), `agents/specs/commit-sync/spec.md` (1.0 to 1.1), `agents/specs/cli/spec.md` (1.2 to 1.3), `agents/specs/reports/spec.md` (1.14 to 1.15), `agents/specs/web-app/spec.md` (1.0 to 1.1), `agents/specs/terminal-report/spec.md` and `agents/specs/html-report/spec.md` (1.2 to 1.3), and `agents/specs/implementation-order.md` (1.12 to 1.13, step 15)
**Task list written against it:** none yet
**Review page:** https://claude.ai/artifact/A4mkjSKLidFRN1j7ei8Jsk (approve or flag each choice there; answers are copied into Answers below)

## What is being reviewed and how

The system spec accepted "one timezone per report" for the first release: every record is dated by its local date in `--tz`. On 2026-11-02 the user chose to lift it (`TODO.md`, "A report has one timezone"). The amendments add an opt-in `author` mode in which each commit is dated on its author's calendar, from a per-author setting or the offset git recorded, while every other record stays in the report zone. The design decisions were answered on 2026-11-03 through the question tool and are recorded under Answers. What remains is the choices made while writing the amendments, listed under The items: approve each, or flag it with a comment saying what to change. Work on the task list stops until every item has an answer.

## Automatic checks

- `git diff --check` over the amended specs: pass.
- Every relative link in the specs and this review resolves to a file: pass.
- `bin/audit-check.sh` (the whole-tree audit, including spec signature drift): pass, with no new acceptance.
- Measured on 2026-11-03 on `pallets/flask`'s latest default-branch commits: GraphQL `authoredDate`, GraphQL `author { date }` and REST `commit.author.date` all return UTC (`2026-10-30T15:05:20Z`); `git log --format=%aI` on the bare clone returns `2026-10-30T08:05:20-07:00` for the same commit: pass, as the spec says.
- The report zone decides only local dates: no stats module reads the hour of day or the weekday (searched `src/wambatic/stats` for `hour`, `weekday` and `punch` on 2026-11-03; only duration hours were found): pass.
- No code has been written; the task list's tests are the first check of the behaviour: **needs attention** (item 13).

## The items

1. **Only a clone gives an offset.** `GitCommit.authored_offset` comes from `%aI`; the `api` and `api-files` methods leave `Commit.authored_offset` `None`, because GitHub's dates carry none (measured above). No extra request is made to look for one.
2. **The offset is stored as minutes east of UTC, and `authored_at` stays UTC.** A nullable `commits.authored_offset` column; nothing that orders or compares commits changes.
3. **One schema raise, to 6, with no migration.** A cache of 5 is refused once with the usual `CacheVersionError` message and the user clears and refetches it, as for every earlier raise; clone-read repositories refetch cheaply, API-read ones cost their usual first sync.
4. **The per-author setting wins everywhere.** `stats.author_timezones` overrides a recorded offset in cloned repositories too, so a laptop clock left on UTC can be corrected; logins are compared case-insensitively; an `unattributed` commit uses its offset, else the report zone.
5. **The setting is a JSON object, stored as sorted pairs.** `{"octocat": "Europe/London"}` in the config file becomes `(('octocat', 'Europe/London'),)`, by a new `convert` branch, so the settings stay hashable; an unknown zone is a `SettingsError` naming `stats.author_timezones.<login>` when settings load.
6. **Only a commit's day moves.** Bucket labels, bucket boundaries, partial-bucket marks and the default `until` (today) stay in the report zone; a commit already dated tomorrow by an author east of it is outside a range ending today, until tomorrow.
7. **The read window is unchanged.** It is already the UTC range of the requested dates widened by one day each side, which covers every real offset (UTC-12 to UTC+14).
8. **`active_days` follows the author's calendar too**, in the series and in the `top_contributors` table, because both use the commit's dated day.
9. **One `unavailable` row per repository with an undated-by-author commit.** In `author` mode, a repository whose commits in the range include one dated in the report zone (no offset, no setting entry) gets `{'metric': 'commit dates: <owner/name>', 'reason': ...}`; no row in `report` mode.
10. **Provenance records the mode.** `commit_timezone` whenever `commits` is read, and `author_timezones` (the JSON map) in `author` mode; `timezone` keeps the report zone.
11. **The title text.** In `author` mode the terminal title's and HTML header's zone becomes `commits in authors' zones, other events in <tz>`; in `report` mode both are unchanged.
12. **The web app gets the option too.** A form select (report zone or authors' zones, preset from the setting) sent as `commit_tz`, parsed by the CLI's `service.make_request`, a 400 on a bad value; `StatsRequest` itself is unchanged, the override being applied to the settings first as `--tz` is.
13. **Nothing is built yet.** The implementation order's step 15 names what a task list must prove: `report` mode unchanged, a `+09:00` Monday commit counted on Monday in a UTC report, the setting overriding the offset, an API-read repository dated in the report zone with its row, `--commit-tz` overriding the setting, the two-zone title, and a cache of 5 refused.

## Decisions

None open. The decisions this change needed were answered on 2026-11-03 and are recorded below.

## Answers

Answered on 2026-11-03 through the question tool, before the amendments were written:

- **Where an author's zone comes from:** the commit's own recorded offset, with a per-author setting (login to IANA zone) that overrides it.
- **Default:** opt in, by a setting; the default keeps every existing report unchanged.
- **Non-commit records** (pull requests, issues, runs, releases, stars, forks): the report zone, as today.
- **Which date decides bucket and range:** the commit's local date in its author's zone, for both.
- **How the report shows it:** the title names both zones; the provenance records the mode and the map.
- **A CLI flag:** yes, `--commit-tz` overrides the setting for one run.
- **A commit with no recorded offset** (asked after the measurement showed GitHub's API gives none): dated in the report zone, and its repository named in `tables['unavailable']` and so in the reports.

Item verdicts, answered on the review page on 2026-11-03 between 05:49 and 05:50 UTC: items 1 to 13 **approved**, with no comments.
