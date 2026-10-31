# wambatic

Visualisation and report of statistics from github.com for a user, a repo or an organisation.

## Layout

- `src/wambatic/fetch`: GitHub access and the SQLite cache
- `src/wambatic/stats`: pure computation from cached records
- `src/wambatic/reports`: terminal, HTML, JSON and the web app
- `src/tests`: tests, mirroring the source layout
- `bin`: entry-point and check scripts
- `agents/specs`: the specifications
- `agents/tasks`: task lists
- `agents/audit-reviews`: audit reviews

## Tools

- Runtime: aiohttp, cappa, fastapi, loguru, plotly, rich, uvicorn
- Development: hypothesis, httpx, mypy, playwright, pre-commit, pytest, ruff
- Environment and dependencies: uv (`uv sync` installs the development tools)

## Shared rules and skills

Shared rules and skills come from the [agents](https://github.com/bnomis/agents)
repository, a git submodule at `.agents/`:

- `.claude/rules` links to `.agents/claude/rules`
- `.claude/skills/*` link to `.agents/claude/skills/*`

@.agents/claude/CLAUDE.md

After cloning: `git submodule update --init`. It must run before the pre-commit hooks and the rules links work. Claude Code cloud sessions do this in the SessionStart hook (`.claude/hooks/session-start.sh`). To update the shared set:
`git submodule update --remote .agents`, then commit the new pointer.

Project-specific rules and skills go in this repository's own `claude/`
directory, not in agents (see `.agents/claude/rules/rule-scope.md`).

## Tests

`src/tests/fetch/test_fetcher.py` is deliberately separate from `test_base.py`: it holds the `Fetcher` sync tests and is too long to merge into the module-level tests of `fetch/base.py` (audit review 1, F16).
