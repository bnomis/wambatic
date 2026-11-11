import collections.abc
import dataclasses
import pathlib
import typing

import playwright.sync_api
import pytest

import tests.fixtures.reports
import tests.reports.conftest
import wambatic.reports.assets
import wambatic.reports.figures
import wambatic.reports.html
import wambatic.settings
import wambatic.stats.base

pytestmark = pytest.mark.browser

FIRST_CHART = 'activity-commits'
DARK_SURFACE = wambatic.reports.figures.PALETTE['dark'].surface
LIGHT_SURFACE = wambatic.reports.figures.PALETTE['light'].surface


@dataclasses.dataclass
class Opened:
    page: playwright.sync_api.Page
    requests: list[str]
    problems: list[str]


@pytest.fixture
def open_report(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> collections.abc.Iterator[collections.abc.Callable[..., Opened]]:
    contexts: list[playwright.sync_api.BrowserContext] = []

    def open_page(
        theme: wambatic.settings.Theme = 'auto',
        scheme: typing.Literal['dark', 'light'] = 'light',
        report: wambatic.reports.html.HtmlReport = org_report,
    ) -> Opened:
        out = wambatic.reports.html.render_html(report, tmp_path / 'out' / 'report.html', theme)
        context = chromium.new_context(color_scheme=scheme)
        contexts.append(context)
        page = context.new_page()
        folder = (out.parent / wambatic.reports.assets.assets_folder_name()).as_uri() + '/'
        requests, problems = tests.reports.conftest.watch_page(
            page, lambda url: url == out.as_uri() or url.startswith(folder)
        )
        page.goto(out.as_uri())
        page.wait_for_selector(f'#{FIRST_CHART} .main-svg')
        return Opened(page, requests, problems)

    yield open_page
    for context in contexts:
        context.close()


def show_chart(page: playwright.sync_api.Page, key: str) -> None:
    """Open the tab holding chart `key` and wait for it to be drawn."""
    panel: str = page.evaluate(f'document.getElementById("{key}").closest("[role=tabpanel]").id')
    page.click(f'[role=tab][aria-controls={panel}]')
    page.wait_for_selector(f'#{key} .main-svg')


def keys(report: wambatic.reports.html.HtmlReport) -> list[str]:
    figures = [
        figure
        for result in report.periods.values()
        for figure in wambatic.reports.figures.build_figures(result)
    ]
    calendar = wambatic.reports.figures.build_calendar(
        report.periods[wambatic.stats.base.Granularity.DAY]
    )
    assert calendar is not None
    figures += wambatic.reports.figures.build_range_figures(report.total) + [calendar]
    return sorted({figure.key for figure in figures})


def test_the_file_opens_offline_without_errors_and_every_chart_is_drawn(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> None:
    opened = open_report()
    expected = keys(org_report)
    assert 'activity-calendar' in expected
    for key in expected:
        show_chart(opened.page, key)
        width: float = opened.page.evaluate(
            f'document.getElementById("{key}").getBoundingClientRect().width'
        )
        assert width > 0, key
    assert opened.requests == []
    assert opened.problems == []


def test_a_delivery_report_draws_every_chart_with_no_request_or_error(
    delivery_report: wambatic.reports.html.HtmlReport,
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report(report=delivery_report)
    expected = keys(delivery_report)
    assert {'delivery-runs', 'delivery-lead-time', 'delivery-time-to-restore'} <= set(expected)
    for key in expected:
        show_chart(opened.page, key)
    for granularity in wambatic.reports.html.PERIODS:
        opened.page.check(f'input[name=granularity][value={granularity}]')
        show_chart(opened.page, 'delivery-runs')
    assert opened.requests == []
    assert opened.problems == []


def test_a_popularity_report_draws_every_chart_with_no_request_or_error(
    popularity_report: wambatic.reports.html.HtmlReport,
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report(report=popularity_report)
    expected = keys(popularity_report)
    assert {'popularity-stars-added', 'popularity-languages'} <= set(expected)
    for key in expected:
        show_chart(opened.page, key)
    for granularity in wambatic.reports.html.PERIODS:
        opened.page.check(f'input[name=granularity][value={granularity}]')
        show_chart(opened.page, 'popularity-stars-total')
    assert opened.requests == []
    assert opened.problems == []


def visible_tables(page: playwright.sync_api.Page) -> set[str]:
    found = page.eval_on_selector_all(
        'table.period',
        'tables => tables.filter(t => !t.hidden).map(t => t.dataset.granularity)',
    )
    return set(found)


def test_each_granularity_shows_its_own_buckets_and_tables(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> None:
    opened = open_report()
    page = opened.page
    assert visible_tables(page) == tests.fixtures.reports.MONTH_ONLY
    for granularity in wambatic.reports.html.PERIODS:
        figures = wambatic.reports.figures.build_figures(org_report.periods[granularity])
        expected = len(figures[0].data[0]['x'])  # type: ignore[arg-type]
        page.check(f'input[name=granularity][value={granularity}]')
        page.wait_for_function(
            f'document.getElementById("{FIRST_CHART}").data[0].x.length === {expected}'
        )
        assert visible_tables(page) == {str(granularity)}
    assert opened.requests == []
    assert opened.problems == []


def surface(page: playwright.sync_api.Page) -> str:
    colour: str = page.evaluate(
        f'document.getElementById("{FIRST_CHART}")._fullLayout.paper_bgcolor'
    )
    return colour


def test_auto_follows_the_system_scheme_and_a_change_of_it(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    dark = open_report('auto', 'dark')
    assert surface(dark.page) == DARK_SURFACE
    dark.page.emulate_media(color_scheme='light')
    dark.page.wait_for_function(
        f'document.getElementById("{FIRST_CHART}")._fullLayout.paper_bgcolor === "{LIGHT_SURFACE}"'
    )
    light = open_report('auto', 'light')
    assert surface(light.page) == LIGHT_SURFACE
    assert dark.problems == [] and light.problems == []


def test_a_fixed_theme_ignores_the_system_scheme(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report('light', 'dark')
    assert surface(opened.page) == LIGHT_SURFACE
    opened.page.emulate_media(color_scheme='dark')
    opened.page.wait_for_timeout(300)
    assert surface(opened.page) == LIGHT_SURFACE
    fixed_dark = open_report('dark', 'light')
    assert surface(fixed_dark.page) == DARK_SURFACE


def test_the_series_take_the_themes_colours(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report('auto', 'dark')
    colour: str = opened.page.evaluate(
        f'document.getElementById("{FIRST_CHART}").data[0].marker.color'
    )
    assert colour == wambatic.reports.figures.PALETTE['dark'].categorical[0]


def test_a_page_opened_without_its_folder_shows_the_missing_files_notice(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    lonely = tmp_path / 'copy' / 'report.html'
    lonely.parent.mkdir()
    lonely.write_bytes(out.read_bytes())
    context = chromium.new_context()
    try:
        page = context.new_page()
        page.goto(lonely.as_uri())
        notice = page.locator('.assets-missing')
        notice.wait_for(state='visible')
        folder = wambatic.reports.assets.assets_folder_name()
        assert notice.inner_text() == (
            f"This report's files ({folder}) did not load; keep the page beside that folder."
        )
        assert page.locator('table:not([hidden])').first.is_visible()
    finally:
        context.close()


def test_a_page_opened_with_its_folder_hides_the_missing_files_notice(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report()
    assert not opened.page.locator('.assets-missing').is_visible()


def selected_tab(page: playwright.sync_api.Page) -> str:
    selected: str = page.eval_on_selector(
        '[role=tab][aria-selected=true]', 'button => button.getAttribute("aria-controls")'
    )
    return selected


def test_a_tab_first_opened_after_a_granularity_switch_shows_that_granularity(
    open_report: collections.abc.Callable[..., Opened], org_report: wambatic.reports.html.HtmlReport
) -> None:
    opened = open_report()
    page = opened.page
    page.check('input[name=granularity][value=day]')
    page.click('[role=tab][aria-controls=tab-lines]')
    figures = wambatic.reports.figures.build_figures(
        org_report.periods[wambatic.stats.base.Granularity.DAY]
    )
    lines = next(f for f in figures if f.key == 'activity-lines')
    expected = len(lines.data[0]['x'])  # type: ignore[arg-type]
    page.wait_for_function(
        f'document.getElementById("activity-lines").data[0].x.length === {expected}'
    )
    assert opened.problems == []


def test_the_first_tab_shows_on_load_and_the_arrow_keys_home_and_end_move_the_selection(
    open_report: collections.abc.Callable[..., Opened],
) -> None:
    opened = open_report()
    page = opened.page
    tabs = page.eval_on_selector_all(
        '[role=tab]', 'buttons => buttons.map(b => b.getAttribute("aria-controls"))'
    )
    assert tabs[0] == 'tab-commits' and len(tabs) >= 4
    assert selected_tab(page) == tabs[0]
    shown = page.eval_on_selector_all(
        '[role=tabpanel]', 'panels => panels.filter(p => !p.hidden).map(p => p.id)'
    )
    assert shown == [tabs[0]]
    page.focus(f'[role=tab][aria-controls={tabs[0]}]')
    page.keyboard.press('ArrowRight')
    assert selected_tab(page) == tabs[1]
    page.keyboard.press('End')
    assert selected_tab(page) == tabs[-1]
    page.keyboard.press('ArrowRight')
    assert selected_tab(page) == tabs[0]
    page.keyboard.press('ArrowLeft')
    assert selected_tab(page) == tabs[-1]
    page.keyboard.press('Home')
    assert selected_tab(page) == tabs[0]
    assert page.url.endswith('#tab-commits')
    assert opened.problems == []


def test_a_fragment_opens_on_its_tab(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    context = chromium.new_context()
    try:
        page = context.new_page()
        page.goto(f'{out.as_uri()}#tab-flow')
        page.wait_for_selector('#tab-flow:not([hidden])')
        assert selected_tab(page) == 'tab-flow'
    finally:
        context.close()


def test_with_script_disabled_every_panel_shows(
    org_report: wambatic.reports.html.HtmlReport,
    tmp_path: pathlib.Path,
    chromium: playwright.sync_api.Browser,
) -> None:
    out = wambatic.reports.html.render_html(org_report, tmp_path / 'out' / 'report.html', 'auto')
    context = chromium.new_context(java_script_enabled=False)
    try:
        page = context.new_page()
        page.goto(out.as_uri())
        panels = page.locator('[role=tabpanel]')
        assert panels.count() >= 4
        for index in range(panels.count()):
            assert panels.nth(index).is_visible()
        assert not page.locator('[role=tablist]').is_visible()
    finally:
        context.close()
