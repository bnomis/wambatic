"""The GraphQL API of the web app: stats for a target, a sync mutation and job progress."""

import collections.abc
import dataclasses
import datetime
import enum
import typing

import fastapi
import graphql
import loguru
import strawberry
import strawberry.extensions
import strawberry.fastapi
import strawberry.scalars
import strawberry.types

import wambatic.fetch.cache
import wambatic.reports.base
import wambatic.reports.errors
import wambatic.reports.jobs
import wambatic.reports.service
import wambatic.settings
import wambatic.version

JSON_CONTENT_TYPE = 'application/json'
NEEDS_JSON = 'POST /graphql needs Content-Type: application/json'
SYNC_NEEDED = 'the cache is older than fetch.max_age; run the sync mutation'
CODES = {400: 'BAD_REQUEST', 404: 'NOT_FOUND', 502: 'UPSTREAM', 500: 'INTERNAL'}


class UnsupportedMediaType(Exception):
    """A POST to the API whose body is not declared as JSON."""


# Not frozen and without slots: the router sets `request` and `response` on a context that
# inherits from BaseContext.
@dataclasses.dataclass
class ApiContext(strawberry.fastapi.BaseContext):
    settings: wambatic.settings.Settings
    cache: wambatic.fetch.cache.Cache
    jobs: wambatic.reports.jobs.Jobs
    clock: collections.abc.Callable[[], datetime.datetime]
    sync_runner: collections.abc.Callable[
        [wambatic.reports.jobs.Query], wambatic.reports.jobs.RunSync
    ]


@strawberry.enum
class Granularity(enum.Enum):
    TOTAL = 'total'
    YEAR = 'year'
    MONTH = 'month'
    WEEK = 'week'
    DAY = 'day'


@strawberry.enum
class CommitTimezone(enum.Enum):
    REPORT = 'report'
    AUTHOR = 'author'


@strawberry.enum
class JobState(enum.Enum):
    QUEUED = 'queued'
    LISTING = 'listing'
    SYNCING = 'syncing'
    DONE = 'done'
    FAILED = 'failed'


@strawberry.input
class StatsInput:
    target: str
    by: Granularity = Granularity.MONTH
    since: str | None = None
    until: str | None = None
    groups: list[str] | None = None
    by_author: bool = False
    tz: str | None = None
    commit_tz: CommitTimezone | None = None
    job: strawberry.ID | None = None


@strawberry.type
class SyncNeeded:
    message: str


@strawberry.type
class Subject:
    kind: str
    login: str
    name: str | None


@strawberry.type
class RequestInfo:
    granularity: Granularity
    groups: list[str]
    since: str | None
    until: str | None
    by_author: bool
    tz: str
    settings: strawberry.scalars.JSON


@strawberry.type
class Point:
    label: str
    start: str
    value: float


@strawberry.type
class Series:
    metric: str
    unit: str
    by: str | None
    by_kind: str | None
    points: list[Point]


def series_of(data: dict[str, typing.Any]) -> Series:
    return Series(
        metric=data['metric'],
        unit=data['unit'],
        by=data['by'],
        by_kind=data['by_kind'],
        points=[
            Point(label=p['label'], start=p['start'], value=p['value']) for p in data['points']
        ],
    )


def filter_series(
    data: list[dict[str, typing.Any]], metrics: list[str] | None, by: str | None
) -> list[Series]:
    return [
        series_of(item)
        for item in data
        if (metrics is None or item['metric'] in metrics) and (by is None or item['by'] == by)
    ]


@strawberry.type
class Stats:
    format_version: int
    subject: Subject
    request: RequestInfo
    since: str
    until: str
    all_series: strawberry.Private[list[dict[str, typing.Any]]]
    tables: strawberry.scalars.JSON
    provenance: strawberry.scalars.JSON

    @strawberry.field
    def series(self, metrics: list[str] | None = None, by: str | None = None) -> list[Series]:
        return filter_series(self.all_series, metrics, by)


StatsOutcome = typing.Annotated[Stats | SyncNeeded, strawberry.union('StatsOutcome')]


@strawberry.type
class SyncJob:
    id: strawberry.ID
    state: JobState
    repos_listed: int | None
    repos_pending: int | None
    repos_done: int | None
    rows_written: int | None
    error: str | None
    status: int | None


def build_stats(data: dict[str, typing.Any]) -> Stats:
    request = data['request']
    return Stats(
        format_version=data['format_version'],
        subject=Subject(**data['subject']),
        request=RequestInfo(
            granularity=Granularity(request['granularity']),
            groups=request['groups'],
            since=request['since'],
            until=request['until'],
            by_author=request['by_author'],
            tz=request['tz'],
            settings=request['settings'],
        ),
        since=data['since'],
        until=data['until'],
        all_series=data['series'],
        tables=data['tables'],
        provenance=data['provenance'],
    )


def build_job(job: wambatic.reports.jobs.SyncJob) -> SyncJob:
    progress = wambatic.reports.jobs.progress_json(job)
    return SyncJob(
        id=strawberry.ID(job.id),
        state=JobState(job.state),
        repos_listed=typing.cast(int | None, progress['repos_listed']),
        repos_pending=typing.cast(int | None, progress['repos_pending']),
        repos_done=typing.cast(int | None, progress['repos_done']),
        rows_written=typing.cast(int | None, progress['rows_written']),
        error=job.error,
        status=job.status,
    )


def parse_input(context: ApiContext, input: StatsInput) -> wambatic.reports.jobs.Query:
    raw = wambatic.reports.jobs.RawQuery(
        target=input.target,
        by=input.by.value,
        since=input.since,
        until=input.until,
        groups=None if input.groups is None else ','.join(input.groups),
        by_author='1' if input.by_author else None,
        tz=input.tz,
        commit_tz=None if input.commit_tz is None else input.commit_tz.value,
        job=None if input.job is None else str(input.job),
    )
    return wambatic.reports.jobs.parse_query(context.settings, raw, context.clock(), page=False)


Info = strawberry.Info[ApiContext, None]


@strawberry.type
class Query:
    @strawberry.field
    async def stats(self, info: Info, input: StatsInput) -> StatsOutcome:
        context = info.context
        query = parse_input(context, input)
        if query.job is not None:
            found = context.jobs.get(query.job)
            if found is None:
                raise wambatic.reports.errors.UsageError(f'job {query.job} is unknown')
            if found.key != query.key:
                raise wambatic.reports.errors.UsageError(
                    f'job {query.job} is of another target or groups'
                )
        outcome = await wambatic.reports.jobs.ready_results(
            context.settings,
            context.cache,
            context.jobs,
            context.clock,
            target=query.target,
            key=query.key,
            job_id=query.job,
            requests=[query.request],
        )
        if outcome is None:
            return SyncNeeded(message=SYNC_NEEDED)
        if isinstance(outcome, wambatic.reports.jobs.SyncJob):
            raise wambatic.reports.errors.UsageError(f'job {outcome.id} has not finished')
        return build_stats(wambatic.reports.base.result_to_dict(outcome[0]))

    @strawberry.field
    def job(self, info: Info, id: strawberry.ID) -> SyncJob | None:
        jobs = info.context.jobs
        found = jobs.get(str(id))
        if found is None:
            return None
        reply = build_job(found)
        if found.phase == 'failed':
            jobs.forget(found)
        return reply

    @strawberry.field
    def version(self) -> str:
        return wambatic.version.VERSION


@strawberry.type
class Mutation:
    @strawberry.mutation
    def sync(self, info: Info, input: StatsInput) -> SyncJob:
        context = info.context
        query = parse_input(context, input)
        return build_job(context.jobs.start(query.key, context.sync_runner(query)))


class WambaticErrors(strawberry.extensions.SchemaExtension):
    """Replaces each error after execution with one that holds a code, a status and a redacted
    message, and no traceback."""

    def on_operation(self) -> collections.abc.Generator[None]:
        yield
        result = self.execution_context.result
        if result is not None and result.errors:
            result.errors = [self.convert(error) for error in result.errors]

    @staticmethod
    def convert(error: graphql.GraphQLError) -> graphql.GraphQLError:
        original = error.original_error
        extensions: dict[str, object]
        if original is None:
            message, extensions = error.message, {'code': 'BAD_QUERY'}
        else:
            status = wambatic.reports.jobs.error_status(original)
            if status == 500:
                message = wambatic.reports.jobs.INTERNAL_ERROR
                loguru.logger.opt(exception=original).error(
                    f'Unexpected error: {wambatic.reports.service.redact_error(original)}'
                )
            else:
                message = wambatic.reports.service.redact_environment_token(str(original))
            extensions = {'code': CODES[status], 'status': status}
        return graphql.GraphQLError(
            message,
            nodes=error.nodes,
            source=error.source,
            positions=error.positions,
            path=error.path,
            extensions=extensions,
        )


class WambaticSchema(strawberry.Schema):
    def process_errors(
        self,
        errors: list[graphql.GraphQLError],
        execution_context: strawberry.types.ExecutionContext | None = None,
    ) -> None:
        """The errors are logged by `WambaticErrors`; the default would log their text with a
        traceback."""


schema = WambaticSchema(query=Query, mutation=Mutation, extensions=[WambaticErrors])


async def require_json(request: fastapi.Request) -> None:
    """Refuse a POST that is not declared as JSON, before Strawberry reads the body."""
    if request.method != 'POST':
        return
    media_type = request.headers.get('content-type', '').split(';')[0].strip().lower()
    if media_type != JSON_CONTENT_TYPE:
        raise UnsupportedMediaType(NEEDS_JSON)


def graphql_router(context: ApiContext) -> strawberry.fastapi.GraphQLRouter[ApiContext, None]:
    """The router web.make_app mounts at /graphql: GraphiQL on a browser GET, queries over GET
    and POST, mutations over POST only, and every resolver given `context`."""

    def get_context() -> ApiContext:
        return context

    return strawberry.fastapi.GraphQLRouter(
        schema,
        context_getter=get_context,
        graphql_ide='graphiql',
        allow_queries_via_get=True,
        multipart_uploads_enabled=False,
        include_in_schema=False,
        dependencies=[fastapi.Depends(require_json)],
    )
