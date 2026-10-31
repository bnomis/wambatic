"""Tests for bin/record-fixtures.py, run against a fake upstream that replays the recordings."""

import importlib.util
import io
import json
import pathlib
import re
import subprocess
import types
import typing
import urllib.parse
import urllib.request

import pytest

import tests.fixtures.fetch.recorded
import tests.fixtures.fetch.upstream
import wambatic.fetch.queries

TOKEN = 'test-token-value'
QUERY_NAME = re.compile(r'query (\w+)')
RECORDED_BY_QUERY = {
    'CommitCounts': tests.fixtures.fetch.recorded.COMMIT_COUNTS_OK,
    'CommitHistory': tests.fixtures.fetch.recorded.COMMIT_HISTORY_OK,
    'Issues': tests.fixtures.fetch.recorded.ISSUES_OK,
    'OwnerRepositories': tests.fixtures.fetch.recorded.OWNER_REPOSITORIES_OK,
    'PullRequestReviews': tests.fixtures.fetch.recorded.BOT_REVIEWS_OK,
    'PullRequests': tests.fixtures.fetch.recorded.PULL_REQUESTS_OK,
    'Releases': tests.fixtures.fetch.recorded.RELEASES_OK,
    'Repository': tests.fixtures.fetch.recorded.REPOSITORY_OK,
    'Stargazers': tests.fixtures.fetch.recorded.STARGAZERS_OK,
}
RECORDED_BY_PATH = {
    '/repos/bnomis/ab2cb/forks': tests.fixtures.fetch.recorded.FORKS_OK,
    '/repos/miguelangellv/ha-gas-station-spain/actions/runs': (
        tests.fixtures.fetch.recorded.WORKFLOW_RUNS_OK
    ),
    '/repos/octocat/Hello-World': tests.fixtures.fetch.recorded.REPO,
    '/users/github': tests.fixtures.fetch.recorded.ORGANIZATION_OK,
    '/users/octocat': tests.fixtures.fetch.recorded.USER_OK,
}


def plain(value: object) -> object:
    """`value` with its read-only containers turned into dicts and lists."""
    return json.loads(json.dumps(value, default=dict))


def sent_json(request: urllib.request.Request) -> dict[str, typing.Any]:
    assert isinstance(request.data, bytes)
    payload = json.loads(request.data)
    assert isinstance(payload, dict)
    return payload


class FakeResponse(io.BytesIO):
    def __init__(self, body: object, headers: dict[str, str]) -> None:
        super().__init__(json.dumps(body, default=dict).encode())
        self.headers = dict(headers)

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()


class FakeUpstream:
    """Stands in for `urllib.request.urlopen`: answers from the recordings, keeps each request."""

    def __init__(self) -> None:
        self.requests: list[urllib.request.Request] = []

    def __call__(self, request: urllib.request.Request, timeout: float) -> FakeResponse:
        self.requests.append(request)
        path = urllib.parse.urlparse(request.full_url).path
        if path == '/graphql':
            assert request.data is not None
            name = QUERY_NAME.search(sent_json(request)['query'])
            assert name is not None
            return FakeResponse(RECORDED_BY_QUERY[name.group(1)], {})
        if tests.fixtures.fetch.upstream.COMPARE_PATH.fullmatch(path):
            return FakeResponse(tests.fixtures.fetch.recorded.COMPARE_AHEAD, {})
        run = tests.fixtures.fetch.upstream.RUNS_PATH.fullmatch(path)
        if run is not None and run.group('id'):
            return FakeResponse(tests.fixtures.fetch.recorded.WORKFLOW_RUN_OK, {})
        headers = {'ETag': tests.fixtures.fetch.recorded.REPO_ETAG}
        return FakeResponse(RECORDED_BY_PATH[path], headers if path.endswith('Hello-World') else {})


@pytest.fixture
def upstream(monkeypatch: pytest.MonkeyPatch) -> FakeUpstream:
    fake = FakeUpstream()
    monkeypatch.setattr(urllib.request, 'urlopen', fake)
    return fake


@pytest.fixture
def formatted(
    monkeypatch: pytest.MonkeyPatch, record_fixtures: types.ModuleType
) -> list[list[str]]:
    """The `ruff format` commands the script runs, which are not run for real."""
    commands: list[list[str]] = []

    def run(command: list[str], check: bool) -> None:
        commands.append(command)

    monkeypatch.setattr(record_fixtures.subprocess, 'run', run)
    return commands


def test_send_with_params_and_a_body(
    upstream: FakeUpstream, record_fixtures: types.ModuleType
) -> None:
    recorder = record_fixtures.Recorder(TOKEN)
    body, headers = recorder.send(
        'POST', '/users/octocat', {'page': '2', 'per_page': '5'}, {'query': 'x'}
    )
    (request,) = upstream.requests
    assert request.full_url == f'{record_fixtures.API}/users/octocat?page=2&per_page=5'
    assert request.get_method() == 'POST'
    assert sent_json(request) == {'query': 'x'}
    assert request.get_header('Authorization') == f'Bearer {TOKEN}'
    assert str(request.get_header('User-agent')).startswith('wambatic/')
    assert body == plain(tests.fixtures.fetch.recorded.USER_OK)
    assert headers == {}


def test_send_without_params_or_a_body(
    upstream: FakeUpstream, record_fixtures: types.ModuleType
) -> None:
    recorder = record_fixtures.Recorder(TOKEN)
    _, headers = recorder.send('GET', '/repos/octocat/Hello-World')
    (request,) = upstream.requests
    assert request.full_url == f'{record_fixtures.API}/repos/octocat/Hello-World'
    assert request.data is None
    assert headers == {'ETag': tests.fixtures.fetch.recorded.REPO_ETAG}


@pytest.mark.parametrize('failure', [OSError('refused'), json.JSONDecodeError('bad', '', 0)])
def test_send_reports_a_failed_request_in_one_error(
    monkeypatch: pytest.MonkeyPatch, record_fixtures: types.ModuleType, failure: Exception
) -> None:
    def fail(request: urllib.request.Request, timeout: float) -> None:
        raise failure

    monkeypatch.setattr(urllib.request, 'urlopen', fail)
    with pytest.raises(record_fixtures.RecordingError, match='GET .*/users/octocat failed'):
        record_fixtures.Recorder(TOKEN).send('GET', '/users/octocat')


def test_rest_returns_the_body_alone(
    upstream: FakeUpstream, record_fixtures: types.ModuleType
) -> None:
    assert record_fixtures.Recorder(TOKEN).rest('/users/github') == plain(
        tests.fixtures.fetch.recorded.ORGANIZATION_OK
    )


def test_graphql_returns_the_body(
    upstream: FakeUpstream, record_fixtures: types.ModuleType
) -> None:
    body = record_fixtures.Recorder(TOKEN).graphql(
        wambatic.fetch.queries.REPOSITORY, owner='octocat', name='Hello-World'
    )
    assert body == plain(tests.fixtures.fetch.recorded.REPOSITORY_OK)
    sent = sent_json(upstream.requests[0])
    assert sent['variables'] == {'owner': 'octocat', 'name': 'Hello-World'}


@pytest.mark.parametrize('body', [{'errors': [{'message': 'nope'}]}, ['x']])
def test_graphql_refuses_an_error_body(
    monkeypatch: pytest.MonkeyPatch, record_fixtures: types.ModuleType, body: object
) -> None:
    monkeypatch.setattr(urllib.request, 'urlopen', lambda request, timeout: FakeResponse(body, {}))
    with pytest.raises(RuntimeError, match='GraphQL error'):
        record_fixtures.Recorder(TOKEN).graphql('query X { x }')


def test_pick_keeps_the_fields_present(record_fixtures: types.ModuleType) -> None:
    assert record_fixtures.pick({'a': 1, 'b': 2, 'c': 3}, ('c', 'a', 'z')) == {'c': 3, 'a': 1}
    with pytest.raises(RuntimeError, match='Expected an object'):
        record_fixtures.pick(['a'], ('a',))


def compare_node(**changes: object) -> dict[str, object]:
    node: dict[str, object] = {
        'sha': 'abc',
        'extra': 1,
        'commit': {'author': {'date': '2026-10-01T09:00:00Z', 'name': 'dropped'}},
        'author': {'login': 'octocat', 'id': 1},
        'parents': [{'sha': 'p1', 'url': 'dropped'}],
    }
    return {**node, **changes}


def test_compare_commit_trims_to_what_the_parser_reads(
    record_fixtures: types.ModuleType,
) -> None:
    assert record_fixtures.compare_commit(compare_node()) == {
        'sha': 'abc',
        'commit': {'author': {'date': '2026-10-01T09:00:00Z'}},
        'author': {'login': 'octocat'},
        'parents': [{'sha': 'p1'}],
    }


def test_compare_commit_keeps_a_deleted_account_as_none(
    record_fixtures: types.ModuleType,
) -> None:
    assert record_fixtures.compare_commit(compare_node(author=None))['author'] is None


@pytest.mark.parametrize('changes', [{'commit': None}, {'parents': 'p1'}])
def test_compare_commit_refuses_an_unexpected_shape(
    record_fixtures: types.ModuleType, changes: dict[str, object]
) -> None:
    with pytest.raises(RuntimeError, match='Unexpected compare commit'):
        record_fixtures.compare_commit(compare_node(**changes))


def test_write_fixtures_writes_then_formats(
    tmp_path: pathlib.Path, record_fixtures: types.ModuleType, formatted: list[list[str]]
) -> None:
    out = tmp_path / 'recorded.py'
    record_fixtures.write_fixtures('X = 1\n', out)
    assert out.read_text() == 'X = 1\n'
    assert formatted == [['ruff', 'format', '--quiet', str(out)]]


def test_write_fixtures_reports_an_unwritable_file(
    tmp_path: pathlib.Path, record_fixtures: types.ModuleType
) -> None:
    with pytest.raises(record_fixtures.RecordingError, match='cannot write'):
        record_fixtures.write_fixtures('X = 1\n', tmp_path / 'missing' / 'recorded.py')


@pytest.mark.parametrize(
    'failure', [FileNotFoundError('ruff'), subprocess.CalledProcessError(1, 'ruff')]
)
def test_write_fixtures_reports_a_failed_format(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    record_fixtures: types.ModuleType,
    failure: Exception,
) -> None:
    def fail(command: list[str], check: bool) -> None:
        raise failure

    monkeypatch.setattr(record_fixtures.subprocess, 'run', fail)
    with pytest.raises(record_fixtures.RecordingError, match='cannot format'):
        record_fixtures.write_fixtures('X = 1\n', tmp_path / 'recorded.py')


def test_main_records_to_the_named_file(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    upstream: FakeUpstream,
    formatted: list[list[str]],
    record_fixtures: types.ModuleType,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', TOKEN)
    out = tmp_path / 'recorded.py'
    assert record_fixtures.main(['--out', str(out)]) == 0
    assert capsys.readouterr().out.strip() == str(out)
    assert formatted == [['ruff', 'format', '--quiet', str(out)]]
    text = out.read_text()
    assert TOKEN not in text
    assert all(
        request.get_header('Authorization') == f'Bearer {TOKEN}' for request in upstream.requests
    )
    spec = importlib.util.spec_from_file_location('written_recording', out)
    assert spec is not None
    assert spec.loader is not None
    written = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(written)
    for name in (
        'COMMIT_COUNTS_OK',
        'COMMIT_HISTORY_OK',
        'COMPARE_AHEAD',
        'FORKS_OK',
        'ORGANIZATION_OK',
        'REPO',
        'REPO_ETAG',
        'REPOSITORY_OK',
        'USER_OK',
        'WORKFLOW_RUN_OK',
        'WORKFLOW_RUNS_OK',
    ):
        assert getattr(written, name) == getattr(tests.fixtures.fetch.recorded, name), name
    assert written.QUERY_SHA256 == tests.fixtures.fetch.recorded.QUERY_SHA256


def test_main_reports_a_failure_in_one_line(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    upstream: FakeUpstream,
    formatted: list[list[str]],
    record_fixtures: types.ModuleType,
) -> None:
    monkeypatch.setenv('GITHUB_TOKEN', TOKEN)
    assert record_fixtures.main(['--out', str(tmp_path / 'missing' / 'recorded.py')]) == 1
    captured = capsys.readouterr()
    assert captured.err.startswith('record-fixtures: cannot write')
    assert TOKEN not in captured.err
    assert captured.out == ''
