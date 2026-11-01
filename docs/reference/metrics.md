# Metrics

Every metric, with its group, unit and definition. Each event is placed in the period of its own date in the report time zone. `p50` is the median and `p90` the 90th percentile of the values in the period; a period with no value has no point (the terminal shows `-`), because a median of nothing is not zero.

## Groups

| Group | Default | Meaning |
|-------|---------|---------|
| `activity` | yes | Commits, contributors and lines |
| `delivery` | no | Workflow runs, releases and the DORA proxies |
| `flow` | yes | Pull requests and issues |
| `popularity` | no | Stars and forks, with watchers and languages as snapshots |

## Metrics table

| Metric | Group | Unit | Definition |
|--------|-------|------|------------|
| `commits` | activity | count | Commits on the default branch in the period; merge commits count as commits but add no lines |
| `contributors` | activity | count | Distinct commit authors in the period, leaving out `stats.bot_logins` |
| `active_days` | activity | days | Days in the period with at least one commit |
| `lines_added` | activity | lines | Lines added by the commits in the period |
| `lines_deleted` | activity | lines | Lines deleted by the commits in the period |
| `lines_net` | activity | lines | Lines added minus lines deleted |
| `prs_opened` | flow | count | Pull requests created in the period |
| `prs_merged` | flow | count | Pull requests merged in the period; one closed without merging counts only in `prs_opened` |
| `issues_opened` | flow | count | Issues created in the period |
| `issues_closed` | flow | count | Issues closed in the period and still closed; a reopened issue is open |
| `time_to_first_review_p50` | flow | hours | Median hours from a pull request being opened to its first review, by the date of the review. Reviews by the pull request's author and by bots are left out |
| `time_to_first_review_p90` | flow | hours | The 90th percentile of the same |
| `time_to_merge_p50` | flow | hours | Median hours from a pull request being opened to being merged, by the date of the merge |
| `time_to_merge_p90` | flow | hours | The 90th percentile of the same |
| `time_to_close_p50` | flow | hours | Median hours from an issue being opened to being closed, by the date of the close |
| `time_to_close_p90` | flow | hours | The 90th percentile of the same |
| `pr_size_p50` | flow | lines | The median of added plus deleted lines over the pull requests merged in the period |
| `workflow_runs` | delivery | count | Workflow runs created in the period, whatever their state |
| `workflow_success_rate` | delivery | ratio | Of the completed runs created in the period whose conclusion is success, failure, timed out or startup failure, the share that succeeded; cancelled and skipped runs are left out. Shown as a percentage |
| `workflow_duration_p50` | delivery | minutes | Median minutes from a completed run starting to its last update; an approximation, since GitHub does not report a run's end time |
| `workflow_duration_p90` | delivery | minutes | The 90th percentile of the same |
| `release_count` | delivery | count | Releases published in the period, prereleases included, drafts left out |
| `release_interval_p50` | delivery | days | The median whole days since the repository's previous release, for the releases published in the period; a repository's first release has none |
| `deployments` | delivery | count | A release that is not a prerelease, at the time it was published. With `stats.deploy_workflow` set, a successful, completed run of that workflow, at the time the run finished. Counted for each repository |
| `lead_time_p50` | delivery | hours | Median hours from a merged pull request's first commit (its creation, when that is not known) to the first deployment of the same repository at or after the merge, in the period of the deployment. A pull request that no deployment has followed yet is not counted |
| `lead_time_p90` | delivery | hours | The 90th percentile of the same |
| `change_failure_rate` | delivery | ratio | Of the deployments in the period, the share followed, within `stats.failure_window`, by a pull request of the same repository that carries a label in `stats.hotfix_labels`. A deployment whose window is still open at the end of the range counts as not failed. Shown as a percentage |
| `time_to_restore_p50` | delivery | hours | Median hours from a hotfix pull request being opened to being merged, in the period of the merge |
| `time_to_restore_p90` | delivery | hours | The 90th percentile of the same |
| `stars_added` | popularity | count | Stars given in the period, by the date they were given |
| `stars_total` | popularity | count | The stars that exist now, counted by when they were given, up to the end of the period |
| `forks_added` | popularity | count | Direct forks made in the period, by the date they were made |
| `forks_total` | popularity | count | The forks that exist now, counted by when they were made, up to the end of the period |
