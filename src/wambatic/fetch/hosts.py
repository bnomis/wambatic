import dataclasses
import datetime
import re
import types

import wambatic.fetch.errors

# The oldest Enterprise Server release GitHub supported on 2026-11-02; a wambatic release raises it.
MIN_SERVER_VERSION = (3, 19)

# The "Closing down date" of each supported release on GitHub's All releases page
# (https://docs.github.com/en/enterprise-server@latest/admin/all-releases), read on 2026-11-04.
# A test fails once MIN_SERVER_VERSION's date has passed, as the reminder to raise it.
CLOSING_DOWN_DATES = types.MappingProxyType(
    {
        (3, 19): datetime.date(2026, 12, 9),
        (3, 20): datetime.date(2027, 3, 17),
        (3, 21): datetime.date(2027, 6, 11),
        (3, 22): datetime.date(2027, 9, 8),
    }
)

HOST_NAME = re.compile(r'[a-z0-9.-]+')
VERSION = re.compile(r'(\d+)\.(\d+)(?:\.|$)')


@dataclasses.dataclass(frozen=True, slots=True)
class GitHubHost:
    name: str
    rest_url: str
    graphql_url: str

    @property
    def is_dotcom(self) -> bool:
        return self.name == 'github.com'


GITHUB_COM = GitHubHost(
    name='github.com',
    rest_url='https://api.github.com',
    graphql_url='https://api.github.com/graphql',
)


def parse_host(name: str) -> GitHubHost:
    """The addresses of a host name already checked by the settings.

    Raises:
        InvalidRequestError: `name` fails the settings' host rules.
    """
    if name == 'github.com':
        return GITHUB_COM
    host, separator, port = name.partition(':')
    port_ok = not separator or (port.isascii() and port.isdigit() and 1 <= int(port) <= 65535)
    if not (HOST_NAME.fullmatch(host) and '.' in host and port_ok):
        raise wambatic.fetch.errors.InvalidRequestError('Not a GitHub host name')
    return GitHubHost(
        name=name,
        rest_url=f'https://{name}/api/v3',
        graphql_url=f'https://{name}/api/graphql',
    )


def parse_server_version(text: str) -> tuple[int, int]:
    """(3, 19) from '3.19.2'.

    Raises:
        ServerVersionError: `text` does not start with two dot-separated integers.
    """
    match = VERSION.match(text)
    if match is None:
        raise wambatic.fetch.errors.ServerVersionError(None, text or None, MIN_SERVER_VERSION)
    return int(match.group(1)), int(match.group(2))
