import os
import subprocess

import wambatic.fetch.errors
import wambatic.fetch.hosts

ENTERPRISE_VARIABLES = ('GH_ENTERPRISE_TOKEN', 'GITHUB_ENTERPRISE_TOKEN')


def fetch_token(host: wambatic.fetch.hosts.GitHubHost = wambatic.fetch.hosts.GITHUB_COM) -> str:
    """The token for `host`, as the `gh` CLI finds it.

    github.com: GITHUB_TOKEN, else `gh auth token`. An Enterprise host: GH_ENTERPRISE_TOKEN,
    else GITHUB_ENTERPRISE_TOKEN, else `gh auth token --hostname <host.name>`; GITHUB_TOKEN is
    never read, so a github.com token is not sent to another server.

    Raises:
        AuthError: no token is found.
    """
    variables = ('GITHUB_TOKEN',) if host.is_dotcom else ENTERPRISE_VARIABLES
    for variable in variables:
        token = os.environ.get(variable, '').strip()
        if token:
            return token
    message = (
        wambatic.fetch.errors.NO_TOKEN_MESSAGE
        if host.is_dotcom
        else (
            f'No GitHub token found for {host.name}: set GH_ENTERPRISE_TOKEN '
            f'or run `gh auth login --hostname {host.name}`'
        )
    )
    command = ['gh', 'auth', 'token']
    if not host.is_dotcom:
        command += ['--hostname', host.name]
    try:
        # auditme: accept[subprocess-without-memoisation] once per sync; a cache outlives gh auth
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
    except OSError, UnicodeDecodeError, subprocess.TimeoutExpired:
        raise wambatic.fetch.errors.AuthError(message) from None
    token = result.stdout.strip()
    if result.returncode == 0 and token:
        return token
    raise wambatic.fetch.errors.AuthError(message)


def redact(text: str, token: str) -> str:
    """`text` with every occurrence of `token` replaced by `***`."""
    if not token:
        return text
    return text.replace(token, '***')
