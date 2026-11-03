# Terminal report

**Version:** 1.3
**Status:** proposed
**Date:** 2026-11-03

The `rich` report `wambatic report` prints by default, and the table rows it shares with the HTML page. Part of [Reports](../reports/spec.md).

Version 1.0 is the reports spec 1.12 text moved here, with only its cross-references updated, when that spec was split on 2026-11-02, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked. `review-N.md` in the text below means the [reports reviews](../reports/review-1.md) in `agents/specs/reports/`.

Version 1.1 names the GitHub host, and the server version, in the provenance footer when the host is not github.com ([Fetch](../fetch/spec.md) 1.16, [fetch review 1](../fetch/review-1.md)).

Version 1.2 says in the provenance footer which branches were counted and which files were left out of line counts ([Commit sync](../commit-sync/spec.md), [Stats](../stats/spec.md) 1.11; [commit sync review 1](../commit-sync/review-1.md)).

Version 1.3 names both zones in the title when commits are dated in their authors' zones ([Author timezones](../author-timezones/spec.md); [author timezones review 1](../author-timezones/review-1.md)).

## Module location

`src/wambatic/reports/terminal.py` and `src/wambatic/reports/rows.py`, with tests in `src/tests/reports/`.

## API

```python
import rich.console

def render_terminal(result: StatsResult, console: rich.console.Console) -> None: ...
def sparkline(values: list[float]) -> str:
    """One block character per value from U+2581 to U+2588, scaled from min to max; all-equal
    values give U+2581 throughout; an empty list gives ''."""
```

## Implementation

**Terminal.** [Rich](https://rich.readthedocs.io/) output, in this order; every table is a `rich.table.Table` and numbers are right-aligned with thousands separators (`1,234`), `lines_net` with an explicit sign (`+1,234`, `-56`, `0`), so nothing depends on colour. Items 2, 4 and 5 appear when the result has `activity` series, items 6 and 7 when it has `flow` series, item 8 when it has `delivery` series, item 9 when it has a DORA proxy series, items 10 to 12 when it has `popularity` series, and item 3 when it has any series with a trend line, so `--groups flow` prints no activity tables but does print the flow trend lines:

1. A title line: the subject (`repo octocat/Hello-World`, `user octocat`, `org octo-org`), the resolved range (`2026-01-01 to 2026-10-29`), the granularity (`by month`, or `total`) and the timezone; since 1.3, when `provenance['commit_timezone']` is `'author'`, `commits in authors' zones, other events in <timezone>` in its place.
2. **Activity by period**: one row per bucket, columns Period, Commits, Contributors, Active days, Added, Deleted, Net, from the total series. A partial bucket's label (from `provenance['partial_buckets']`) ends in ` *` and the table's caption says `* partial period`. With more than one bucket a footer row `Total` sums commits, active days, added, deleted and net (all additive over disjoint buckets), and gives as contributors the number of `top_contributors` rows other than `unattributed` (contributors are not additive over buckets).
3. **Trends**: with more than one bucket, one line per total series that has a value in every bucket (the activity metrics, then the flow counts `prs_opened`, `prs_merged`, `issues_opened` and `issues_closed`, then the delivery counts `workflow_runs`, `release_count` and `deployments`, then the popularity counts `stars_added`, `stars_total`, `forks_added` and `forks_total`), `<metric>  <sparkline>  <min> to <max>`; the duration and size medians (`*_p50`, `*_p90`) and the ratios have no trend line, because their empty buckets have no value; when there are more buckets than fit in `console.width` less the label and range columns, the line shows the latest buckets that fit and says `last N periods`.
4. **By repository** and **By author**: one table per `by_kind` present, columns Name, Commits, Added, Deleted, Net, each the sum of that breakdown series' points over the range; rows ordered by commits descending then name; rows whose four values are all zero are left out.
5. **Top contributors**: `tables['top_contributors']` in its own order, columns Login, Commits, Added, Deleted, Net, Active days; the first `TOP_CONTRIBUTORS_SHOWN = 20` rows, then a line `and N more` when there are more (the JSON output has every row).
6. **Flow by period**: one row per bucket, columns Period, PRs opened, PRs merged, Issues opened, Issues closed, from the flow count series, with partial marks as in item 2 and, with more than one bucket, a `Total` footer row summing each column.
7. **Flow times by period**: one row per bucket, columns Period, Review p50, Review p90, Merge p50, Merge p90, Close p50, Close p90 (hours, one decimal place) and PR size p50 (lines), from the duration and size series; a bucket with no value shows `-`. There is no `Total` row, because medians do not add up over buckets; the caption says `hours; - no data`.
8. **Delivery by period**: one row per bucket, columns Period, Runs, Success (the success rate as a percentage with one decimal place, `87.5%`), Duration p50, Duration p90 (minutes, one decimal place), Releases and Release interval p50 (days), from the Actions and release series, with partial marks as in item 2; a bucket with no value shows `-`. With more than one bucket a `Total` footer row sums Runs and Releases and shows `-` in the other columns, which do not add up over buckets. The caption says `minutes and days; - no data`.
9. **DORA proxies by period**: one row per bucket, columns Period, Deployments, Lead time p50, Lead time p90 (hours), Change failure (percentage), Restore p50 and Restore p90 (hours), holding only the columns of the proxies the result has; a `Total` footer row sums Deployments as in item 8. The caption says `proxies: see the README; hours; - no data`. Proxies that are not emitted are in item 13.
10. **Popularity by period**: one row per bucket, columns Period, Stars added, Stars total, Forks added, Forks total, from the popularity series, with partial marks as in item 2. With more than one bucket a `Total` footer row sums Stars added and Forks added and gives the last bucket's Stars total and Forks total (cumulative counts do not add up over buckets). The caption says `totals: stars and forks that exist now, by when they were made`.
11. **Popularity now**: `tables['popularity']`, columns Repository, Stars, Forks, Watchers, with a `Total` footer row summing each column when there is more than one row. The caption says `as of the last sync; forks: whole network`.
12. **Languages**: `tables['languages']`, columns Language, Bytes and Share (percentage with one decimal place), when the table is not empty: every row up to `TOP_LANGUAGES_SHOWN = 10`; with more, the first `TOP_LANGUAGES_SHOWN - 1` rows and one `Other` row summing the rest (the JSON output has every row).
13. **Unavailable**: `tables['unavailable']`, columns Metric and Reason, when not empty. With the popularity group it also holds one row per repository whose stargazers the token could not see ([Metric groups](../metric-groups/spec.md), popularity), so a star series that leaves that repository out is never shown without the reason. Popularity now still shows GitHub's star count for it. The JSON output carries the same rows in `tables`, and the HTML page lists them in its Unavailable section.
14. A provenance footer: when `github_host` is not `github.com`, a first line `GitHub host: <host> (Enterprise Server <server_version>)` (1.1); when `branches` is present (1.2), a line `Commits read by: <commit_methods>` (`clone` shown as `local clone`, `api-files` as `API with files`, `api` as `API totals`), a line `Branches: default branch` for `[]`, else `Branches: default branch and <patterns, comma-separated>`, and a line `Line counts leave out: <stats.exclude_paths, comma-separated>`, followed by `; linguist-generated and linguist-vendored files` when `linguist` is `'true'` (`nothing` when both are off); then `computed_at`, each `fetched_at:<resource>`, `wambatic_version` and `schema_version`; when `version_override_at` is present, a warning line that the cache was read with `--ignore-cache-version` at that time.
