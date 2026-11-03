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

## Commit settings

These settings decide how commits are read and what the line counts include; the others are in the
[settings reference](../reference/settings.md).

- `fetch.branches`: branch name patterns followed beside the default branch. Empty (the default) follows
  the default branch only; `["*"]` follows every branch.
- `fetch.clone_repos`: `owner/name` patterns of private or internal repositories you allow to be cloned.
  Public repositories are cloned without it.
- `fetch.api_history`: `totals` (the default) or `files`, for a repository that is not cloned.
- `fetch.clone_dir`: where the bare clones are kept.
- `stats.exclude_paths` and `stats.linguist`: which files the line counts leave out.
- `stats.commit_timezone`: `report` (the default) dates commits in the report zone; `author` dates each
  in its author's zone unless `--commit-tz` says otherwise. See [Periods](periods.md).
- `stats.author_timezones`: a JSON object from login to [IANA time zone](https://www.iana.org/time-zones),
  such as `{"octocat": "Asia/Tokyo"}`. Logins are matched without regard to case, and an unknown zone
  stops the run before any sync. It applies in `author` mode and overrides the offset git recorded.

[How commits are read](activity.md#how-commits-are-read) says what each combination does. A list replaces
its default, it does not add to it.

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
