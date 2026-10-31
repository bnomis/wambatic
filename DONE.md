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
