# Configuration

How settings are layered, where the file is, and what it looks like.

Most people never need a file: the defaults work. Write one when you pass the same option on every run.

```shell
mkdir -p ~/.config/wambatic
cat > ~/.config/wambatic/config.json <<'JSON'
{"stats": {"timezone": "Europe/Berlin"}}
JSON
wambatic report repo:pallets/click
```

## The layers

```mermaid
flowchart LR
    defaults[Built-in defaults] --> file[JSON file<br/>~/.config/wambatic/config.json<br/>or WAMBATIC_CONFIG]
    file --> flags[Command line flags]
    flags --> run([The settings of this run])
```

A later layer wins. Command line flags such as `--tz`, `--format`, `--max-age` and `--out` override the
file for one run.

The file is `~/.config/wambatic/config.json`. Set the `WAMBATIC_CONFIG` environment variable to use
another file. A missing file named that way is an error, while a missing default file is not. The GitHub
token is not a setting: see [The GitHub token](../token.md).

## An annotated example

```json
{
  "fetch": {
    "workers": 8,
    "max_age": "1h"
  },
  "stats": {
    "timezone": "Europe/Berlin",
    "bot_logins": ["dependabot[bot]"]
  },
  "report": {
    "format": "json"
  }
}
```

- `fetch.workers`: fetch eight repositories at once instead of the default. More is faster and closer to
  GitHub's secondary limits.
- `fetch.max_age`: skip the network when everything was synced within the last hour.
- `stats.timezone`: bucket periods in this [IANA time zone](https://www.iana.org/time-zones) unless `--tz`
  says otherwise.
- `stats.bot_logins`: only this author is left out of contributor counts, so `renovate[bot]` now counts.
  A list replaces the default, it does not add to it.
- `report.format`: print JSON unless `--format` says otherwise.

## Values

- A duration is a whole number and one unit, `s`, `m`, `h`, `d` or `w`, such as `"30d"`.
- A leading `~` in a path is expanded.
- Booleans are JSON `true` and `false`.
- An unknown section, an unknown key or a value of the wrong type is an error that names it, and wambatic
  exits with status 2.

Every setting, its type and its default are in the [settings reference](../reference/settings.md).

## Related

- [The cache](cache.md) for the `fetch.*` settings that decide when to sync
- [Troubleshooting](troubleshooting.md) for config errors
