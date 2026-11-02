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
