import pytest

import tests.fixtures.constants
import wambatic.fetch.errors
import wambatic.fetch.hosts


def test_github_com() -> None:
    host = wambatic.fetch.hosts.parse_host('github.com')
    assert host is wambatic.fetch.hosts.GITHUB_COM
    assert host.rest_url == 'https://api.github.com'
    assert host.graphql_url == 'https://api.github.com/graphql'
    assert host.is_dotcom


def test_enterprise_host() -> None:
    host = wambatic.fetch.hosts.parse_host('ghe.example.com')
    assert host.rest_url == 'https://ghe.example.com/api/v3'
    assert host.graphql_url == 'https://ghe.example.com/api/graphql'
    assert not host.is_dotcom


def test_enterprise_host_with_port() -> None:
    host = wambatic.fetch.hosts.parse_host('ghe.example.com:8443')
    assert host.graphql_url == 'https://ghe.example.com:8443/api/graphql'


@pytest.mark.parametrize(
    'name',
    ['', 'nodot', 'https://ghe.example.com', 'ghe.example.com/x', 'a.b:0', 'a.b:65536', 'A.b'],
)
def test_refused_names(name: str) -> None:
    with pytest.raises(wambatic.fetch.errors.InvalidRequestError):
        wambatic.fetch.hosts.parse_host(name)


@pytest.mark.parametrize(
    tests.fixtures.constants.DURATION_CASE_FIELDS,
    [('3.19.2', (3, 19)), ('3.19', (3, 19)), ('3.9.0-rc1', (3, 9))],
)
def test_parse_server_version(text: str, expected: tuple[int, int]) -> None:
    assert wambatic.fetch.hosts.parse_server_version(text) == expected


@pytest.mark.parametrize('text', ['3', 'x.y', '', '3.x', '3.19x'])
def test_unparsable_versions(text: str) -> None:
    with pytest.raises(wambatic.fetch.errors.ServerVersionError):
        wambatic.fetch.hosts.parse_server_version(text)
