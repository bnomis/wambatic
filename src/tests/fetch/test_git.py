import asyncio
import base64
import collections.abc
import pathlib
import stat
import subprocess

import pytest

import wambatic.fetch.errors
import wambatic.fetch.git
import wambatic.fetch.hosts

TOKEN = 'ghp_secrettoken123'
REPO = 'octo/widgets'


@pytest.fixture(autouse=True)
def isolated_git(monkeypatch: pytest.MonkeyPatch) -> None:
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


class Upstream:
    """A working repository pushing to a local bare remote that `Git` clones from."""

    def __init__(self, root: pathlib.Path) -> None:
        self.remote_root = root / 'remotes'
        self.remote = self.remote_root / f'{REPO}.git'
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


@pytest.fixture
def upstream(tmp_path: pathlib.Path) -> Upstream:
    made = Upstream(tmp_path)
    made.create()
    return made


def make_git(
    upstream: Upstream,
    tmp_path: pathlib.Path,
    git_class: type[wambatic.fetch.git.Git] = wambatic.fetch.git.Git,
) -> wambatic.fetch.git.Git:
    return git_class(
        TOKEN,
        wambatic.fetch.hosts.GITHUB_COM,
        tmp_path / 'clones',
        url_for=upstream.url_for,
    )


class Recording(wambatic.fetch.git.Git):
    calls: list[list[str]]

    async def run(
        self,
        repo: str,
        verb: str,
        args: collections.abc.Sequence[str],
        stdin: bytes | None = None,
    ) -> wambatic.fetch.git.GitResult:
        if not hasattr(self, 'calls'):
            self.calls = []
        self.calls.append(self.arguments(args))
        return await super().run(repo, verb, args, stdin)


def test_clone_url() -> None:
    host = wambatic.fetch.hosts.parse_host('ghe.example.com')
    assert (
        wambatic.fetch.git.clone_url(wambatic.fetch.hosts.GITHUB_COM, 'a/b')
        == 'https://github.com/a/b.git'
    )
    assert wambatic.fetch.git.clone_url(host, 'a/b') == 'https://ghe.example.com/a/b.git'


def test_first_clone_then_incremental_fetch(upstream: Upstream, tmp_path: pathlib.Path) -> None:
    upstream.write('a.txt', 'one\ntwo\n')
    first = upstream.commit('first')
    upstream.push()
    git = make_git(upstream, tmp_path)

    async def scenario() -> tuple[dict[str, str], frozenset[str], dict[str, str], frozenset[str]]:
        await git.update(REPO)
        before = await git.branches(REPO)
        before_reachable = await git.reachable(REPO, list(before.values()))
        upstream.add_and_push('b.txt', 'one\ntwo\nthree\n')
        await git.update(REPO)
        after = await git.branches(REPO)
        return before, before_reachable, after, await git.reachable(REPO, list(after.values()))

    before, before_reachable, after, after_reachable = asyncio.run(scenario())
    assert before == {'main': first}
    assert before_reachable == {first}
    assert after['main'] != first
    assert after_reachable == {first, after['main']}
    assert git.path(REPO) == tmp_path / 'clones' / 'octo' / 'widgets.git'


def test_commit_counts_rename_binary_and_merge(upstream: Upstream, tmp_path: pathlib.Path) -> None:
    upstream.write('old name.py', ''.join(f'line {n}\n' for n in range(10)))
    base = upstream.commit('base')
    upstream.write('é.txt', 'x\n')
    upstream.write('blob.bin', b'\x00\x01\x02\x03')
    added = upstream.commit('add binary and unicode')
    run_git(upstream.work, 'mv', 'old name.py', 'new name.py')
    upstream.write('new name.py', ''.join(f'line {n}\n' for n in range(10)) + 'extra\n')
    renamed = upstream.commit('rename')
    run_git(upstream.work, 'checkout', '-b', 'feature')
    upstream.write('feature.txt', 'a\nb\nc\n')
    upstream.commit('feature work')
    run_git(upstream.work, 'checkout', 'main')
    upstream.write('main-only.txt', 'z\n')
    upstream.commit('main work')
    run_git(upstream.work, 'merge', '--no-ff', '-m', 'merge feature', 'feature')
    merge = run_git(upstream.work, 'rev-parse', 'HEAD')
    upstream.push('main', 'feature')
    git = make_git(upstream, tmp_path)

    async def scenario() -> dict[str, wambatic.fetch.git.GitCommit]:
        await git.update(REPO)
        heads = await git.branches(REPO)
        oids = await git.reachable(REPO, list(heads.values()))
        return {commit.oid: commit for commit in await git.commits(REPO, oids)}

    commits = asyncio.run(scenario())
    assert commits[base].parents == ()
    assert commits[base].files[0].path == 'old name.py'
    assert (commits[base].files[0].additions, commits[base].files[0].deletions) == (10, 0)
    by_path = {file.path: file for file in commits[added].files}
    assert by_path['é.txt'].additions == 1
    assert by_path['blob.bin'].binary
    assert (by_path['blob.bin'].additions, by_path['blob.bin'].deletions) == (0, 0)
    assert not by_path['é.txt'].binary
    assert [(f.path, f.additions, f.deletions) for f in commits[renamed].files] == [
        ('new name.py', 1, 0)
    ]
    assert len(commits[merge].parents) == 2
    assert [(f.path, f.additions) for f in commits[merge].files] == [('feature.txt', 3)]
    assert commits[base].authored_at.utcoffset().total_seconds() == 0  # type: ignore[union-attr]
    assert commits[base].authored_at.hour == 1
    assert not any(file.generated for commit in commits.values() for file in commit.files)


def test_force_pushed_and_deleted_branches(upstream: Upstream, tmp_path: pathlib.Path) -> None:
    upstream.write('a.txt', 'a\n')
    root = upstream.commit('root')
    run_git(upstream.work, 'checkout', '-b', 'topic')
    upstream.write('t.txt', 't\n')
    topic = upstream.commit('topic')
    run_git(upstream.work, 'checkout', 'main')
    upstream.write('a.txt', 'a\nb\n')
    old_main = upstream.commit('old main')
    upstream.push('main', 'topic')
    git = make_git(upstream, tmp_path)

    async def reach() -> frozenset[str]:
        await git.update(REPO)
        return await git.reachable(REPO, list((await git.branches(REPO)).values()))

    assert asyncio.run(reach()) == {root, topic, old_main}
    run_git(upstream.work, 'reset', '--hard', root)
    upstream.write('a.txt', 'rewritten\n')
    new_main = upstream.commit('new main')
    upstream.push('main')
    run_git(upstream.work, 'push', 'origin', '--delete', 'topic')
    assert asyncio.run(reach()) == {root, new_main}
    assert asyncio.run(git.branches(REPO)) == {'main': new_main}


def test_attributes_probe_and_generated_paths(upstream: Upstream, tmp_path: pathlib.Path) -> None:
    upstream.write('src/code.py', 'x\n')
    upstream.write('gen/out.txt', 'y\n')
    upstream.write('third/lib.js', 'z\n')
    upstream.write('.gitattributes', 'gen/** linguist-generated\n')
    upstream.commit('first')
    upstream.push()
    git = make_git(upstream, tmp_path)
    paths = ['src/code.py', 'gen/out.txt', 'third/lib.js']

    async def read() -> tuple[str, frozenset[str]]:
        await git.update(REPO)
        head = (await git.branches(REPO))['main']
        return await git.attributes_probe(REPO, head), await git.generated_paths(REPO, head, paths)

    probe, generated = asyncio.run(read())
    assert generated == {'gen/out.txt'}
    assert asyncio.run(read())[0] == probe

    upstream.write(
        '.gitattributes', 'third/** linguist-vendored\ngen/** linguist-generated=false\n'
    )
    upstream.commit('change attributes')
    upstream.push()
    changed_probe, changed = asyncio.run(read())
    assert changed_probe != probe
    assert changed == {'third/lib.js'}

    async def none() -> frozenset[str]:
        return await git.generated_paths(REPO, 'main', [])

    assert asyncio.run(none()) == frozenset()


def test_probe_without_attribute_files_is_stable(
    upstream: Upstream, tmp_path: pathlib.Path
) -> None:
    upstream.write('a.txt', 'a\n')
    upstream.commit('first')
    upstream.push()
    git = make_git(upstream, tmp_path)

    async def read() -> str:
        await git.update(REPO)
        return await git.attributes_probe(REPO, (await git.branches(REPO))['main'])

    assert asyncio.run(read()) == asyncio.run(read())


def test_git_missing(
    monkeypatch: pytest.MonkeyPatch,
    upstream: Upstream,
    tmp_path: pathlib.Path,
) -> None:
    empty = tmp_path / 'empty'
    empty.mkdir()
    monkeypatch.setenv('PATH', str(empty))
    git = make_git(upstream, tmp_path)
    with pytest.raises(wambatic.fetch.errors.GitError, match='not found on PATH'):
        asyncio.run(git.check_version())


def fake_git(directory: pathlib.Path, body: str) -> None:
    directory.mkdir()
    script = directory / 'git'
    script.write_text(f'#!/bin/sh\n{body}\n')
    script.chmod(script.stat().st_mode | stat.S_IEXEC)


def test_git_too_old(
    monkeypatch: pytest.MonkeyPatch,
    upstream: Upstream,
    tmp_path: pathlib.Path,
) -> None:
    fake_git(tmp_path / 'old', 'echo "git version 2.39.0"')
    monkeypatch.setenv('PATH', str(tmp_path / 'old'))
    git = make_git(upstream, tmp_path)
    with pytest.raises(wambatic.fetch.errors.GitError, match=r'2\.39 is too old.*2\.40 or later'):
        asyncio.run(git.update(REPO))
    assert not git.path(REPO).exists()


def test_command_past_timeout_is_killed(
    monkeypatch: pytest.MonkeyPatch,
    upstream: Upstream,
    tmp_path: pathlib.Path,
) -> None:
    fake_git(tmp_path / 'slow', 'exec sleep 30')
    monkeypatch.setenv('PATH', f'{tmp_path / "slow"}:/bin:/usr/bin')
    git = wambatic.fetch.git.Git(
        TOKEN,
        wambatic.fetch.hosts.GITHUB_COM,
        tmp_path / 'clones',
        url_for=upstream.url_for,
        timeout=0.3,
    )
    with pytest.raises(wambatic.fetch.errors.GitError, match='ran longer than'):
        asyncio.run(git.run(REPO, 'log', ['log']))


@pytest.mark.parametrize('form', ['token', 'basic'])
def test_failing_command_redacts_the_token(form: str, tmp_path: pathlib.Path) -> None:
    basic = base64.b64encode(f'x-access-token:{TOKEN}'.encode()).decode()
    secret = TOKEN if form == 'token' else basic
    git = wambatic.fetch.git.Git(
        TOKEN,
        wambatic.fetch.hosts.GITHUB_COM,
        tmp_path / 'clones',
        url_for=lambda _: str(tmp_path / 'missing' / secret),
    )
    with pytest.raises(wambatic.fetch.errors.GitError) as caught:
        asyncio.run(git.update(REPO))
    message = str(caught.value)
    assert secret not in message
    assert '***' in message
    assert 'git clone for octo/widgets failed' in message


def test_token_reaches_git_only_through_the_environment(
    upstream: Upstream,
    tmp_path: pathlib.Path,
) -> None:
    upstream.write('a.txt', 'a\n')
    upstream.commit('first')
    upstream.push()
    git = make_git(upstream, tmp_path, Recording)
    assert isinstance(git, Recording)
    basic = base64.b64encode(f'x-access-token:{TOKEN}'.encode()).decode()

    async def scenario() -> None:
        await git.update(REPO)
        upstream.add_and_push('b.txt', 'a\nb\n')
        await git.update(REPO)
        heads = await git.branches(REPO)
        oids = await git.reachable(REPO, list(heads.values()))
        await git.commits(REPO, oids)
        await git.attributes_probe(REPO, heads['main'])
        await git.generated_paths(REPO, heads['main'], ['a.txt'])

    asyncio.run(scenario())
    assert {'clone', 'fetch', 'for-each-ref', 'rev-list', 'log', 'ls-tree', 'check-attr'} <= {
        word for call in git.calls for word in call
    }
    for call in git.calls:
        assert call[:5] == ['git', '-c', 'credential.helper=', '-c', 'core.quotePath=false']
        assert not any(TOKEN in argument or basic in argument for argument in call)
    config = (git.path(REPO) / 'config').read_text()
    assert TOKEN not in config
    assert basic not in config
    environment = git.environment()
    assert environment['GIT_TERMINAL_PROMPT'] == '0'
    assert environment['GIT_CONFIG_COUNT'] == '1'
    assert environment['GIT_CONFIG_KEY_0'] == 'http.extraHeader'
    assert environment['GIT_CONFIG_VALUE_0'] == f'Authorization: Basic {basic}'


def test_removing_a_clone(upstream: Upstream, tmp_path: pathlib.Path) -> None:
    upstream.write('a.txt', 'a\n')
    upstream.commit('first')
    upstream.push()
    git = make_git(upstream, tmp_path)
    asyncio.run(git.update(REPO))
    assert git.path(REPO).is_dir()
    git.remove(REPO)
    assert not git.path(REPO).exists()
    git.remove(REPO)


def test_unparsable_log_is_a_git_error() -> None:
    with pytest.raises(wambatic.fetch.errors.GitError, match='does not parse'):
        wambatic.fetch.git.parse_log(REPO, '\x01only-one-field\n')
