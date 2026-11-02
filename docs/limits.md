# Limits

What wambatic does not do, and why.

- **Only the default branch's history is read, unless you ask for more.** Commits on other branches and
  unmerged work are not counted unless `fetch.branches` names them, for a repository that is cloned or
  read with `fetch.api_history` set to `files`.
- **A pull request's first review time can be missing.** The first review is found among a pull request's
  first reviews on GitHub. When the author or bots leave more than a few before the first other reviewer,
  the other reviewer's review is not among them and the pull request has no review time. Reading every
  review of every pull request would cost many requests for a small gain.
- **Line counts are filtered only where wambatic can see each commit's files.** A public repository, or
  one `fetch.clone_repos` allows, is cloned and its generated files are left out (`stats.exclude_paths`
  and `stats.linguist`). Any other repository keeps the default branch and unfiltered totals unless
  `fetch.api_history` is `files`, a slow per-commit read that applies `stats.exclude_paths` only. The
  report lists the repositories it could not filter. A repository's attributes are read at its default
  branch's head, and pull request sizes still include generated files.
- **Clones need disk space and `git`.** Bare clones are kept beside the cache until
  `wambatic cache clear`.
- **A report uses one time zone.** Periods are cut by the zone in `--tz` or `stats.timezone`, so all
  numbers in a report agree on where a day, week or month begins. A different zone means a different report.
- **Only some GitHub Enterprise servers are supported.** Enterprise Server is supported from 3.19, as
  [the guide](guide/enterprise.md) describes. Enterprise Cloud with data residency (`*.ghe.com`) is not,
  because it uses different addresses.
- **The DORA figures are proxies.** They are built on conventions GitHub does not enforce: what counts as a
  deployment, and which pull requests are fixes. See [Delivery and DORA](guide/delivery.md) for the
  conventions and the settings that adjust them.
- **Watchers and languages are current snapshots, not histories.** GitHub does not date them, so a report
  shows them as of the last sync.
- **The fork series count direct forks only.** The fork count in Popularity now is GitHub's, which includes
  forks of forks, so the two can differ.

## Related

- [How wambatic works](concepts.md)
- [Popularity](guide/popularity.md) and [Activity](guide/activity.md)
