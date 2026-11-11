# GraphQL API

**Version:** 1.1
**Status:** proposed
**Date:** 2026-11-11

The web app's API: one GraphQL endpoint, `/graphql`, that answers stats for a target, starts or joins a sync, and reports how a sync job is going. It replaces the REST routes `/api/stats` and `/api/progress` and FastAPI's `/openapi.json` and `/docs`; the user decided on 2026-11-11 to replace REST rather than add GraphQL beside it, and chose [Strawberry](https://strawberry.rocks/) as the library. Part of [Reports](../reports/spec.md); served by the [Web app](../web-app/spec.md) 2.0.

Version 1.1 (2026-11-11) pins strawberry-graphql 0.338.0 instead of 0.341.2, which the project's 14-day dependency quarantine hides; see External dependencies.

A client asks only for the fields it needs, so a script that wants one series of a large org does not receive every table. The data is the same as `report --format json` prints: every field is read from `result_to_dict`, so the API and the JSON output never disagree.

## Module location

- `src/wambatic/reports/api.py`: the Strawberry schema, its resolvers and its error extension, and `graphql_router`.
- `src/wambatic/reports/jobs.py`: `SyncJob`, `Jobs`, `progress_json`, and the sync-or-compute step `results_or_job`, moved out of `web.py` unchanged, so `api.py` and `web.py` share them without importing each other.
- Tests: `src/tests/reports/test_api.py` and `src/tests/reports/test_jobs.py`.

## API

The schema, as Strawberry prints it (`strawberry export-schema wambatic.reports.api:schema`); the field names are Strawberry's camel case of the Python names:

```graphql
enum Granularity { TOTAL YEAR MONTH WEEK DAY }
enum CommitTimezone { REPORT AUTHOR }
enum JobState { QUEUED LISTING SYNCING DONE FAILED }

input StatsInput {
  target: String!            # as on the command line: repo:OWNER/NAME, user:NAME, org:NAME or NAME
  by: Granularity! = MONTH
  since: String              # YYYY-MM-DD
  until: String              # YYYY-MM-DD
  groups: [String!]          # default: stats.groups
  byAuthor: Boolean! = false
  tz: String                 # overrides stats.timezone
  commitTz: CommitTimezone   # overrides stats.commit_timezone
  job: ID                    # a finished sync job of this target and these groups
}

type Query {
  stats(input: StatsInput!): StatsOutcome!
  job(id: ID!): SyncJob      # null for an unknown job
  version: String!           # wambatic's version
}

type Mutation {
  sync(input: StatsInput!): SyncJob!   # start a sync of the target's groups, or join the one queued or running
}

union StatsOutcome = Stats | SyncNeeded

type SyncNeeded { message: String! }  # "the cache is older than fetch.max_age; run the sync mutation"

type Stats {
  formatVersion: Int!
  subject: Subject!
  request: RequestInfo!
  since: String!
  until: String!
  series(metrics: [String!], by: String): [Series!]!   # filters by metric names and by `by`; all when omitted
  tables: JSON!              # result_to_dict()['tables']
  provenance: JSON!          # result_to_dict()['provenance']
}

type Subject { kind: String!  login: String!  name: String }
type RequestInfo { granularity: Granularity!  groups: [String!]!  since: String  until: String  byAuthor: Boolean!  tz: String!  settings: JSON! }
type Series { metric: String!  unit: String!  by: String  byKind: String  points: [Point!]! }
type Point { label: String!  start: String!  value: Float! }

type SyncJob {
  id: ID!
  state: JobState!
  reposListed: Int
  reposPending: Int
  reposDone: Int
  rowsWritten: Int
  error: String              # the redacted message when failed
  status: Int                # the HTTP status the error maps to, as in the web app's Error handling
}
```

The Python side:

```python
import dataclasses
import datetime
import collections.abc

import fastapi
import strawberry.fastapi

@dataclasses.dataclass   # not frozen: the router sets `request` and `response` on a BaseContext
class ApiContext(strawberry.fastapi.BaseContext):
    settings: Settings
    cache: Cache
    jobs: Jobs
    clock: collections.abc.Callable[[], datetime.datetime]
    sync_runner: collections.abc.Callable[[Query], RunSync]   # the sync a query's job runs

schema: strawberry.Schema   # Query, Mutation, with the WambaticErrors extension

def graphql_router(context: ApiContext) -> strawberry.fastapi.GraphQLRouter:
    """The router web.make_app mounts at /graphql: GraphiQL on a browser GET, queries over GET and
    POST, mutations over POST only, and every resolver given `context`."""
```

## Error handling

- A resolver's error reaches the client in the response's `errors`, each with `message` and `extensions: {code, status}`. `status` is the HTTP status the [Web app](../web-app/spec.md) maps the exception to: 400 (`BAD_REQUEST`) for `UsageError`, `SettingsError`, `UnknownGroupError`, `InvalidRangeError` and `InvalidRequestError`; 404 (`NOT_FOUND`) for `NotFoundError` and `EmptySubjectError`; 502 (`UPSTREAM`) for any other `FetchError`; 500 (`INTERNAL`) for anything else, with the message `internal error; see the server log` and the exception logged with `loguru.logger.exception`. Every message passes through `redact_environment_token`, and no response holds a traceback (Strawberry's default would include the exception's text, so the `WambaticErrors` schema extension replaces each error after execution).
- The HTTP status stays 200 when the request was a valid GraphQL operation, as GraphQL over HTTP asks for `application/json` responses, so a client reads `errors` rather than the status. A syntax or validation error in the query keeps graphql-core's own message, which holds no data, with code `BAD_QUERY`.
- An input value the CLI would reject is the CLI's message: `target`, `since`, `until`, `groups`, `tz` and `byAuthor` go through `service.parse_target` and `service.make_request`, as the REST parameters did. `by: TOTAL` is allowed (`report --format json --by total` allows it).
- `job(id)` of an unknown job is `null`, not an error. `stats` with an `input.job` that is unknown, not finished, or of another target or groups is a `BAD_REQUEST` error naming which.
- A failed sync job is reported by `job(id)` with state `FAILED`, `error` and `status`; it is forgotten after the first `job` query that returns its failure, so the next `sync` retries, as before.

## Implementation

- *Stats.* `stats` computes at once when `input.job` is the finished job of the same key (target and groups) or when the target is a `Subject` and `needs_sync` with `fetch.max_age` (the fetching flags off) is false, and returns `Stats`; otherwise it returns `SyncNeeded`. It never starts a sync: a query has no side effects, and a client that wants fresh data calls the `sync` mutation, polls `job`, then queries `stats` with `job`. The computation runs off the event loop as the web app's routes do (`results_or_job` in `jobs.py`), and `Stats` is built from `result_to_dict(result)`, whose keys map to the fields above (`format_version` to `formatVersion`, `by_kind` to `byKind`, `by_author` to `byAuthor`).
- *Sync.* `sync` calls `Jobs.start` with the key and `context.sync_runner(query)`, the same runner the progress page's jobs use (it takes the parsed query because the job's key does not hold `by_author`), and returns the job; one sync runs at a time and the others wait as `QUEUED`, as in the web app. A bare NAME is resolved inside the job, so `sync` answers at once.
- *Transport.* `strawberry.fastapi.GraphQLRouter(schema, context_getter=..., graphql_ide='graphiql', allow_queries_via_get=True, multipart_uploads_enabled=False)`, mounted with `app.include_router(router, prefix='/graphql')`. Strawberry refuses mutations over GET. The web app's existing middlewares apply: the loopback `Host` check, the debug request log, and `convert_errors` for anything raised outside a resolver.
- *Cross-site requests.* A web page on another site cannot read the answer (no CORS headers are sent), but it could make the browser POST a form to a loopback server and start a sync with the operator's token. So a POST to `/graphql` whose `Content-Type` is not `application/json` gets 415 `{"error": "POST /graphql needs Content-Type: application/json"}` from a check in `api.py` before Strawberry reads the body: a browser sends a JSON content type cross-site only after a CORS preflight, which the server never approves.
- *GraphiQL.* A browser's GET of `/graphql` with no query shows Strawberry's GraphiQL page, which loads its script and stylesheet from a CDN (unpkg), so it needs a network connection where the app's own pages do not; this replaces FastAPI's `/docs`, which loaded from jsDelivr for the same reason.
- *Schema size.* The schema has no cycles (no type reaches itself), so a query's depth is bounded by the schema, and no depth or cost limit is added.
- *Removed.* `/api/stats`, `/api/progress`, `/openapi.json` and `/docs` are gone (`fastapi.FastAPI(openapi_url=None, docs_url=None, redoc_url=None)`) and answer 404. The progress page polls GraphQL instead (Web app 2.0).
- *Testing.* `test_api.py` drives `make_app` with `httpx.AsyncClient` over `httpx.ASGITransport`, as `test_web.py` does, against the stats fixtures' cache and the `Upstream` fake GitHub: `stats` on fresh data matches `result_to_dict` field by field for each granularity; `series(metrics:, by:)` filters; `stats` on stale data is `SyncNeeded` and starts nothing; `sync` then `job` polling reaches `DONE` and `stats(job:)` returns the data; two `sync` calls for one key return one job; each error class gives its `code` and `status`, a planted exception gives `INTERNAL` with no traceback and no token (the token set in the environment for the test) in the body; a mutation over GET is refused; a POST with `text/plain` or `application/x-www-form-urlencoded` gets 415; the four removed routes answer 404; and the exported schema equals the SDL above, so the schema cannot drift from this spec.

## External dependencies

- [strawberry-graphql](https://strawberry.rocks/) 0.338.0 (MIT, released 2026-10-26, read on PyPI 2026-11-11), with its FastAPI integration. The project's `[tool.uv] exclude-newer = "14 days"` hides any release younger than 14 days, so the pin is the newest release outside that window on the day the list ran; 1.0 of this spec named 0.341.2 (released 2026-11-07), which `uv lock` could not resolve (found by tasks-1.md Task 1 on 2026-11-11). It is before 1.0 and releases often, with breaking changes noted in its changelog, so `pyproject.toml` pins it exactly (`strawberry-graphql[fastapi]==0.338.0`) and an upgrade is a deliberate change that re-runs the schema test. It brings `graphql-core` (`>=3.3,<3.4`; 3.3.1 resolved). Its PyPI classifiers do not list Python 3.14 (checked 2026-11-11), but it imports and answers a query through FastAPI under Python 3.14.7 (checked 2026-11-11); the first task repeats that check as a test.
- FastAPI and uvicorn, as in the [Web app](../web-app/spec.md).
