# Metric groups

**Version:** 1.1
**Status:** implemented
**Date:** 2026-11-02

What each of the `activity`, `flow`, `delivery` and `popularity` groups counts: its series names, units and order, and its tables. Part of [Stats](../stats/spec.md), which holds the API, the range, the reading of the cache, aggregation and provenance.

Version 1.0 is the stats spec 1.9 text moved here, with only its cross-references updated, when that spec was split on 2026-11-02, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked. `review-N.md` in the text below means the [stats reviews](../stats/review-1.md) in `agents/specs/stats/`.

Version 1.1 leaves generated files out of the `activity` line counts, from each commit's per-file counts ([Commit sync](../commit-sync/spec.md), [Stats](../stats/spec.md) 1.11); the choices are in the [commit sync review 1](../commit-sync/review-1.md), decided 2026-11-02.

## Module location

`src/wambatic/stats/activity.py`, `flow.py`, `delivery.py`, `popularity.py` and `percentile.py`, with tests in `src/tests/stats/`.

## Groups

**activity** (all subjects; per repository and aggregated)

- `commits` (unit `count`): commits in the bucket, merge commits included.
- `contributors` (unit `count`): distinct author logins with a commit in the bucket, compared case-insensitively, excluding `stats.bot_logins` and excluding unattributed commits (they cannot be told apart by person).
- `active_days` (unit `days`): distinct local dates with at least one commit in the bucket.
- **Code contributions:** `lines_added`, `lines_deleted`, `lines_net` (added minus deleted, unit `lines`), summed per bucket. Since 1.1 they depend on how the repository's commits were read (`Fetcher.commit_method`, [Commit sync](../commit-sync/spec.md)): for `clone` and `api-files`, from each commit's kept files, where a file of `Commit.files` is left out when its path matches a `stats.exclude_paths` pattern (`PurePosixPath(path).full_match(pattern)`) or, with `stats.linguist`, when it is `generated`, and a commit's lines are the sums of its other files' `additions` and `deletions`; for `api`, from the commit's own `additions` and `deletions`, generated files included. The choice follows the recorded method, never whether a commit happens to have files. A commit whose every file is left out still counts in `commits`, `contributors` and `active_days`, with no lines. Merge commits are excluded when `stats.exclude_merge_commits` is true (the default) so lines are not double counted; the setting does not affect `commits`. Bot commits are counted in `commits` and lines; `stats.bot_logins` only affects contributor counts. Until 1.1 generated and vendored files were not filtered, because the cache held only per-commit totals.
- *Repositories that could not be filtered (1.1).* `tables['unavailable']` gets one row per repository of the subject, ordered by name: for an `api` repository `{'metric': 'lines_added, lines_deleted, lines_net: <owner/name>', 'reason': 'generated files are counted: the repository is not cloned (public repositories, and those fetch.clone_repos allows, are cloned; fetch.api_history files reads per-file counts by API)'}`, and when `fetch.branches` is not empty a second row `{'metric': 'commits: <owner/name>', 'reason': 'default branch only: the repository is not cloned and fetch.api_history is totals'}`; for an `api-files` repository with `stats.linguist` on, `{'metric': 'lines_added, lines_deleted, lines_net: <owner/name>', 'reason': 'linguist attributes not read: the repository is not cloned; stats.exclude_paths applies'}`. The series still count every repository; the rows say which part is unfiltered.
- Stars, forks, watchers and languages were listed here until step 10, which moves them to `popularity` (review-4.md decision 1).
- `tables['top_contributors']`: one row per author over the whole range, `{'login', 'commits', 'lines_added', 'lines_deleted', 'lines_net', 'active_days'}`, with the same merge and file rules as the series, ordered by `commits` descending then `login`. Bots are left out; unattributed commits are one row with `login` `'unattributed'`. Produced for every subject, with or without `by_author`.

**flow** (pull requests and issues; total series only, built in step 6)

- Counts (unit `count`), each bucketed by the local date of its event: `prs_opened` (`created_at`), `prs_merged` (`merged_at`), `issues_opened` (`created_at`), `issues_closed` (`closed_at`, issues closed now; a reopened issue is open). A pull request closed without merging counts in `prs_opened` only.
- Durations (unit `hours`), each bucketed by the local date of its end event, as `<name>_p50` (`statistics.median`) and `<name>_p90` (`statistics.quantiles(values, n=10, method='inclusive')[8]`, which stays inside the values, unlike the default `exclusive` method, and accepts one value on Python 3.13 and later): `time_to_first_review` (pull request `created_at` to `first_review_at`), `time_to_merge` (`created_at` to `merged_at`) and `time_to_close` (issue `created_at` to `closed_at`; pull requests have `time_to_merge`). Hours are `(end - start).total_seconds() / 3600`.
- `pr_size_p50` (unit `lines`): `statistics.median_low` of `additions + deletions` over the pull requests merged in the bucket (GitHub's pull request totals, generated files included: an accepted limit, 1.1), so the value is one pull request's real size and an integer, as the JSON output requires of `lines`.
- Bots are counted: `stats.bot_logins` affects contributor counts only, as in `activity`. Who reviewed is settled by the fetch layer (`first_review_at` leaves out the author and bots).
- Series order: `prs_opened`, `prs_merged`, `issues_opened`, `issues_closed`, `time_to_first_review_p50`, `time_to_first_review_p90`, `time_to_merge_p50`, `time_to_merge_p90`, `time_to_close_p50`, `time_to_close_p90`, `pr_size_p50`.

**delivery** (CI and delivery; approximations, labelled as proxies in reports)

Built in step 8; total series only. Percentiles are computed as in `flow` (`statistics.median` for p50, `statistics.quantiles(values, n=10, method='inclusive')[8]` for p90), and an empty bucket has no value for a percentile or a ratio and zero for a count.

- **Actions.** Every workflow run counts, whatever its workflow, event or branch, bucketed by the local date of its `created_at`:
  - `workflow_runs` (unit `count`): runs created in the bucket, finished or not.
  - `workflow_success_rate` (unit `ratio`, 0 to 1): of the bucket's completed runs whose `conclusion` is `success`, `failure`, `timed_out` or `startup_failure`, the share that is `success`. `cancelled`, `skipped`, `neutral`, `action_required` and `stale` are not outcomes of the code and are left out of both counts; a bucket with none of the four has no value.
  - `workflow_duration_p50` and `workflow_duration_p90` (unit `minutes`): `(updated_at - run_started_at).total_seconds() / 60` over the bucket's completed runs with a `run_started_at`, the wall-clock time of the latest attempt. This is a proxy: GitHub's per-run timing endpoint would cost a request per run, and a run's `updated_at` can move after it finishes (a re-run request resets it), which reads as a longer run.
- **Releases.** Published releases only (drafts are not stored), prereleases included, bucketed by the local date of `published_at`:
  - `release_count` (unit `count`).
  - `release_interval_p50` (unit `days`): `statistics.median_low` of the whole days (`(later - earlier).days`) between each release and the previous release of the same repository by `published_at`, bucketed by the later one, so the value is one real interval and an integer, as the JSON output requires of `days`. A repository's first release has no interval.
- **DORA proxies**, following the [four keys](https://dora.dev/guides/dora-metrics-four-keys/). They lean on conventions GitHub does not enforce, so each is emitted only when its inputs exist and is otherwise a row in `tables['unavailable']` naming what is missing:
  - *Deployments.* With `stats.deploy_workflow` set, a deployment is a completed run with `conclusion` `success` whose workflow file name (`workflow_path` with any trailing `@ref` removed, then taken after its last `/`, such as `deploy.yml`) or `name` equals the setting, at its `updated_at` (when it finished). Without the setting, a deployment is a release that is not a prerelease, at its `published_at`. Deployments are per repository.
  - `deployments` (unit `count`): deployments in the bucket. Emitted when the subject has at least one deployment in the cache (at any time); otherwise unavailable with `no releases in the cache and stats.deploy_workflow is not set`, or `no successful run of the workflow named by stats.deploy_workflow`.
  - `lead_time_p50` and `lead_time_p90` (unit `hours`): for each merged pull request, from its `first_commit_at` (its `created_at` when that is `None`) to the first deployment of the same repository at or after its `merged_at`, bucketed by that deployment's local date. A pull request with no deployment after its merge yet is not counted. Emitted with `deployments`, under the same condition.
  - `change_failure_rate` (unit `ratio`): of the bucket's deployments, the share followed by a hotfix pull request of the same repository whose `created_at` is after the deployment and no later than `stats.failure_window` after it. A hotfix pull request is one with a label in `stats.hotfix_labels`, compared case-insensitively. Emitted when `deployments` is and the subject has at least one hotfix pull request in the cache; otherwise unavailable, naming whichever is missing. A deployment within `stats.failure_window` of the end of the range (`until`, not the current time) is counted as not failed, since its window is still open; measuring against the end of the range means a report of a closed range never changes when it is run again.
  - `time_to_restore_p50` and `time_to_restore_p90` (unit `hours`): hotfix pull requests from `created_at` to `merged_at`, bucketed by the local date of `merged_at`. Emitted when the subject has at least one hotfix pull request; it needs no deployments.
- Bots are counted, as in `flow`; `stats.bot_logins` affects contributor counts only.
- Series order: `workflow_runs`, `workflow_success_rate`, `workflow_duration_p50`, `workflow_duration_p90`, `release_count`, `release_interval_p50`, `deployments`, `lead_time_p50`, `lead_time_p90`, `change_failure_rate`, `time_to_restore_p50`, `time_to_restore_p90`; a proxy that is not emitted is left out, never sent as an empty series.

**popularity** (stars, forks, watchers, languages; built in step 10)

A star, a fork or a watch belongs to a repository, not to an author, so for every subject kind the group counts every star and fork of the subject's repositories, as `delivery` does. Total series only.

- Per bucket (unit `count`), by the local date of the event: `stars_added` (stargazers whose `starred_at` is in the bucket) and `forks_added` (direct forks whose `created_at` is in the bucket).
- Cumulative (unit `count`): `stars_total` and `forks_total`, the stargazers (or direct forks) in the cache whose local date is on or before the bucket's last day, or `until` for the last bucket. They count the stars and forks that exist now, by when they were made: a star since removed, or a fork since deleted, is not in any bucket, so a cumulative series never falls and can be below the count GitHub showed at the time. Its last value can also differ from the table below, which is GitHub's own count at the last listing (stars made since the sync, and for forks the whole network).
- A repository whose `Fetcher.stars_hidden` is true has no star history: GitHub listed its stargazers to nobody the token could see, so a series from the cache would read as no stars at all. `compute` leaves its cached stars out of `stars_added` and `stars_total` (its forks stay in), and adds a row to `tables['unavailable']`, `{'metric': 'stars_added, stars_total: <owner/name>', 'reason': ...}`, one per such repository ordered by name, whose reason says GitHub did not list the stargazers to this token and gives the star count of the listing. The repository's `tables['popularity']` row keeps GitHub's own count. The series of a subject with such a repository count only the stars of the others, which the row says.
- Watchers have no series: GitHub records no time of watching (fetch spec, Incremental sync step 2).
- `tables['popularity']`: one row per repository of the subject, `{'repo', 'stars', 'forks', 'watchers'}` from `Repo.stargazer_count`, `fork_count` and `watcher_count` as of the last listing, ordered by `stars` descending, then `repo`.
- `tables['languages']`: one row per language over the subject's repositories, `{'language', 'bytes', 'share'}`: `bytes` summed by language name from `Repo.languages`; each repository's `languages_size` less its listed languages' bytes, summed, is one row `'Other'` when above zero; `share` (0 to 1) is a row's bytes over the sum of every row's bytes. Ordered by `bytes` descending then `language`, with `'Other'` last. Empty when no repository has a language.
- Series order: `stars_added`, `stars_total`, `forks_added`, `forks_total`.
