# GitHub Enterprise Server

Read a GitHub Enterprise Server instead of github.com.

```shell
export GH_ENTERPRISE_TOKEN=<token created on your server>
wambatic report org:my-team --github-host ghe.example.com
```

The first report syncs from `ghe.example.com`, using its own cache file and its own token, and prints as
any other report does.

## Set the host

Pass `--github-host` to `report`, `serve` or `cache`, or set `fetch.github_host` in the
[configuration](config.md) to make it the default:

```json
{"fetch": {"github_host": "ghe.example.com"}}
```

The value is a host name with an optional port, such as `ghe.example.com:8443`. wambatic reads the
server's REST API at `/api/v3` and GraphQL API at `/api/graphql` on that host. The default is
`github.com`. `api.github.com` and `*.ghe.com` are refused.

## The token

An Enterprise host never uses `GITHUB_TOKEN`, so a github.com token is not sent to your server. wambatic
looks for the token in this order:

1. `GH_ENTERPRISE_TOKEN`
2. `GITHUB_ENTERPRISE_TOKEN`
3. `gh auth token --hostname <host>`, after `gh auth login --hostname <host>`

See [The GitHub token](../token.md) for the scopes.

## The server version

Before it syncs, wambatic asks the server for its version and stops with a one-line error if the version
is older than the minimum, which is 3.19, or cannot be read. A report that makes no request does not
check.

## One cache file per host

A host other than github.com keeps its cache in `~/.cache/wambatic/cache-<host>.sqlite3`, with `:` in a
port written as `-`, so two hosts never share a file. The cache records its host and the server's
version; `wambatic cache info --github-host <host>` shows both. A cache made for another host is refused
even with `--ignore-cache-version`: see [The cache](cache.md).

## Rate limits that are switched off

An administrator can switch rate limiting off, and the server then sends no rate-limit headers.
wambatic syncs without them on an Enterprise host. On github.com a response without them is still an
error.

## What is not supported

- GitHub Enterprise Cloud with data residency (`*.ghe.com`), which uses different addresses.
- Servers older than the minimum version above.

## Related

- [The GitHub token](../token.md)
- [Command line](../reference/cli.md) and [Settings](../reference/settings.md)
- [Limits](../limits.md)
