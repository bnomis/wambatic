# How wambatic works

How data gets from GitHub to a report, and what limits how fast it goes.

## The pieces

```mermaid
flowchart LR
    gql[GitHub GraphQL API] --> fetch
    rest[GitHub REST API] --> fetch
    fetch[fetch<br/>sync what is new] --> cache[(SQLite cache)]
    cache --> stats[stats<br/>pure computation]
    stats --> terminal[Terminal report]
    stats --> html[HTML report]
    stats --> json[JSON]
    stats --> web[Web app]
```

- **fetch** talks to GitHub: the [GraphQL API](https://docs.github.com/en/graphql) lists repositories,
  commits, pull requests and issues, and the [REST API](https://docs.github.com/en/rest) supplies workflow
  runs, releases, stars, forks and the statistics endpoints. It writes what it reads to the cache.
- **The cache** is a [SQLite](https://www.sqlite.org/) file. It is derived data: delete it and the next
  report rebuilds it. See [The cache](guide/cache.md).
- **stats** computes the numbers from the cache alone, with no network. That is why a report from a warm
  cache works offline.
- **The front ends** render the same result: terminal, HTML, JSON and the web app.

## An incremental sync

The first sync of a repository reads its whole history. Later syncs read only what changed.

```mermaid
sequenceDiagram
    participant W as wambatic
    participant C as Cache
    participant G as GitHub
    W->>G: List the repositories of the target
    G-->>W: Names, last-push times, counts
    W->>C: Read the watermark for each repository
    Note over W: Nothing new in the listing: no request of its own
    W->>G: Fetch changes since watermark minus fetch.overlap
    G-->>W: New and changed rows
    W->>C: Store rows, move the watermark
    W->>G: REST request with the stored ETag
    G-->>W: 304 Not Modified (free) or a new body
    W->>C: Compute the report from the cache
```

- **The watermark** is the time of the last sync of a resource. The next sync starts a little before it,
  by `fetch.overlap`, so an item that arrived late is not missed.
- **Conditional requests.** For the REST endpoints wambatic keeps the
  [ETag](https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api#use-conditional-requests-if-appropriate)
  GitHub sent. Asking again with it costs nothing against the rate limit when nothing has changed.
- **Full refreshes.** An incremental sync cannot see a deletion, so a resource is read in full again once
  `fetch.full_refresh_after` has passed since its last full read. `--full-refresh` forces it.

## Rate limits

GitHub limits how many requests a token may make: see the
[REST rate limits](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api) and the
[GraphQL rate limits](https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api).
When the limit is reached, `fetch.on_rate_limit` decides what happens:

- `wait` (the default) sleeps until the limit resets and carries on.
- `fail` stops with an error that gives the reset time.

`fetch.workers` sets how many repositories are fetched at once. More is faster and closer to GitHub's
secondary limits, which wambatic answers by retrying up to `fetch.max_retries` times.

## Next

[Targets](guide/targets.md) says what you can report on.
