import asyncio
import json
import pathlib
import time
import typing

import graphql
import httpx
import loguru
import pytest
import strawberry.printer

import tests.conftest
import tests.fixtures.fetch.server
import tests.fixtures.reports
import tests.reports.test_web
import wambatic.fetch.base
import wambatic.fetch.cache
import wambatic.fetch.errors
import wambatic.reports.api
import wambatic.reports.base
import wambatic.reports.errors
import wambatic.stats.errors
import wambatic.version

SPEC = pathlib.Path(__file__).parents[3] / 'agents' / 'specs' / 'graphql-api' / 'spec.md'
STATS_QUERY = 'query Q($input: StatsInput!) { stats(input: $input) { __typename SELECTION } }'
FRESH = {'byAuthor': True, 'since': '2026-10-01', 'target': 'org:octo-org', 'until': '2027-01-21'}
ALPHA = {'since': '2026-10-01', 'target': 'repo:octo-org/alpha', 'until': '2027-01-21'}
SYNC = 'mutation S($input: StatsInput!) { sync(input: $input) { id state } }'
JOB = (
    'query J($id: ID!) { job(id: $id) '
    '{ id state reposListed reposPending reposDone rowsWritten error status } }'
)


async def gql(
    client: httpx.AsyncClient, query: str, variables: dict[str, typing.Any] | None = None
) -> dict[str, typing.Any]:
    response = await client.post('/graphql', json={'query': query, 'variables': variables or {}})
    assert response.status_code == 200
    return typing.cast(dict[str, typing.Any], response.json())


async def settled(client: httpx.AsyncClient, job_id: str) -> dict[str, typing.Any]:
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        job = (await gql(client, JOB, {'id': job_id}))['data']['job']
        if job['state'] in ('DONE', 'FAILED'):
            return typing.cast(dict[str, typing.Any], job)
        await asyncio.sleep(0.02)
    raise AssertionError('the job did not finish')


def stats_query(selection: str) -> str:
    return STATS_QUERY.replace('SELECTION', selection)


def camel(name: str) -> str:
    head, *rest = name.split('_')
    return head + ''.join(word.capitalize() for word in rest)


def full_stats() -> str:
    return stats_query(
        """... on Stats { formatVersion subject { kind login name }
        request { granularity groups since until byAuthor tz settings }
        since until
        series { metric unit by byKind points { label start value } }
        tables provenance }"""
    )


@pytest.mark.parametrize('by', ['TOTAL', 'YEAR', 'MONTH', 'WEEK', 'DAY'])
def test_stats_of_a_fresh_cache_equals_the_json_report(
    stats_cache: wambatic.fetch.cache.Cache,
    stats_fetcher: wambatic.fetch.base.Fetcher,
    by: str,
) -> None:
    settings = tests.reports.test_web.web_settings()
    expected = tests.reports.test_web.direct(stats_fetcher, settings, by.lower())

    async def scenario() -> dict[str, typing.Any]:
        async with tests.reports.test_web.serving(settings, stats_cache) as client:
            body = await gql(client, full_stats(), {'input': {**FRESH, 'by': by}})
            return typing.cast(dict[str, typing.Any], body['data']['stats'])

    got = asyncio.run(scenario())
    assert got.pop('__typename') == 'Stats'
    assert got['formatVersion'] == expected['format_version']
    assert got['subject'] == expected['subject']
    assert got['since'] == expected['since']
    assert got['until'] == expected['until']
    assert got['tables'] == expected['tables']
    assert got['provenance'] == expected['provenance']
    request = typing.cast(dict[str, typing.Any], expected['request'])
    assert got['request'] == {
        **{camel(key): value for key, value in request.items()},
        'granularity': by,
    }
    assert [
        {**{camel(k): v for k, v in series.items() if k != 'points'}, 'points': series['points']}
        for series in typing.cast(list[dict[str, typing.Any]], expected['series'])
    ] == got['series']


def test_series_filters(stats_cache: wambatic.fetch.cache.Cache) -> None:
    settings = tests.reports.test_web.web_settings()

    async def scenario() -> tuple[list[typing.Any], list[typing.Any], list[typing.Any]]:
        async with tests.reports.test_web.serving(settings, stats_cache) as client:

            async def fetch(arguments: str) -> list[typing.Any]:
                query = (
                    'query Q($input: StatsInput!) { stats(input: $input) { ... on Stats '
                    f'{{ series{arguments} {{ metric by }} }} }} }}'
                )
                body = await gql(client, query, {'input': FRESH})
                return typing.cast(list[typing.Any], body['data']['stats']['series'])

            everything = await fetch('')
            name = everything[0]['metric']
            return everything, await fetch(f'(metrics: ["{name}"])'), await fetch('(by: "nobody")')

    everything, named, nobody = asyncio.run(scenario())
    assert len(everything) > len(named) > 0
    assert {item['metric'] for item in named} == {everything[0]['metric']}
    assert named == [item for item in everything if item['metric'] == everything[0]['metric']]
    assert nobody == []


def test_stale_data_is_sync_needed_and_starts_no_job(
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    async def scenario() -> tuple[typing.Any, typing.Any]:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings('0s'), stats_cache
        ) as client:
            first = await gql(
                client,
                stats_query('... on SyncNeeded { message }'),
                {'input': FRESH},
            )
            jobs = await gql(client, JOB, {'id': 'anything'})
            return first, jobs

    first, jobs = asyncio.run(scenario())
    assert first['data']['stats'] == {
        '__typename': 'SyncNeeded',
        'message': 'the cache is older than fetch.max_age; run the sync mutation',
    }
    assert jobs['data']['job'] is None


def test_sync_then_job_polling_then_stats_with_the_job(
    monkeypatch: pytest.MonkeyPatch,
    make_client: tests.conftest.MakeClient,
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    upstream = tests.fixtures.reports.alpha_upstream()

    async def scenario() -> tuple[str, dict[str, typing.Any], str, int]:
        async with tests.fixtures.fetch.server.ReplayServer({}, upstream.respond) as server:
            tests.fixtures.reports.install_replay(monkeypatch, make_client, server)
            async with tests.reports.test_web.serving(
                tests.reports.test_web.web_settings('0s'), stats_cache
            ) as client:
                needed = await gql(client, stats_query(''), {'input': ALPHA})
                started = (await gql(client, SYNC, {'input': ALPHA}))['data']['sync']
                done = await settled(client, started['id'])
                requests = len(server.received)
                result = await gql(
                    client, stats_query(''), {'input': {**ALPHA, 'job': started['id']}}
                )
                return (
                    needed['data']['stats']['__typename'],
                    done,
                    result['data']['stats']['__typename'],
                    len(server.received) - requests,
                )

    needed, done, result, extra = asyncio.run(scenario())
    assert (needed, result, extra) == ('SyncNeeded', 'Stats', 0)
    assert done['state'] == 'DONE'
    assert done['reposListed'] == 1
    assert done['reposDone'] == done['reposPending']
    assert done['error'] is None


def test_two_syncs_share_a_job(
    monkeypatch: pytest.MonkeyPatch,
    make_client: tests.conftest.MakeClient,
    stats_cache: wambatic.fetch.cache.Cache,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', 'test-token')
    upstream = tests.fixtures.reports.alpha_upstream()

    async def scenario() -> tuple[str, str]:
        async with tests.fixtures.fetch.server.ReplayServer({}, upstream.respond) as server:
            tests.fixtures.reports.install_replay(monkeypatch, make_client, server)
            async with tests.reports.test_web.serving(
                tests.reports.test_web.web_settings('0s'), stats_cache
            ) as client:
                # Mutations of one document run in order without yielding to the event loop,
                # so the first job cannot have finished when the second sync asks.
                body = await gql(
                    client,
                    'mutation S($input: StatsInput!) '
                    '{ one: sync(input: $input) { id } two: sync(input: $input) { id } }',
                    {'input': ALPHA},
                )
                one, two = body['data']['one']['id'], body['data']['two']['id']
                await settled(client, one)
                return one, two

    one, two = asyncio.run(scenario())
    assert one == two


def test_a_failed_job_is_reported_once_and_then_forgotten(
    monkeypatch: pytest.MonkeyPatch, stats_cache: wambatic.fetch.cache.Cache
) -> None:
    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    monkeypatch.setenv('HOME', '/nonexistent')

    async def scenario() -> tuple[dict[str, typing.Any], typing.Any]:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings('0s'), stats_cache
        ) as client:
            started = (await gql(client, SYNC, {'input': FRESH}))['data']['sync']
            failed = await settled(client, started['id'])
            again = (await gql(client, JOB, {'id': started['id']}))['data']['job']
            return failed, again

    failed, again = asyncio.run(scenario())
    assert failed['state'] == 'FAILED'
    assert failed['status'] in (502, 500)
    assert failed['error']
    assert again is None


@pytest.mark.parametrize(
    ('variables', 'code', 'status', 'message'),
    [
        ({'target': 'a/b/c'}, 'BAD_REQUEST', 400, 'the target must be one of'),
        ({**FRESH, 'since': '2026-1-1'}, 'BAD_REQUEST', 400, '--since must be a date'),
        ({**FRESH, 'groups': ['nope']}, 'BAD_REQUEST', 400, 'unknown groups: nope'),
        ({**FRESH, 'tz': 'Mars/Base'}, 'BAD_REQUEST', 400, 'not a known time zone'),
        ({**FRESH, 'job': 'nojob'}, 'BAD_REQUEST', 400, 'job nojob is unknown'),
    ],
)
def test_each_error_has_its_code_and_status(
    stats_cache: wambatic.fetch.cache.Cache,
    variables: dict[str, typing.Any],
    code: str,
    status: int,
    message: str,
) -> None:
    async def scenario() -> dict[str, typing.Any]:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            return await gql(client, stats_query(''), {'input': variables})

    errors = asyncio.run(scenario())['errors']
    assert len(errors) == 1
    assert errors[0]['extensions'] == {'code': code, 'status': status}
    assert message in errors[0]['message']
    assert 'Traceback' not in json.dumps(errors)


def test_a_syntax_or_validation_error_is_bad_query(stats_cache: wambatic.fetch.cache.Cache) -> None:
    async def scenario() -> list[dict[str, typing.Any]]:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            syntax = await client.post('/graphql', json={'query': '{ version'})
            invalid = await client.post('/graphql', json={'query': '{ nothing }'})
            return [syntax.json()['errors'][0], invalid.json()['errors'][0]]

    for error in asyncio.run(scenario()):
        assert error['extensions'] == {'code': 'BAD_QUERY'}


def test_a_planted_exception_is_internal_without_traceback_or_token(
    monkeypatch: pytest.MonkeyPatch, stats_cache: wambatic.fetch.cache.Cache
) -> None:
    token = 'ghp_fake_token_for_tests'
    monkeypatch.setenv('GITHUB_TOKEN', token)

    def boom(result: object) -> dict[str, object]:
        raise RuntimeError(f'request failed with {token}')

    monkeypatch.setattr(wambatic.reports.base, 'result_to_dict', boom)
    messages: list[str] = []
    sink = loguru.logger.add(messages.append, level='ERROR', diagnose=False)

    async def scenario() -> str:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            response = await client.post(
                '/graphql', json={'query': stats_query(''), 'variables': {'input': FRESH}}
            )
            return response.text

    try:
        text = asyncio.run(scenario())
    finally:
        loguru.logger.remove(sink)
    error = json.loads(text)['errors'][0]
    assert error['message'] == 'internal error; see the server log'
    assert error['extensions'] == {'code': 'INTERNAL', 'status': 500}
    assert 'Traceback' not in text
    assert token not in text
    log = ''.join(messages)
    assert 'Unexpected error: request failed with ***' in log
    assert 'Traceback' in log
    assert token not in log


def test_a_mutation_over_get_is_refused(stats_cache: wambatic.fetch.cache.Cache) -> None:
    async def scenario() -> tuple[int, int]:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            mutation = await client.get(
                '/graphql',
                params={
                    'query': 'mutation { sync(input: {target: "org:octo-org"}) { id } }',
                },
            )
            query = await client.get('/graphql', params={'query': '{ version }'})
            return mutation.status_code, query.status_code

    mutation, query = asyncio.run(scenario())
    assert mutation in (400, 405)
    assert query == 200


def test_version_is_wambatics(stats_cache: wambatic.fetch.cache.Cache) -> None:
    async def scenario() -> tuple[typing.Any, str]:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            response = await client.post(
                '/graphql',
                content='{"query": "{ version }"}',
                headers={'Content-Type': 'application/json; charset=utf-8'},
            )
            return response.json(), response.headers['content-type']

    body, _ = asyncio.run(scenario())
    assert body == {'data': {'version': wambatic.version.VERSION}}


@pytest.mark.parametrize('content_type', ['text/plain', 'application/x-www-form-urlencoded', None])
def test_a_post_that_is_not_json_gets_415(
    stats_cache: wambatic.fetch.cache.Cache, content_type: str | None
) -> None:
    async def scenario() -> httpx.Response:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            headers = {} if content_type is None else {'Content-Type': content_type}
            return await client.post('/graphql', content='{ version }', headers=headers)

    response = asyncio.run(scenario())
    assert response.status_code == 415
    assert response.json() == {'error': 'POST /graphql needs Content-Type: application/json'}


def test_graphiql_is_served_to_a_browser(stats_cache: wambatic.fetch.cache.Cache) -> None:
    async def scenario() -> httpx.Response:
        async with tests.reports.test_web.serving(
            tests.reports.test_web.web_settings(), stats_cache
        ) as client:
            return await client.get('/graphql', headers={'Accept': 'text/html'})

    response = asyncio.run(scenario())
    assert response.status_code == 200
    assert 'graphiql' in response.text.lower()


def spec_schema() -> graphql.GraphQLSchema:
    text = SPEC.read_text()
    start = text.index('```graphql\n') + len('```graphql\n')
    sdl = text[start : text.index('```', start)]
    return graphql.build_schema('scalar JSON\n' + sdl)


def test_the_schema_equals_the_sdl_of_the_spec() -> None:
    printed = graphql.build_schema(strawberry.printer.print_schema(wambatic.reports.api.schema))
    spec = spec_schema()
    assert graphql.find_breaking_changes(spec, printed) == []
    assert graphql.find_breaking_changes(printed, spec) == []
    for name, expected in spec.type_map.items():
        if name.startswith('__') or not hasattr(expected, 'fields'):
            continue
        got = printed.type_map[name]
        assert sorted(got.fields) == sorted(expected.fields), name  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ('error', 'code', 'status'),
    [
        (wambatic.reports.errors.UsageError('x'), 'BAD_REQUEST', 400),
        (wambatic.fetch.errors.NotFoundError('x'), 'NOT_FOUND', 404),
        (wambatic.stats.errors.EmptySubjectError('x'), 'NOT_FOUND', 404),
        (wambatic.fetch.errors.FetchError('x'), 'UPSTREAM', 502),
        (RuntimeError('x'), 'INTERNAL', 500),
    ],
)
def test_the_error_extension_maps_each_exception_class(
    error: Exception, code: str, status: int
) -> None:
    converted = wambatic.reports.api.WambaticErrors.convert(
        graphql.GraphQLError('wrapped', original_error=error)
    )
    assert converted.extensions == {'code': code, 'status': status}
