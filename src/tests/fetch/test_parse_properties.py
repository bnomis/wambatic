"""Property tests for the GraphQL and REST parsers and the small helpers beneath them.

Valid shapes parse to the record they describe; a field of the wrong type raises the fetch domain
error (`GraphQLError`) and nothing else.
"""

import collections.abc
import datetime

import hypothesis
import hypothesis.strategies
import pytest

import tests.fixtures.constants
import wambatic.fetch.base
import wambatic.fetch.errors

INSTANTS = hypothesis.strategies.datetimes(
    min_value=datetime.datetime(2000, 1, 1),
    max_value=datetime.datetime(2100, 1, 1),
    timezones=hypothesis.strategies.just(datetime.UTC),
).map(lambda value: value.replace(microsecond=0))
COUNTS = hypothesis.strategies.integers(0, 10_000_000)
NAMES = hypothesis.strategies.text(min_size=1, max_size=30)
WRONG_TYPES = hypothesis.strategies.one_of(
    hypothesis.strategies.none(),
    hypothesis.strategies.lists(hypothesis.strategies.integers(), max_size=3),
    hypothesis.strategies.dictionaries(
        hypothesis.strategies.text(), hypothesis.strategies.none(), max_size=2
    ),
)
NON_OBJECTS = hypothesis.strategies.one_of(
    hypothesis.strategies.none(),
    hypothesis.strategies.booleans(),
    hypothesis.strategies.integers(),
    hypothesis.strategies.text(),
    hypothesis.strategies.lists(hypothesis.strategies.integers(), max_size=3),
)
REPO = 'octocat/Hello-World'
SAME_EXAMPLES = hypothesis.settings(max_examples=20, deadline=10000)


def stamp(value: datetime.datetime) -> str:
    return value.strftime('%Y-%m-%dT%H:%M:%SZ')


def pull_request_node(created: datetime.datetime, number: int) -> dict[str, object]:
    return {
        'number': number,
        'state': 'OPEN',
        'createdAt': stamp(created),
        'updatedAt': stamp(created),
        'mergedAt': None,
        'closedAt': None,
        'additions': 1,
        'deletions': 2,
        'author': {'login': 'octocat'},
        'reviews': {'nodes': []},
        'labels': {'nodes': []},
        'commits': {'nodes': []},
    }


def issue_node(created: datetime.datetime, number: int) -> dict[str, object]:
    return {
        'number': number,
        'state': 'OPEN',
        'createdAt': stamp(created),
        'updatedAt': stamp(created),
        'closedAt': None,
        'author': None,
    }


def release_node(created: datetime.datetime, tag: str) -> dict[str, object]:
    return {
        'tagName': tag,
        'createdAt': stamp(created),
        'publishedAt': stamp(created),
        'isDraft': False,
        'isPrerelease': False,
    }


def workflow_run_node(created: datetime.datetime, run_id: int) -> dict[str, object]:
    return {
        'id': run_id,
        'name': 'ci',
        'path': '.github/workflows/ci.yml',
        'event': 'push',
        'head_branch': 'main',
        'status': 'completed',
        'conclusion': 'success',
        'created_at': stamp(created),
        'updated_at': stamp(created),
        'run_started_at': None,
    }


def history_node(authored: datetime.datetime, oid: str) -> dict[str, object]:
    return {
        'oid': oid,
        'authoredDate': stamp(authored),
        'author': None,
        'additions': 3,
        'deletions': 4,
        'parents': {'totalCount': 1},
    }


def compare_node(authored: datetime.datetime, sha: str) -> dict[str, object]:
    return {
        'sha': sha,
        'commit': {'author': {'date': stamp(authored)}},
        'author': None,
        'parents': [{'sha': 'p'}],
    }


def repo_node(name: str, updated: datetime.datetime) -> dict[str, object]:
    return {
        'nameWithOwner': name,
        'defaultBranchRef': None,
        'pushedAt': None,
        'updatedAt': stamp(updated),
        'pullRequests': {'nodes': []},
        'issues': {'nodes': []},
        'releases': {'totalCount': 0, 'nodes': []},
        'stargazerCount': 1,
        'forkCount': 2,
        'watchers': {'totalCount': 3},
        'languages': None,
    }


def assert_domain_error(parse: collections.abc.Callable[[], object]) -> None:
    with pytest.raises(wambatic.fetch.errors.GraphQLError):
        parse()


def broken(node: dict[str, object], key: str, junk: object) -> dict[str, object]:
    return {**node, key: junk}


@SAME_EXAMPLES
@hypothesis.given(value=INSTANTS)
def test_timestamp_reads_what_isoformat_writes(value: datetime.datetime) -> None:
    assert wambatic.fetch.base.timestamp(value.isoformat(), 'when') == value
    assert wambatic.fetch.base.timestamp(stamp(value), 'when') == value


@SAME_EXAMPLES
@hypothesis.given(value=hypothesis.strategies.text(max_size=40))
def test_timestamp_is_aware_or_a_domain_error(value: str) -> None:
    try:
        parsed = wambatic.fetch.base.timestamp(value, 'when')
    except wambatic.fetch.errors.GraphQLError:
        return
    assert parsed.utcoffset() == datetime.timedelta(0)


@SAME_EXAMPLES
@hypothesis.given(value=INSTANTS)
def test_timestamp_refuses_a_naive_time(value: datetime.datetime) -> None:
    assert_domain_error(
        lambda: wambatic.fetch.base.timestamp(value.replace(tzinfo=None).isoformat(), 'when')
    )


@SAME_EXAMPLES
@hypothesis.given(value=WRONG_TYPES | hypothesis.strategies.integers())
def test_timestamp_refuses_a_non_string(value: object) -> None:
    assert_domain_error(lambda: wambatic.fetch.base.timestamp(value, 'when'))


@SAME_EXAMPLES
@hypothesis.given(login=NAMES, bot=hypothesis.strategies.booleans())
def test_actor_login_marks_a_bot(login: str, bot: bool) -> None:
    value = {'login': login, '__typename': 'Bot'} if bot else {'login': login}
    expected = f'{login}{wambatic.fetch.base.BOT_SUFFIX}' if bot else login
    assert wambatic.fetch.base.actor_login(value, 'author') == expected


@SAME_EXAMPLES
@hypothesis.given(value=NON_OBJECTS.filter(lambda value: value is not None))
def test_actor_login_refuses_a_non_object(value: object) -> None:
    assert wambatic.fetch.base.actor_login(None, 'author') is None
    assert_domain_error(lambda: wambatic.fetch.base.actor_login(value, 'author'))


@SAME_EXAMPLES
@hypothesis.given(count=COUNTS)
def test_count_of_probe_reads_a_count(count: int) -> None:
    assert wambatic.fetch.base.count_of_probe(str(count)) == count


@SAME_EXAMPLES
@hypothesis.given(probe=hypothesis.strategies.none() | hypothesis.strategies.text(max_size=40))
def test_count_of_probe_never_fails(probe: str | None) -> None:
    result = wambatic.fetch.base.count_of_probe(probe)
    assert result is None or result >= 0


@SAME_EXAMPLES
@hypothesis.given(
    created=INSTANTS,
    number=COUNTS,
    key=hypothesis.strategies.sampled_from(
        ('number', 'state', 'createdAt', 'updatedAt', 'additions', 'deletions')
    ),
    junk=WRONG_TYPES,
)
def test_parse_pull_request(
    created: datetime.datetime, number: int, key: str, junk: object
) -> None:
    node = pull_request_node(created, number)
    parsed = wambatic.fetch.base.parse_pull_request(REPO, node)
    assert (parsed.number, parsed.created_at, parsed.author_login) == (number, created, 'octocat')
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_pull_request(REPO, broken(node, key, junk))
    )


@SAME_EXAMPLES
@hypothesis.given(
    created=INSTANTS,
    number=COUNTS,
    key=hypothesis.strategies.sampled_from(('number', 'state', 'createdAt', 'updatedAt')),
    junk=WRONG_TYPES,
)
def test_parse_issue(created: datetime.datetime, number: int, key: str, junk: object) -> None:
    node = issue_node(created, number)
    parsed = wambatic.fetch.base.parse_issue(REPO, node)
    assert (parsed.number, parsed.created_at, parsed.author_login) == (number, created, None)
    assert_domain_error(lambda: wambatic.fetch.base.parse_issue(REPO, broken(node, key, junk)))


@SAME_EXAMPLES
@hypothesis.given(
    created=INSTANTS,
    tag=NAMES,
    key=hypothesis.strategies.sampled_from(('tagName', 'createdAt')),
    junk=WRONG_TYPES,
)
def test_parse_release(created: datetime.datetime, tag: str, key: str, junk: object) -> None:
    node = release_node(created, tag)
    parsed = wambatic.fetch.base.parse_release(REPO, node)
    assert parsed is not None
    assert (parsed.tag_name, parsed.published_at) == (tag, created)
    assert wambatic.fetch.base.parse_release(REPO, {**node, 'isDraft': True}) is None
    assert_domain_error(lambda: wambatic.fetch.base.parse_release(REPO, broken(node, key, junk)))


@SAME_EXAMPLES
@hypothesis.given(
    created=INSTANTS,
    run_id=COUNTS,
    key=hypothesis.strategies.sampled_from(tests.fixtures.constants.WORKFLOW_RUN_REQUIRED_FIELDS),
    junk=WRONG_TYPES,
)
def test_parse_workflow_run(
    created: datetime.datetime, run_id: int, key: str, junk: object
) -> None:
    node = workflow_run_node(created, run_id)
    parsed = wambatic.fetch.base.parse_workflow_run(REPO, node)
    assert (parsed.id, parsed.created_at, parsed.run_attempt) == (run_id, created, 1)
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_workflow_run(REPO, broken(node, key, junk))
    )


@SAME_EXAMPLES
@hypothesis.given(starred=INSTANTS, user=NAMES, junk=WRONG_TYPES)
def test_parse_star_edge(starred: datetime.datetime, user: str, junk: object) -> None:
    edge: dict[str, object] = {'starredAt': stamp(starred), 'node': {'id': user}}
    parsed = wambatic.fetch.base.parse_star_edge(REPO, edge)
    assert (parsed.user_id, parsed.starred_at) == (user, starred)
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_star_edge(REPO, broken(edge, 'starredAt', junk))
    )
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_star_edge(REPO, broken(edge, 'node', junk))
    )


@SAME_EXAMPLES
@hypothesis.given(
    created=INSTANTS,
    fork_id=COUNTS,
    key=hypothesis.strategies.sampled_from(('id', 'created_at')),
    junk=WRONG_TYPES,
)
def test_parse_fork(created: datetime.datetime, fork_id: int, key: str, junk: object) -> None:
    node = {'id': fork_id, 'created_at': stamp(created)}
    parsed = wambatic.fetch.base.parse_fork(REPO, node)
    assert (parsed.id, parsed.created_at) == (fork_id, created)
    assert_domain_error(lambda: wambatic.fetch.base.parse_fork(REPO, broken(node, key, junk)))


@SAME_EXAMPLES
@hypothesis.given(
    authored=INSTANTS,
    oid=NAMES,
    key=hypothesis.strategies.sampled_from(
        ('oid', 'authoredDate', 'additions', 'deletions', 'parents')
    ),
    junk=WRONG_TYPES,
)
def test_parse_history_node(authored: datetime.datetime, oid: str, key: str, junk: object) -> None:
    node = history_node(authored, oid)
    parsed = wambatic.fetch.base.parse_history_node(REPO, node)
    assert (parsed.oid, parsed.authored_at, parsed.is_merge) == (oid, authored, False)
    assert wambatic.fetch.base.parse_history_node(
        REPO, {**node, 'parents': {'totalCount': 2}}
    ).is_merge
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_history_node(REPO, broken(node, key, junk))
    )


@SAME_EXAMPLES
@hypothesis.given(
    authored=INSTANTS,
    sha=NAMES,
    key=hypothesis.strategies.sampled_from(('sha', 'commit', 'parents')),
    junk=WRONG_TYPES,
)
def test_parse_compare_commit(
    authored: datetime.datetime, sha: str, key: str, junk: object
) -> None:
    node = compare_node(authored, sha)
    parsed = wambatic.fetch.base.parse_compare_commit(node)
    assert (parsed.oid, parsed.authored_at, parsed.is_merge) == (sha, authored, False)
    hypothesis.assume(not (key == 'parents' and isinstance(junk, list)))
    assert_domain_error(lambda: wambatic.fetch.base.parse_compare_commit(broken(node, key, junk)))


@SAME_EXAMPLES
@hypothesis.given(
    updated=INSTANTS,
    name=NAMES,
    key=hypothesis.strategies.sampled_from(
        ('nameWithOwner', 'updatedAt', 'stargazerCount', 'forkCount', 'watchers', 'releases')
    ),
    junk=WRONG_TYPES,
)
def test_parse_repo(updated: datetime.datetime, name: str, key: str, junk: object) -> None:
    node = repo_node(name, updated)
    parsed = wambatic.fetch.base.parse_repo(node)
    assert (parsed.name_with_owner, parsed.updated_at, parsed.languages) == (name, updated, ())
    assert_domain_error(lambda: wambatic.fetch.base.parse_repo(broken(node, key, junk)))


@SAME_EXAMPLES
@hypothesis.given(
    languages=hypothesis.strategies.lists(hypothesis.strategies.tuples(NAMES, COUNTS), max_size=8),
    junk=WRONG_TYPES.filter(lambda value: value is not None),
)
def test_parse_languages(languages: list[tuple[str, int]], junk: object) -> None:
    edges = [{'node': {'name': name}, 'size': size} for name, size in languages]
    total = sum(size for _, size in languages)
    assert wambatic.fetch.base.parse_languages({'edges': edges, 'totalSize': total}) == (
        tuple(languages),
        total,
    )
    assert wambatic.fetch.base.parse_languages(None) == ((), 0)
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_languages({'edges': edges, 'totalSize': junk})
    )
    assert_domain_error(
        lambda: wambatic.fetch.base.parse_languages({'edges': str(junk), 'totalSize': total})
    )


@SAME_EXAMPLES
@hypothesis.given(node=NON_OBJECTS)
def test_every_parser_refuses_a_non_object(node: object) -> None:
    for parse in (
        wambatic.fetch.base.parse_repo,
        wambatic.fetch.base.parse_compare_commit,
    ):
        assert_domain_error(lambda parse=parse: parse(node))  # type: ignore[misc]
    for parse_in_repo in (
        wambatic.fetch.base.parse_pull_request,
        wambatic.fetch.base.parse_issue,
        wambatic.fetch.base.parse_release,
        wambatic.fetch.base.parse_workflow_run,
        wambatic.fetch.base.parse_star_edge,
        wambatic.fetch.base.parse_fork,
        wambatic.fetch.base.parse_history_node,
    ):
        assert_domain_error(lambda parse_in_repo=parse_in_repo: parse_in_repo(REPO, node))  # type: ignore[misc]
