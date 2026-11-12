import asyncio
import collections.abc
import contextlib
import dataclasses
import datetime
import ipaddress
import json
import pathlib
import re
import time
import typing

import httpx
import hypothesis
import hypothesis.strategies
import loguru
import pytest

import tests.conftest
import tests.fixtures.fetch.server
import tests.fixtures.fetch.upstream
import tests.fixtures.reports
import tests.fixtures.stats
import wambatic.fetch.base
import wambatic.fetch.cache
import wambatic.fetch.errors
import wambatic.reports.assets
import wambatic.reports.base
import wambatic.reports.errors
import wambatic.reports.html
import wambatic.reports.jobs
import wambatic.reports.service
import wambatic.reports.web
import wambatic.settings
import wambatic.stats.errors

KEY = ('org:octo-org', tests.fixtures.stats.RESOURCES_ACTIVITY)
OTHER = ('org:other', tests.fixtures.stats.RESOURCES_ACTIVITY)


# The app

BASE = 'http://127.0.0.1:8000'
FRESH_PARAMS = 'target=org:octo-org&since=2026-10-01&until=2027-01-21&by=month&by_author=1'
HTML_PARAMS = FRESH_PARAMS.replace('until=2027-01-21', 'until=2027-01-31')
ALPHA_PARAMS = 'target=repo:octo-org/alpha&since=2026-10-01&until=2027-01-21'


def web_settings(max_age: str = '30d', theme: str = 'auto') -> wambatic.settings.Settings:
    return wambatic.settings.load_settings(
        None, {'fetch': {'max_age': max_age}, 'report': {'html_theme': theme}}
    )


@contextlib.asynccontextmanager
async def serving(
    settings: wambatic.settings.Settings,
    cache: wambatic.fetch.cache.Cache,
    *,
    allow_remote: bool = False,
    default_target: str | None = None,
    clock: datetime.datetime = tests.fixtures.stats.NOW,
) -> collections.abc.AsyncIterator[httpx.AsyncClient]:
    """An HTTPX client for the app, with its lifespan entered (`ASGITransport` does not)."""
    settings = dataclasses.replace(
        settings, report=dataclasses.replace(settings.report, allow_remote=allow_remote)
    )
    app = wambatic.reports.web.make_app(
        settings, cache, default_target=default_target, clock=lambda: clock
    )
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url=BASE) as client:
            yield client


JOB_QUERY = (
    'query($id: ID!) { job(id: $id) { state reposListed reposPending reposDone rowsWritten '
    'error status } }'
)


async def job_progress(client: httpx.AsyncClient, job_id: str) -> dict[str, typing.Any] | None:
    """The `job` query of the progress page, as the page sends it."""
    response = await client.post('/graphql', json={'query': JOB_QUERY, 'variables': {'id': job_id}})
    return typing.cast(dict[str, typing.Any] | None, response.json()['data']['job'])


async def finished(
    client: httpx.AsyncClient, job_id: str, seconds: float = 10.0
) -> dict[str, typing.Any]:
    """The progress of a job once it is done or failed."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        body = await job_progress(client, job_id)
        if body is not None and body['state'] not in ('QUEUED', 'LISTING', 'SYNCING'):
            return body
        await asyncio.sleep(0.02)
    raise AssertionError('the job did not finish')


def direct(
    cache_fetcher: wambatic.fetch.base.Fetcher,
    settings: wambatic.settings.Settings,
    by: str,
    subject: wambatic.fetch.base.Subject = tests.fixtures.stats.ORG,
) -> dict[str, object]:
    request = wambatic.reports.service.make_request(
        by,
        '2026-10-01',
        '2027-01-21',
        None,
        True,
        settings,
        tests.fixtures.stats.NOW,
    )
    result = tests.conftest.run_stats(cache_fetcher, subject, request)
    return typing.cast(
        dict[str, object], json.loads(json.dumps(wambatic.reports.base.result_to_dict(result)))
    )


@pytest.mark.parametrize('path', ['/api/progress', '/api/stats', '/docs', '/openapi.json'])
def test_the_removed_rest_and_openapi_routes_answer_404(
    stats_cache: wambatic.fetch.cache.Cache, path: str
) -> None:
    async def scenario() -> int:
        async with serving(web_settings(), stats_cache) as client:
            return (await client.get(path)).status_code

    assert asyncio.run(scenario()) == 404


def test_a_report_page_with_a_date_before_github_answers_400(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    async def scenario() -> int:
        async with serving(web_settings(), stats_cache) as client:
            return (await client.get('/report?target=org:octo-org&since=0001-01-01')).status_code

    assert asyncio.run(scenario()) == 400


@pytest.mark.parametrize(
    ('host', 'status'),
    [
        ('localhost:8000', 200),
        ('127.0.0.1:8000', 200),
        ('[::1]:8000', 200),
        ('evil.example:8000', 403),
        ('localhost:9999', 403),
        ('127.0.0.1', 403),
        ('127.0.0.1.evil.example:8000', 403),
    ],
)
def test_the_host_header_is_checked_against_loopback_and_the_port(
    stats_cache: wambatic.fetch.cache.Cache, host: str, status: int
) -> None:
    async def scenario() -> tuple[int, str]:
        async with serving(web_settings(), stats_cache) as client:
            response = await client.get('/', headers={'Host': host})
            return response.status_code, response.text

    code, text = asyncio.run(scenario())
    assert code == status
    if status == 403:
        assert json.loads(text) == {'error': 'unexpected Host header'}


def test_the_host_check_is_off_when_remote_access_is_allowed(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    async def scenario() -> int:
        async with serving(web_settings(), stats_cache, allow_remote=True) as client:
            return (await client.get('/', headers={'Host': 'example.com'})).status_code

    assert asyncio.run(scenario()) == 200


def test_no_cors_header_is_sent(stats_cache: wambatic.fetch.cache.Cache) -> None:
    async def scenario() -> list[dict[str, str]]:
        async with serving(web_settings(), stats_cache) as client:
            headers = {'Origin': 'https://example.com'}
            return [
                dict((await client.get(path, headers=headers)).headers)
                for path in ('/graphql?query=%7Bversion%7D', '/', '/report?target=x')
            ]

    assert all(
        not any(name.lower().startswith('access-control') for name in found)
        for found in asyncio.run(scenario())
    )


# The pages


def progress_data(text: str) -> dict[str, typing.Any]:
    match = re.search(r'<script type="application/json" id="progress-data">(.*?)</script>', text)
    assert match is not None
    return typing.cast(dict[str, typing.Any], json.loads(match[1]))


def test_the_form_posts_to_report_and_escapes_the_default_target(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    async def scenario() -> tuple[str, str]:
        async with serving(web_settings(), stats_cache, default_target='org:<b>"x"') as client:
            plain = await client.get('/')
        async with serving(web_settings(), stats_cache) as client:
            empty = await client.get('/')
            assert empty.headers['content-type'] == 'text/html; charset=utf-8'
            return plain.text, empty.text

    plain, empty = asyncio.run(scenario())
    assert '<form action="/report" method="get">' in plain
    assert 'value="org:&lt;b&gt;&quot;x&quot;"' in plain
    assert '<b>' not in plain
    assert 'name="target" value=""' in empty
    for field in ('target', 'by', 'since', 'until', 'groups', 'by_author', 'tz', 'commit_tz'):
        assert f'name="{field}"' in plain
    assert 'Comma-separated: activity, flow, delivery, popularity' in plain


@pytest.mark.parametrize(
    ('setting', 'selected', 'other'),
    [
        ('report', 'value="report" selected', 'value="author" selected'),
        ('author', 'value="author" selected', 'value="report" selected'),
    ],
)
def test_the_form_presets_the_commit_dates_select_from_the_setting(
    stats_cache: wambatic.fetch.cache.Cache, setting: str, selected: str, other: str
) -> None:
    settings = wambatic.settings.load_settings(None, {'stats': {'commit_timezone': setting}})

    async def scenario() -> str:
        async with serving(settings, stats_cache) as client:
            return (await client.get('/')).text

    text = asyncio.run(scenario())
    assert '<select name="commit_tz">' in text
    assert selected in text
    assert other not in text


@pytest.mark.parametrize(
    ('setting', 'param', 'expected'),
    [
        ('report', 'author', 'author'),
        ('author', 'report', 'report'),
        ('author', '', 'author'),
        ('report', None, 'report'),
    ],
)
def test_the_commit_tz_parameter_overrides_the_setting(
    setting: str, param: str | None, expected: str
) -> None:
    settings = wambatic.settings.load_settings(None, {'stats': {'commit_timezone': setting}})
    raw = wambatic.reports.jobs.RawQuery(
        target='org:octo-org',
        by=None,
        since=None,
        until=None,
        groups=None,
        by_author=None,
        tz=None,
        commit_tz=param,
        job=None,
    )
    query = wambatic.reports.jobs.parse_query(settings, raw, tests.fixtures.stats.NOW, page=False)
    assert query.request.settings.commit_timezone == expected


@pytest.mark.parametrize('theme', ['auto', 'dark'])
def test_report_of_a_fresh_cache_is_the_html_report_document(
    stats_cache: wambatic.fetch.cache.Cache,
    stats_fetcher: wambatic.fetch.base.Fetcher,
    theme: str,
) -> None:
    report = tests.conftest.make_report(
        stats_fetcher,
        tests.fixtures.stats.ORG,
        by_author=True,
        clock=tests.fixtures.stats.AFTER_FIXTURE_RANGES,
    )
    expected = wambatic.reports.html.html_document(
        report,
        theme,  # type: ignore[arg-type]
        f'/assets/{wambatic.reports.assets.assets_hash()}/',
    )

    async def scenario() -> tuple[int, str, str]:
        async with serving(
            web_settings(theme=theme),
            stats_cache,
            clock=tests.fixtures.stats.AFTER_FIXTURE_RANGES,
        ) as client:
            response = await client.get(f'/report?{HTML_PARAMS}')
            return response.status_code, response.headers['content-type'], response.text

    assert asyncio.run(scenario()) == (200, 'text/html; charset=utf-8', expected)


def test_report_by_total_is_a_400_message_page(stats_cache: wambatic.fetch.cache.Cache) -> None:
    async def scenario() -> tuple[int, str, str]:
        async with serving(web_settings(), stats_cache) as client:
            response = await client.get(f'/report?{FRESH_PARAMS}&by=total')
            return response.status_code, response.headers['content-type'], response.text

    status, content_type, text = asyncio.run(scenario())
    assert (status, content_type) == (400, 'text/html; charset=utf-8')
    assert 'by=total is not for the report page' in text
    assert '<a href="/">Back to the form</a>' in text


def test_a_message_page_escapes_what_the_request_put_in_it(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    async def scenario() -> tuple[int, str]:
        async with serving(web_settings(), stats_cache) as client:
            response = await client.get('/report', params={'target': 'org:octo-org', 'by': '<i>'})
            return response.status_code, response.text

    status, text = asyncio.run(scenario())
    assert status == 400
    assert '<i>' not in text


def test_report_of_a_stale_cache_shows_progress_then_the_report_without_a_second_sync(
    monkeypatch: pytest.MonkeyPatch,
    make_client: tests.conftest.MakeClient,
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    upstream = tests.fixtures.reports.alpha_upstream()

    async def scenario() -> tuple[int, str, dict[str, typing.Any], int, int, str]:
        async with tests.fixtures.fetch.server.ReplayServer({}, upstream.respond) as server:
            tests.fixtures.reports.install_replay(monkeypatch, make_client, server)
            async with serving(web_settings('0s'), stats_cache) as client:
                first = await client.get(f'/report?{ALPHA_PARAMS}')
                data = progress_data(first.text)
                await finished(client, data['job'])
                requests = len(server.received)
                second = await client.get(data['reload'])
                return (
                    first.status_code,
                    first.text,
                    data,
                    second.status_code,
                    len(server.received) - requests,
                    second.text,
                )

    status, text, data, second_status, extra, report = asyncio.run(scenario())
    assert status == 202
    assert set(data) == {'job', 'reload'}
    assert data['reload'].startswith('/report?target=repo%3Aocto-org%2Falpha&')
    assert data['reload'].endswith(f'&job={data["job"]}')
    assert 'repo:octo-org/alpha' in text
    assert (second_status, extra) == (200, 0)
    assert '<title>wambatic: repo octo-org/alpha</title>' in report
    assert 'id="wambatic-data"' in report


def test_a_failed_job_is_reported_once_then_a_new_request_starts_a_new_job(
    monkeypatch: pytest.MonkeyPatch,
    make_client: tests.conftest.MakeClient,
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    upstream = tests.fixtures.reports.alpha_upstream()

    async def scenario() -> tuple[str, int, dict[str, typing.Any] | None, bool]:
        async with tests.fixtures.fetch.server.ReplayServer({}, upstream.respond) as server:
            tests.fixtures.reports.install_replay(monkeypatch, make_client, server)
            async with serving(web_settings('0s'), stats_cache) as client:
                params = 'target=repo:ghost/none'
                first = await client.get(f'/report?{params}')
                data = progress_data(first.text)
                reported = await finished(client, data['job'])
                gone = await job_progress(client, data['job'])
                again = await client.get(f'/report?{params}')
                return (
                    reported['state'],
                    reported['status'],
                    gone,
                    progress_data(again.text)['job'] != data['job'],
                )

    assert asyncio.run(scenario()) == ('FAILED', 404, None, True)


# Loopback


@pytest.mark.parametrize('host', ['localhost', '127.0.0.1', '127.1.2.3', '::1', '[::1]'])
def test_loopback_hosts(host: str) -> None:
    assert wambatic.reports.web.is_loopback(host)


@pytest.mark.parametrize(
    'host',
    ['0.0.0.0', '::', '[::]', '192.168.1.2', 'localhost.example', 'example.com', '', 'LOCALHOST'],
)
def test_other_hosts_are_not_loopback(host: str) -> None:
    assert not wambatic.reports.web.is_loopback(host)


@hypothesis.settings(max_examples=20, deadline=10000)
@hypothesis.given(address=hypothesis.strategies.ip_addresses(v=4))
def test_is_loopback_agrees_with_ipaddress_for_ipv4(address: ipaddress.IPv4Address) -> None:
    assert wambatic.reports.web.is_loopback(str(address)) is address.is_loopback


def test_warn_on_bind_refuses_a_public_host_unless_allowed_and_then_warns() -> None:
    wambatic.reports.web.warn_on_bind('127.0.0.1', False)
    with pytest.raises(wambatic.reports.errors.UsageError, match='--allow-remote'):
        wambatic.reports.web.warn_on_bind('0.0.0.0', False)
    messages: list[str] = []
    sink = loguru.logger.add(
        lambda message: messages.append(
            f'{message.record["level"].name} {message.record["message"]}'
        )
    )
    try:
        wambatic.reports.web.warn_on_bind('0.0.0.0', True)
        wambatic.reports.web.warn_on_bind('127.0.0.1', True)
    finally:
        loguru.logger.remove(sink)
    assert len(messages) == 1
    assert messages[0].startswith('WARNING Listening on 0.0.0.0')


# A large org

ANSWER_WITHIN = 1.0
LARGE_ORG_DELAY = 0.05


def test_a_large_orgs_sync_does_not_block_the_pages(
    monkeypatch: pytest.MonkeyPatch,
    make_client: tests.conftest.MakeClient,
    tmp_path: pathlib.Path,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    upstream = tests.fixtures.fetch.upstream.large_org()
    upstream.history_delay = LARGE_ORG_DELAY
    cache = wambatic.fetch.cache.Cache.open(tmp_path / 'large' / 'cache.sqlite3')

    async def timed(client: httpx.AsyncClient, url: str) -> tuple[httpx.Response, float]:
        started = time.monotonic()
        response = await client.get(url)
        return response, time.monotonic() - started

    async def scenario() -> tuple[int, list[float], list[int], int, float]:
        async with tests.fixtures.fetch.server.ReplayServer({}, upstream.respond) as server:
            tests.fixtures.reports.install_replay(monkeypatch, make_client, server)
            async with serving(web_settings('0s'), cache) as client:
                first, first_seconds = await timed(client, '/report?target=org:octo-org')
                data = progress_data(first.text)
                waits = [first_seconds]
                done_counts: list[int] = []
                while True:
                    page, seconds = await timed(client, '/')
                    assert page.status_code == 200
                    started = time.monotonic()
                    body = await job_progress(client, data['job'])
                    waits += [seconds, time.monotonic() - started]
                    assert body is not None
                    assert body['state'] != 'FAILED', body['error']
                    if body['state'] == 'DONE':
                        break
                    if body['reposDone'] is not None:
                        done_counts.append(body['reposDone'])
                    await asyncio.sleep(0.2)
                report = await client.get(data['reload'])
                return first.status_code, waits, done_counts, report.status_code, first_seconds

    try:
        status, waits, done_counts, report_status, first_seconds = asyncio.run(scenario())
    finally:
        cache.close()
    assert status == 202
    assert max(waits) < ANSWER_WITHIN
    assert len(set(done_counts)) > 1
    assert done_counts == sorted(done_counts)
    assert report_status == 200


def test_assets_are_served_with_their_media_type_and_a_long_cache_lifetime(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    digest = wambatic.reports.assets.assets_hash()

    async def scenario() -> list[httpx.Response]:
        async with serving(web_settings(), stats_cache) as client:
            return [
                await client.get(f'/assets/{digest}/report.js'),
                await client.get(f'/assets/{digest}/report.css'),
                await client.get(f'/assets/{digest}/plotly.min.js'),
            ]

    script, style, plotly = asyncio.run(scenario())
    assert script.status_code == 200
    assert script.headers['content-type'] == 'text/javascript; charset=utf-8'
    assert style.headers['content-type'] == 'text/css; charset=utf-8'
    assert plotly.content == next(
        a.content for a in wambatic.reports.assets.page_assets() if a.name == 'plotly.min.js'
    )
    for response in (script, style, plotly):
        assert response.headers['cache-control'] == 'public, max-age=31536000, immutable'
    assert script.content == next(
        a.content for a in wambatic.reports.assets.page_assets() if a.name == 'report.js'
    )


@pytest.mark.parametrize('path', ['/assets/000000000000/report.js', '/assets/{digest}/nope.js'])
def test_another_hash_or_name_is_a_404(stats_cache: wambatic.fetch.cache.Cache, path: str) -> None:
    url = path.replace('{digest}', wambatic.reports.assets.assets_hash())

    async def scenario() -> httpx.Response:
        async with serving(web_settings(), stats_cache) as client:
            return await client.get(url)

    response = asyncio.run(scenario())
    assert response.status_code == 404
    assert 'cache-control' not in response.headers


def test_the_report_page_points_at_the_assets_of_this_hash(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    async def scenario() -> str:
        async with serving(
            web_settings(), stats_cache, clock=tests.fixtures.stats.AFTER_FIXTURE_RANGES
        ) as client:
            return (await client.get(f'/report?{HTML_PARAMS}')).text

    text = asyncio.run(scenario())
    base = f'/assets/{wambatic.reports.assets.assets_hash()}/'
    assert f'<script defer src="{base}report.js"></script>' in text
    assert f'<link rel="stylesheet" href="{base}report.css">' in text
