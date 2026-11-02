# TODO

Open work only, in implementation order, nearest first. Finished items move to
`DONE.md` unchanged. See the shared `todo-add` and `todo-review` skills for
the shape of an item.

## The reports and stats specs are still one file each

Found on 2026-11-02 by `/todo-review`. Audit review 2 decided on 2026-10-31
(`agents/audit-reviews/review-2.md`, Decision 2, answer A) to split
`fetch-and-cache/spec.md` at once and to split `reports` and `stats` "when
they next change". Both changed later that day (commits `1072e10` and
`e4bd689`, audit-review tasks-2 Tasks 5 and 6) and neither was split. Measured
on 2026-11-02: `agents/specs/reports/spec.md` was 347 lines and
`agents/specs/stats/spec.md` 274, against the specdev guide of about 200.

Cause: the split was tied to the next change, and the changes that came were
audit fixes made inside a task list that did not include it.

Fix direction: split them with `/specdev` before any feature below edits them:
`reports` into the CLI, terminal, HTML and web app specs, and `stats` into its
API and its metric groups, as `cdb829e` did for fetch and cache. Update
`agents/specs/index.md`, the implementation order's links and every
cross-reference.

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

## Line counts include generated files

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

## Only default-branch history is counted

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
