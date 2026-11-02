# Settings

Every setting, with its default and type. Settings are layered, and a later layer wins: built-in defaults, then the JSON file `~/.config/wambatic/config.json`, then command line flags. Set `WAMBATIC_CONFIG` to use another file. The token is not a setting.

A duration is a whole number and one unit, `s`, `m`, `h`, `d` or `w`, such as `30d`. A leading `~` in a path is expanded.

## Settings table

| Setting | Type | Default | Meaning and trade-off |
|---------|------|---------|-----------------------|
| `fetch.cache_path` | path or none | `none` | Where the cache lives; unset uses `~/.cache/wambatic/cache.sqlite3` for `github.com` and `~/.cache/wambatic/cache-<host>.sqlite3` for another host, so each host has its own cache |
| `fetch.full_refresh_after` | duration | `30d` | Age of the last full read after which a resource is read in full again to catch deletions; shorter is more accurate and costs more requests |
| `fetch.github_host` | host name | `github.com` | The GitHub host to read: `github.com`, or the host name of a GitHub Enterprise Server with an optional `:port`; lower-cased on load. `api.github.com` and `*.ghe.com` (data residency) are refused |
| `fetch.include_archived` | boolean | `false` | Include archived repositories of a user or organisation |
| `fetch.include_forks` | boolean | `false` | Include forks of a user or organisation |
| `fetch.max_age` | duration | `0s` | Skip the network when the subject was synced more recently than this; zero always syncs |
| `fetch.max_retries` | integer | `5` | Retries for transient and secondary-limit errors |
| `fetch.on_rate_limit` | `wait` or `fail` | `wait` | `wait` sleeps until the limit resets, `fail` stops with an error that gives the reset time |
| `fetch.overlap` | duration | `1h` | Safety margin subtracted from the watermark so a late arrival is not missed |
| `fetch.stats_retries` | integer | `6` | Retries while a REST statistics endpoint is still computing |
| `fetch.workers` | integer | `4` | Repositories fetched at once; more is faster and closer to GitHub's secondary limits |
| `report.allow_remote` | boolean | `false` | Let `serve` listen on an address other than loopback; anyone who can reach the port then acts with your token |
| `report.format` | `terminal`, `html` or `json` | `terminal` | The default output format |
| `report.html_theme` | `auto`, `dark` or `light` | `auto` | The HTML report's colours: `auto` follows the viewer's system setting, `light` and `dark` are fixed |
| `report.out_dir` | path | `./wambatic-reports` | The directory the HTML report is written to when `--out` is absent |
| `report.web_host` | string | `127.0.0.1` | The address `serve` listens on |
| `report.web_port` | integer | `8000` | The port `serve` listens on |
| `stats.bot_logins` | list of strings | `["dependabot[bot]", "renovate[bot]"]` | Authors left out of contributor counts and the top-contributors table |
| `stats.deploy_workflow` | string or none | `none` | The workflow whose successful runs are the deployments, matched against a run's workflow file name (`deploy.yml`) or its name; unset, releases that are not prereleases are the deployments |
| `stats.exclude_merge_commits` | boolean | `true` | Leave merge commits out of line counts |
| `stats.failure_window` | duration | `7d` | How long after a deployment a hotfix pull request marks it as failed |
| `stats.hotfix_labels` | list of strings | `["hotfix"]` | Pull request labels that mark a failure fix, compared without regard to case |
| `stats.timezone` | string | `UTC` | The zone used when `--tz` is absent; an unknown zone is an error |

## Example

```json
{
  "fetch": {"workers": 8, "max_age": "1h"},
  "stats": {"timezone": "Europe/Berlin", "bot_logins": ["dependabot[bot]"]},
  "report": {"format": "json"}
}
```

An unknown key or a value of the wrong type is an error that names the key.
