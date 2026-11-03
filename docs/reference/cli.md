# Command line

Every command-line option. Global options come before the command: `wambatic -v report ...`. `python -m wambatic` runs the same program.

## Global options

| Option | Default | Meaning |
|--------|---------|---------|
| `-v`, `--verbose` | off | Log debugging detail, with time and source location |
| `-q`, `--quiet` | off | Log warnings and errors only; cannot be used with `-v` |
| `-h`, `--help` | | Show the help and exit |
| `--completion generate\|complete` | | Print the shell completion source (`generate`), or complete a command line (`complete`) |

## report

`wambatic report TARGET [options]` prints a report of a user, an organisation or a repository.

| Option | Default | Meaning |
|--------|---------|---------|
| `TARGET` | required | `user:NAME`, `org:NAME`, `repo:OWNER/NAME`, `OWNER/NAME` or a bare `NAME` |
| `--format terminal\|html\|json` | `report.format` | The output format |
| `--out PATH` | `report.out_dir` | With `--format html`, the file to write, or an existing directory to write the report into; an error with another format |
| `--by year\|month\|week\|day\|total` | `month` | The period to bucket by; weeks are ISO weeks starting on Monday. With `--format html`, the period shown when the page opens, and `total` is an error |
| `--since YYYY-MM-DD` | the first commit | First day, inclusive, in the report time zone; not before 2008-01-01 |
| `--until YYYY-MM-DD` | today | Last day, inclusive, in the report time zone; not after tomorrow in that zone |
| `--groups NAMES` | `activity,flow` | Comma-separated metric groups: `activity`, `delivery`, `flow`, `popularity`. `delivery` and `popularity` are off by default because they read every workflow run, star and fork, which costs requests |
| `--by-author` | off | Break activity down by author; not for a user target |
| `--tz ZONE` | `stats.timezone` | An [IANA time zone](https://www.iana.org/time-zones) such as `Europe/Berlin` |
| `--commit-tz report\|author` | `stats.commit_timezone` | `report` dates every commit in the report zone; `author` dates each commit in its author's zone |
| `--full-refresh` | off | Read all history again and ignore `--max-age`; cannot be used with `--no-fetch` |
| `--no-fetch` | off | Use the cache only, with no network and no token |
| `--max-age DURATION` | `fetch.max_age` | Skip the network when every resource was synced more recently, for example `30m` or `1d` |
| `--ignore-cache-version` | off | Read a cache written by a different wambatic or schema version, and say so in the report |
| `--github-host HOST` | `fetch.github_host` | The GitHub Enterprise Server host to read, such as `ghe.example.com`, or `github.com`; it also picks that host's cache file |

Dates must be written `YYYY-MM-DD`; other ISO forms are rejected. Without `--no-fetch` and `--max-age`, every run syncs first, because `fetch.max_age` defaults to zero.

## serve

`wambatic serve [TARGET] [options]` runs the web app, on this machine only unless told otherwise.

| Option | Default | Meaning |
|--------|---------|---------|
| `TARGET` | none | Optional. Fills in the form and names the first report URL; a malformed target is an error before the server starts |
| `--host ADDRESS` | `report.web_host` | The address to listen on. Only `localhost` and loopback addresses are accepted without `--allow-remote`; no name is looked up, so use `127.0.0.1` or `::1` |
| `--port PORT` | `report.web_port` | The port, from 1 to 65535 |
| `--allow-remote` | `report.allow_remote` | Listen on an address other than loopback, and turn off the `Host` check; logs a warning |
| `--max-age DURATION` | `fetch.max_age` | As for `report` |
| `--ignore-cache-version` | off | As for `report` |
| `--github-host HOST` | `fetch.github_host` | As for `report`; unrelated to `--host`, the address to listen on |

## cache

`wambatic cache info|clear` shows or removes the local cache. Neither uses the network.

| Option | Default | Meaning |
|--------|---------|---------|
| `ACTION` | required | `info` describes the cache, including its `github_host` and `server_version`; `clear` removes it and its `-wal` and `-shm` files without asking |
| `--github-host HOST` | `fetch.github_host` | Act on that host's cache file |
