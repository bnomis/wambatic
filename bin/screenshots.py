#!/usr/bin/env python3
"""Rebuild every screenshot of the user guide from real GitHub data.

Syncs `repo:pallets/click` and `org:pallets` into a dedicated cache (never the user's own),
then writes under `--out` (default docs/images):

- terminal/: the terminal report as SVG, whole and one file for each section, and `cache info`;
- html/: the HTML report as PNG, full pages light and dark, and one crop for each entry of
  SELECTORS;
- web/: the pages of `wambatic serve` as PNG.

Only the images listed in WANTED are written. It also writes docs/snippets/captured.md, the
dated note the guide pages include. Run it by hand when the output changes
(bin/screenshots.sh). It needs GITHUB_TOKEN or `gh auth token`, and Playwright's Chromium
(`playwright install chromium`). The token is read only through wambatic's own lookup and is
never written out.

Every failure is one line on stderr and exit status 1; images the run has not reached are left
as they were.
"""

import argparse
import asyncio
import collections.abc
import contextlib
import dataclasses
import datetime
import io
import json
import os
import pathlib
import re
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse

import playwright.sync_api
import rich.console

import wambatic.cli
import wambatic.fetch.auth
import wambatic.fetch.base
import wambatic.fetch.cache
import wambatic.fetch.errors
import wambatic.reports.errors
import wambatic.reports.html
import wambatic.reports.service
import wambatic.reports.terminal
import wambatic.settings
import wambatic.stats.base
import wambatic.stats.errors
import wambatic.version

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / 'docs/images'
CAPTURED = ROOT / 'docs/snippets/captured.md'
DOCS_CACHE = pathlib.Path('~/.cache/wambatic/docs.sqlite3').expanduser()

# Fixed, so that a re-run on a later day shows the same periods.
REPO_TARGET = 'repo:pallets/click'
ORG_TARGET = 'org:pallets'
SINCE = '2024-11-01'
UNTIL = '2026-10-31'
GROUPS = 'activity,flow,delivery,popularity'
BY = 'month'

TERMINAL_WIDTH = 110
VIEWPORT = {'height': 800, 'width': 1280}
FULL_PAGE_SCALE = 0.45  # a full page is tall; at full size it passes the 1 MB limit
MAX_BYTES = 1_000_000
SERVER_TIMEOUT = 30.0
PROGRESS_TIMEOUT = 60.0
STOP_TIMEOUT = 10.0
PAGE_TIMEOUT_MS = 30_000

TOKEN_FIX = 'set GITHUB_TOKEN, or sign in with `gh auth login`'
CHROMIUM_FIX = 'run `playwright install chromium`'


@dataclasses.dataclass(frozen=True, slots=True)
class Crop:
    """One element of the HTML report, photographed alone. `before` is a selector clicked first,
    to show a state other than the one the page opens in."""

    name: str
    selector: str
    before: str | None = None


# The crops of the HTML report. The selectors are those of reports/templates/report.html and
# of the markup reports/html.py writes.
SELECTORS: tuple[Crop, ...] = (
    Crop('tiles', 'dl.tiles'),
    Crop('switch', 'fieldset.switch'),
    Crop('calendar', 'figure:has(#activity-calendar)'),
    Crop(
        'partial-period',
        'figure:has(#activity-commits)',
        before='input[name="granularity"][value="year"]',
    ),
    Crop('delivery-charts', '#delivery .charts'),
    Crop('popularity-charts', '#popularity .charts'),
    Crop('languages', 'figure:has(#popularity-languages)'),
)

# The images the guide pages use, relative to the image directory. The script writes these and no
# others; `test_images_exist` in src/tests/test_docs.py fails on an image no page references, so a
# page that starts to use another image adds it here.
WANTED: frozenset[str] = frozenset(
    {
        'html/org-pallets-calendar.png',
        'html/org-pallets-dark.png',
        'html/org-pallets-languages.png',
        'html/org-pallets-light.png',
        'html/org-pallets-popularity-charts.png',
        'html/org-pallets-switch.png',
        'html/org-pallets-tiles.png',
        'html/repo-pallets-click-delivery-charts.png',
        'html/repo-pallets-click-light.png',
        'html/repo-pallets-click-partial-period.png',
        'terminal/cache-info.svg',
        'terminal/org-pallets-full.svg',
        'terminal/repo-pallets-click-overview.svg',
        'terminal/repo-pallets-click-provenance.svg',
        'terminal/repo-pallets-click-trends.svg',
        'web/api-docs.png',
        'web/form.png',
        'web/progress.png',
        'web/report.png',
    }
)

EVERY_CHART_DRAWN = """() => {
  const plots = [...document.querySelectorAll('.plot')];
  return plots.length > 0 && plots.every((plot) => plot.querySelector('.main-svg'));
}"""
SYNCING = 'Syncing repositories'


class ScreenshotError(Exception):
    """A failure that ends the run with one line on stderr."""


def slug(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')


def subject_slug(subject: wambatic.fetch.base.Subject) -> str:
    """`repo-pallets-click` or `org-pallets`."""
    return wambatic.reports.html.report_filename(subject).removesuffix('.html')


def is_wanted(out_dir: pathlib.Path, path: pathlib.Path) -> bool:
    """Whether `path`, under `out_dir`, is an image the guide uses."""
    return path.relative_to(out_dir).as_posix() in WANTED


def check_size(path: pathlib.Path) -> pathlib.Path:
    """`path` itself, if it is within the size limit.

    Raises:
        ScreenshotError: the file is over 1 MB.
    """
    size = path.stat().st_size
    if size > MAX_BYTES:
        raise ScreenshotError(f'{path} is {size} bytes, over the {MAX_BYTES} byte limit')
    return path


def write_text(path: pathlib.Path, text: str) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [line.rstrip() for line in text.splitlines()]
    path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return check_size(path)


def check_token() -> None:
    """Raise ScreenshotError, naming the fix, when no token can be found. The token itself is
    discarded."""
    try:
        wambatic.fetch.auth.fetch_token()
    except wambatic.fetch.errors.AuthError:
        raise ScreenshotError(f'no GitHub token found: {TOKEN_FIX}') from None


def write_config(directory: pathlib.Path, cache_path: pathlib.Path) -> pathlib.Path:
    """A config file in `directory` for the docs: its own cache, and UTC dates."""
    config = {'fetch': {'cache_path': str(cache_path)}, 'stats': {'timezone': 'UTC'}}
    path = directory / 'config.json'
    path.write_text(json.dumps(config), encoding='utf-8')
    return path


@contextlib.contextmanager
def config_environment(config_path: pathlib.Path) -> collections.abc.Generator[None]:
    """Point WAMBATIC_CONFIG at `config_path` for the in-process calls, then put it back."""
    before = os.environ.get('WAMBATIC_CONFIG')
    os.environ['WAMBATIC_CONFIG'] = str(config_path)
    try:
        yield
    finally:
        if before is None:
            del os.environ['WAMBATIC_CONFIG']
        else:
            os.environ['WAMBATIC_CONFIG'] = before


def compute(
    target: str, *, by_author: bool, skip_sync: bool
) -> list[wambatic.stats.base.StatsResult]:
    """The five results of an HTML report of `target` (total, year, month, week, day), synced
    first unless `skip_sync`. The cache and time zone come from WAMBATIC_CONFIG."""
    settings = wambatic.settings.load_settings(None, {})
    now = datetime.datetime.now(datetime.UTC)
    request = wambatic.reports.service.make_request(
        BY, SINCE, UNTIL, GROUPS, by_author, settings, now
    )
    cache = wambatic.fetch.cache.Cache.open(settings.fetch.cache_path)
    try:
        _, results = asyncio.run(
            wambatic.reports.service.sync_and_compute(
                settings,
                cache,
                wambatic.reports.service.parse_target(target),
                wambatic.reports.html.period_requests(request),
                full_refresh=False,
                no_fetch=skip_sync,
            )
        )
    finally:
        cache.close()
    return results


def split_sections(
    render: collections.abc.Callable[[rich.console.Console], None],
) -> dict[str, str]:
    """Run `render` on a recording console and cut its output into SVGs at each `heading` line.

    The first section, before any heading, is named `overview`; the others by their heading.
    This follows `render_terminal`: each section function calls
    `wambatic.reports.terminal.heading` before its own output.
    """
    console = rich.console.Console(
        record=True, width=TERMINAL_WIDTH, force_terminal=True, file=io.StringIO()
    )
    sections: dict[str, str] = {}
    current = 'overview'
    original = wambatic.reports.terminal.heading

    def flush() -> None:
        name, number = current, 2
        while name in sections:
            name, number = f'{current}-{number}', number + 1
        sections[name] = console.export_svg(title='wambatic')

    def cutting(console: rich.console.Console, text: str) -> None:
        nonlocal current
        flush()
        current = slug(text)
        original(console, text)

    wambatic.reports.terminal.heading = cutting
    try:
        render(console)
    finally:
        wambatic.reports.terminal.heading = original
    flush()
    return sections


def whole_report(render: collections.abc.Callable[[rich.console.Console], None]) -> str:
    console = rich.console.Console(
        record=True, width=TERMINAL_WIDTH, force_terminal=True, file=io.StringIO()
    )
    render(console)
    return console.export_svg(title='wambatic')


def capture_terminal(
    result: wambatic.stats.base.StatsResult, out_dir: pathlib.Path
) -> list[pathlib.Path]:
    """Render `result` as the terminal report; write one SVG per section and the whole report."""

    def render(console: rich.console.Console) -> None:
        wambatic.reports.terminal.render_terminal(result, console)

    name = subject_slug(result.subject)
    folder = out_dir / 'terminal'
    written = []
    full = folder / f'{name}-full.svg'
    if is_wanted(out_dir, full):
        written.append(write_text(full, whole_report(render)))
    for section, svg in split_sections(render).items():
        path = folder / f'{name}-{section}.svg'
        if is_wanted(out_dir, path):
            written.append(write_text(path, svg))
    return written


def capture_cache_info(out_dir: pathlib.Path) -> pathlib.Path:
    """`wambatic cache info` for the cache WAMBATIC_CONFIG names."""
    settings = wambatic.settings.load_settings(None, {})

    def render(console: rich.console.Console) -> None:
        wambatic.cli.run_cache(wambatic.cli.CacheCommand('info'), settings, console)

    return write_text(out_dir / 'terminal/cache-info.svg', whole_report(render))


@contextlib.contextmanager
def launch_chromium() -> collections.abc.Generator[playwright.sync_api.Browser]:
    """A headless Chromium.

    Raises:
        ScreenshotError: Chromium is not installed or cannot be launched.
    """
    with playwright.sync_api.sync_playwright() as driver:
        try:
            browser = driver.chromium.launch()
        except playwright.sync_api.Error as e:
            raise ScreenshotError(
                # auditme: accept[except-interpolation] the launch failure says what is missing
                f'Chromium cannot be launched ({str(e).splitlines()[0]}): {CHROMIUM_FIX}'
            ) from None
        try:
            yield browser
        finally:
            browser.close()


def save_png(
    target: playwright.sync_api.Page | playwright.sync_api.Locator, path: pathlib.Path
) -> pathlib.Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(target, playwright.sync_api.Page):
        target.screenshot(path=path, full_page=True, scale='device')
    else:
        target.screenshot(path=path, scale='css')
    return check_size(path)


def open_report(
    browser: playwright.sync_api.Browser,
    report_path: pathlib.Path,
    scheme: str,
    device_scale_factor: float = 1.0,
) -> tuple[playwright.sync_api.BrowserContext, playwright.sync_api.Page]:
    context = browser.new_context(
        viewport=VIEWPORT,  # type: ignore[arg-type]
        color_scheme=scheme,  # type: ignore[arg-type]
        device_scale_factor=device_scale_factor,
    )
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    page.goto(report_path.as_uri())
    page.wait_for_function(EVERY_CHART_DRAWN)
    return context, page


def crop_report(
    browser: playwright.sync_api.Browser, report_path: pathlib.Path, crop: Crop, out: pathlib.Path
) -> pathlib.Path:
    """Photograph the element `crop` names, in a fresh page.

    Raises:
        ScreenshotError: the selector matches nothing.
    """
    context, page = open_report(browser, report_path, 'light')
    try:
        if crop.before is not None:
            page.locator(crop.before).first.click()
            page.wait_for_function(EVERY_CHART_DRAWN)
        found = page.locator(crop.selector)
        if found.count() == 0:
            raise ScreenshotError(f'the selector {crop.selector} matches nothing in {report_path}')
        return save_png(found.first, out)
    finally:
        context.close()


def capture_html(report_path: pathlib.Path, out_dir: pathlib.Path) -> list[pathlib.Path]:
    """Screenshot the HTML report, light and dark, and the element crops named in SELECTORS."""
    name = report_path.stem.removeprefix('report-')
    folder = out_dir / 'html'
    written = []
    with launch_chromium() as browser:
        for scheme in ('light', 'dark'):
            path = folder / f'{name}-{scheme}.png'
            if not is_wanted(out_dir, path):
                continue
            context, page = open_report(browser, report_path, scheme, FULL_PAGE_SCALE)
            try:
                written.append(save_png(page, path))
            finally:
                context.close()
        for crop in SELECTORS:
            path = folder / f'{name}-{crop.name}.png'
            if is_wanted(out_dir, path):
                written.append(crop_report(browser, report_path, crop, path))
    return written


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return int(sock.getsockname()[1])


def wait_for_port(port: int, server: subprocess.Popen[bytes]) -> None:
    """Return once something listens on `port`.

    Raises:
        ScreenshotError: the server exits, or does not answer within the time limit.
    """
    deadline = time.monotonic() + SERVER_TIMEOUT
    while time.monotonic() < deadline:
        if server.poll() is not None:
            raise ScreenshotError(f'wambatic serve exited with status {server.returncode}')
        with contextlib.suppress(OSError), socket.create_connection(('127.0.0.1', port), 0.5):
            return
        time.sleep(0.2)
    raise ScreenshotError(f'wambatic serve did not answer on port {port} within 30 seconds')


@contextlib.contextmanager
def running_server(config_path: pathlib.Path, *extra: str) -> collections.abc.Generator[str]:
    """The base URL of `wambatic serve` on a free loopback port, stopped on exit."""
    port = free_port()
    server = subprocess.Popen(
        [sys.executable, '-m', 'wambatic', 'serve', '--port', str(port), *extra],
        env={**os.environ, 'WAMBATIC_CONFIG': str(config_path)},
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        wait_for_port(port, server)
        yield f'http://127.0.0.1:{port}'
    finally:
        server.terminate()
        try:
            server.wait(STOP_TIMEOUT)
        except subprocess.TimeoutExpired:
            server.kill()
            server.wait()


def report_query(target: str) -> str:
    fields = {'target': target, 'by': BY, 'since': SINCE, 'until': UNTIL, 'groups': GROUPS}
    if target.startswith('org:'):
        fields['by_author'] = 'true'
    return urllib.parse.urlencode(fields)


def web_page(
    browser: playwright.sync_api.Browser, device_scale_factor: float = 1.0
) -> tuple[playwright.sync_api.BrowserContext, playwright.sync_api.Page]:
    context = browser.new_context(
        viewport=VIEWPORT,  # type: ignore[arg-type]
        device_scale_factor=device_scale_factor,
    )
    page = context.new_page()
    page.set_default_timeout(PAGE_TIMEOUT_MS)
    return context, page


def capture_web(config_path: pathlib.Path, out_dir: pathlib.Path) -> list[pathlib.Path]:
    """Start `wambatic serve`, screenshot its pages, stop it."""
    folder = out_dir / 'web'
    written = []
    with launch_chromium() as browser, running_server(config_path, '--max-age', '30d') as base:
        context, page = web_page(browser)
        try:
            page.goto(f'{base}/')
            written.append(save_png(page, folder / 'form.png'))
            page.goto(f'{base}/docs')
            page.wait_for_selector('.opblock')
            written.append(save_png(page, folder / 'api-docs.png'))
        finally:
            context.close()
        context, page = web_page(browser, FULL_PAGE_SCALE)
        try:
            page.goto(f'{base}/report?{report_query(REPO_TARGET)}')
            page.wait_for_function(EVERY_CHART_DRAWN)
            written.append(save_png(page, folder / 'report.png'))
        finally:
            context.close()
    return written


def capture_progress(out_dir: pathlib.Path, scratch: pathlib.Path) -> pathlib.Path:
    """The progress page of a sync of `org:pallets` into an empty cache.

    Raises:
        ScreenshotError: the page never reads "Syncing repositories", or the server fails.
    """
    config = write_config(scratch, scratch / 'progress.sqlite3')
    with launch_chromium() as browser, running_server(config) as base:
        context, page = web_page(browser)
        try:
            page.goto(f'{base}/report?{report_query(ORG_TARGET)}')
            try:
                page.wait_for_function(
                    '(text) => document.getElementById("state")?.textContent === text',
                    arg=SYNCING,
                    timeout=PROGRESS_TIMEOUT * 1000,
                )
            except playwright.sync_api.TimeoutError:
                raise ScreenshotError(
                    f'the progress page never read "{SYNCING}" within 60 seconds'
                ) from None
            return save_png(page, out_dir / 'web/progress.png')
        finally:
            context.close()


def captured_note(today: datetime.date) -> str:
    return (
        f'Screenshots captured on {today.isoformat()} from `pallets/click` and `org:pallets` '
        f'with wambatic {wambatic.version.VERSION}, covering {SINCE} to {UNTIL}.\n'
    )


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Rebuild every screenshot of the user guide from real GitHub data.',
    )
    parser.add_argument(
        '--out',
        type=pathlib.Path,
        default=DEFAULT_OUT,
        help='image directory (default: %(default)s)',
    )
    parser.add_argument(
        '--skip-sync',
        action='store_true',
        help='use the docs cache as it is, without the network',
    )
    return parser.parse_args(argv)


def run(args: argparse.Namespace) -> None:
    """Every capture, in order.

    Raises:
        ScreenshotError: a capture fails.
    """
    if not args.skip_sync:
        check_token()
    out_dir: pathlib.Path = args.out
    with tempfile.TemporaryDirectory(prefix='wambatic-docs-') as scratch_name:
        scratch = pathlib.Path(scratch_name)
        config = write_config(scratch, DOCS_CACHE)
        with config_environment(config):
            repo = compute(REPO_TARGET, by_author=False, skip_sync=args.skip_sync)
            org = compute(ORG_TARGET, by_author=True, skip_sync=args.skip_sync)
            written: list[pathlib.Path] = []
            for results in (repo, org):
                month = next(r for r in results if r.request.granularity.value == BY)
                written += capture_terminal(month, out_dir)
                report = wambatic.reports.html.html_report(
                    results, wambatic.stats.base.Granularity(BY)
                )
                path = wambatic.reports.html.render_html(
                    report,
                    scratch / f'report-{subject_slug(month.subject)}.html',
                    'auto',
                )
                written += capture_html(path, out_dir)
            written.append(capture_cache_info(out_dir))
            written += capture_web(config, out_dir)
            written.append(capture_progress(out_dir, scratch))
    now = datetime.datetime.now(datetime.UTC)
    written.append(write_text(CAPTURED, captured_note(now.date())))
    for path in written:
        sys.stdout.write(f'{path}\n')


def main(argv: list[str] | None = None) -> int:
    """Sync the docs cache, capture everything, write docs/snippets/captured.md; return the exit
    status."""
    args = parse_args(argv)
    try:
        run(args)
    except ScreenshotError as e:
        sys.stderr.write(
            # auditme: accept[except-interpolation] the one line is the failure's own message
            f'screenshots: {wambatic.reports.service.redact_environment_token(str(e))}\n'
        )
        return 1
    except (
        wambatic.fetch.errors.FetchError,
        wambatic.reports.errors.ReportsError,
        wambatic.settings.SettingsError,
        wambatic.stats.errors.StatsError,
    ) as e:
        sys.stderr.write(
            # auditme: accept[except-interpolation] the one line is the failure's own message
            f'screenshots: {wambatic.reports.service.redact_environment_token(str(e))}\n'
        )
        return 1
    except playwright.sync_api.Error as e:
        # auditme: accept[except-interpolation] the one line is the failure's own message
        sys.stderr.write(f'screenshots: the browser failed: {str(e).splitlines()[0]}\n')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
