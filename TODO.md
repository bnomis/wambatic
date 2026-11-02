# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## The commit sync reads only default-branch totals

Consolidated on 2026-11-02 by `/todo-review` from the two findings below.
Both lift a limit the system spec accepted for the first release by changing
the same artefact: how commits are synced from GitHub and stored in the cache.
Line counts need per-file figures for each commit, and other branches need a
sync state each, so either one changes the commit records, the cache schema
and the incremental sync. Done apart, the second would rework the schema and
sync the first had just changed.

Fix direction: one spec change to `fetch`, `cache` and `metric-groups` (the
`activity` line counts; the metric groups were split out of the stats spec on
2026-11-02, commit `1110cec`) that covers both findings, with one cache schema
version raise: per-file line counts and exclude patterns recorded in the
provenance, then the branches to follow, a sync state per branch, commits
de-duplicated by oid across branches and rewritten-history detection per
branch. Measure the extra requests against the rate limit before choosing how
per-file counts are fetched. Generated files are filtered before other
branches are counted, so commits from other branches are filtered from the
start.

Spec: agents/specs/commit-sync/spec.md (1.0, with the fetch, cache, stats, metric-groups, system, CLI, terminal-report and HTML-report amendments; review agents/specs/commit-sync/review-1.md); tasks: agents/tasks/commit-sync/tasks-1.md.

### Line counts include generated files

Found on 2026-11-02 by `/todo-review`, from the limits the system spec
(`agents/specs/system/spec.md`, "Limits accepted for the first release")
accepted for the first release: "line counts are not filtered for generated
files". The user chose on 2026-11-02 to lift it.

Cause: each commit's additions and deletions are stored as totals, so a lock
file, vendored code or build output cannot be told apart from written code.

Fix direction: a spec change to `fetch`, `cache` and `stats`: per-file line
counts for each commit (a cost to measure against the rate limit first),
configurable exclude patterns with a default set, and the patterns recorded in
the provenance so reports made with different patterns are not mixed. Do this
before counting all branches, so commits from other branches are filtered from
the start.

### Only default-branch history is counted

Found on 2026-11-02 by `/todo-review`, from the limits the system spec
(`agents/specs/system/spec.md`, "Limits accepted for the first release")
accepted for the first release: "Default-branch history only". The user chose
on 2026-11-02 to lift it.

Cause: incremental sync follows one head per repository, from the stored head
of its default branch.

Fix direction: a spec change to `fetch`, `cache` and `stats`: which branches
to follow (a setting), a sync state per branch, commits de-duplicated by oid
across branches, and rewritten-history detection per branch.

## A report has one timezone

Found on 2026-11-02 by `/todo-review`, from the limits the system spec
(`agents/specs/system/spec.md`, "Limits accepted for the first release")
accepted for the first release: "one timezone per report". The user chose on
2026-11-02 to lift it.

Cause: bucketing takes a single `--tz` for every author and repository.

Fix direction: a spec change to `stats` and `reports`: a timezone per author
(from settings, or the commit's own offset), how buckets are formed when
authors are in different zones, and how the report says which zone each
figure uses.

Note 2026-11-02: since `1110cec` split the reports and stats specs, `--tz` is in the
`cli` spec and how a zone is shown is in the `terminal-report` and
`html-report` specs; bucketing stays in `stats`.

## The oldest Enterprise Server release accepted is fixed at 3.19

Found on 2026-11-02 by `/todo-review`, from the fetch spec
(`agents/specs/fetch/spec.md`, "Server version"): `MIN_SERVER_VERSION` is
`(3, 19)`, the oldest Enterprise Server release GitHub supported on
2026-11-02, and "is raised by a release, not at run time". GitHub's "All
releases" page, read on 2026-11-02, gives 3.19 a closing date of 2026-12-09.
No item recorded raising it.

Cause: the constant in `src/wambatic/fetch/hosts.py` is set by hand, and
nothing reminds anyone when a release closes.

Fix direction: after 2026-12-09, re-read GitHub's "All releases" page, raise
`MIN_SERVER_VERSION` to the oldest release still supported, and update the
fetch spec's API block and the user guide where they name the version.
