# wambatic

Visualisation and report of statistics from github.com for a user, a repo or an organisation.

## Layout

- `src/wambatic/fetch`: GitHub access and the SQLite cache
- `src/wambatic/stats`: pure computation from cached records
- `src/wambatic/reports`: terminal, HTML, JSON and the web app
- `src/tests`: tests, mirroring the source layout
- `bin`: entry-point and check scripts
- `docs`: the user guide (MkDocs site, built from `mkdocs.yml`)
- `agents/specs`: the specifications
- `agents/tasks`: task lists
- `agents/audit-reviews`: audit reviews

## Tools

- Runtime: aiohttp, cappa, fastapi, loguru, plotly, rich, uvicorn
- Development: hypothesis, httpx, mypy, playwright, pre-commit, pytest, ruff
- Environment and dependencies: uv (`uv sync` installs the development tools)
- User guide: mkdocs and mkdocs-material, in the `docs` group (`uv sync --group docs`)

## Shared rules and skills

Shared rules and skills come from the [agents](https://github.com/bnomis/agents)
repository, a git submodule at `.agents/`:

- `.claude/rules` links to `.agents/claude/rules`
- `.claude/skills/*` link to `.agents/claude/skills/*`

@.agents/claude/CLAUDE.md

After cloning: `git submodule update --init`. It must run before the pre-commit hooks and the rules links work. Claude Code cloud sessions do this in the SessionStart hook (`.claude/hooks/session-start.sh`). To update the shared set:
`git submodule update --remote .agents`, then commit the new pointer.

Project-specific rules and skills go in this repository's own `claude/`
directory, not in agents (see `.agents/claude/rules/rule-scope.md`). That directory is created with the first project rule.

The web server keeps two deliberate error boundaries, `Jobs.execute` and the `convert_errors` middleware in `reports/web.py`: without them a failed job would hang its progress page and an unexpected error would reach the client unredacted (review-2 Decision 1).

Logins and repository names are logged by design: they are public identifiers the user typed, and the only sink is local stderr.

## Tests

`src/tests/fetch/test_fetcher.py` is deliberately separate from `test_base.py`: it holds the `Fetcher` sync tests and is too long to merge into the module-level tests of `fetch/base.py` (audit review 1, F16).

Other deliberate test-layout exceptions: property tests, browser tests, live tests, `test_layering.py`, `test_package.py`, the bin-script tests, `test_docs.py` (the user guide against the code) and the fixtures of the fake GitHub do not mirror a source module.

## The user guide

A change to user-visible behaviour (options, settings, defaults, output, errors) updates the guide in `docs` in the same commit. When the output changes, re-run `bin/screenshots.sh` and commit the new images. When the logo `docs/assets/wambatic-mark.svg` or the favicon `docs/assets/favicon.svg` changes, re-run `bin/animate-logo.sh` to rebuild their rippling versions; a test fails while either is stale.

## Checks

- On commit (pre-commit): ruff with the rules in `pyproject.toml`, ruff format, mypy, and the end-of-file and trailing-whitespace hooks.
- On push (pre-push): `bin/audit-check.sh`, the whole-tree audit script; any unaccepted hit refuses the push.
- In CI: all of the above, plus the tests, in the `check`, `browser`, `live` and `audit` jobs.
- In CI, the `docs` workflow runs `mkdocs build --strict` on pull requests and deploys the site to GitHub Pages from main.
- `--no-verify` is never used; fix the hit or record the accepted exception.

Install both hook types: `pre-commit install --hook-type pre-commit --hook-type pre-push`.

`.gitmodules` keeps `.agents` on the HTTPS URL because Claude Code cloud sessions fill it from there and have no SSH key. An SSH-only checkout sets `git config submodule..agents.url git@github.com:bnomis/agents.git` locally. The CI `audit` job reads the private repository with a read-only deploy key held as the Actions secret `AGENTS_DEPLOY_KEY`.
