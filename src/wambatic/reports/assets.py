"""The files an HTML report page loads: plotly.js, the vendored Excel writer, the page scripts and
the stylesheet. They are written to a folder named after a hash of their contents, beside the page
or served by the web app, so a page always loads the files it was made with."""

import dataclasses
import functools
import hashlib
import importlib.resources
import os
import pathlib
import shutil
import string
import tempfile

import plotly.offline

import wambatic.reports.errors
import wambatic.reports.figures

WRITE_EXCEL_FILE_VERSION = '4.1.1'
WRITE_EXCEL_FILE_SHA256 = 'd57b59731b19d443f6b7333c5af0aa7250c87146a106f8a746f63429e7694c8e'
FOLDER_PREFIX = 'wambatic-assets-'
HASH_LENGTH = 12
FOLDER_MODE = 0o755
JAVASCRIPT = 'text/javascript; charset=utf-8'
STYLESHEET = 'text/css; charset=utf-8'
# auditme: accept[non-alphabetical-literal] the order the page loads the scripts in
SCRIPT_NAMES = ('plotly.min.js', 'write-excel-file.min.js', 'tables.js', 'report.js')
STYLESHEET_NAME = 'report.css'
TEMPLATE_NAMES = (
    'form.html',
    'message.html',
    'progress.html',
    'progress.js',
    'report.css',
    'report.html',
    'report.js',
    'tables.js',
)


@dataclasses.dataclass(frozen=True, slots=True)
class Asset:
    """One file of the assets folder."""

    name: str
    content: bytes
    media_type: str


@functools.cache
def read_template(name: str) -> str:
    """The packaged template `name`.

    Raises:
        OutputError: when the template cannot be read or is not UTF-8.
    """
    resource = importlib.resources.files('wambatic.reports') / 'templates' / name
    try:
        return resource.read_text(encoding='utf-8')
    except OSError, UnicodeDecodeError:
        raise wambatic.reports.errors.OutputError(
            f'cannot read the report template {name}; reinstall wambatic'
        ) from None


def read_plotlyjs() -> str:
    """The plotly.js bundled with plotly.

    Raises:
        OutputError: when the file cannot be read or is not UTF-8.
    """
    try:
        return str(plotly.offline.get_plotlyjs())
    except OSError, UnicodeDecodeError:
        raise wambatic.reports.errors.OutputError(
            'cannot read the plotly.js bundled with plotly; reinstall wambatic'
        ) from None


def read_vendored(name: str) -> bytes:
    """The vendored file `name`.

    Raises:
        OutputError: when the file cannot be read.
    """
    resource = importlib.resources.files('wambatic.reports') / 'vendor' / name
    try:
        return resource.read_bytes()
    except OSError:
        raise wambatic.reports.errors.OutputError(
            f'cannot read the vendored file {name}; reinstall wambatic'
        ) from None


def tokens(theme: wambatic.reports.figures.Theme) -> str:
    """A theme's colours as the CSS custom properties the stylesheet reads."""
    declarations = {
        'page': theme.page,
        'surface': theme.surface,
        'ink': theme.ink,
        'ink-secondary': theme.ink_secondary,
        'grid': theme.grid,
        **{f'series-{n}': colour for n, colour in enumerate(theme.categorical, 1)},
        **{f'sequential-{n}': colour for n, colour in enumerate(theme.sequential, 1)},
    }
    return '\n  '.join(f'--{name}: {colour};' for name, colour in declarations.items())


def stylesheet() -> str:
    palette = wambatic.reports.figures.PALETTE
    return string.Template(read_template(STYLESHEET_NAME)).substitute(
        light=tokens(palette['light']), dark=tokens(palette['dark'])
    )


@functools.cache
def page_assets() -> tuple[Asset, ...]:
    """Every file the page loads, in a fixed order."""
    contents = {
        'plotly.min.js': read_plotlyjs().encode(),
        'write-excel-file.min.js': read_vendored('write-excel-file.min.js'),
        'tables.js': read_template('tables.js').encode(),
        'report.js': read_template('report.js').encode(),
        STYLESHEET_NAME: stylesheet().encode(),
    }
    return tuple(
        Asset(name, content, STYLESHEET if name.endswith('.css') else JAVASCRIPT)
        for name, content in contents.items()
    )


def assets_hash() -> str:
    """The first 12 hex digits of the SHA-256 of every asset's name and content, in order."""
    digest = hashlib.sha256()
    for asset in page_assets():
        digest.update(asset.name.encode() + b'\0' + asset.content + b'\0')
    return digest.hexdigest()[:HASH_LENGTH]


def assets_folder_name() -> str:
    return FOLDER_PREFIX + assets_hash()


def write_assets(directory: pathlib.Path) -> pathlib.Path:
    """Write `assets_folder_name()` under `directory` unless it already exists; return its path.
    The folder is written as a temporary sibling and renamed into place, so it is complete or
    absent. An existing folder is kept only when it is a real directory holding exactly these
    bytes, so a folder planted in a shared directory cannot put its scripts in the page.

    Raises:
        OutputError: `cannot write PATH: REASON` when it cannot be written, or when it exists
            and does not hold this version's files.
    """
    target = directory / assets_folder_name()
    if target.exists() or target.is_symlink():
        return checked_folder(target)
    temporary: pathlib.Path | None = None
    try:
        directory.mkdir(parents=True, exist_ok=True)
        temporary = pathlib.Path(tempfile.mkdtemp(dir=directory, prefix='.assets-', suffix='.tmp'))
        for asset in page_assets():
            (temporary / asset.name).write_bytes(asset.content)
        temporary.chmod(FOLDER_MODE)
        try:
            os.rename(temporary, target)
        except OSError:
            # Another run made the same folder meanwhile: keep it.
            if not (target.exists() or target.is_symlink()):
                raise
            checked_folder(target)
    except OSError as e:
        # auditme: accept[except-interpolation] the OS reason says what to fix
        message = f'cannot write {target}: {e.strerror or e}'
        raise wambatic.reports.errors.OutputError(message) from e
    finally:
        if temporary is not None:
            # auditme: accept[filesystem-op-without-envelope] best-effort cleanup
            shutil.rmtree(temporary, ignore_errors=True)
    return target


def checked_folder(target: pathlib.Path) -> pathlib.Path:
    """Return `target` when it is a real directory whose files match `page_assets()` byte for byte.

    Raises:
        OutputError: `cannot write PATH: it exists and does not hold this version's files;
            remove it` otherwise.
    """
    try:
        matches = (
            not target.is_symlink()
            and target.is_dir()
            and all(
                not (target / asset.name).is_symlink()
                and (target / asset.name).read_bytes() == asset.content
                for asset in page_assets()
            )
        )
    except OSError:
        matches = False
    if not matches:
        message = (
            f"cannot write {target}: it exists and does not hold this version's files; remove it"
        )
        raise wambatic.reports.errors.OutputError(message)
    return target
