# Review: fetch 1.16, GitHub Enterprise Server

**Date:** 2026-11-02
**Spec:** `agents/specs/fetch/spec.md` (1.15 to 1.16), with amendments to `agents/specs/cache/spec.md` (1.0 to 1.1), `agents/specs/system/spec.md` (1.9 to 1.10), `agents/specs/cli/spec.md` (1.0 to 1.1), `agents/specs/reports/spec.md` (1.13 to 1.14), `agents/specs/terminal-report/spec.md` and `agents/specs/html-report/spec.md` (1.0 to 1.1), and `agents/specs/implementation-order.md` (1.10 to 1.11, step 13)
**Task list written against it:** none yet
**Review page:** https://claude.ai/artifact/5AvrqMwHXM4Cj5V7nkLfky (approve or flag each choice there; answers are copied into Answers below)

## What is being reviewed and how

The system spec accepted, for the first release, that GitHub Enterprise Server was out of scope. On 2026-11-02 the user chose to lift that limit (`TODO.md`, "GitHub Enterprise Server is not supported", found 2026-11-02). The amendments let wambatic read one Enterprise Server host instead of github.com: a host setting and flag, each host's REST and GraphQL addresses, the token for an Enterprise host, rate limits that may be switched off, a check of the server's version, and the host in the cache and the provenance. The four design decisions were answered on 2026-11-02 through the question tool and are recorded under Answers. What remains is the choices made while writing the amendments, listed under The items: approve each, or flag it with a comment saying what to change. Work on the task list stops until every item has an answer.

## Automatic checks

- `git diff --check` over the amended specs: pass (no whitespace errors).
- Every relative link in the amended specs and this review resolves to a file: pass.
- pre-commit on the changed files (end-of-file and trailing-whitespace hooks; no code changed): pass.
- GitHub's facts the amendments rest on, read from GitHub's Enterprise Server documentation on 2026-11-02:
  - REST is at `http(s)://HOSTNAME/api/v3` (REST "Rate limit" page, Enterprise Server 3.22 docs) and GraphQL at `http(s)://HOSTNAME/api/graphql` ("Forming calls with GraphQL"): pass, as the spec says.
  - "Rate limits are disabled by default for GitHub Enterprise Server" (GraphQL "Rate limits and query limits", 3.17 docs): pass. What the GraphQL `rateLimit` object returns when limits are off is **not documented**; item 2 below is built so that either answer works.
  - REST API version `2022-11-28` is the one supported version, and the default when the header is absent (REST "API versions", 3.17 docs): pass.
  - `GET /meta` returns `installed_version`, a string (REST "Meta", 3.19 docs): pass.
  - Supported releases are 3.19, 3.20, 3.21 and 3.22; 3.19 closes on 2026-12-09 ("All releases"): pass. `MIN_SERVER_VERSION` is therefore `(3, 19)`.
  - The `gh` CLI reads `GH_ENTERPRISE_TOKEN`, then `GITHUB_ENTERPRISE_TOKEN`, for an Enterprise Server host (`gh help environment`, local `gh`): pass.
- No Enterprise server was available to record responses from, so nothing could be checked against a live server: **needs attention** (item 7).

## The items

1. **The client takes a `GitHubHost`, not an `api_url`.** On Enterprise Server GraphQL is at `/api/graphql`, outside `/api/v3`, so the old `{api_url}/graphql` would have posted to the wrong address. A `GitHubHost` holds the REST and GraphQL addresses separately; tests build one with the replay server's URLs.
2. **Rate limits that are switched off.** A response without `x-ratelimit-*` headers leaves the rate-limit state unchanged on any host (it never becomes exhausted), and on an Enterprise host a GraphQL `rateLimit` that is absent or `null` is accepted. On github.com a missing `rateLimit` is still an error, so a query that forgot to select it still fails its first test. Accepting the absence only where GitHub documents that limits may be off follows the shared rule that a guess needs evidence for it.
3. **Which host names are accepted.** Lower-cased; `github.com`, or a dotted host name with an optional port; no scheme or path. `api.github.com` is refused with a hint to use `github.com`, and `*.ghe.com` (GitHub Enterprise Cloud with data residency, whose API lives at `api.<subdomain>.ghe.com`) is refused as out of scope rather than sent to wrong addresses. Only HTTPS.
4. **A cache with no host recorded is a github.com cache.** Caches made before this change have no `github_host` row. Every one of them was made against github.com, the only host the code could reach, so the row is written as `github.com` and the cache keeps working. No schema version increase, so no github.com user has to clear a cache.
5. **The server version is recorded but is not part of the identity.** `server_version` is a `meta` row beside `version_override_at`, rewritten at each sync. An Enterprise server upgrade therefore does not refuse the cache; the provenance names the version the data was last fetched with.
6. **Reports name an Enterprise host.** The terminal and HTML provenance footers gain a line `GitHub host: <host> (Enterprise Server <version>)` when the host is not github.com; github.com reports are unchanged. The JSON output already carries every provenance key, so it needs no change.
7. **Enterprise fixtures are written from GitHub's documentation.** No Enterprise server is available to record from, so the `GET /meta`, `rateLimit: null` and header-less fixtures are built from the documented shapes, each naming the page it came from, and the live tests stay on github.com. The first run against a real server is therefore the first real check.
8. **`MIN_SERVER_VERSION` moves with releases, not with the calendar.** It is a constant set to the oldest release GitHub supported when the wambatic release was made. A server that GitHub stops supporting after that keeps working until a later wambatic release raises the constant.
9. **GraphQL errors from an Enterprise host name the host and version.** A field that an older server's schema lacks fails as a `GraphQLError`; its message names the server version so the cause is visible, rather than a separate per-field capability check.
10. **`--github-host` on `cache clear` and `cache info` too.** Each host has its own default cache file, so the cache commands need the host to find the right file.

## Decisions

None open. The four decisions this change needed were answered on 2026-11-02 and are recorded below.

## Answers

Answered on 2026-11-02 through the question tool, before the amendments were written:

- **How a user picks the host:** the `fetch.github_host` setting, default `github.com`, plus a `--github-host` flag on `report` and `serve` (not `--host`, which `serve` uses for its bind address).
- **Where an Enterprise host's token comes from:** as the `gh` CLI does: `GH_ENTERPRISE_TOKEN`, then `GITHUB_ENTERPRISE_TOKEN`, then `gh auth token --hostname HOST`; github.com is unchanged, so a github.com token is never sent to another server.
- **How the cache keeps hosts apart:** one default file per host (github.com keeps today's path), the host recorded in the cache, and a cache made for another host refused with `CacheHostError`, which `--ignore-cache-version` does not override.
- **Whether the server's version is checked:** recorded in the provenance, and a server older than the oldest release GitHub supported at the wambatic release (3.19 on 2026-11-02) is refused with `ServerVersionError`.

Item verdicts, answered on the review page on 2026-11-02 at 13:55 UTC: items 1 to 10 all **approved**, with no comments.
