# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## GitHub Enterprise Server is not supported

Found on 2026-11-02 by `/todo-review`, from the limits the system spec
(`agents/specs/system/spec.md`, "Limits accepted for the first release")
accepted for the first release: "GitHub Enterprise Server is out of scope".
The user chose on 2026-11-02 to lift it.

Cause: `GitHubClient` in `src/wambatic/fetch/client.py` takes an `api_url`
but defaults it to `https://api.github.com`, and no setting passes another;
the fetch spec assumes GitHub.com's API features and rate limits.

Fix direction: a spec change to `fetch` and `system` for a configurable API
address, a check of what the server supports (GraphQL fields the listing
selects, rate-limit reporting) that fails with a typed error, and the cache
identity recording the host so two hosts never share a cache.

Spec: agents/specs/fetch/spec.md (1.16, with the cache, system, CLI, reports, terminal-report and HTML-report amendments; review agents/specs/fetch/review-1.md); tasks: agents/tasks/fetch/tasks-1.md.

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
