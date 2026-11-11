import asyncio
import datetime

import pytest

import tests.fixtures.stats
import wambatic.fetch.errors
import wambatic.reports.errors
import wambatic.reports.jobs
import wambatic.settings
import wambatic.stats.errors

KEY = ('org:octo-org', tests.fixtures.stats.RESOURCES_ACTIVITY)
OTHER = ('org:other', tests.fixtures.stats.RESOURCES_ACTIVITY)


@pytest.mark.parametrize(
    'error,status',
    [
        (wambatic.reports.errors.UsageError('x'), 400),
        (wambatic.settings.SettingsError('x'), 400),
        (wambatic.stats.errors.UnknownGroupError('x'), 400),
        (wambatic.stats.errors.InvalidRangeError('x'), 400),
        (wambatic.stats.errors.InvalidRequestError('x'), 400),
        (wambatic.fetch.errors.NotFoundError('x'), 404),
        (wambatic.stats.errors.EmptySubjectError('x'), 404),
        (wambatic.fetch.errors.AuthError('x'), 502),
        (
            wambatic.fetch.errors.RateLimitError(
                datetime.datetime(2027, 1, 1, tzinfo=datetime.UTC)
            ),
            502,
        ),
        (wambatic.fetch.errors.GraphQLError([('X', 'x')]), 502),
        (wambatic.fetch.errors.StatsPendingError('x'), 502),
        (RuntimeError('x'), 500),
        (wambatic.reports.jobs.JobError('x', 404), 404),
    ],
)
def test_error_status_maps_each_error_class(error: Exception, status: int) -> None:
    assert wambatic.reports.jobs.error_status(error) == status


def test_an_unexpected_error_shows_only_a_pointer_to_the_log() -> None:
    status, message = wambatic.reports.jobs.error_response(RuntimeError('secret detail'))
    assert (status, message) == (500, 'internal error; see the server log')


def test_a_second_start_for_a_running_key_returns_the_same_job() -> None:
    async def scenario() -> None:
        jobs = wambatic.reports.jobs.Jobs()
        release = asyncio.Event()

        async def run(job: wambatic.reports.jobs.SyncJob) -> None:
            await release.wait()

        first = jobs.start(KEY, run)
        await asyncio.sleep(0)
        assert jobs.start(KEY, run) is first
        states = [first.state]
        first.progress.repos_listed = 3
        states.append(first.state)
        assert states == ['listing', 'syncing']
        release.set()
        await jobs.close()

    asyncio.run(scenario())


def test_jobs_for_two_keys_run_one_after_the_other() -> None:
    async def scenario() -> list[str]:
        jobs = wambatic.reports.jobs.Jobs()
        release = asyncio.Event()
        events: list[str] = []

        async def run(job: wambatic.reports.jobs.SyncJob) -> None:
            events.append(f'start {job.key[0]}')
            await release.wait()
            events.append(f'end {job.key[0]}')

        first = jobs.start(KEY, run)
        second = jobs.start(OTHER, run)
        await asyncio.sleep(0.01)
        assert (first.state, second.state) == ('listing', 'queued')
        assert events == ['start org:octo-org']
        release.set()
        while second.state != 'done':
            await asyncio.sleep(0.01)
        assert first.state == 'done'
        return events

    assert asyncio.run(scenario()) == [
        'start org:octo-org',
        'end org:octo-org',
        'start org:other',
        'end org:other',
    ]


def test_a_failing_job_records_the_mapped_status_and_a_redacted_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', 'ghp_secret_value')

    async def scenario() -> wambatic.reports.jobs.SyncJob:
        jobs = wambatic.reports.jobs.Jobs()

        async def run(job: wambatic.reports.jobs.SyncJob) -> None:
            raise wambatic.fetch.errors.NotFoundError('no such thing ghp_secret_value')

        job = jobs.start(KEY, run)
        while job.phase in ('queued', 'running'):
            await asyncio.sleep(0.01)
        return job

    job = asyncio.run(scenario())
    assert job.state == 'failed'
    assert job.status == 404
    assert job.error is not None
    assert 'ghp_secret_value' not in job.error
    assert 'no such thing' in job.error


def test_after_a_job_is_done_start_makes_a_new_one_and_forget_drops_the_latest() -> None:
    async def scenario() -> None:
        jobs = wambatic.reports.jobs.Jobs()

        async def run(job: wambatic.reports.jobs.SyncJob) -> None:
            return None

        first = jobs.start(KEY, run)
        while first.phase != 'done':
            await asyncio.sleep(0.01)
        second = jobs.start(KEY, run)
        assert second is not first
        assert jobs.get(first.id) is None
        assert jobs.get(second.id) is second
        jobs.forget(first)
        assert jobs.get(second.id) is second
        while second.phase != 'done':
            await asyncio.sleep(0.01)
        jobs.forget(second)
        assert jobs.get(second.id) is None

    asyncio.run(scenario())


def test_close_cancels_a_running_job() -> None:
    async def scenario() -> bool:
        jobs = wambatic.reports.jobs.Jobs()
        cancelled = asyncio.Event()

        async def run(job: wambatic.reports.jobs.SyncJob) -> None:
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                cancelled.set()
                raise

        jobs.start(KEY, run)
        await asyncio.sleep(0.01)
        await jobs.close()
        return cancelled.is_set()

    assert asyncio.run(scenario())
