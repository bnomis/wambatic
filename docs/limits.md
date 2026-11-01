# Limits

What wambatic does not do, and why.

- **Only the default branch's history is read.** Commits on other branches and unmerged work are not
  counted. GitHub's own commit history for a branch is the one cheap, complete record; reading every branch
  would multiply the requests and double count commits that are later merged.
- **A pull request's first review time can be missing.** The first review is found among a pull request's
  first reviews on GitHub. When the author or bots leave more than a few before the first other reviewer,
  the other reviewer's review is not among them and the pull request has no review time. Reading every
  review of every pull request would cost many requests for a small gain.
- **Line counts are not filtered for generated files.** A commit that adds a lock file or a vendored
  library adds its lines. GitHub does not mark generated files, and any list of patterns wambatic kept
  would be a guess that differs between projects.
- **A report uses one time zone.** Periods are cut by the zone in `--tz` or `stats.timezone`, so all
  numbers in a report agree on where a day, week or month begins. A different zone means a different report.
- **GitHub Enterprise Server is not supported.** wambatic talks to github.com only.
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
