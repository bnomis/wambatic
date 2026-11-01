# Troubleshooting

Each error wambatic prints, and what to do about it.

wambatic prints one line to stderr and exits with a status that tells the kind of failure (see
[Exit statuses](../reference/exit-statuses.md)). Add `-v` for debugging detail. The messages below are
quoted from the program; a `...` stands for a value that varies.

## Token and access

| Message | What to do |
|---------|------------|
| `No GitHub token found: set GITHUB_TOKEN or run gh auth login` | Set `GITHUB_TOKEN` or sign in with the [GitHub CLI](https://cli.github.com/). See [The GitHub token](../token.md). A report from the cache with `--no-fetch` needs none |
| `GitHub rejected the token (401)` | The token is wrong, expired or revoked. Create a new one and set `GITHUB_TOKEN` |
| `GitHub denied access (403)`, perhaps with `the endpoint accepts scopes: ...` | The token lacks a scope or permission. Use `repo` for private repositories and `read:org` for private organisation membership, or the permissions listed on the token page. A fine-grained token reaches only the repositories selected when it was made |
| `... not found or not visible`, `... not found` or `... is not a user or an organisation` | Check the spelling of the target, and that the token can see a private repository |

## Rate limits and slow syncs

| Message | What to do |
|---------|------------|
| `GitHub rate limit exhausted; resets at ...` | The limit is used up until the time shown, in UTC. Wait until then; with `fetch.on_rate_limit` set to `fail` wambatic stops with this message, while the default `wait` sleeps until the reset. Report from the cache meanwhile with `--no-fetch`. The message also appears when `wait` gives up after `fetch.max_retries` retries of a secondary limit; lower `fetch.workers` to stay clear of those |
| `GitHub is still computing ...; try again later` | GitHub builds some statistics on request. Run the report again in a minute. `fetch.stats_retries` sets how long wambatic waits |
| `GitHub answered HTTP ... to ...` or `GitHub request ... failed: ...` | GitHub or the network failed after the retries. Run it again; what was already fetched is kept |

A first sync of a large target is slow, because it reads the whole history: about one request for each
hundred commits, runs, stars or forks. Later syncs read only what is new. `delivery` and `popularity` are
the costly groups, so leave them out of `--groups` if you do not need them. See
[The cache](cache.md).

## The cache

| Message | What to do |
|---------|------------|
| `The cache was written by a different version (...)` | Run `wambatic cache clear` and report again, or pass `--ignore-cache-version` for one run |
| `cache ...: ...` or `cannot delete ...: ...` | The cache file is locked, corrupt, on a full disc or in a directory that cannot be made. Close other wambatic runs, free space, or run `wambatic cache clear` |
| `the cache holds no repositories for ...` or `no ... records in the cache for this range` | Nothing to report. With `--no-fetch`, run once without it to fill the cache; otherwise widen `--since` and `--until` |

## Options

These exit with status 2.

| Message | What to do |
|---------|------------|
| `the target must be one of user:NAME, org:NAME, repo:OWNER/NAME, OWNER/NAME or NAME ...` | Fix the target. See [Targets](targets.md) |
| `-v and -q cannot be used together` | Use one of them |
| `--full-refresh and --no-fetch cannot be combined` | A full refresh needs the network; drop one |
| `--no-fetch needs user:NAME or org:NAME: a bare NAME is resolved with the network` | Write the target with its prefix |
| `--out is for --format html` | Drop `--out`, or add `--format html` |
| `--by total is not for --format html ...` | Choose `year`, `month`, `week` or `day` for the page to open on |
| `--by-author is for an organisation or a repository; a user is already one author` | Drop `--by-author` for a `user:` target |
| `--since may not be before 2008-01-01, when GitHub began` and `--until may not be after ..., tomorrow in ...` | Move the date inside the allowed range. Dates are `YYYY-MM-DD` |
| `since ... is after until ...` | Swap the dates (this one exits with status 1) |
| `unknown groups: ...` | Use `activity`, `flow`, `delivery` or `popularity` (this one exits with status 1) |

## Configuration

These exit with status 2. See [Configuration](config.md).

| Message | What to do |
|---------|------------|
| `config file ... does not exist` | `WAMBATIC_CONFIG` names a file that is not there |
| `config file ... cannot be read (...)` or `... is not UTF-8 text` | Fix the permissions, or save the file as UTF-8 |
| `config file ... is not valid JSON (...)` | Fix the JSON at the place the parser names |
| `...: unknown section ...` or `...: unknown setting ...` | Remove or correct the key; the [settings reference](../reference/settings.md) lists them all |
| `... has the wrong type`, `... must be one of ...` or `a duration is a non-negative integer and one unit of s, m, h, d or w` | Correct the value |

## The HTML report and the web app

| Message | What to do |
|---------|------------|
| `cannot write ...: ...` | The path or directory cannot be written; choose another `--out` |
| `cannot read the report template ...; reinstall wambatic` | The install is damaged: run `uv sync` again |
| `... is not a loopback address, so anyone who can reach it would act with your GitHub token; ...` | Use a loopback address, or pass `--allow-remote` knowing the risk. See [The web app](web.md) |
| `cannot listen on ...: ...` | The port is in use or not allowed; pass `--port` with another |

## The star history is missing

The Unavailable section of a report may say `GitHub did not list the stargazers of ... to this token, so
its star history is left out`. GitHub did not give that token the list of who starred a repository. The
star count under Popularity now is still shown. Try a token that can read the repository, then run again
with `--full-refresh`. See [Popularity](popularity.md).

## An unexpected error

`Unexpected error: ...` followed by a traceback is a bug. Run again with `-v` and report the output at
<https://github.com/bnomis/wambatic/issues>, leaving out any token.

## Related

- [Exit statuses](../reference/exit-statuses.md)
- [The cache](cache.md) and [Configuration](config.md)
