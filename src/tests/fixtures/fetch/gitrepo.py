"""Local git repositories for tests: a working copy pushing to a bare remote that `Git` clones."""

import pathlib
import subprocess

import pytest


def isolate(monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep the user's git configuration out of a test and fix the commit identity and dates."""
    monkeypatch.setenv('GIT_CONFIG_GLOBAL', '/dev/null')
    monkeypatch.setenv('GIT_CONFIG_NOSYSTEM', '1')
    monkeypatch.setenv('GIT_AUTHOR_NAME', 'Tester')
    monkeypatch.setenv('GIT_AUTHOR_EMAIL', 'tester@example.com')
    monkeypatch.setenv('GIT_COMMITTER_NAME', 'Tester')
    monkeypatch.setenv('GIT_COMMITTER_EMAIL', 'tester@example.com')
    monkeypatch.setenv('GIT_AUTHOR_DATE', '2026-01-02T03:04:05+02:00')
    monkeypatch.setenv('GIT_COMMITTER_DATE', '2026-01-02T03:04:05+02:00')


def run_git(cwd: pathlib.Path, *args: str) -> str:
    result = subprocess.run(
        ['git', *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


class LocalRemote:
    """A working repository pushing to a local bare remote that `Git` clones from."""

    def __init__(self, root: pathlib.Path, repo: str) -> None:
        self.repo = repo
        self.remote_root = root / 'remotes'
        self.remote = self.remote_root / f'{repo}.git'
        self.work = root / 'work'

    def create(self) -> None:
        self.remote.parent.mkdir(parents=True)
        run_git(self.remote_root, 'init', '--bare', '-b', 'main', str(self.remote))
        self.work.mkdir()
        run_git(self.work, 'init', '-b', 'main')
        run_git(self.work, 'remote', 'add', 'origin', str(self.remote))

    def url_for(self, repo: str) -> str:
        return str(self.remote_root / f'{repo}.git')

    def write(self, name: str, text: str | bytes) -> None:
        path = self.work / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(text, bytes):
            path.write_bytes(text)
        else:
            path.write_text(text)

    def commit(self, message: str = 'change') -> str:
        run_git(self.work, 'add', '-A')
        run_git(self.work, 'commit', '-m', message)
        return run_git(self.work, 'rev-parse', 'HEAD')

    def add_and_push(self, name: str, text: str) -> None:
        self.write(name, text)
        self.commit('later')
        self.push()

    def push(self, *refspecs: str) -> None:
        run_git(self.work, 'push', '--force', 'origin', *(refspecs or ('main',)))
