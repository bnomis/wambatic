# DONE

Finished items, moved unchanged from `TODO.md`.

## The auditme checker's 2026-10-31 rules report hits here

Found on 2026-10-31 by running the shared auditme checker at agents `108559d`
on this repository at `1b9e2fa0`. Two checker changes shipped that day (agents
`c437b07`) report hits here:

- `mutable-module-level-exported` now counts the builtin constructor calls
  `list(...)`, `dict(...)` and `set(...)` as their literals:
  - `src/wambatic/stats/delivery.py:36` `UNITS`, a `dict(...)` read by one
    other file
- the new `raises-section-drift` rule (A4) compares each `Raises:` section with
  the domain errors reaching the caller: none. Measured
  on the local clone, which was 17 commits behind `origin/main`; re-run after
  pulling.

Cause: the checker gained the rules; the code predates them.

Fix direction: fix or accept each hit - wrap an exported constructor call in
`tuple(...)`, `frozenset(...)` or `types.MappingProxyType(...)`, and correct each
`Raises:` section from the body. A hit the rule gets wrong is accepted with
`# auditme: accept[<rule>] <reason>` on its `def` or assignment line, and the
pattern raised as a request in the auditme skill's `requests.md`. Then add
the change to `agents/audit-reviews/summary.md`, under its checker changes, so
the next audit's convergence note accounts for it.
Re-run with `pre-commit run auditme-all --hook-stage manual --all-files` once
the hooks are adopted, or `python3 ~/.claude/skills/auditme/checks/audit.py .`.

Spec: agents/audit-reviews/review-2.md (G2); tasks: agents/tasks/audit-reviews/tasks-2.md.

Done: 2026-10-31 - fixed by review-2 G2 (tasks-2 Task 1); the UNITS hit was already fixed by tasks-1 Task 7. Source: agents/audit-reviews/review-2.md; tasks: agents/tasks/audit-reviews/tasks-2.md.

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

Done: 2026-11-02 - split on branch `docs/split-reports-stats-specs`: reports spec 1.13 keeps what the front ends share, with the CLI, Terminal report, HTML report and Web app specs 1.0; stats spec 1.10 keeps the API, with the Metric groups spec 1.0. Source: agents/audit-reviews/review-2.md (Decision 2).

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

Done: 2026-11-02 - built by agents/tasks/fetch/tasks-1.md against fetch spec 1.16.

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

Done: 2026-11-02 - built by agents/tasks/commit-sync/tasks-1.md against commit sync spec 1.0.

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

Spec: agents/specs/author-timezones/spec.md (1.0, with the amendments listed in its review); tasks: agents/tasks/author-timezones/tasks-1.md.

Done: 2026-11-03 - built by agents/tasks/author-timezones/tasks-1.md against author timezones spec 1.0.

## Dependabot reports open alerts the token cannot read

Found on 2026-11-02 and again on 2026-11-03 in GitHub's reply to every push
of `main`: "GitHub found 2 vulnerabilities on bnomis/wambatic's default
branch (1 critical, 1 high)", pointing at
https://github.com/bnomis/wambatic/security/dependabot. On 2026-11-03
`gh api repos/bnomis/wambatic/dependabot/alerts` answered HTTP 403
("Resource not accessible by personal access token"), so which packages and
versions are affected is not known here.

Cause: not known until the alerts are read; the token in use has no
Dependabot alerts permission.

Fix direction: read the alerts (on the page above, or with a token granted
"Dependabot alerts: read"), then upgrade each affected dependency in
`pyproject.toml` and `uv.lock` (`uv.lock` changes only with the user's
explicit instruction), run the tests, and check the alerts close.

Done: 2026-11-03 - dismissed by the user, not fixed: the alerts (certifi via httpx, virtualenv via pre-commit, both development-only) are to be ignored; uv.lock is unchanged.
