import collections.abc
import pathlib

import playwright.sync_api
import pytest

import wambatic.reports.html

# The Chromium that Claude Code's cloud environment preinstalls; Playwright's own is tried first.
PREINSTALLED_CHROMIUM = pathlib.Path('/opt/pw-browsers/chromium')


@pytest.fixture(autouse=True)
def fresh_templates() -> collections.abc.Iterator[None]:
    """Templates are read once per process; a test that makes one unreadable must see the read."""
    wambatic.reports.html.read_template.cache_clear()
    yield
    wambatic.reports.html.read_template.cache_clear()


def launch_failure(error: playwright.sync_api.Error) -> str:
    return f'no Chromium can be launched: {str(error).splitlines()[0]}'


def watch_page(
    page: playwright.sync_api.Page, allowed: collections.abc.Callable[[str], bool]
) -> tuple[list[str], list[str]]:
    """Let only the URLs `allowed` accepts load. Returns the URLs it refused and the console
    errors and page errors seen, both filled in as the page runs."""
    refused: list[str] = []
    problems: list[str] = []

    def route(route: playwright.sync_api.Route) -> None:
        if allowed(route.request.url):
            route.continue_()
        else:
            refused.append(route.request.url)
            route.abort()

    page.route('**/*', route)
    page.on('console', lambda m: problems.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: problems.append(str(e)))
    return refused, problems


@pytest.fixture
def chromium() -> collections.abc.Iterator[playwright.sync_api.Browser]:
    """A launched Chromium. It is per test, not per session: Playwright's sync API runs an event
    loop while it is open, and computing the report (`asyncio.run`) cannot happen then, so tests
    ask for their report fixtures before this one."""
    with playwright.sync_api.sync_playwright() as driver:
        try:
            browser = driver.chromium.launch()
        except playwright.sync_api.Error as first:
            if not PREINSTALLED_CHROMIUM.exists():
                pytest.skip(launch_failure(first))
            try:
                browser = driver.chromium.launch(executable_path=str(PREINSTALLED_CHROMIUM))
            except playwright.sync_api.Error as second:
                pytest.skip(launch_failure(second))
        yield browser
        browser.close()
