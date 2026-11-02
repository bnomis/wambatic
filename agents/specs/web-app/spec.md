# Web app

**Version:** 1.0
**Status:** implemented
**Date:** 2026-11-02

The local web app `wambatic serve` runs: its routes, sync jobs and progress page, security checks, logging, binding and shutdown. Part of [Reports](../reports/spec.md).

Version 1.0 is the reports spec 1.12 text moved here, with only its cross-references updated, when that spec was split on 2026-11-02, as [audit review 2](../../audit-reviews/review-2.md) Decision 2 (answer A, 2026-10-31) asked. `review-N.md` in the text below means the [reports reviews](../reports/review-1.md) in `agents/specs/reports/`.

## Module location

`src/wambatic/reports/web.py` and its `templates/` (`form.html`, `progress.html`, `progress.js`, `message.html`), with tests in `src/tests/reports/test_web.py`.

## API

```python
import dataclasses
import typing

# web.py
@dataclasses.dataclass(slots=True)
class SyncJob:
    id: str                                  # opaque, unique for the server's lifetime
    key: tuple[str, frozenset[str]]          # (the target as given, the resources synced)
    phase: typing.Literal['queued', 'running', 'done', 'failed']
    progress: SyncProgress
    subject: Subject | None                  # set once a bare NAME is resolved
    error: str | None                        # the redacted message when failed
    status: int | None                       # the HTTP status the error maps to when failed
    # state (a property): `listing` while running until `progress.repos_listed` is set, then
    # `syncing`; otherwise the phase

class Jobs:
    """Each key's latest job; one job syncs at a time, the others wait as `queued`."""
    def start(self, key: tuple[str, frozenset[str]],
              run: Callable[[SyncJob], Awaitable[None]]) -> SyncJob:
        """The key's running or queued job, else a new one running `run`."""
    def get(self, job_id: str) -> SyncJob | None: ...
    def forget(self, job: SyncJob) -> None: ...
    async def close(self) -> None:
        """Cancel the running and queued jobs."""

def make_app(settings: Settings, cache: Cache, *, default_target: str | None = None,
             clock: Callable[[], datetime.datetime] = utc_now) -> fastapi.FastAPI: ...
def is_loopback(host: str) -> bool:
    """Exactly 'localhost', or an IP address (IPv6 in brackets or not) that is loopback."""
def warn_on_bind(host: str, allow_remote: bool) -> None:
    """UsageError for a non-loopback host without `allow_remote`; a warning with it."""
def serve(settings: Settings, *, default_target: str | None, ignore_cache_version: bool) -> None:
    """Open the cache, bind `report.web_host:report.web_port`, then run the app on uvicorn until
    Ctrl-C."""
```

## Error handling

- The web app answers 400 for `UsageError`, `SettingsError`, `UnknownGroupError`, `InvalidRangeError` and `InvalidRequestError`, and FastAPI's `RequestValidationError`; 404 for `NotFoundError` and `EmptySubjectError`; 502 with the upstream message for any other `FetchError`; and 500 with `internal error; see the server log` for anything else, logged with `loguru.logger.exception`. Messages pass through `redact_environment_token`, and no response shows a traceback. `/api/*` answers errors as `{"error": message}` JSON, `/` and `/report` as the `message.html` page (review-3.md choice 8).

## Implementation

**Web app.** A [FastAPI](https://fastapi.tiangolo.com/) application (review-3.md decision 1, answered 2026-10-30), built by `make_app` and run by `serve` on [uvicorn](https://www.uvicorn.org/). Its routes, all `GET`:

- `/`: `form.html`, a plain HTML form submitting to `/report` with fields target (filled with `serve`'s target when given), by (year, month, week, day; month checked), since, until, groups, by-author and tz. It works without script.
- `/report?target=&by=&since=&until=&groups=&by_author=&tz=&job=`: the page `report --format html` writes, `html_document(html_report(...), report.html_theme)`, with status 200; or, when a sync is needed, 202 with `progress.html` for the job.
- `/api/stats?` the same parameters: `result_to_dict` of the one result at `by` (`total` allowed) with status 200; or 202 with `{"job": ID, "progress": "/api/progress?job=ID"}`.
- `/api/progress?job=ID`: `{"job", "state", "repos_listed", "repos_pending", "repos_done", "rows_written", "error", "status"}` (counts `null` until known); 404 for an unknown job.
- FastAPI's own `/openapi.json` and `/docs`, which describe `/api/stats` and `/api/progress`; `/` and `/report` are left out of the schema. `/docs` is FastAPI's Swagger UI page, which loads its script and stylesheet from jsDelivr, so it needs a network connection where the app's own pages do not; `/redoc` is turned off (review-3.md choice 18).

*Parameters* are declared to FastAPI as optional strings (`Annotated[str | None, Query(description=...)]`), so they appear in the OpenAPI schema and FastAPI's own validation rejects nothing, and are parsed by `service.parse_target` and `service.make_request`, the CLI's code, so a value the CLI rejects is a 400 with the same message. `by_author` is `1`, `true` or `on` (the form's checkbox), else absent; `tz` overrides `stats.timezone`; `by=total` is a 400 for `/report` as `--by total` is for HTML. Parameters not listed are ignored (review-3.md choice 7).

*Sync jobs* (review-3.md choices 5 and 6). `/report` and `/api/stats` compute at once when the request carries the id of the finished job for its own target and resources, or when the target is a `Subject` and `needs_sync` (with `fetch.max_age`, the fetching flags off) is false. Otherwise they start a job with `Jobs.start`, or join the one running or queued for the same key, and answer 202. A job resolves the token (`fetch_token`) and a bare NAME, then runs `Fetcher.sync` with a `SyncProgress` (fetch spec) as an asyncio task on the server's loop (uvicorn with `loop='asyncio'`; FastAPI's `BackgroundTasks` are not used, since they belong to one response), holding the one lock that lets one job sync at a time; `state` is `queued` until it holds the lock, `listing` until `repos_listed` is set, `syncing`, then `done` or `failed` with the redacted message and the status it maps to (see Error handling). Each key keeps its latest job; a failed job is forgotten after the request that reports its error, so the next request retries. The progress page shows the state and counts, polls `/api/progress` once a second with `progress.js` and, when the job is done, loads the same URL with `&job=ID` added; on failure it shows the message. The cache is one `Cache` opened by `serve` before it listens, shared by every job and computation.

*Security.* The token comes from the server's environment only; no response carries it. Binding to a host other than loopback (`is_loopback`: exactly `localhost`, or an IP address whose `ipaddress` `is_loopback` is true; no name is resolved) needs `--allow-remote` or `report.allow_remote`, else `serve` exits 2 before binding; with it, a warning says that anyone who can reach the port acts with the operator's token (review-3.md choice 10). On a loopback bind, a middleware answers 403 to any request whose `Host` is not `localhost`, `127.0.0.1` or `[::1]` followed by the server's port, which stops DNS rebinding from reading the JSON; with remote access allowed the check is off (`make_app` reads `report.allow_remote` itself; it takes no separate switch). No CORS headers are sent (review-3.md choice 11).

*Logging.* uvicorn runs with `log_config=None`, `access_log=False` and `log_level='warning'`, so its own stdlib logging stays unconfigured and only its warnings reach stderr; a middleware logs each request at `debug` through loguru (method, path, status and milliseconds). `serve` logs one `info` line when listening, `Serving on http://HOST:PORT/ (Ctrl-C to stop)`, and the report URL of its target when given (review-3.md choice 12).

*Errors.* One HTTP middleware converts every exception a route raises with the Error handling mapping, and a handler for FastAPI's `RequestValidationError` answers 400 instead of 422, so the app has no 422 response.

*Binding.* `serve` binds the socket itself (`socket.create_server`) and passes it to `uvicorn.Server.run(sockets=[...])`: uvicorn logs a bind failure and calls `sys.exit(1)` itself, which would skip `main`'s error conversion, so binding first makes a busy port an ordinary `ServeError` (exit 1, `cannot listen on HOST:PORT` with the reason) (review-3.md choice 19).

*Stopping.* On Ctrl-C uvicorn shuts down gracefully: the app's lifespan cancels the running and queued jobs with `Jobs.close`, `serve` closes the socket and the cache in a `finally`, and uvicorn re-raises the captured interrupt, so the exit status is 130, as for `report`. A sync cancelled part-way resumes on the next sync, since its state advances per repository (fetch spec). A `CacheVersionError` from opening the cache stops `serve` before it listens (review-3.md choice 13).

*Pages.* `form.html`, `progress.html` (with `progress.js` inlined) and `message.html` (an error's status and message, and a link back to `/`) live in `templates/` beside the report's, are read with `importlib.resources` and filled with `string.Template`; every value from the request reaches them through `html.escape`, and they load nothing from outside the server (review-3.md choice 14).

*Testing* (review-3.md choice 15). `src/tests/reports/test_service.py` and `src/tests/reports/test_web.py` drive `make_app` with `httpx.AsyncClient` over `httpx.ASGITransport` under `asyncio.run`, entering the app's lifespan themselves (the transport does not run it), against the stats fixtures' cache for fresh data and the `Upstream` fake GitHub (`tests.fixtures.fetch.upstream`) for syncs, through `service.make_fetcher`. Starlette's synchronous `TestClient` is not used: it runs the app on a thread and loop of its own. A generated org of a few hundred repositories with `Upstream.history_delay` set shows that, while its sync runs, `/` and `/api/progress` answer within a second and `repos_done` rises. A `browser` test runs a real `uvicorn.Server` on a socket bound to `127.0.0.1` in a thread, opens `/report`, and checks that the progress page becomes the report with every chart drawn and no request outside the server.
