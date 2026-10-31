# Audit Summary

**Last updated:** 2026-10-31
**Last review:** review-1
**Total reviews conducted:** 1
**Last script run hit count:** 0 unaccepted (`bin/audit-check.sh` exits 0, 2026-10-31)
**Script version:** `4d7de71faa4067b7b05e53afe41973ffdfdc298f80d249b86f5085cfd7bac365` (from `find -L ~/.claude/skills/auditme/checks -name '*.py' | sort | xargs cat | shasum -a 256`)

## Unresolved findings

### F19: Spec template gaps

- **Rule or category:** Doc / spec review
- **Severity:** low
- **Location:** `agents/specs/fetch-and-cache/spec.md` (469 lines), `reports/spec.md` (315), `stats/spec.md` (225), `system/spec.md:100-103`, `implementation-order.md:7`, `:20`, `:25-29`, `:65-73`
- **First raised:** review-1 (2026-10-31)
- **Description:** Three specs are over the specdev size guide of about 200 lines. The environment-variable table has no Type column. `implementation-order.md` has inconsistent links and puts step 10 before step 9. Two links into `.agents` do not resolve in this checkout (F11).
- **Recommendation:** Split `fetch-and-cache/spec.md` (fetch and cache are natural halves) when it next changes. Fix the table and the ordering now.

## Recently resolved

| Finding | Severity | Raised in | Resolved in |
|---------|----------|-----------|-------------|
| Mechanical hits (checks/audit.py) | low to medium (per rule in review-1) | review-1 | tasks-1 (2026-10-31) |
| F1: Web server logs unexpected errors without redacting the token | high | review-1 | tasks-1 (2026-10-31) |
| F2: Third-party errors escape as tracebacks instead of domain errors | medium | review-1 | tasks-1 (2026-10-31) |
| F3: Settings validation lets an `OverflowError` through | medium | review-1 | tasks-1 (2026-10-31) |
| F4: The web report accepts an unbounded date range | medium | review-1 | tasks-1 (2026-10-31) |
| F5: Stdlib exceptions raised in packages that define domain errors | medium | review-1 | tasks-1 (2026-10-31) |
| F6: Two sources of truth for the same setting | medium | review-1 | tasks-1 (2026-10-31) |
| F7: `match`/`if` chains over enums and literals end in `raise`, not `assert_never` | medium | review-1 | tasks-1 (2026-10-31) |
| F8: Repeated computation across the five periods of an HTML report | medium | review-1 | tasks-1 (2026-10-31) |
| F9: Spec and code disagree | medium | review-1 | tasks-1 (2026-10-31) |
| F10: README drift | medium | review-1 | tasks-1 (2026-10-31) |
| F11: AGENTS.md has no structure or tools section, and its links do not resolve here | medium | review-1 | tasks-1 (2026-10-31) |
| F12: Blocking calls on the event loop | medium | review-1 | tasks-1 (2026-10-31) |
| F13: Mutable module-level containers read from other modules | low | review-1 | tasks-1 (2026-10-31) |
| F14: Duplicated record construction between the parsers and the cache | low | review-1 | tasks-1 (2026-10-31) |
| F15: Smaller architecture findings | low | review-1 | tasks-1 (2026-10-31) |
| F16: Standards findings | low | review-1 | tasks-1 (2026-10-31) |
| F17: Test coverage gaps | low | review-1 | tasks-1 (2026-10-31) |
| F18: Dev tools declared but never imported | low | review-1 | tasks-1 (2026-10-31) |

## Recurring patterns

- (none yet: one review so far)

## Checker changes since the last review

- (none: first review)
