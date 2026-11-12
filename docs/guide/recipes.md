# Recipes

Common workflows, ready to copy. Replace the names with your own.

## Reports from the terminal

```shell
# Sync only if the cache is more than a day old
wambatic report org:github --max-age 1d

# How a repository ships: runs, releases and the DORA proxies
wambatic report repo:OWNER/NAME --groups delivery

# How a project is growing: stars, forks and languages
wambatic report org:NAME --groups popularity

# Who did the work in an organisation
wambatic report org:github --by-author --since 2026-01-01

# One bucket for the whole range, in another time zone
wambatic report user:octocat --by total --tz Europe/Berlin

# Read all the history again, for example after a force-push you suspect
wambatic report repo:octocat/Hello-World --full-refresh
```

## A file to share

```shell
# An HTML page and its assets folder, opening on the week view, written to a file of your choice
wambatic report org:github --format html --by week --out reports/github.html
```

## Machine-readable output

```shell
# Logs stay on stderr, so the JSON can be piped
wambatic report org:github --format json | jq '.series[0].points'
```

See [JSON output](json.md) and the [jq manual](https://jqlang.org/manual/).

## An offline report from the cache

Sync while you have a network and a token, then report without either, for instance on a laptop on a
train.

```shell
# Online: bring the cache up to date
wambatic report repo:octocat/Hello-World

# Offline: no network, no token
wambatic report repo:octocat/Hello-World --no-fetch
```

`--no-fetch` needs `user:NAME`, `org:NAME` or `repo:OWNER/NAME`, because a bare `NAME` is resolved with the
network. If the cache holds nothing for the subject or the range, the report says so and suggests a sync.

## A nightly HTML report with cron

```shell
# crontab -e: every night at 02:30, write the report to a fixed file
30 2 * * * GITHUB_TOKEN=<token> /path/to/wambatic/.venv/bin/wambatic -q report org:NAME --format html --out /var/reports/NAME.html
```

[`cron`](https://man7.org/linux/man-pages/man5/crontab.5.html) runs with a bare environment, so give the
full path to `wambatic`, set `GITHUB_TOKEN` (see [The GitHub token](../token.md); keep the crontab private,
because the token sits in it) and use `-q` so only warnings and errors are mailed. `<token>` is a personal
access token from <https://github.com/settings/tokens>. Because only what is new is fetched, a nightly run is cheap.

The exit status says whether it worked: see [Exit statuses](../reference/exit-statuses.md).

## Related

- [The terminal report](terminal.md), [The HTML report](html.md) and [The web app](web.md)
- [The cache](cache.md) for how syncs are decided
