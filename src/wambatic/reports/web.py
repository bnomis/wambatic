"""The local web app: the report page and the JSON of a result for any target, with the syncs
a large target needs run as jobs, so no request waits for a sync."""

import asyncio
import collections.abc
import contextlib
import datetime
import ipaddress
import socket
import string
import time
import typing
import urllib.parse

import fastapi
import fastapi.exceptions
import fastapi.responses
import loguru
import uvicorn

import wambatic.fetch.base
import wambatic.fetch.cache
import wambatic.fetch.errors
import wambatic.fetch.ratelimit
import wambatic.reports.api
import wambatic.reports.assets
import wambatic.reports.base
import wambatic.reports.errors
import wambatic.reports.html
import wambatic.reports.jobs
import wambatic.reports.service
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.engine
import wambatic.stats.errors
import wambatic.version

# auditme: accept[non-alphabetical-literal] loopback names before addresses
LOOPBACK_HOSTS = ('localhost', '127.0.0.1', '[::1]')
ASSET_HEADERS = {'Cache-Control': 'public, max-age=31536000, immutable'}
PAGE_PATHS = frozenset({'/', '/report'})


Target = typing.Annotated[
    str | None,
    fastapi.Query(description='user:NAME, org:NAME, repo:OWNER/NAME, OWNER/NAME or a bare NAME'),
]
By = typing.Annotated[
    str | None,
    fastapi.Query(description='year, month, week, day or total (default month)'),
]
Since = typing.Annotated[
    str | None, fastapi.Query(description='First day, YYYY-MM-DD (default: first commit)')
]
Until = typing.Annotated[
    str | None, fastapi.Query(description='Last day, YYYY-MM-DD (default: today)')
]
Groups = typing.Annotated[
    str | None,
    fastapi.Query(
        description=(
            'Comma-separated metric groups: activity, flow, delivery, popularity '
            '(default: activity,flow)'
        )
    ),
]
ByAuthor = typing.Annotated[
    str | None,
    fastapi.Query(description='1, true or on to break activity down by author'),
]
Tz = typing.Annotated[str | None, fastapi.Query(description='Time zone (default: stats.timezone)')]
CommitTz = typing.Annotated[
    str | None,
    fastapi.Query(description='report or author (default: stats.commit_timezone)'),
]
JobId = typing.Annotated[
    str | None,
    fastapi.Query(description='The job a 202 answer named, to read the result once it is done'),
]


# auditme: accept[passthrough-shim] the FastAPI dependency that reads the query string
def raw_query(
    target: Target = None,
    by: By = None,
    since: Since = None,
    until: Until = None,
    groups: Groups = None,
    by_author: ByAuthor = None,
    tz: Tz = None,
    commit_tz: CommitTz = None,
    job: JobId = None,
) -> wambatic.reports.jobs.RawQuery:
    return wambatic.reports.jobs.RawQuery(
        target, by, since, until, groups, by_author, tz, commit_tz, job
    )


CallNext = collections.abc.Callable[[fastapi.Request], collections.abc.Awaitable[fastapi.Response]]


def reload_path(url: urllib.parse.SplitResult, job_id: str | None) -> str:
    """The path and query of `url` with its `job` parameter set to `job_id`, or removed."""
    pairs = [(k, v) for k, v in urllib.parse.parse_qsl(url.query) if k != 'job']
    if job_id is not None:
        pairs.append(('job', job_id))
    return urllib.parse.urlunsplit(('', '', url.path, urllib.parse.urlencode(pairs), ''))


def make_app(
    settings: wambatic.settings.Settings,
    cache: wambatic.fetch.cache.Cache,
    *,
    default_target: str | None = None,
    clock: collections.abc.Callable[[], datetime.datetime] = wambatic.fetch.ratelimit.utc_now,
) -> fastapi.FastAPI:
    for name in wambatic.reports.assets.TEMPLATE_NAMES:
        wambatic.reports.assets.read_template(name)
    wambatic.reports.assets.page_assets()
    jobs = wambatic.reports.jobs.Jobs()
    theme = settings.report.html_theme

    def page(name: str, **values: str) -> str:
        return string.Template(wambatic.reports.assets.read_template(name)).substitute(
            theme_attribute=wambatic.reports.html.theme_attribute(theme),
            style=wambatic.reports.assets.stylesheet(),
            **values,
        )

    def error_reply(request: fastapi.Request, status: int, message: str) -> fastapi.Response:
        if request.url.path in PAGE_PATHS:
            body = page(
                'message.html',
                status=str(status),
                message=wambatic.reports.html.escape(message),
            )
            return fastapi.responses.HTMLResponse(body, status_code=status)
        return fastapi.responses.JSONResponse({'error': message}, status_code=status)

    def sync_runner(query: wambatic.reports.jobs.Query) -> wambatic.reports.jobs.RunSync:
        async def run(job: wambatic.reports.jobs.SyncJob) -> None:
            job.subject = await wambatic.reports.service.sync_target(
                settings,
                cache,
                query.target,
                query.request,
                full_refresh=False,
                no_fetch=False,
                sync=True,
                progress=job.progress,
                clock=clock,
            )

        return run

    async def results_or_job(
        query: wambatic.reports.jobs.Query, requests: list[wambatic.stats.base.StatsRequest]
    ) -> list[wambatic.stats.base.StatsResult] | wambatic.reports.jobs.SyncJob:
        return await wambatic.reports.jobs.results_or_job(
            settings,
            cache,
            jobs,
            clock,
            sync_runner(query),
            target=query.target,
            key=query.key,
            job_id=query.job,
            requests=requests,
        )

    @contextlib.asynccontextmanager
    async def lifespan(app: fastapi.FastAPI) -> collections.abc.AsyncIterator[None]:
        yield
        await jobs.close()

    app = fastapi.FastAPI(
        title='wambatic', version=wambatic.version.VERSION, lifespan=lifespan, redoc_url=None
    )

    @app.middleware('http')
    async def convert_errors(
        request: fastapi.Request,
        call_next: CallNext,
    ) -> fastapi.Response:
        # Error boundary (review-2 Decision 1): an unexpected error would
        # otherwise reach the client unredacted.
        try:
            return await call_next(request)
        # auditme: accept[silent-broad-except] logged by wambatic.reports.jobs.error_response()
        except Exception as e:  # noqa: BLE001 - logged by wambatic.reports.jobs.error_response()
            return error_reply(request, *wambatic.reports.jobs.error_response(e))

    @app.middleware('http')
    async def check_host_header(
        request: fastapi.Request,
        call_next: CallNext,
    ) -> fastapi.Response:
        if not settings.report.allow_remote:
            server = request.scope.get('server')
            port = server[1] if server else None
            suffix = '' if port is None else f':{port}'
            if request.headers.get('host') not in {f'{name}{suffix}' for name in LOOPBACK_HOSTS}:
                return fastapi.responses.JSONResponse(
                    {'error': 'unexpected Host header'}, status_code=403
                )
        return await call_next(request)

    @app.middleware('http')
    async def log_requests(
        request: fastapi.Request,
        call_next: CallNext,
    ) -> fastapi.Response:
        started = time.monotonic()
        response = await call_next(request)
        milliseconds = (time.monotonic() - started) * 1000
        loguru.logger.debug(
            f'{request.method} {request.url.path} {response.status_code} {milliseconds:.0f} ms'
        )
        return response

    @app.exception_handler(fastapi.exceptions.RequestValidationError)
    async def invalid_request(
        request: fastapi.Request, error: fastapi.exceptions.RequestValidationError
    ) -> fastapi.Response:
        message = '; '.join(
            f'{".".join(str(part) for part in item["loc"])}: {item["msg"]}'
            for item in error.errors()
        )
        return error_reply(request, 400, message)

    @app.exception_handler(wambatic.reports.api.UnsupportedMediaType)
    async def unsupported_media_type(
        request: fastapi.Request, error: wambatic.reports.api.UnsupportedMediaType
    ) -> fastapi.Response:
        return fastapi.responses.JSONResponse({'error': str(error)}, status_code=415)

    app.include_router(
        wambatic.reports.api.graphql_router(
            wambatic.reports.api.ApiContext(settings, cache, jobs, clock, sync_runner)
        ),
        prefix='/graphql',
    )

    @app.get('/', include_in_schema=False)
    async def form() -> fastapi.responses.HTMLResponse:
        target = wambatic.reports.html.escape(default_target or '')
        mode = settings.stats.commit_timezone
        return fastapi.responses.HTMLResponse(
            page(
                'form.html',
                target=target,
                report_selected=' selected' if mode == 'report' else '',
                author_selected=' selected' if mode == 'author' else '',
            )
        )

    @app.get('/report', include_in_schema=False)
    async def report(
        request: fastapi.Request,
        raw: typing.Annotated[wambatic.reports.jobs.RawQuery, fastapi.Depends(raw_query)],
    ) -> fastapi.responses.HTMLResponse:
        query = wambatic.reports.jobs.parse_query(settings, raw, clock(), page=True)
        outcome = await results_or_job(query, wambatic.reports.html.period_requests(query.request))
        if isinstance(outcome, wambatic.reports.jobs.SyncJob):
            reload = reload_path(request.url.components, outcome.id)
            data = {
                'job': outcome.id,
                'progress': f'/api/progress?job={outcome.id}',
                'reload': reload,
            }
            body = page(
                'progress.html',
                target=wambatic.reports.html.escape(query.key[0]),
                retry=wambatic.reports.html.escape(reload_path(request.url.components, None)),
                data=wambatic.reports.html.json_for_script(data),
                script=wambatic.reports.assets.read_template('progress.js'),
            )
            return fastapi.responses.HTMLResponse(body, status_code=202)
        document = await asyncio.to_thread(
            wambatic.reports.html.html_document,
            wambatic.reports.html.html_report(outcome, query.request.granularity),
            theme,
            f'/assets/{wambatic.reports.assets.assets_hash()}/',
        )
        return fastapi.responses.HTMLResponse(document)

    @app.get('/assets/{digest}/{name}', include_in_schema=False)
    async def asset(digest: str, name: str) -> fastapi.Response:
        found = next(
            (a for a in wambatic.reports.assets.page_assets() if a.name == name),
            None,
        )
        if found is None or digest != wambatic.reports.assets.assets_hash():
            return fastapi.responses.JSONResponse({'error': 'no such file'}, status_code=404)
        return fastapi.Response(found.content, media_type=found.media_type, headers=ASSET_HEADERS)

    @app.get('/api/stats')
    async def stats(
        raw: typing.Annotated[wambatic.reports.jobs.RawQuery, fastapi.Depends(raw_query)],
    ) -> fastapi.responses.JSONResponse:
        """The result as `report --format json` prints it, or 202 and a job to follow."""
        query = wambatic.reports.jobs.parse_query(settings, raw, clock(), page=False)
        outcome = await results_or_job(query, [query.request])
        if isinstance(outcome, wambatic.reports.jobs.SyncJob):
            return fastapi.responses.JSONResponse(
                {'job': outcome.id, 'progress': f'/api/progress?job={outcome.id}'},
                status_code=202,
            )
        return fastapi.responses.JSONResponse(wambatic.reports.base.result_to_dict(outcome[0]))

    @app.get('/api/progress')
    async def progress(job: JobId = None) -> fastapi.responses.JSONResponse:
        """How a sync job is going."""
        found = jobs.get(job) if job else None
        if found is None:
            return fastapi.responses.JSONResponse({'error': 'no such job'}, status_code=404)
        return fastapi.responses.JSONResponse(wambatic.reports.jobs.progress_json(found))

    return app


def is_loopback(host: str) -> bool:
    """Exactly `localhost`, or an IP address (IPv6 in brackets or not) that is loopback; no name
    is resolved."""
    if host == 'localhost':
        return True
    try:
        return ipaddress.ip_address(host.strip('[]')).is_loopback
    except ValueError:
        return False


def warn_on_bind(host: str, allow_remote: bool) -> None:
    """Refuse a host that other machines can reach unless remote access was asked for.

    Raises:
        UsageError: the host is not a loopback address and no override is given.
    """
    if is_loopback(host):
        return
    if not allow_remote:
        raise wambatic.reports.errors.UsageError(
            f'{host} is not a loopback address, so anyone who can reach it would act with your '
            'GitHub token; pass --allow-remote (or set report.allow_remote) to allow that'
        )
    loguru.logger.warning(
        f'Listening on {host}: anyone who can reach this port acts with your GitHub token'
    )


def listen(host: str, port: int) -> socket.socket:
    """The listening socket, bound here rather than by uvicorn, which logs a bind failure and
    exits the process itself.

    Raises:
        ServeError: the address cannot be listened on.
    """
    bare = host.strip('[]')
    family = socket.AF_INET6 if ':' in bare else socket.AF_INET
    try:
        return socket.create_server((bare, port), family=family)
    except OSError as e:
        raise wambatic.reports.errors.ServeError(
            # auditme: accept[except-interpolation] the OS reason says why the port cannot be used
            f'cannot listen on {host}:{port}: {e.strerror or e}'
        ) from e


def serve(
    settings: wambatic.settings.Settings, *, default_target: str | None, ignore_cache_version: bool
) -> None:
    """Open the cache, bind `report.web_host:report.web_port`, then run the app on uvicorn until
    Ctrl-C, which ends in the KeyboardInterrupt uvicorn raises again after a graceful stop.

    Raises:
        UsageError: the bind address is refused.
        ServeError: the address cannot be listened on.
        CacheError: the cache cannot be opened or closed.
        CacheVersionError: the cache was written by another version and the check is not ignored.
    """
    report = settings.report
    warn_on_bind(report.web_host, report.allow_remote)
    if not 1 <= report.web_port <= 65535:
        raise wambatic.reports.errors.UsageError('the port must be from 1 to 65535')
    if default_target is not None:
        wambatic.reports.service.parse_target(default_target)
    cache = wambatic.fetch.cache.Cache.open(
        wambatic.settings.cache_path_for(settings.fetch),
        host=settings.fetch.github_host,
        ignore_version=ignore_cache_version,
    )
    sock: socket.socket | None = None
    try:
        sock = listen(report.web_host, report.web_port)
        app = make_app(settings, cache, default_target=default_target)
        shown = f'[{report.web_host}]' if ':' in report.web_host else report.web_host
        base = f'http://{shown}:{sock.getsockname()[1]}'
        loguru.logger.info(f'Serving on {base}/ (Ctrl-C to stop)')
        if default_target is not None:
            quoted = urllib.parse.quote(default_target, safe='')
            loguru.logger.info(f'Report of {default_target}: {base}/report?target={quoted}')
        config = uvicorn.Config(
            app,
            loop='asyncio',
            lifespan='on',
            log_config=None,
            access_log=False,
            log_level='warning',
        )
        try:
            uvicorn.Server(config).run(sockets=[sock])
        except OSError as e:
            raise wambatic.reports.errors.ServeError(
                # auditme: accept[except-interpolation] the OS reason says what to fix
                f'the web server stopped: {e.strerror or e}'
            ) from e
    finally:
        if sock is not None:
            sock.close()
        cache.close()
