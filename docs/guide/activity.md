# Activity

The commit, contributor and line metrics: what was committed, by how many people, and how much code.

```shell
wambatic report repo:pallets/click --by month --groups activity
```

`activity` is one of the default groups. Every metric is defined in the
[metrics reference](../reference/metrics.md); this page says what to watch for when reading them.

| Metric | What it tells you |
|--------|-------------------|
| `commits` | Commits on the default branch (and any `fetch.branches` you follow) in the period |
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
- **Generated and vendored files** are left out of the line counts where wambatic can see each commit's
  files (see [How commits are read](#how-commits-are-read)). A file is left out when its path matches
  `stats.exclude_paths` (lock files, `vendor`, `node_modules`, `dist`, minified files and source maps by
  default), or, with `stats.linguist` on, when the repository's `.gitattributes` marks it
  `linguist-generated` or `linguist-vendored`. The report footer says what the line counts leave out.
- **Only the default branch** is read unless `fetch.branches` names more, so work on branches that was
  never merged does not appear by default.
- **A period is the date of the commit** in the report time zone; see [Periods and ranges](periods.md).

## How commits are read

Each repository's commits are read by one of three methods, and the report footer names the methods used
(`Commits read by`), the branches followed (`Branches`) and what the line counts leave out
(`Line counts leave out`).

| Method | Footer label | Used for | Branches | Generated files |
|--------|--------------|----------|----------|-----------------|
| Clone | `local clone` | A public repository, or a private or internal one that `fetch.clone_repos` allows | The default branch and those `fetch.branches` matches | Left out |
| API totals | `API totals` | Any other repository, when `fetch.api_history` is `totals` (the default) | Default branch only | Counted |
| API with files | `API with files` | Any other repository, when `fetch.api_history` is `files` | The default branch and those `fetch.branches` matches | Left out by `stats.exclude_paths` only |

A clone is a bare clone kept beside the cache (see [The cache](cache.md)); it needs `git` 2.40 or later
(see [Installation](../install.md)).

To allow a private repository to be cloned, list it in `fetch.clone_repos`:

```json
{
  "fetch": {
    "clone_repos": ["my-org/*"],
    "branches": ["main", "release/*"]
  }
}
```

Patterns use shell wildcards. `fetch.api_history` set to `files` reads one request per commit, so it is
slow and uses much of the rate limit; choose it only for a repository you may not clone. Changing
`fetch.branches` makes the stored commits stale: a report with `--no-fetch` or `--max-age` then stops with
a `BranchesMismatchError` until you sync again.

### Unavailable rows

A repository that is read by API cannot be filtered fully. The report lists it under Unavailable, naming
the repository and the reason:

- `lines_added, lines_deleted, lines_net: <repository>`: generated files are counted, because the
  repository is not cloned and `fetch.api_history` is `totals`; or, with `files`, the linguist attributes
  were not read and only `stats.exclude_paths` applied.
- `commits: <repository>`: only the default branch was read, though `fetch.branches` names more.

A repository's attributes are read at its default branch's head. Pull request sizes still include
generated files.

## By repository and by author

An organisation or user target adds a By repository table. `--by-author` adds a By author table, and
per-author series in the [JSON output](json.md). `--by-author` is an error for a user target. See
[Targets](targets.md) and [The terminal report](terminal.md).

## Related

- [Flow](flow.md) for pull requests and issues.
- [Metrics](../reference/metrics.md) for the definition of every metric.
