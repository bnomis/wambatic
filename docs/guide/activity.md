# Activity

The commit, contributor and line metrics: what was committed, by how many people, and how much code.

```shell
wambatic report repo:pallets/click --by month --groups activity
```

`activity` is one of the default groups. Every metric is defined in the
[metrics reference](../reference/metrics.md); this page says what to watch for when reading them.

| Metric | What it tells you |
|--------|-------------------|
| `commits` | Commits on the default branch in the period |
| `contributors` | Distinct commit authors in the period |
| `active_days` | Days in the period with at least one commit |
| `lines_added`, `lines_deleted`, `lines_net` | Lines changed by the commits in the period |

## Merge commits

`commits` counts merge commits. The line metrics leave them out by default, because a merge commit
reports the lines of the branch it merges and they would be counted twice. Set
`stats.exclude_merge_commits` to `false` to count them; it never changes `commits`. See
[Settings](../reference/settings.md).

## Bots

`stats.bot_logins` (by default `dependabot[bot]` and `renovate[bot]`) is left out of `contributors` and
of the Top contributors table. A bot's commits still count in `commits` and in the lines, and the
per-author breakdown from `--by-author` lists bots, because their lines are counted. Commits that GitHub
cannot attribute to a login are not counted as contributors, since they cannot be told apart by person;
the Top contributors table shows them as one `unattributed` row.

## Reading the numbers

- **`active_days`** is a count of days, not of commits: ten commits on one day make one active day.
- **`lines_net`** is added minus deleted, and carries an explicit sign in the terminal.
- **Generated and vendored files** are not filtered. GitHub does not report per-file statistics cheaply,
  so a commit that adds a lock file or a vendored library adds its lines. See [Limits](../limits.md).
- **Only the default branch** is read, so work on branches that was never merged does not appear.
- **A period is the date of the commit** in the report time zone; see [Periods and ranges](periods.md).

## By repository and by author

An organisation or user target adds a By repository table. `--by-author` adds a By author table, and
per-author series in the [JSON output](json.md). `--by-author` is an error for a user target. See
[Targets](targets.md) and [The terminal report](terminal.md).

## Related

- [Flow](flow.md) for pull requests and issues.
- [Metrics](../reference/metrics.md) for the definition of every metric.
