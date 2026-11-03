import asyncio
import base64
import collections.abc
import dataclasses
import datetime
import hashlib
import os
import pathlib
import re
import shutil

import wambatic.fetch.auth
import wambatic.fetch.base
import wambatic.fetch.errors
import wambatic.fetch.hosts

MIN_GIT_VERSION: tuple[int, int] = (2, 40)
GIT_TIMEOUT: float = 600.0

RECORD_START = '\x01'
FIELD_SEPARATOR = '\x02'
GIT_VERSION = re.compile(r'git version (\d+)\.(\d+)')
STDERR_LINES = 5
GENERATED_VALUES = frozenset({'set', 'true'})
ATTRIBUTES = ('linguist-generated', 'linguist-vendored')


def clone_url(host: wambatic.fetch.hosts.GitHubHost, repo: str) -> str:
    """'https://github.com/<owner>/<name>.git', or 'https://<host.name>/<owner>/<name>.git'."""
    return f'https://{host.name}/{repo}.git'


@dataclasses.dataclass(frozen=True, slots=True)
class GitCommit:
    oid: str
    parents: tuple[str, ...]
    authored_at: datetime.datetime
    authored_offset: int
    files: tuple[wambatic.fetch.base.CommitFile, ...]


@dataclasses.dataclass(frozen=True, slots=True)
class GitResult:
    stdout: bytes
    stderr: str


class Git:
    def __init__(
        self,
        token: str,
        host: wambatic.fetch.hosts.GitHubHost,
        clones_dir: pathlib.Path,
        *,
        url_for: collections.abc.Callable[[str], str] | None = None,
        timeout: float = GIT_TIMEOUT,
    ) -> None:
        self.token = token
        self.host = host
        self.clones_dir = clones_dir
        self.url_for = url_for or (lambda repo: clone_url(host, repo))
        self.timeout = timeout
        self.version_checked = False

    def basic_credential(self) -> str:
        return base64.b64encode(f'x-access-token:{self.token}'.encode()).decode()

    def redact(self, text: str) -> str:
        if not self.token:
            return text
        text = wambatic.fetch.auth.redact(text, self.token)
        return wambatic.fetch.auth.redact(text, self.basic_credential())

    def environment(self) -> dict[str, str]:
        env = dict(os.environ)
        env['GIT_TERMINAL_PROMPT'] = '0'
        if self.token:
            env['GIT_CONFIG_COUNT'] = '1'
            env['GIT_CONFIG_KEY_0'] = 'http.extraHeader'
            env['GIT_CONFIG_VALUE_0'] = f'Authorization: Basic {self.basic_credential()}'
        return env

    def arguments(self, args: collections.abc.Sequence[str]) -> list[str]:
        return ['git', '-c', 'credential.helper=', '-c', 'core.quotePath=false', *args]

    async def run(
        self,
        repo: str,
        verb: str,
        args: collections.abc.Sequence[str],
        stdin: bytes | None = None,
    ) -> GitResult:
        """Run one git command; tests record or replace commands through this seam.

        Raises:
            GitError: git cannot start, runs past the timeout, or exits non-zero.
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *self.arguments(args),
                stdin=asyncio.subprocess.PIPE if stdin is not None else asyncio.subprocess.DEVNULL,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=self.environment(),
            )
        except OSError as error:
            reason = self.redact(error.strerror or 'unknown error')
            raise wambatic.fetch.errors.GitError(
                f'git {verb} for {repo} could not start: {reason}'
            ) from None
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(stdin), self.timeout)
        except TimeoutError:
            process.kill()
            await process.wait()
            raise wambatic.fetch.errors.GitError(
                f'git {verb} for {repo} ran longer than {self.timeout:g} seconds and was killed'
            ) from None
        text = self.redact(stderr.decode(errors='replace'))
        if process.returncode != 0:
            tail = '\n'.join(text.strip().splitlines()[-STDERR_LINES:])
            raise wambatic.fetch.errors.GitError(f'git {verb} for {repo} failed: {tail}')
        return GitResult(stdout=stdout, stderr=text)

    async def inside(
        self,
        repo: str,
        verb: str,
        args: collections.abc.Sequence[str],
        stdin: bytes | None = None,
    ) -> GitResult:
        return await self.run(repo, verb, ['-C', str(self.path(repo)), *args], stdin)

    async def check_version(self) -> None:
        if self.version_checked:
            return
        minimum = '.'.join(str(part) for part in MIN_GIT_VERSION)
        try:
            process = await asyncio.create_subprocess_exec(
                'git',
                '--version',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(process.communicate(), self.timeout)
        except OSError:
            raise wambatic.fetch.errors.GitError(
                f'git was not found on PATH; install git {minimum} or later'
            ) from None
        text = stdout.decode(errors='replace').strip()
        match = GIT_VERSION.match(text)
        if match is None:
            raise wambatic.fetch.errors.GitError(
                f'git printed no version ({text!r}); install git {minimum} or later'
            )
        found = (int(match.group(1)), int(match.group(2)))
        if found < MIN_GIT_VERSION:
            raise wambatic.fetch.errors.GitError(
                f'git {found[0]}.{found[1]} is too old; install git {minimum} or later'
            )
        self.version_checked = True

    def path(self, repo: str) -> pathlib.Path:
        owner, _, name = repo.partition('/')
        return self.clones_dir / owner / f'{name}.git'

    async def update(self, repo: str) -> None:
        await self.check_version()
        target = self.path(repo)
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            await self.run(
                repo,
                'clone',
                ['clone', '--bare', '--no-tags', '--quiet', self.url_for(repo), str(target)],
            )
            return
        await self.inside(
            repo,
            'fetch',
            [
                'fetch',
                '--prune',
                '--no-tags',
                '--quiet',
                'origin',
                '+refs/heads/*:refs/heads/*',
            ],
        )

    async def branches(self, repo: str) -> dict[str, str]:
        result = await self.inside(
            repo,
            'for-each-ref',
            [
                'for-each-ref',
                '--format=%(refname:strip=2) %(objectname)',
                'refs/heads',
            ],
        )
        heads: dict[str, str] = {}
        for line in result.stdout.decode().splitlines():
            name, _, oid = line.rpartition(' ')
            if not name or not oid:
                raise wambatic.fetch.errors.GitError(
                    f'git for-each-ref for {repo} printed an unreadable line'
                )
            heads[name] = oid
        return heads

    async def reachable(self, repo: str, heads: collections.abc.Collection[str]) -> frozenset[str]:
        if not heads:
            return frozenset()
        result = await self.inside(
            repo,
            'rev-list',
            ['rev-list', '--stdin'],
            stdin=''.join(f'{head}\n' for head in sorted(heads)).encode(),
        )
        return frozenset(result.stdout.decode().split())

    async def commits(self, repo: str, oids: collections.abc.Collection[str]) -> list[GitCommit]:
        if not oids:
            return []
        result = await self.inside(
            repo,
            'log',
            [
                'log',
                '--no-walk=unsorted',
                '--stdin',
                '-z',
                '-M',
                '--diff-merges=first-parent',
                '--numstat',
                '--format=%x01%H%x02%P%x02%aI',
            ],
            stdin=''.join(f'{oid}\n' for oid in sorted(oids)).encode(),
        )
        return parse_log(repo, result.stdout.decode(errors='replace'))

    async def attributes_probe(self, repo: str, head: str) -> str:
        result = await self.inside(
            repo,
            'ls-tree',
            ['ls-tree', '-r', '-z', '--full-tree', head],
        )
        found: list[tuple[str, str]] = []
        for entry in result.stdout.decode(errors='replace').split('\0'):
            meta, _, name = entry.partition('\t')
            if not name or pathlib.PurePosixPath(name).name != '.gitattributes':
                continue
            fields = meta.split()
            if len(fields) != 3:
                raise wambatic.fetch.errors.GitError(
                    f'git ls-tree for {repo} printed an unreadable entry'
                )
            found.append((name, fields[2]))
        digest = hashlib.sha256()
        for name, oid in sorted(found):
            digest.update(f'{name}\0{oid}\0'.encode())
        return digest.hexdigest()

    async def generated_paths(
        self,
        repo: str,
        head: str,
        paths: collections.abc.Collection[str],
    ) -> frozenset[str]:
        if not paths:
            return frozenset()
        result = await self.inside(
            repo,
            'check-attr',
            [
                'check-attr',
                '-z',
                '--stdin',
                '--source',
                head,
                *ATTRIBUTES,
            ],
            stdin=''.join(f'{path}\0' for path in sorted(paths)).encode(),
        )
        fields = result.stdout.decode(errors='replace').split('\0')
        if fields and fields[-1] == '':
            fields.pop()
        if len(fields) % 3:
            raise wambatic.fetch.errors.GitError(
                f'git check-attr for {repo} printed output that does not parse'
            )
        return frozenset(
            fields[index]
            for index in range(0, len(fields), 3)
            if fields[index + 2] in GENERATED_VALUES
        )

    def remove(self, repo: str) -> None:
        shutil.rmtree(self.path(repo), ignore_errors=True)


def parse_count(repo: str, oid: str, text: str) -> int:
    if text == '-':
        return 0
    try:
        return int(text)
    except ValueError:
        raise wambatic.fetch.errors.GitError(
            f'git log for {repo} printed a count that does not parse for {oid}'
        ) from None


def parse_log(repo: str, text: str) -> list[GitCommit]:
    """The commits of `git log -z --numstat` with the spec's format.

    Raises:
        GitError: a header, date or numstat line does not parse.
    """
    commits: list[GitCommit] = []
    for record in text.split(RECORD_START):
        if not record.strip('\0\n'):
            continue
        header, _, body = record.partition('\0')
        fields = header.rstrip('\n').split(FIELD_SEPARATOR)
        if len(fields) != 3:
            raise wambatic.fetch.errors.GitError(
                f'git log for {repo} printed a commit header that does not parse'
            )
        oid, parents, date = fields
        try:
            written = datetime.datetime.fromisoformat(date)
            offset = written.utcoffset()
            authored_at = written.astimezone(datetime.UTC)
        except ValueError:
            raise wambatic.fetch.errors.GitError(
                f'git log for {repo} printed a date that does not parse for {oid}'
            ) from None
        if offset is None:
            raise wambatic.fetch.errors.GitError(
                f'git log for {repo} printed a date with no offset for {oid}'
            )
        commits.append(
            GitCommit(
                oid=oid,
                parents=tuple(parents.split()),
                authored_at=authored_at,
                authored_offset=offset // datetime.timedelta(minutes=1),
                files=parse_numstat(repo, oid, body),
            )
        )
    return commits


def parse_numstat(repo: str, oid: str, body: str) -> tuple[wambatic.fetch.base.CommitFile, ...]:
    tokens = body.split('\0')
    while tokens and tokens[-1] in {'', '\n'}:
        tokens.pop()
    files: dict[str, wambatic.fetch.base.CommitFile] = {}
    index = 0
    while index < len(tokens):
        counts = tokens[index].lstrip('\n').split('\t')
        if len(counts) != 3:
            raise wambatic.fetch.errors.GitError(
                f'git log for {repo} printed a numstat line that does not parse for {oid}'
            )
        added, deleted, path = counts
        if path:
            index += 1
        else:
            if index + 2 >= len(tokens):
                raise wambatic.fetch.errors.GitError(
                    f'git log for {repo} printed a rename that does not parse for {oid}'
                )
            path = tokens[index + 2]
            index += 3
        files[path] = wambatic.fetch.base.CommitFile(
            path=path,
            additions=parse_count(repo, oid, added),
            deletions=parse_count(repo, oid, deleted),
            binary=added == '-' and deleted == '-',
        )
    return tuple(files.values())
