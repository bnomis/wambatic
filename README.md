# wambatic

Statistics from github.com for a user, an organisation or a single repository, as a report in your terminal, as one self-contained HTML page, as JSON or in a web app on your own machine.

wambatic reads the default-branch history, pull requests, issues, releases and GitHub Actions runs from GitHub's GraphQL and REST APIs, keeps them in a local SQLite cache, and reports commits, contributors, active days and lines added, deleted and net, together with how pull requests and issues flow (opened, merged, closed, and how long that takes) and how the project delivers (runs, releases and proxies for the DORA metrics), by year, month, week or day. Only the changes since the last run are fetched, so a repeat run is fast and a report from a warm cache works offline.

## Install

You need Python 3.14.7 or later 3.14 and [uv](https://docs.astral.sh/uv/).

```shell
git clone https://github.com/bnomis/wambatic
cd wambatic
uv sync
source bin/activate.sh
wambatic --help
```

`wambatic --help` lists the `report`, `serve` and `cache` commands. `python -m wambatic` runs the same program.
## The token

wambatic reads a GitHub token from the `GITHUB_TOKEN` environment variable, and falls back to `gh auth token` when the [GitHub CLI](https://cli.github.com/) is signed in. `public_repo` is enough for public repositories. The [token page](https://bnomis.github.io/wambatic/token/) lists the scopes and says how to get one.

```shell
export GITHUB_TOKEN=<token from https://github.com/settings/tokens>
```

## A first report

```shell
wambatic report repo:octocat/Hello-World --by month
```

The first run reads the whole history of the repository; later runs fetch only what is new.

## Documentation

The user guide is at <https://bnomis.github.io/wambatic/>. It covers every option, setting and metric, the HTML report and the web app, the cache, the config file, recipes and troubleshooting. Its source is in [docs](docs/).

## More

The design is in [the system spec](agents/specs/system/spec.md), [fetch](agents/specs/fetch/spec.md), [cache](agents/specs/cache/spec.md), [stats](agents/specs/stats/spec.md) with its [metric groups](agents/specs/metric-groups/spec.md), and [reports](agents/specs/reports/spec.md) with the [CLI](agents/specs/cli/spec.md), [terminal report](agents/specs/terminal-report/spec.md), [HTML report](agents/specs/html-report/spec.md) and [web app](agents/specs/web-app/spec.md); the order of work is in [the implementation order](agents/specs/implementation-order.md). Contributors: the project layout, tools and checks are in [AGENTS.md](AGENTS.md), and the shared rules are in the `.agents` submodule. The user guide is at <https://bnomis.github.io/wambatic/>.

## Updating the shared rules

The shared rules, skills and audit checker come from the [agents](https://github.com/bnomis/agents) repository, pinned as the git submodule `.agents`. The pin means the pre-push hook, CI and an audit all run the same checker, and a checker change reaches this project only when the pointer is moved on purpose.

To move it to the latest `agents` commit:

1. Push the change in `agents` first: the update fetches from GitHub, not from a local clone.

   ```shell
   git -C ~/src/agents push
   ```

2. Move the submodule to the tip of agents' `main`, or pin a particular commit:

   ```shell
   git submodule update --remote .agents
   # or: git -C .agents fetch && git -C .agents checkout <commit>
   ```

3. Check it, then commit the new pointer:

   ```shell
   git submodule status    # the new commit, with no leading + or -
   bin/audit-check.sh      # a newer checker may report hits in unchanged code
   git add .agents
   git commit -m "chore: update agents submodule"
   ```

Run `bin/audit-check.sh` before committing the pointer: the pre-push hook runs the same check and refuses the push until every hit is fixed or accepted.

After a pull, or in another checkout, `git submodule update` (without `--remote`) checks out the commit this repository records. A fresh clone needs `git submodule update --init` once; an SSH-only checkout first sets `git config submodule..agents.url git@github.com:bnomis/agents.git`, since `.gitmodules` keeps the HTTPS URL for Claude Code cloud sessions.
