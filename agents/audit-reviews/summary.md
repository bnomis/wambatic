# Audit Summary

**Last updated:** 2026-10-31
**Last review:** review-2
**Total reviews conducted:** 2
**Last script run hit count:** none unaccepted (`bin/audit-check.sh` exits 0, 2026-10-31)
**Script version:** `4e66ac0cd1e99ce2a8457ebf58915f45c56af2e4191b064a8eb6bc34f85edbc1` (agents `108559d`; the gates now run agents `f7d5fcd`; from `find -L ~/.claude/skills/auditme/checks -name '*.py' | sort | xargs cat | shasum -a 256`)

## Unresolved findings

### G13: Dev tools declared but never imported

- **Rule or category:** D / D2
- **Severity:** low
- **Location:** `pyproject.toml`
- **First raised:** review-1 F18 (2026-10-31)
- **Description:** `mypy`, `pre-commit` and `ruff` are command-line tools in the dev group.
- **Recommendation:** no change (chosen in review-1).

## Recently resolved

| Finding | Severity | Raised in | Resolved in |
|---------|----------|-----------|-------------|
| Mechanical hits of the review-1 rules | low to medium | review-1 | tasks-1, confirmed in review-2 |
| F1: Web server logs unexpected errors without redacting the token | high | review-1 | tasks-1, confirmed in review-2 |
| F3: Settings validation lets an `OverflowError` through | medium | review-1 | tasks-1, confirmed in review-2 |
| F4: The web report accepts an unbounded date range | medium | review-1 | tasks-1, confirmed in review-2 |
| F7: `match`/`if` chains end in `raise`, not `assert_never` | medium | review-1 | tasks-1, confirmed in review-2 |
| F9: Spec and code disagree | medium | review-1 | tasks-1, confirmed in review-2 |
| F10: README drift | medium | review-1 | tasks-1, confirmed in review-2 |
| F11: AGENTS.md has no structure or tools section | medium | review-1 | tasks-1, confirmed in review-2 |
| F12: Blocking calls on the event loop | medium | review-1 | tasks-1, confirmed in review-2 |
| F13: Mutable module-level containers read from other modules | low | review-1 | tasks-1, confirmed in review-2 |
| F14: Duplicated record construction between the parsers and the cache | low | review-1 | tasks-1, confirmed in review-2 |
| F15: Smaller architecture findings | low | review-1 | tasks-1, confirmed in review-2 |
| F16: Standards findings | low | review-1 | tasks-1, confirmed in review-2 |
| F17: Test coverage gaps | low | review-1 | tasks-1, confirmed in review-2 |
| G1: A malformed JSON body on a 200 response escapes as a `ValueError` | medium | review-2 | tasks-2 |
| G2: `Raises:` sections leave out errors that reach the caller | low | review-2 | tasks-2 |
| G3: Small envelope gaps outside the fetch path | low | review-2 | tasks-2 |
| G4: Two sources of truth for the timezone | low | review-2 | tasks-2 |
| G5: Remaining naming, exhaustiveness and slot findings | low | review-2 | tasks-2 |
| G6: Repeated reads and derivations left after the read-once change | low | review-2 | tasks-2 |
| G7: Construction and return-value leftovers | low | review-2 | tasks-2 |
| G8: Broad handlers that degrade gracefully (kept, reason recorded) | low | review-2 | tasks-2 |
| G9: Public surface and a compatibility shim | low | review-2 | tasks-2 |
| G10: Naming and layout standards | low | review-2 | tasks-2 |
| G11: GitHub logins in INFO logs (kept by design, recorded) | low | review-2 | tasks-2 |
| G12: Test gaps | low | review-2 | tasks-2 |
| G14: AGENTS.md and README details | low | review-2 | tasks-2 |
| G15: Spec text that no longer matches the code | medium | review-2 | tasks-2 |
| G16: Spec structure and the implementation order | low | review-2 | tasks-2 |

F2, F5, F6 and F8 are now resolved in full by tasks-2; F18 stays open by choice (G13).

## Recurring patterns

- Docstring `Raises:` sections drift from what reaches the caller as error envelopes are added (review-1 A4 by hand, review-2 G2 by script).
- Spec text lags behind behaviour changes made in task lists (review-1 F9, review-2 G15).

## Checker changes since the last review

- `raises-section-drift` added and `mutable-module-level-exported` refined for builtin constructor calls (agents `c437b07`, digest `4d7de71f...` to `4e66ac0c...`): 16 new hits in this project, all `raises-section-drift`.
