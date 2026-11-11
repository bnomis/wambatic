"""The sync jobs the web pages and the GraphQL API share."""

import asyncio
import collections.abc
import dataclasses
import datetime
import secrets
import typing

import loguru

import wambatic.fetch.base
import wambatic.fetch.cache
import wambatic.fetch.errors
import wambatic.reports.errors
import wambatic.reports.service
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.engine
import wambatic.stats.errors

JobKey = tuple[str, frozenset[str]]
INTERNAL_ERROR = 'internal error; see the server log'
BAD_REQUEST = (
    wambatic.settings.SettingsError,
    wambatic.stats.errors.UnknownGroupError,
    wambatic.stats.errors.InvalidRangeError,
    wambatic.stats.errors.InvalidRequestError,
)
TRUE_VALUES = frozenset({'1', 'on', 'true'})
NOT_FOUND = (wambatic.fetch.errors.NotFoundError, wambatic.stats.errors.EmptySubjectError)


class JobError(Exception):
    """A failed job's error, raised again for the request that reports it."""

    def __init__(self, message: str, status: int) -> None:
        super().__init__(message)
        self.status = status


def error_status(error: BaseException) -> int:
    """The HTTP status an error maps to (reports spec, Error handling)."""
    if isinstance(error, JobError):
        return error.status
    if isinstance(error, (wambatic.reports.errors.UsageError, *BAD_REQUEST)):
        return 400
    if isinstance(error, NOT_FOUND):
        return 404
    if isinstance(error, wambatic.fetch.errors.FetchError):
        return 502
    return 500


def error_response(error: BaseException) -> tuple[int, str]:
    """The status and the message a response may show: redacted, and for an unexpected error
    only a pointer to the log, where its traceback is."""
    status = error_status(error)
    if status == 500:
        loguru.logger.exception(f'Unexpected error: {wambatic.reports.service.redact_error(error)}')
        return status, INTERNAL_ERROR
    return status, wambatic.reports.service.redact_environment_token(str(error))


@dataclasses.dataclass(slots=True)
class SyncJob:
    # Mutable by design: the background sync updates the phase and progress that the page polls.
    id: str
    key: JobKey
    phase: typing.Literal['queued', 'running', 'done', 'failed'] = 'queued'
    progress: wambatic.fetch.base.SyncProgress = dataclasses.field(
        default_factory=wambatic.fetch.base.SyncProgress
    )
    subject: wambatic.fetch.base.Subject | None = None
    error: str | None = None
    status: int | None = None

    @property
    def state(self) -> typing.Literal['queued', 'listing', 'syncing', 'done', 'failed']:
        """`listing` until the fetcher has read the repository listing, then `syncing`."""
        if self.phase == 'running':
            return 'listing' if self.progress.repos_listed is None else 'syncing'
        return self.phase


class Jobs:
    """Each key's latest job; one job syncs at a time, the others wait as `queued`."""

    def __init__(self) -> None:
        self.latest: dict[JobKey, SyncJob] = {}
        self.by_id: dict[str, SyncJob] = {}
        self.tasks: set[asyncio.Task[None]] = set()
        self.lock = asyncio.Lock()

    def start(
        self, key: JobKey, run: collections.abc.Callable[[SyncJob], collections.abc.Awaitable[None]]
    ) -> SyncJob:
        """The key's running or queued job, else a new one running `run`."""
        current = self.latest.get(key)
        if current is not None and current.phase in ('queued', 'running'):
            return current
        if current is not None:
            del self.by_id[current.id]
        job = SyncJob(secrets.token_hex(8), key)
        self.latest[key] = job
        self.by_id[job.id] = job
        task = asyncio.get_running_loop().create_task(self.execute(job, run))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return job

    def get(self, job_id: str) -> SyncJob | None:
        return self.by_id.get(job_id)

    def forget(self, job: SyncJob) -> None:
        """Drop `job` unless a newer job has replaced it."""
        if self.latest.get(job.key) is job:
            del self.latest[job.key]
            del self.by_id[job.id]

    async def execute(
        self,
        job: SyncJob,
        run: collections.abc.Callable[[SyncJob], collections.abc.Awaitable[None]],
    ) -> None:
        # Error boundary (review-2 Decision 1): a failed job would otherwise
        # leave its progress page hanging.
        try:
            async with self.lock:
                job.phase = 'running'
                await run(job)
            job.phase = 'done'
        # auditme: accept[silent-broad-except] logged by error_response()
        except Exception as e:  # noqa: BLE001 - logged by error_response()
            job.status, job.error = error_response(e)
            job.phase = 'failed'

    async def close(self) -> None:
        """Cancel the running and queued jobs and wait for them to end."""
        tasks = list(self.tasks)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)


def progress_json(job: SyncJob) -> dict[str, object]:
    progress = job.progress
    rows = None if progress.repos_listed is None else sum(progress.rows_written.values())
    return {
        'job': job.id,
        'state': job.state,
        'repos_listed': progress.repos_listed,
        'repos_pending': progress.repos_pending,
        'repos_done': None if progress.repos_pending is None else progress.repos_done,
        'rows_written': rows,
        'error': job.error,
        'status': job.status,
    }


RunSync = collections.abc.Callable[[SyncJob], collections.abc.Awaitable[None]]


async def ready_results(
    settings: wambatic.settings.Settings,
    cache: wambatic.fetch.cache.Cache,
    jobs: Jobs,
    clock: collections.abc.Callable[[], datetime.datetime],
    *,
    target: wambatic.fetch.base.Subject | str,
    key: JobKey,
    job_id: str | None,
    requests: list[wambatic.stats.base.StatsRequest],
) -> list[wambatic.stats.base.StatsResult] | SyncJob | None:
    """The results at once when the cache is fresh or the request names its finished job; the
    unfinished job the request names; else None, when a sync is needed. Starts nothing.

    Raises:
        JobError: the finished job for the request failed.
        EmptySubjectError: there is nothing to report.
        UnknownGroupError: a group is outside `GROUPS`.
        InvalidRequestError: the request is invalid for the subject.
        InvalidRangeError: `since` is after `until`.
        CacheError: the cache cannot be read.
    """

    async def stale(subject: wambatic.fetch.base.Subject) -> bool:
        reader = wambatic.reports.service.make_fetcher('', cache, settings.fetch)
        provenance = await reader.provenance(subject, key[1])
        return wambatic.reports.service.needs_sync(
            provenance, key[1], settings.fetch, full_refresh=False, no_fetch=False, now=clock()
        )

    async def compute(
        subject: wambatic.fetch.base.Subject,
    ) -> list[wambatic.stats.base.StatsResult]:
        _, results = await wambatic.reports.service.sync_and_compute(
            settings,
            cache,
            subject,
            requests,
            full_refresh=False,
            no_fetch=False,
            sync=False,
            clock=clock,
        )
        return results

    job = jobs.get(job_id) if job_id is not None else None
    if job is not None and job.key == key:
        if job.phase == 'failed':
            jobs.forget(job)
            raise JobError(job.error or INTERNAL_ERROR, job.status or 500)
        if job.phase == 'done' and job.subject is not None:
            return await compute(job.subject)
        if job.phase != 'done':
            return job
    if not isinstance(target, str) and not await stale(target):
        return await compute(target)
    return None


async def results_or_job(
    settings: wambatic.settings.Settings,
    cache: wambatic.fetch.cache.Cache,
    jobs: Jobs,
    clock: collections.abc.Callable[[], datetime.datetime],
    run: RunSync,
    *,
    target: wambatic.fetch.base.Subject | str,
    key: JobKey,
    job_id: str | None,
    requests: list[wambatic.stats.base.StatsRequest],
) -> list[wambatic.stats.base.StatsResult] | SyncJob:
    """The results of `ready_results`, else the job that brings the cache up to date, started
    with `run`.

    Raises:
        JobError: the finished job for the request failed.
        EmptySubjectError: there is nothing to report.
        UnknownGroupError: a group is outside `GROUPS`.
        InvalidRequestError: the request is invalid for the subject.
        InvalidRangeError: `since` is after `until`.
        CacheError: the cache cannot be read.
    """
    ready = await ready_results(
        settings,
        cache,
        jobs,
        clock,
        target=target,
        key=key,
        job_id=job_id,
        requests=requests,
    )
    return jobs.start(key, run) if ready is None else ready


@dataclasses.dataclass(frozen=True, slots=True)
class RawQuery:
    """The query parameters of a data request, as the client sent them."""

    target: str | None
    by: str | None
    since: str | None
    until: str | None
    groups: str | None
    by_author: str | None
    tz: str | None
    commit_tz: str | None
    job: str | None


@dataclasses.dataclass(frozen=True, slots=True)
class Query:
    """A data request after parsing: the target, the request and the key its sync job has."""

    target: wambatic.fetch.base.Subject | str
    request: wambatic.stats.base.StatsRequest
    key: wambatic.reports.jobs.JobKey
    job: str | None


def blank_to_none(value: str | None) -> str | None:
    """A form submits an empty field as an empty value, which means the field was left out."""
    return value.strip() or None if value is not None else None


def parse_query(
    settings: wambatic.settings.Settings,
    raw: RawQuery,
    today: datetime.datetime,
    *,
    page: bool,
) -> Query:
    """The CLI's parsers applied to the parameters, so a value the CLI rejects is rejected with
    the same message.

    Raises:
        UsageError: a query parameter is invalid.
        SettingsError: `settings.stats.timezone` is not a known time zone.
        UnknownGroupError: a group is outside `GROUPS`.
    """
    text = (blank_to_none(raw.target) or '').strip()
    if not text:
        raise wambatic.reports.errors.UsageError(
            f'target is required: {wambatic.reports.service.TARGET_FORMS}'
        )
    target = wambatic.reports.service.parse_target(text)
    by = blank_to_none(raw.by) or 'month'
    if page and by == 'total':
        raise wambatic.reports.errors.UsageError(
            'by=total is not for the report page: the page shows the totals as tiles and '
            'switches between year, month, week and day'
        )
    by_author = (raw.by_author or '').lower() in TRUE_VALUES
    if by_author and not isinstance(target, str):
        wambatic.reports.service.check_by_author(target)
    tz = blank_to_none(raw.tz)
    commit_tz = blank_to_none(raw.commit_tz)
    stats = settings.stats
    if tz is not None:
        stats = dataclasses.replace(stats, timezone=tz)
    if commit_tz is not None:
        stats = dataclasses.replace(
            stats, commit_timezone=wambatic.reports.service.parse_commit_tz(commit_tz)
        )
    effective = dataclasses.replace(settings, stats=stats)
    request = wambatic.reports.service.make_request(
        by,
        blank_to_none(raw.since),
        blank_to_none(raw.until),
        blank_to_none(raw.groups),
        by_author,
        effective,
        today,
    )
    resources = (
        wambatic.stats.engine.resources_for(request.groups) & wambatic.fetch.base.BUILT_RESOURCES
    )
    return Query(target, request, (text, resources), blank_to_none(raw.job))
